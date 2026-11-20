import type { Profile } from './generated/types.ts';

// A recursive alias cannot use Record, so this is an interface with an index signature.
interface Dict {
  [key: string]: Json;
}
type Json = null | boolean | number | string | Json[] | Dict;

/** The slot that identifies the entries of each list of objects. */
const IDENTIFIERS: Record<string, string> = {
  columns: 'name',
  values: 'code',
  observed: 'code',
  mappings: 'object_id',
};

const isDict = (value: Json | undefined): value is Dict =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const isEmpty = (value: Json | undefined): boolean =>
  value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0);

function joinLists(base: Json[], incoming: Json[], identifier: string): Json[] {
  const key = (entry: Json): Json | undefined => (isDict(entry) ? entry[identifier] : undefined);
  const found = (list: Json[], entry: Json): Json | undefined => list.find((other) => key(other) === key(entry));
  return [...base, ...incoming.filter((entry) => !found(base, entry))].map(
    (entry) => join(entry, found(incoming, entry), '') ?? null,
  );
}

function join(base: Json | undefined, incoming: Json | undefined, slot: string): Json | undefined {
  if (isDict(base) && isDict(incoming)) {
    const keys = new Set([...Object.keys(base), ...Object.keys(incoming)]);
    return Object.fromEntries([...keys].map((key) => [key, join(base[key], incoming[key], key)])) as Json;
  }
  const identifier = IDENTIFIERS[slot];
  if (identifier && Array.isArray(base) && Array.isArray(incoming)) return joinLists(base, incoming, identifier);
  return isEmpty(incoming) ? base : incoming;
}

/**
 * Completes `base` with what `incoming` says.
 *
 * Columns, values and mappings are matched by name, code and concept.
 */
export function merge(base: Profile, incoming: Profile): Profile {
  return join(base as unknown as Json, incoming as unknown as Json, '') as unknown as Profile;
}
