import { inference as rules } from './constants.ts';
import type { Count, Datatype, Level, Profile } from './generated/types.ts';

export type Cell = string | number | boolean | null;
export interface Inferred {
  datatype: Datatype;
  level?: Level;
}
export interface Options {
  /** The header of the column; names such as id mark identifiers. */
  name?: string;
  /** Whether the column is an identifier, if that is known. Replaces the decision from the name. */
  identifier?: boolean;
  /** True if the column has value labels, which count as evidence for categories. */
  labelled?: boolean;
  /** Replaces the most distinct values of a text or numeric column that can still be categories. */
  limits?: Partial<Record<'text' | 'number', number>>;
}

type Kind = 'empty' | 'boolean' | 'date' | 'datetime' | 'categorical' | 'number' | 'text';

const whole = (pattern: string): RegExp => new RegExp(`^(?:${pattern})$`);
const {
  number: NUMBER,
  leading_zero: LEADING_ZERO,
  date: DATE,
  dotted_date: DOTTED,
  time: TIME,
} = Object.fromEntries(Object.entries(rules.patterns).map(([name, pattern]) => [name, whole(pattern)])) as Record<
  keyof typeof rules.patterns,
  RegExp
>;
const IDENTIFIER = whole(rules.identifier_names);
const DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

const isMissing = (cell: Cell): boolean => cell === null || rules.missing.includes(String(cell));

export function isNumeric(cell: Cell): boolean {
  if (typeof cell === 'number') return Number.isFinite(cell);
  return typeof cell === 'string' && NUMBER.test(cell) && !LEADING_ZERO.test(cell) && Number.isFinite(Number(cell));
}

function daysIn(year: number, month: number): number {
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  return month === 2 && leap ? 29 : (DAYS[month - 1] ?? 0);
}

const isDay = (year: number, month: number, day: number): boolean => day >= 1 && day <= daysIn(year, month);

function isTime(text: string): boolean {
  const [, hours, minutes, seconds] = TIME.exec(text) ?? [];
  return hours !== undefined && Number(hours) < 24 && Number(minutes) < 60 && Number(seconds ?? 0) < 60;
}

/** A date, or a date with a time, in ISO 8601 or day.month.year form. */
function dateKind(cell: Cell): 'date' | 'datetime' | undefined {
  const iso = DATE.exec(String(cell));
  const dotted = DOTTED.exec(String(cell));
  if (!iso) return dotted && isDay(Number(dotted[3]), Number(dotted[2]), Number(dotted[1])) ? 'date' : undefined;
  const time = iso[4];
  if (!isDay(Number(iso[1]), Number(iso[2]), Number(iso[3])) || (time && !isTime(time))) return undefined;
  return time ? 'datetime' : 'date';
}

const isInteger = (cell: Cell): boolean => Number.isInteger(Number(cell));

/** 1, 2, 3, and so on without a gap: a row counter. */
const isSequence = (values: Cell[], distinct: number): boolean =>
  values.length >= rules.sequence_from &&
  distinct === values.length &&
  values.every((value, index) => Number(value) === index + Number(values[0]));

function isProse(cell: Cell): boolean {
  const text = String(cell);
  return (
    text.length > rules.prose.characters || /[\r\n]/.test(text) || text.trim().split(/\s+/u).length > rules.prose.words
  );
}

function isTextCategory(values: Cell[], distinct: number): boolean {
  const few = distinct <= rules.small || distinct / values.length <= rules.text_share;
  return values.length >= 3 && !values.some(isProse) && distinct < values.length && few;
}

const distinctCount = (values: Cell[]): number => new Set(values.map((value) => `${typeof value}:${value}`)).size;

const isCodeList = (values: Cell[], distinct: number, limit: number): boolean =>
  values.every(isInteger) && distinct <= limit && distinct < values.length;

const isIdentifier = (options: Options): boolean =>
  options.identifier ?? IDENTIFIER.test((options.name ?? '').toLowerCase());

function isCategorical(values: Cell[], options: Options): boolean {
  const distinct = distinctCount(values);
  const limits = { ...rules.limits, ...options.limits };
  const few = distinct <= limits.text;
  if (isIdentifier(options)) return false;
  if (!values.every(isNumeric)) return few && (options.labelled || isTextCategory(values, distinct));
  if (isSequence(values, distinct)) return false;
  return options.labelled ? few : isCodeList(values, distinct, limits.number);
}

function kindOf(values: Cell[], options: Options): Kind {
  const dates = values.map(dateKind);
  if (!values.length) return 'empty';
  if (values.every((value) => typeof value === 'boolean')) return 'boolean';
  if (dates.every(Boolean)) return dates.includes('datetime') ? 'datetime' : 'date';
  if (isCategorical(values, options)) return 'categorical';
  return values.every(isNumeric) ? 'number' : 'text';
}

function datatypeOf(kind: Kind, values: Cell[]): Datatype {
  if (kind === 'boolean' || kind === 'date' || kind === 'datetime') return kind;
  if (!values.length || !values.every(isNumeric)) return 'string';
  return values.every(isInteger) ? 'integer' : 'number';
}

/** Proposes a datatype and a level for the values of a column. */
export function inferColumn(cells: Cell[], options: Options = {}): Inferred {
  const values = cells.filter((cell) => !isMissing(cell));
  const kind = kindOf(values, options);
  const level = (rules.level as Record<string, Level | undefined>)[kind];
  return level ? { datatype: datatypeOf(kind, values), level } : { datatype: datatypeOf(kind, values) };
}

/** The codes of a column with how often each occurs, in order of first occurrence. Missing values are left out. */
export function observe(cells: Cell[]): Count[] {
  const counts = new Map<string, number>();
  for (const cell of cells.filter((value) => !isMissing(value))) {
    const code = typeof cell === 'string' ? cell : JSON.stringify(cell);
    counts.set(code, (counts.get(code) ?? 0) + 1);
  }
  return [...counts].map(([code, count]) => ({ code, count }));
}

/** Proposes a datatype and a level for every column of `{ name: [values] }`, with the codes of categorical columns. */
export function infer(data: Record<string, Cell[]>): Profile {
  const columnOf = (name: string, cells: Cell[]) => {
    const inferred = inferColumn(cells, { name });
    return inferred.level === 'categorical' ? { name, ...inferred, observed: observe(cells) } : { name, ...inferred };
  };
  return { columns: Object.entries(data).map(([name, cells]) => columnOf(name, cells)) };
}
