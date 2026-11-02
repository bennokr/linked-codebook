import { redcap } from './constants.ts';
import type { Column, Profile, Value } from './generated/types.ts';
import { clean } from './jsonld.ts';

type Row = Record<string, string>;

const FIELD = /("(?:[^"]|"")*"|[^,"\r\n]*)(,|\r\n|\n|\r|$)/y;
const BOM = String.fromCharCode(0xfeff);
const WHOLE_NUMBER = new RegExp(`^(?:${redcap.integer_code})$`);

const normalize = (header: string): string => header.toLowerCase().replace(/[^a-z0-9]/g, '');
const unquote = (field: string): string => (field.startsWith('"') ? field.slice(1, -1).replaceAll('""', '"') : field);

/** The fields of CSV text with the separator that ends each. */
function tokens(source: string): [string, string][] {
  const found: [string, string][] = [];
  FIELD.lastIndex = 0;
  while (FIELD.lastIndex < source.length) {
    const match = FIELD.exec(source);
    if (!match) throw new Error('malformed CSV');
    found.push([unquote(match[1] ?? ''), match[2] ?? '']);
  }
  return found;
}

/** The rows of CSV text: fields may be quoted and then hold commas, doubled quotes and line breaks. */
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [[]];
  for (const [field, end] of tokens(text.startsWith(BOM) ? text.slice(1) : text)) {
    rows.at(-1)?.push(field);
    if (end && end !== ',') rows.push([]);
  }
  return rows.filter((row) => row.some((cell) => cell.trim()));
}

/** The dictionary rows, with the columns that are used under the names of the specification. */
function rowsOf(text: string): Row[] {
  const [head = [], ...body] = parseCsv(text);
  const keys = head.map(normalize);
  return body.map((cells) =>
    Object.fromEntries(
      Object.entries(redcap.headers).map(([slot, names]) => [
        slot,
        (cells[keys.findIndex((key) => names.includes(key))] ?? '').trim(),
      ]),
    ),
  );
}

/** Choices written as "1, Male | 2, Female". */
function choicesOf(text: string): Value[] {
  return text
    .split('|')
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const comma = part.indexOf(',');
      const code = (comma < 0 ? part : part.slice(0, comma)).trim();
      return clean({ code, label: comma < 0 ? undefined : part.slice(comma + 1).trim() }) as unknown as Value;
    });
}

function kindOf(type: string, validation: string): Pick<Column, 'datatype' | 'level'> {
  const fixed = (redcap.types as Record<string, Pick<Column, 'datatype' | 'level'>>)[type];
  const hit = redcap.validation.find(({ pattern }) => new RegExp(`^(?:${pattern})$`).test(validation));
  return (fixed ?? (hit ? clean({ datatype: hit.datatype, level: hit.level }) : { datatype: 'string' })) as Pick<
    Column,
    'datatype' | 'level'
  >;
}

const listed = (pairs: string[][]): Value[] => pairs.map(([code = '', label]) => ({ code, label }));

function categorical(name: string, values: Value[], common: Partial<Column>): Column {
  const whole = values.every((value) => WHOLE_NUMBER.test(value.code));
  return clean({
    name,
    ...common,
    datatype: whole ? 'integer' : 'string',
    level: 'categorical',
    values,
    closed: true,
  }) as unknown as Column;
}

const optional = (value: string | undefined): string | undefined => value || undefined;

function checkboxColumns(row: Row, common: Partial<Column>): Column[] {
  return choicesOf(row['choices'] ?? '').map((choice) => {
    const name = `${row['name']}___${choice.code.toLowerCase().replace(/[^a-z0-9_]/g, '_')}`;
    const label = `${row['label']} (${choice.label ?? choice.code})`;
    return categorical(name, listed(redcap.checkbox_values), { ...common, label });
  });
}

function valuesOf(row: Row): Value[] {
  const type = row['type'] ?? '';
  const builtin = (redcap.builtin as Record<string, string[][]>)[type];
  if (builtin) return listed(builtin);
  return redcap.choice_types.includes(type) ? choicesOf(row['choices'] ?? '') : [];
}

function columnsOf(row: Row): Column[] {
  const { name = '', type = '' } = row;
  if (!name || redcap.skipped.includes(type)) return [];
  const common = {
    label: optional(row['label']),
    description: optional(row['note']),
    applies_when: optional(row['branching']),
  };
  if (type === redcap.checkbox) return checkboxColumns(row, common);
  const values = valuesOf(row);
  if (values.length) return [categorical(name, values, common)];
  return [clean({ name, ...common, ...kindOf(type, row['validation'] ?? '') }) as unknown as Column];
}

/** Reads a REDCap data dictionary (CSV) into a profile. */
export function fromRedcap(text: string): Profile {
  const columns = rowsOf(text).flatMap(columnsOf);
  if (!columns.length) throw new Error('no fields found');
  return { columns };
}
