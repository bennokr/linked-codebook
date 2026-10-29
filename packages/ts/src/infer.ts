import { inference as rules } from './constants.ts';
import type { Datatype, Level, Profile } from './generated/types.ts';

export type Cell = string | number | boolean | null;
export interface Inferred {
  datatype: Datatype;
  level?: Level;
}
export interface Options {
  /** The header of the column; names such as id mark identifiers. */
  name?: string;
  /** True if the column has value labels, which count as evidence for categories. */
  labelled?: boolean;
}

type Kind = 'empty' | 'boolean' | 'date' | 'datetime' | 'categorical' | 'number' | 'text';

const whole = (pattern: string): RegExp => new RegExp(`^(?:${pattern})$`);
const { number: NUMBER, leading_zero: LEADING_ZERO, date: DATE, dotted_date: DOTTED, time: TIME } = Object.fromEntries(Object.entries(rules.patterns).map(([name, pattern]) => [name, whole(pattern)])) as Record<keyof typeof rules.patterns, RegExp>;
const IDENTIFIER = whole(rules.identifier_names);
const DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

const isMissing = (cell: Cell): boolean => cell === null || rules.missing.includes(String(cell));

function isNumeric(cell: Cell): boolean {
  if (typeof cell === 'number') return Number.isFinite(cell);
  return typeof cell === 'string' && NUMBER.test(cell) && !LEADING_ZERO.test(cell) && Number.isFinite(Number(cell));
}

function isDay(year: number, month: number, day: number): boolean {
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  return month >= 1 && month <= 12 && day >= 1 && day <= (DAYS[month - 1] ?? 0) + (leap && month === 2 ? 1 : 0);
}

function isTime(text: string): boolean {
  const [, hours, minutes, seconds] = TIME.exec(text) ?? [];
  return hours !== undefined && Number(hours) < 24 && Number(minutes) < 60 && Number(seconds ?? 0) < 60;
}

/** A date, or a date with a time, in ISO 8601 or day.month.year form. */
function dateKind(cell: Cell): 'date' | 'datetime' | undefined {
  const iso = DATE.exec(String(cell));
  const dotted = DOTTED.exec(String(cell));
  if (iso) return isDay(Number(iso[1]), Number(iso[2]), Number(iso[3])) && (!iso[4] || isTime(iso[4])) ? (iso[4] ? 'datetime' : 'date') : undefined;
  return dotted && isDay(Number(dotted[3]), Number(dotted[2]), Number(dotted[1])) ? 'date' : undefined;
}

const isInteger = (cell: Cell): boolean => Number.isInteger(Number(cell));

/** 1, 2, 3, and so on without a gap: a row counter. */
const isSequence = (values: Cell[], distinct: number): boolean =>
  values.length >= rules.sequence_from && distinct === values.length && values.every((value, index) => Number(value) === index + Number(values[0]));

function isProse(cell: Cell): boolean {
  const text = String(cell);
  return text.length > rules.prose.characters || /[\r\n]/.test(text) || text.trim().split(/\s+/u).length > rules.prose.words;
}

function isTextCategory(values: Cell[], distinct: number): boolean {
  const few = distinct <= rules.small || distinct / values.length <= rules.text_share;
  return values.length >= 3 && !values.some(isProse) && distinct < values.length && few;
}

function isCategorical(values: Cell[], options: Options): boolean {
  const distinct = new Set(values.map((value) => `${typeof value}:${value}`)).size;
  const { limits } = rules;
  if (IDENTIFIER.test((options.name ?? '').toLowerCase())) return false;
  if (!values.every(isNumeric)) return distinct <= limits.text && (options.labelled || isTextCategory(values, distinct));
  if (isSequence(values, distinct)) return false;
  return options.labelled ? distinct <= limits.text : values.every(isInteger) && distinct <= limits.number && distinct < values.length;
}

function kindOf(values: Cell[], options: Options): Kind {
  const dates = values.map(dateKind);
  if (!values.length) return 'empty';
  if (values.every((value) => typeof value === 'boolean')) return 'boolean';
  if (dates.every(Boolean)) return dates.includes('datetime') ? 'datetime' : 'date';
  if (isCategorical(values, options)) return 'categorical';
  return values.every(isNumeric) ? 'number' : 'text';
}

/** Proposes a datatype and a level for the values of a column. */
export function inferColumn(cells: Cell[], options: Options = {}): Inferred {
  const values = cells.filter((cell) => !isMissing(cell));
  const kind = kindOf(values, options);
  const level = (rules.level as Record<string, Level | undefined>)[kind];
  let datatype: Datatype = 'string';
  if (kind === 'boolean' || kind === 'date' || kind === 'datetime') datatype = kind;
  else if (values.length && values.every(isNumeric)) datatype = values.every(isInteger) ? 'integer' : 'number';
  return level ? { datatype, level } : { datatype };
}

/** Proposes a datatype and a level for every column of `{ name: [values] }`. */
export function infer(data: Record<string, Cell[]>): Profile {
  return { columns: Object.entries(data).map(([name, cells]) => ({ name, ...inferColumn(cells, { name }) })) };
}
