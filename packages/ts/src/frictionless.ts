import { frictionless as rules } from './constants.ts';
import type { Column, Profile } from './generated/types.ts';
import { isNumeric } from './infer.ts';
import { clean, pick, type Node } from './jsonld.ts';

const identity = (slots: string[]): Record<string, string> => Object.fromEntries(slots.map((slot) => [slot, slot]));

/** A code as the value its field type expects, so that numbers stay numbers. */
const typed = (code: string, datatype?: string): string | number =>
  (datatype === 'integer' || datatype === 'number') && isNumeric(code) ? Number(code) : code;

function fieldOf(column: Column): Node {
  const values = column.values ?? [];
  return clean({
    ...pick(column, rules.field),
    missingValues: [
      ...(column.missing_values ?? []),
      ...values.filter((value) => value.missing).map((value) => value.code),
    ],
    categories: (column.closed ? values : []).map((value) =>
      value.label
        ? { value: typed(value.code, column.datatype), label: value.label }
        : typed(value.code, column.datatype),
    ),
    categoriesOrdered: column.closed && values.length && column.level === 'ordinal' ? true : undefined,
    constraints: pick(column, { minimum: 'minimum', maximum: 'maximum' }),
    [rules.extension]: pick(column, identity(rules.extension_slots)),
  });
}

/** Writes a profile as a Frictionless Table Schema. Slots of the dataset are kept in the extension property. */
export function toFrictionless(profile: Profile): Node {
  const { columns, ...dataset } = profile;
  return clean({ fields: columns.map(fieldOf), [rules.extension]: clean(dataset) });
}
