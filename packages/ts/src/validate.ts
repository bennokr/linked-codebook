import { jsonld, schema, vocabulary } from './constants.ts';
import { local } from './read.ts';

interface Schema {
  $ref?: string;
  type?: string;
  enum?: string[];
  items?: Schema;
  properties?: Record<string, Schema>;
  required?: string[];
  minimum?: number;
  maximum?: number;
}

const definitions = schema.$defs as unknown as Record<string, Schema>;

function kindOf(value: unknown): string {
  if (Array.isArray(value)) return 'array';
  return value === null ? 'null' : typeof value;
}

/** Whether a value has the type, which may be absent. An integer is a number without a fraction. */
const hasType = (value: unknown, type?: string): boolean =>
  !type || kindOf(value) === type || (type === 'integer' && Number.isInteger(value));

function checkScalar(value: unknown, rule: Schema, path: string): string[] {
  if (rule.enum && !rule.enum.includes(value as string))
    return [`${path}: ${String(value)} is not one of ${rule.enum.join(', ')}`];
  const outside =
    typeof value === 'number' && (value < (rule.minimum ?? -Infinity) || value > (rule.maximum ?? Infinity));
  return outside ? [`${path}: out of range`] : [];
}

function checkObject(value: Record<string, unknown>, rule: Schema, path: string): string[] {
  const missing = (rule.required ?? []).filter((key) => !(key in value)).map((key) => `${path}: ${key} is required`);
  const own = Object.entries(value).flatMap(([key, member]) => {
    const property = rule.properties?.[key];
    return property ? conform(member, property, `${path}/${key}`) : [`${path}/${key}: unknown property`];
  });
  return [...missing, ...own];
}

/** Errors of a value against the JSON Schema, which is generated from the model. */
function conform(value: unknown, rule: Schema, path: string): string[] {
  const resolved = rule.$ref ? { ...definitions[local(rule.$ref)], ...rule } : rule;
  const kind = kindOf(value);
  if (!hasType(value, resolved.type)) return [`${path}: expected ${resolved.type}`];
  if (kind === 'object') return checkObject(value as Record<string, unknown>, resolved, path);
  if (kind === 'array' && resolved.items)
    return (value as unknown[]).flatMap((item, index) => conform(item, resolved.items as Schema, `${path}/${index}`));
  return checkScalar(value, resolved, path);
}

interface Listed {
  name?: string;
  closed?: boolean;
  values?: { code?: string }[];
  observed?: { code?: string }[];
  missing_values?: string[];
}

/** Codes found in the data that a closed list does not allow. */
function unlisted(column: Listed): string[] {
  const allowed = [...(column.values ?? []).map((value) => value.code), ...(column.missing_values ?? [])];
  const found = column.closed ? (column.observed ?? []).map((entry) => entry.code) : [];
  return found
    .filter((code) => !allowed.includes(code))
    .map((code) => `${column.name}: code ${code} occurs in the data but not in the closed list`);
}

/** Names that must not occur twice in a list, and codes outside a closed list. */
function repeated(profile: Record<string, unknown>): string[] {
  const columns = (profile['columns'] ?? []) as Listed[];
  const twice = (names: (string | undefined)[]): string[] =>
    names.filter((name, index) => name !== undefined && names.indexOf(name) !== index) as string[];
  return [
    ...twice(columns.map((column) => column.name)).map((name) => `column ${name} occurs twice`),
    ...columns.flatMap((column) =>
      twice((column.values ?? []).map((value) => value.code)).map(
        (code) => `${column.name}: code ${code} occurs twice`,
      ),
    ),
    ...columns.flatMap(unlisted),
  ];
}

type Context = Record<string, string | { '@id': string }>;

/** Expands a key or type of JSON-LD to an IRI through the context. */
function expand(term: string, context: Context): string {
  const entry = context[term];
  const target = typeof entry === 'object' ? entry['@id'] : (entry ?? term);
  const [prefix = '', rest = ''] = target.split(/:(.*)/s);
  const base = context[prefix];
  return typeof base === 'string' && base !== target && rest !== '' ? `${base}${rest}` : target;
}

const known = new Set(
  Object.values(vocabulary.vocabularies).flatMap((entry) =>
    Object.keys(entry.terms).map((term) => `${entry.namespace}${term}`),
  ),
);

/** Errors for terms of a JSON-LD document that no pinned vocabulary defines. */
function undefinedTerms(value: unknown, context: Context): string[] {
  if (Array.isArray(value)) return value.flatMap((item) => undefinedTerms(item, context));
  if (typeof value !== 'object' || value === null) return [];
  const node = value as Record<string, unknown>;
  const types = [node['@type'] ?? []].flat().map(String);
  // A key whose term is null is dropped by JSON-LD; one mapped to a keyword (such as @nest) is not a property.
  const keys = Object.keys(node).filter(
    (key) =>
      !key.startsWith('@') &&
      !jsonld.extensions.includes(key) &&
      context[key] !== null &&
      !String(context[key]).startsWith('@'),
  );
  const unknown = [...keys, ...types].filter(
    (term) => !known.has(expand(term, context)) && !(jsonld.accepted as string[]).includes(term),
  );
  const below = Object.entries(node)
    .filter(([key]) => key !== '@context' && context[key] !== null)
    .flatMap(([, child]) => undefinedTerms(child, context));
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
