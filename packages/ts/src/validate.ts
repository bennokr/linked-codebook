import { jsonld, schema, vocabulary } from './constants.ts';
import { local } from './read.ts';

type Schema = { $ref?: string; type?: string; enum?: string[]; items?: Schema; properties?: Record<string, Schema>; required?: string[]; additionalProperties?: boolean; minimum?: number; maximum?: number };

const definitions = schema.$defs as unknown as Record<string, Schema>;
const kindOf = (value: unknown): string => (Array.isArray(value) ? 'array' : value === null ? 'null' : typeof value);

/** Errors of a value against the JSON Schema, which is generated from the model. */
function conform(value: unknown, rule: Schema, path: string): string[] {
  const resolved = rule.$ref ? { ...definitions[local(rule.$ref)], ...rule } : rule;
  const kind = kindOf(value);
  if (resolved.type && kind !== resolved.type) return [`${path}: expected ${resolved.type}`];
  if (resolved.enum && !resolved.enum.includes(value as string)) return [`${path}: ${String(value)} is not one of ${resolved.enum.join(', ')}`];
  if (typeof value === 'number' && (value < (resolved.minimum ?? -Infinity) || value > (resolved.maximum ?? Infinity))) return [`${path}: out of range`];
  const members = Object.entries((value ?? {}) as Record<string, unknown>);
  const own = kind === 'object' ? members.flatMap(([key, member]) => (resolved.properties?.[key] ? conform(member, resolved.properties[key], `${path}/${key}`) : [`${path}/${key}: unknown property`])) : [];
  const missing = kind === 'object' ? (resolved.required ?? []).filter((key) => !(key in (value as object))).map((key) => `${path}: ${key} is required`) : [];
  const listed = kind === 'array' && resolved.items ? (value as unknown[]).flatMap((item, index) => conform(item, resolved.items as Schema, `${path}/${index}`)) : [];
  return [...missing, ...own, ...listed];
}

/** Names that must not occur twice in a list. */
function repeated(profile: Record<string, unknown>): string[] {
  const columns = (profile['columns'] ?? []) as { name?: string; values?: { code?: string }[] }[];
  const twice = (names: (string | undefined)[]): string[] => names.filter((name, index) => name !== undefined && names.indexOf(name) !== index) as string[];
  return [
    ...twice(columns.map((column) => column.name)).map((name) => `column ${name} occurs twice`),
    ...columns.flatMap((column) => twice((column.values ?? []).map((value) => value.code)).map((code) => `${column.name}: code ${code} occurs twice`)),
  ];
}

const namespaces = Object.fromEntries(Object.entries(vocabulary.vocabularies).map(([prefix, entry]) => [prefix, entry]));

type Context = Record<string, string | { '@id': string }>;

/** Expands a key or type of JSON-LD to an IRI through the context. */
function expand(term: string, context: Context): string {
  const entry = context[term];
  const target = typeof entry === 'object' ? entry['@id'] : (entry ?? term);
  const [prefix = '', rest = ''] = target.split(/:(.*)/s);
  const base = context[prefix];
  return typeof base === 'string' && base !== target && rest !== '' ? `${base}${rest}` : target;
}

const known = new Set(Object.values(vocabulary.vocabularies).flatMap((entry) => Object.keys(entry.terms).map((term) => `${entry.namespace}${term}`)));

/** Errors for terms of a JSON-LD document that no pinned vocabulary defines. */
function undefinedTerms(value: unknown, context: Context): string[] {
  if (Array.isArray(value)) return value.flatMap((item) => undefinedTerms(item, context));
  if (typeof value !== 'object' || value === null) return [];
  const node = value as Record<string, unknown>;
  const types = [node['@type'] ?? []].flat().map(String);
  const keys = Object.keys(node).filter((key) => !key.startsWith('@') && !jsonld.extensions.includes(key));
  const unknown = [...keys, ...types].filter((term) => !known.has(expand(term, context)) && !(jsonld.accepted as string[]).includes(term));
  const below = Object.entries(node).filter(([key]) => key !== '@context').flatMap(([, child]) => undefinedTerms(child, context));
  return [...unknown.map((term) => `${term}: not defined by a pinned vocabulary`), ...below];
}

/** Checks a profile against the model, or a JSON-LD document against the vocabularies. */
export function validate(document: unknown): string[] {
  const record = (typeof document === 'object' && document !== null ? document : {}) as Record<string, unknown>;
  if (!('@context' in record)) return [...new Set([...conform(document, schema as Schema, ''), ...repeated(record)])];
  const context = record['@context'];
  const own = typeof context === 'object' && context !== null && !Array.isArray(context);
  return [...new Set(undefinedTerms(document, (own ? context : jsonld.context) as Context))];
}
