import type { Profile } from './generated/types.ts';

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

/** The slot that identifies the entries of each list of objects. */
const IDENTIFIERS: Record<string, string> = { columns: 'name', values: 'code', mappings: 'object_id' };

const isObject = (value: Json | undefined): value is { [key: string]: Json } => typeof value === 'object' && value !== null && !Array.isArray(value);

function join(base: Json | undefined, incoming: Json | undefined, slot: string): Json | undefined {
  const identifier = IDENTIFIERS[slot];
  if (isObject(base) && isObject(incoming)) {
    const keys = new Set([...Object.keys(base), ...Object.keys(incoming)]);
    return Object.fromEntries([...keys].map((key) => [key, join(base[key], incoming[key], key)])) as Json;
  }
  if (identifier && Array.isArray(base) && Array.isArray(incoming)) {
    const key = (entry: Json): Json | undefined => (isObject(entry) ? entry[identifier] : undefined);
    const found = (list: Json[], entry: Json): Json | undefined => list.find((other) => key(other) === key(entry));
    return [...base, ...incoming.filter((entry) => !found(base, entry))].map((entry) => join(entry, found(incoming, entry), '') ?? null);
  }
  return incoming === undefined || incoming === null || incoming === '' || (Array.isArray(incoming) && incoming.length === 0) ? base : incoming;
}

/** Adds what the second profile says to the first. Columns, values and mappings are matched by name, code and concept. */
export function merge(base: Profile, incoming: Profile): Profile {
  return join(base as unknown as Json, incoming as unknown as Json, '') as unknown as Profile;
}
