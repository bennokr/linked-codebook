import { enums, table } from './constants.ts';
import type { Column, Profile, Value } from './generated/types.ts';
import { isNumeric } from './infer.ts';
import { clean } from './jsonld.ts';

/** Sheet name to rows; the first row holds the headers. Cells may be text, numbers, booleans or null. */
export type Tables = Record<string, unknown[][]>;
type Record_ = Record<string, unknown>;
type Sheet = 'columns' | 'values' | 'mappings' | 'dataset';

interface SheetSpec {
  title: string;
  headers: string[];
  kinds: Record<string, string>;
  required: string[];
}

const sheets = table.sheets as unknown as Record<Sheet, SheetSpec>;
const TRUE = ['true', 'yes', '1'];
const FALSE = ['false', 'no', '0'];

const key = (name: unknown): string =>
  String(name)
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');

/** A cell as text: booleans as true and false, whole numbers without a decimal point. */
const show = (value: unknown): string => String(value).trim();

function number(text: string, kind: string, where: string): number {
  if (!isNumeric(text) || (kind === 'integer' && !Number.isInteger(Number(text)))) {
    throw new Error(`${where}: '${text}' is not a${kind === 'integer' ? 'n integer' : ' number'}`);
  }
  return Number(text);
}

function boolean(text: string, where: string): boolean {
  const lowered = text.toLowerCase();
  if (![...TRUE, ...FALSE].includes(lowered)) throw new Error(`${where}: '${text}' is not true or false`);
  return TRUE.includes(lowered);
}

function member(text: string, kind: string, where: string): string {
  const allowed = Object.keys((enums as Record<string, object>)[kind] ?? {});
  if (!allowed.includes(text)) throw new Error(`${where}: '${text}' is not one of ${allowed.join(', ')}`);
  return text;
}

const blank = (raw: unknown): boolean => raw === null || raw === undefined || show(raw) === '';

/** The value of a cell of the given kind, or undefined if the cell is blank. */
function convert(raw: unknown, kind: string, where: string): unknown {
  if (blank(raw)) return undefined;
  const text = show(raw);
  if (kind === 'text') return text;
  if (kind === 'number' || kind === 'integer') return number(text, kind, where);
  return kind === 'boolean' ? boolean(text, where) : member(text, kind, where);
}

const sheetOf = (tables: Tables, sheet: Sheet): unknown[][] =>
  Object.entries(tables).find(([name]) => key(name) === key(sheets[sheet].title))?.[1] ?? [];

/** The rows of a sheet with a number (as in a spreadsheet) and the converted cells under their header. */
function records(tables: Tables, sheet: Sheet): [number, Record_][] {
  const [head = [], ...body] = sheetOf(tables, sheet);
  const heads = head.map(key);
  const spec = sheets[sheet];
  return body.flatMap((row, index): [number, Record_][] => {
    if (row.every(blank)) return [];
    const number = index + 2;
    const found = spec.headers.map((header) => {
      const at = heads.indexOf(key(header));
      return [
        header,
        convert(at < 0 ? undefined : row[at], spec.kinds[header] as string, `${spec.title} row ${number}, ${header}`),
      ];
    });
    return [[number, clean(Object.fromEntries(found))]];
  });
}

function requireHeaders(record: Record_, sheet: Sheet, number: number): void {
  for (const header of sheets[sheet].required) {
    if (record[header] === undefined) throw new Error(`${sheets[sheet].title} row ${number}: ${header} is required`);
  }
}

function readColumns(tables: Tables): Map<string, Column> {
  const columns = new Map<string, Column>();
  for (const [number, { missing_low: low, missing_high: high, ...record }] of records(tables, 'columns')) {
    requireHeaders(record, 'columns', number);
    if ((low === undefined) !== (high === undefined)) {
      throw new Error(`Columns row ${number}: missing_low and missing_high go together`);
    }
    const name = record['name'] as string;
    if (columns.has(name)) throw new Error(`Columns row ${number}: column ${name} is listed twice`);
    columns.set(name, clean({ ...record, missing_range: clean({ low, high }) }) as unknown as Column);
  }
  if (!columns.size) throw new Error('no columns found: the Columns sheet needs a name header and one row per column');
  return columns;
}

function columnOf(columns: Map<string, Column>, record: Record_, sheet: Sheet, number: number): Column {
  const column = columns.get(record['column'] as string);
  if (!column) {
    throw new Error(`${sheets[sheet].title} row ${number}: column ${record['column']} is not on the Columns sheet`);
  }
  return column;
}

function readValues(tables: Tables, columns: Map<string, Column>): void {
  for (const [number, record] of records(tables, 'values')) {
    requireHeaders(record, 'values', number);
    const column = columnOf(columns, record, 'values', number);
    const value = clean({ code: record['code'], label: record['label'], description: record['description'] });
    if (record['missing'] && Object.keys(value).length === 1) {
      (column.missing_values ??= []).push(record['code'] as string);
    } else {
      (column.values ??= []).push({ ...value, ...clean({ missing: record['missing'] }) } as unknown as Value);
    }
  }
}

function readMappings(tables: Tables, columns: Map<string, Column>): void {
  for (const [number, { column: _column, code, ...mapping }] of records(tables, 'mappings')) {
    const record = { column: _column, code, ...mapping };
    requireHeaders(record, 'mappings', number);
    const column = columnOf(columns, record, 'mappings', number);
    const owner: { mappings?: unknown[] } | undefined =
      code === undefined ? column : column.values?.find((value) => value.code === code);
    if (!owner) throw new Error(`Mappings row ${number}: ${code} is not a code of ${_column} on the Values sheet`);
    (owner.mappings ??= []).push(mapping);
  }
}

function readDataset(tables: Tables): Record_ {
  const { headers: keys, kinds } = sheets.dataset;
  const found: Record_ = {};
  sheetOf(tables, 'dataset')
    .slice(1)
    .forEach((row, index) => {
      const name = keys.find((candidate) => row[0] !== undefined && key(row[0]) === key(candidate));
      if (name && row.length > 1) found[name] = convert(row[1], kinds[name] as string, `Dataset row ${index + 2}`);
    });
  return clean(found);
}

/**
 * Reads a profile from tables: sheet name to rows, the first row holding the headers. Cells may be text, numbers,
 * booleans or null. Throws an error that names the sheet and row for a cell that does not fit its header or a row
 * that refers to something that does not exist.
 */
export function fromTables(tables: Tables): Profile {
  const columns = readColumns(tables);
  readValues(tables, columns);
  readMappings(tables, columns);
  return { ...readDataset(tables), columns: [...columns.values()] } as unknown as Profile;
}

/** What a reader does not use: sheets and headers it does not know, and headers of the earlier workbook. */
export function tableWarnings(tables: Tables): string[] {
  const titles = new Map((Object.keys(sheets) as Sheet[]).map((sheet) => [key(sheets[sheet].title), sheet]));
  return Object.entries(tables).flatMap(([name, rows]) => {
    const sheet = titles.get(key(name));
    if (!sheet) return [`sheet ${name} is not used`];
    const known = [...sheets[sheet].headers, ...(sheet === 'dataset' ? ['key', 'value'] : [])].map(key);
    return (rows[0] ?? [])
      .filter((head) => head !== null && head !== undefined)
      .map(show)
      .filter((head) => !known.includes(key(head)))
      .map((head) => `${sheets[sheet].title} header ${head} is not used`);
  });
}

const valueRecord = (column: string, value: Value): Record_ =>
  clean({ column, code: value.code, label: value.label, description: value.description, missing: value.missing });

function columnRecord(column: Column): Record_ {
  const { missing_range: range, ...slots } = column as unknown as Record_ & {
    missing_range?: { low: number; high: number };
  };
  const picked = Object.fromEntries(sheets.columns.headers.map((header) => [header, slots[header]]));
  return clean({ ...picked, missing_low: range?.low, missing_high: range?.high });
}

function valueRecords(column: Column): Record_[] {
  return [
    ...(column.values ?? []).map((value) => valueRecord(column.name, value)),
    ...(column.missing_values ?? []).map((code) => ({ column: column.name, code, missing: true })),
  ];
}

function mappingRecords(column: Column): Record_[] {
  const owners: [Record_, { mappings?: object[] }][] = [
    [{}, column],
    ...(column.values ?? []).map((value): [Record_, { mappings?: object[] }] => [{ code: value.code }, value]),
  ];
  return owners.flatMap(([owner, holder]) =>
    (holder.mappings ?? []).map((mapping) => clean({ column: column.name, ...owner, ...mapping })),
  );
}

/** A sheet of the headers that have a cell somewhere, in the order of the specification. */
function grid(sheet: Sheet, rows: Record_[]): string[][] {
  const spec = sheets[sheet];
  const heads = spec.headers.filter((head) => spec.required.includes(head) || rows.some((row) => head in row));
  return [heads, ...rows.map((row) => heads.map((head) => (head in row ? show(row[head]) : '')))];
}

/** Writes a profile as tables. Observed counts are left out: they describe one copy of the data. */
export function toTables(profile: Profile): Tables {
  const { columns } = profile;
  const parts: [Sheet, Record_[]][] = [
    ['columns', columns.map(columnRecord)],
    ['values', columns.flatMap(valueRecords)],
    ['mappings', columns.flatMap(mappingRecords)],
  ];
  const tables: Tables = {};
  for (const [sheet, rows] of parts) {
    if (rows.length || sheet === 'columns') tables[sheets[sheet].title] = grid(sheet, rows);
  }
  const dataset = sheets.dataset.headers
    .filter((name) => (profile as unknown as Record_)[name] !== undefined)
    .map((name) => [name, show((profile as unknown as Record_)[name])]);
  if (dataset.length) tables[sheets.dataset.title] = [['key', 'value'], ...dataset];
  return tables;
}
