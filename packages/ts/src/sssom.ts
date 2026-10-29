import { enums, inference, sssom } from './constants.ts';
import type { Column, Mapping, Profile } from './generated/types.ts';
import { codeIri, datasetIri, variableIri } from './iri.ts';
import { clean } from './jsonld.ts';
import { local } from './read.ts';

type Prefixes = Map<string, string>;
type Row = Record<string, string>;

const NUMBER = new RegExp(`^(?:${inference.patterns.number})$`);

const cell = (value: unknown): string => String(value ?? '').replace(/[\t\r\n]+/g, ' ');

/** Shortens an IRI to a CURIE where SSSOM tools expect one, and records the prefix. */
function shorten(iri: string, prefixes: Prefixes): string {
  const obo = new RegExp(`^(?:${sssom.obo})$`).exec(iri);
  const [prefix, base] = obo
    ? [obo[1], iri.slice(0, iri.length - (obo[2] ?? '').length)]
    : (Object.entries(sssom.compact).find(([, known]) => iri.startsWith(known)) ?? []);
  if (!prefix || !base) return iri;
  prefixes.set(prefix, base);
  return `${prefix}:${iri.slice(base.length)}`;
}

function row(subject: string, label: string, mapping: Mapping, prefixes: Prefixes): string {
  const slots: Row = {
    subject_id: subject,
    subject_label: label,
    predicate_id: enums.MatchType[mapping.match_type] ?? '',
    object_id: shorten(mapping.object_id, prefixes),
    mapping_justification: sssom.justification,
    ...Object.fromEntries(
      Object.entries(sssom.fields).map(([slot, name]) => [name, cell({ ...mapping }[slot as keyof Mapping])]),
    ),
  };
  slots['mapping_date'] = (slots['mapping_date'] ?? '').slice(0, 10);
  return sssom.columns.map((name) => slots[name] ?? '').join('\t');
}

function rows(dataset: string, column: Column, prefixes: Prefixes): string[] {
  const variable = variableIri(dataset, column);
  const short = (iri: string): string =>
    iri.startsWith(`${dataset}#`) ? `${sssom.subject_prefix}:${iri.slice(dataset.length + 1)}` : iri;
  return [
    ...(column.mappings ?? []).map((mapping) => row(short(variable), column.label ?? column.name, mapping, prefixes)),
    ...(column.values ?? []).flatMap((value) =>
      (value.mappings ?? []).map((mapping) =>
        row(short(codeIri(variable, value.code)), value.label ?? value.code, mapping, prefixes),
      ),
    ),
  ];
}

/** Writes the mappings of a profile as SSSOM TSV. */
export function toSssom(profile: Profile): string {
  const dataset = datasetIri(profile);
  const prefixes: Prefixes = new Map([...Object.entries(sssom.prefixes), [sssom.subject_prefix, `${dataset}#`]]);
  const body = profile.columns.flatMap((column) => rows(dataset, column, prefixes));
  const header = [
    '#curie_map:',
    ...[...prefixes].map(([prefix, base]) => `#  ${prefix}: ${base}`),
    `#mapping_set_id: ${dataset}#mappings`,
  ];
  return `${[...header, sssom.columns.join('\t'), ...body].join('\n')}\n`;
}

function expand(value: string, prefixes: Prefixes): string {
  const [prefix = '', rest = ''] = value.split(/:(.*)/s);
  const base = prefixes.get(prefix);
  return /^(https?|urn):/.test(value) || base === undefined ? value : `${base}${rest}`;
}

/** The prefixes and the rows of an SSSOM TSV text. */
function readTable(text: string): { prefixes: Prefixes; rows: Row[] } {
  const lines = text.split(/\r?\n/).filter((line) => line.trim() !== '');
  const prefixes: Prefixes = new Map(Object.entries({ ...sssom.prefixes, ...sssom.compact }));
  for (const line of lines) {
    const [, prefix, base] = /^#\s+(\S+?):\s+(\S+)$/.exec(line) ?? [];
    if (prefix && base) prefixes.set(prefix, base);
  }
  const [header = '', ...table] = lines.filter((line) => !line.startsWith('#'));
  const names = header.split('\t');
  const rows = table.map((line) =>
    Object.fromEntries(names.map((name, index) => [name, (line.split('\t')[index] ?? '').trim()])),
  );
  return { prefixes, rows };
}

function mappingOf(row: Row, prefixes: Prefixes): Mapping | undefined {
  const predicate = local(expand(row['predicate_id'] ?? '', prefixes));
  const type = Object.entries(enums.MatchType).find(([, meaning]) => local(meaning) === predicate)?.[0];
  const fields = Object.entries(sssom.fields).map(([slot, name]) => [slot, row[name]]);
  const confidence = NUMBER.test(row[sssom.fields.confidence] ?? '') ? Number(row[sssom.fields.confidence]) : undefined;
  return type && row['object_id']
    ? (clean({
        match_type: type,
        object_id: expand(row['object_id'], prefixes),
        ...Object.fromEntries(fields),
        confidence,
      }) as unknown as Mapping)
    : undefined;
}

interface Target {
  iri: string;
  name: string;
  code?: string;
}

/** The IRIs that a subject can have: those of the variables and codes of the profile. */
function targetsOf(profile: Profile): Target[] {
  const dataset = datasetIri(profile);
  return profile.columns.flatMap((column) => {
    const variable = variableIri(dataset, column);
    const codes = (column.values ?? []).map((value) => ({
      iri: codeIri(variable, value.code),
      name: column.name,
      code: value.code,
    }));
    return [{ iri: variable, name: column.name }, ...codes];
  });
}

/** The column that maps a row, found by IRI or else by the label of the column. */
function targetOf(row: Row, prefixes: Prefixes, targets: Target[]): Target | undefined {
  const subject = expand(row['subject_id'] ?? '', prefixes);
  return (
    targets.find((candidate) => candidate.iri === subject) ??
    targets.find((candidate) => candidate.code === undefined && candidate.name === row['subject_label'])
  );
}

function mapped(column: Column, found: { target: Target; mapping: Mapping }[]): Column[] {
  const mine = found.filter((entry) => entry.target.name === column.name);
  const mappingsOf = (code?: string): Mapping[] =>
    mine.filter((entry) => entry.target.code === code).map((entry) => entry.mapping);
  const values = (column.values ?? []).map((value) => ({ code: value.code, mappings: mappingsOf(value.code) }));
  const mappings = mappingsOf();
  const coded = values.filter((value) => value.mappings.length);
  return mappings.length || coded.length
    ? [clean({ name: column.name, mappings, values: coded }) as unknown as Column]
    : [];
}

/**
 * Reads SSSOM TSV into the columns and values of a profile that it maps. A subject is found by
 * its IRI or else by the label of the column; rows with other subjects are dropped.
 */
export function fromSssom(text: string, profile: Profile): Profile {
  const { prefixes, rows: table } = readTable(text);
  const targets = targetsOf(profile);
  const found = table.flatMap((row) => {
    const target = targetOf(row, prefixes, targets);
    const mapping = mappingOf(row, prefixes);
    return target && mapping ? [{ target, mapping }] : [];
  });
  return { columns: profile.columns.flatMap((column) => mapped(column, found)) };
}
