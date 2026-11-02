import { enums, jsonld } from './constants.ts';
import type { Column, Mapping, Profile } from './generated/types.ts';
import { codeIri, datasetIri, fill, variableIri } from './iri.ts';

export type Node = Record<string, unknown>;

const { keys, node_keys: nodeKeys, types } = jsonld;

const isEmpty = (value: unknown): boolean =>
  value === undefined ||
  value === '' ||
  (Array.isArray(value) && value.length === 0) ||
  (typeof value === 'object' && value !== null && !Array.isArray(value) && Object.keys(value).length === 0);

/** Drops the entries that have no value: nothing, empty text, empty lists and empty objects. */
export const clean = (node: Node): Node =>
  Object.fromEntries(Object.entries(node).filter(([, value]) => !isEmpty(value)));

export const pick = (source: object, slots: Record<string, string>): Node =>
  clean(Object.fromEntries(Object.entries(slots).map(([slot, key]) => [key, (source as Node)[slot]])));

/** Only approved links are asserted; a link is approved when it has a reviewer. */
function links(mappings: Mapping[] = []): Record<string, string[]> {
  const result: Record<string, string[]> = {};
  for (const mapping of mappings.filter((candidate) => candidate.reviewer_id)) {
    (result[`${mapping.match_type}Match`] ??= []).push(mapping.object_id);
  }
  return result;
}

function concept(id: string, label?: string, definition?: string, mappings?: Mapping[]): Node {
  return clean({
    '@id': id,
    '@type': types.concept,
    [nodeKeys.label]: label,
    [nodeKeys.definition]: definition,
    ...links(mappings),
  });
}

function codeBook(column: Column, variable: string): Node | undefined {
  const scheme = fill('scheme', { variable });
  const ordinal = column.level === 'ordinal';
  const top = (column.values ?? []).map((value, index) =>
    clean({
      ...concept(codeIri(variable, value.code), value.label, value.description, value.mappings),
      [nodeKeys.in_scheme]: { '@id': scheme },
      [nodeKeys.notation]: value.code,
      [nodeKeys.position]: ordinal ? index + 1 : undefined,
    }),
  );
  return top.length ? { '@id': scheme, '@type': types.scheme, [nodeKeys.top]: top } : undefined;
}

/** The concept of the variable of a column, with the page that documents it. */
const variableNode = (column: Column, id: string, label: string): Node =>
  clean({
    ...concept(id, label, column.description, column.mappings),
    [nodeKeys.source]: column.source ? { '@id': column.source } : undefined,
  });

/** Properties that no vocabulary defines, so they are written as plain keys. */
const extensions = (column: Column): Node => ({
  missingRange: column.missing_range,
  codeBookClosed: column.closed || undefined,
  appliesWhen: column.applies_when,
});

function columnNode(dataset: string, column: Column): Node {
  const variable = variableIri(dataset, column);
  const label = column.label ?? column.name;
  const nulls = [
    ...(column.missing_values ?? []),
    ...(column.values ?? []).filter((value) => value.missing).map((value) => value.code),
  ];
  const ids = { dataset, name: column.name };
  return clean({
    '@id': fill('column', ids),
    '@type': types.column,
    ...pick(column, keys.column),
    titles: label,
    nullValues: nulls,
    ...extensions(column),
    columnProperty: clean({
      '@id': fill('property', ids),
      '@type': types.property,
      hasVariable: variableNode(column, variable, label),
      hasUnit: column.unit_iri,
      unitText: column.unit,
      hasCodeBook: codeBook(column, variable),
    }),
    summaryStatistics: statistics(fill('statistics', ids), {
      statisticalDataType: column.level && enums.Level[column.level],
      columnCompleteness: column.completeness,
    }),
  });
}

/** A node of summary statistics, or nothing if there are no statistics. */
function statistics(id: string, properties: Node): Node | undefined {
  const node = clean(properties);
  return Object.keys(node).length ? { '@id': id, '@type': types.statistics, ...node } : undefined;
}

/** Writes a profile as JSON-LD with the DSV ontology. */
export function build(profile: Profile): Node {
  const dataset = datasetIri(profile);
  const license = /^https?:/.test(profile.license ?? '') ? { license: profile.license } : { rights: profile.license };
  return clean({
    '@context': jsonld.context,
    '@id': dataset,
    '@type': types.dataset,
    ...pick(profile, keys.dataset),
    ...license,
    summaryStatistics: statistics(fill('dataset_statistics', { dataset }), {
      numberOfRows: profile.rows,
      numberOfColumns: profile.rows === undefined ? undefined : profile.columns.length,
    }),
    datasetSchema: {
      '@id': fill('schema', { dataset }),
      '@type': types.schema,
      columns: profile.columns.map((column) => columnNode(dataset, column)),
    },
  });
}
