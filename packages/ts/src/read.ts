import { enums, jsonld } from './constants.ts';
import type { Column, Datatype, Level, Mapping, Profile, Value } from './generated/types.ts';
import { isNumeric } from './infer.ts';
import { clean, type Node } from './jsonld.ts';
import { datasetIri, variableIri } from './iri.ts';

const { aliases, datatype_aliases: datatypeAliases, keys, node_keys: nodeKeys } = jsonld;

const isNode = (value: unknown): value is Node => typeof value === 'object' && value !== null && !Array.isArray(value);

/** The name of a term without its prefix or namespace, so that dct:title, dcterms:title and title are alike. */
export const local = (name: string): string => name.split(/[:#/]/).pop() ?? name;

const items = (value: unknown): unknown[] =>
  [value ?? []].flat().flatMap((item) => (isNode(item) && '@list' in item ? items(item['@list']) : [item]));

const named = (node: Node): Node =>
  Object.fromEntries(Object.entries(node).map(([key, value]) => [key.startsWith('@') ? key : local(key), value]));

/** Every object of the document, with unprefixed keys. */
function collect(document: unknown): Node[] {
  if (Array.isArray(document)) return document.flatMap(collect);
  if (!isNode(document)) return [];
  const below = Object.entries(document)
    .filter(([key]) => key !== '@context')
    .flatMap(([, value]) => collect(value));
  return [named(document), ...below];
}

/** The node a value refers to, completed with the other nodes of the document that have its id. */
function resolve(nodes: Node[], value: unknown): Node {
  const first = items(value)[0];
  const node = isNode(first) ? named(first) : { '@id': first };
  const same = nodes.filter((candidate) => node['@id'] !== undefined && candidate['@id'] === node['@id']);
  return Object.assign({}, ...same, node) as Node;
}

function get(node: Node, term: string): unknown {
  return [term, ...((aliases as Record<string, string[]>)[term] ?? [])]
    .map((name) => node[name])
    .find((value) => value !== undefined);
}

function text(value: unknown): string | undefined {
  const first = items(value)[0];
  const result = isNode(first) ? (first['@value'] ?? first['@id']) : first;
  return result === undefined || result === null ? undefined : String(result);
}

function numberOf(value: unknown): number | undefined {
  const found = text(value);
  return found !== undefined && isNumeric(found) ? Number(found) : undefined;
}

function datatypeOf(value: unknown): Datatype | undefined {
  const first = items(value)[0];
  const name = local(text(isNode(first) ? first['base'] : first) ?? '');
  const known = (datatypeAliases as Record<string, string>)[name] ?? name;
  return known in enums.Datatype ? (known as Datatype) : undefined;
}

function levelOf(value: unknown): Level | undefined {
  const name = local(text(value) ?? '');
  return Object.entries(enums.Level).find(([, meaning]) => local(meaning) === name)?.[0] as Level | undefined;
}

function mappingsOf(concept: Node): Mapping[] {
  return Object.keys(enums.MatchType).flatMap((type) =>
    items(get(concept, `${type}Match`))
      .map(text)
      .flatMap((id) => (id ? [{ match_type: type, object_id: id, reviewer_id: jsonld.imported_reviewer }] : [])),
  ) as Mapping[];
}

function valuesOf(nodes: Node[], property: Node, nulls: string[]): Value[] {
  const scheme = resolve(nodes, get(property, 'hasCodeBook'));
  return items(scheme[local(nodeKeys.top)]).map((item) => {
    const concept = resolve(nodes, item);
    const code = text(concept[local(nodeKeys.notation)]) ?? '';
    return clean({
      code,
      label: text(concept[local(nodeKeys.label)]),
      description: text(concept[local(nodeKeys.definition)]),
      missing: nulls.includes(code) || undefined,
      mappings: mappingsOf(concept),
    }) as unknown as Value;
  });
}

function rangeOf(value: unknown): Column['missing_range'] {
  const [low, high] = isNode(value) ? [value['low'], value['high']] : items(value);
  return typeof low === 'number' && typeof high === 'number' ? { low, high } : undefined;
}

function columnOf(nodes: Node[], dataset: string, node: Node): Column {
  const property = resolve(nodes, get(node, 'columnProperty'));
  const variable = resolve(nodes, get(property, 'hasVariable'));
  const statistics = resolve(nodes, get(node, 'summaryStatistics') ?? get(property, 'summaryStatistics'));
  const title = text(get(node, 'titles')) ?? text(variable[local(nodeKeys.label)]);
  const name = text(get(node, 'name')) ?? title ?? '';
  const nulls = items(get(node, 'nullValues')).map(String);
  const values = valuesOf(nodes, property, nulls);
  const id = text(variable['@id']);
  return clean({
    name,
    label: title === name ? undefined : title,
    datatype: datatypeOf(get(node, 'datatype')),
    description: text(variable[local(nodeKeys.definition)]) ?? text(get(node, 'description')),
    level: levelOf(get(statistics, 'statisticalDataType')),
    completeness: numberOf(get(statistics, 'columnCompleteness')),
    unit: text(get(property, 'unitText')),
    unit_iri: text(get(property, 'hasUnit')),
    variable: id === variableIri(dataset, { name }) ? undefined : id,
    values,
    missing_values: nulls.filter((code) => !values.some((value) => value.code === code)),
    missing_range: rangeOf(get(node, 'missingRange')),
    mappings: mappingsOf(variable),
  }) as unknown as Column;
}

/** Reads DSV JSON-LD, nested or as a flat graph, into a profile. */
export function parse(document: unknown): Profile {
  const nodes = collect(document);
  const dataset = nodes.find((node) => get(node, 'datasetSchema') !== undefined) ?? {};
  const schema = resolve(nodes, get(dataset, 'datasetSchema'));
  const columns = items(get(schema, 'columns')).map((item) => resolve(nodes, item));
  if (!columns.length) throw new Error('no columns found');
  const profile = clean({
    ...Object.fromEntries(Object.entries(keys.dataset).map(([slot, key]) => [slot, text(get(dataset, key))])),
    license: text(get(dataset, 'license')) ?? text(get(dataset, 'rights')),
    rows: numberOf(get(resolve(nodes, get(dataset, 'summaryStatistics')), 'numberOfRows')),
  }) as unknown as Profile;
  const base = text(dataset['@id']) ?? datasetIri(profile);
  return { ...profile, columns: columns.map((column) => columnOf(nodes, base, column)) };
}
