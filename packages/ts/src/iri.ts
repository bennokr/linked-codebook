import { iris, jsonld } from './constants.ts';
import type { Column, Profile } from './generated/types.ts';

/** Fills the IRI template of a node kind. Placeholders that are not IRIs are percent-encoded. */
export function fill(kind: string, values: Record<string, string>): string {
  return (iris[kind] ?? '').replace(/\{(\w+)\}/g, (_match, name: string) => {
    const value = values[name] ?? '';
    return jsonld.raw.includes(name) ? value : encodeURIComponent(value);
  });
}

export function datasetIri(profile: Profile): string {
  const id = profile.identifier ?? '';
  return /^(https?:|urn:)/.test(id) ? id : fill('dataset', { id: id || profile.title || 'unnamed' });
}

/** The IRI of the variable of a column: the one it declares, or one made from its name. */
export function variableIri(dataset: string, column: Column): string {
  return column.variable ?? fill('variable', { dataset, name: column.name });
}

export const codeIri = (variable: string, code: string): string => fill('code', { variable, code });
