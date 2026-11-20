import { readstat as rules } from './constants.ts';
import type { Column, Profile, Value } from './generated/types.ts';
import { clean } from './jsonld.ts';

type Cell = number | string | null;

/**
 * One variable as a ReadStat-based reader delivers it, for `fromReadstat`.
 *
 * See section 15 of the specification.
 */
export interface StatVariable {
  name: string;
  label?: string | null;
  type?: number;
  format?: string | null;
  measure?: number;
  valueLabels?: { value: Cell; label: string }[] | null;
  missingRanges?: { lo: Cell; hi: Cell }[] | null;
}

const EXTENDED = new RegExp(rules.extended_missing);
const FORMATS = rules.formats.map(({ pattern, datatype }) => ({ pattern: new RegExp(pattern), datatype }));

/** A value or missing value as the text of a code. */
const codeOf = (value: Cell | undefined): string | undefined =>
  value === null || value === undefined ? undefined : String(value);

function datatypeOf(variable: StatVariable): string {
  if (variable.type === rules.string_type) return 'string';
  const found = FORMATS.find(({ pattern }) => pattern.test(variable.format ?? ''));
  if (found) return found.datatype;
  return rules.integer_types.includes(variable.type ?? -1) ? 'integer' : 'number';
}

function levelOf(variable: StatVariable): string | undefined {
  const level = (rules.measure as Record<string, string>)[String(variable.measure ?? 0)];
  return level ?? (variable.valueLabels?.length ? rules.labelled_level : undefined);
}

/** The one range of missing numbers, and the single missing values. */
function missingOf(variable: StatVariable): { span?: { low: number; high: number }; single: string[] } {
  const ranges = (variable.missingRanges ?? []).map((range) => ({
    ...range,
    lo_text: codeOf(range.lo),
    hi_text: codeOf(range.hi),
  }));
  const spans = ranges.filter((range) => range.lo_text !== range.hi_text);
  if (spans.length > 1) throw new Error(`${variable.name}: more than one range of missing values`);
  const single = ranges.filter((range) => range.lo_text === range.hi_text && range.lo_text !== undefined);
  const span = spans[0];
  return {
    span: span ? { low: Number(span.lo), high: Number(span.hi) } : undefined,
    single: single.map((range) => range.lo_text as string),
  };
}

function columnOf(variable: StatVariable): Column {
  const { span, single } = missingOf(variable);
  const values = (variable.valueLabels ?? []).flatMap((pair): Value[] => {
    const code = codeOf(pair.value);
    return code === undefined
      ? []
      : [
          clean({
            code,
            label: pair.label,
            missing: single.includes(code) || EXTENDED.test(code) || undefined,
          }) as unknown as Value,
        ];
  });
  return clean({
    name: variable.name,
    label: variable.label || undefined,
    datatype: datatypeOf(variable),
    level: levelOf(variable),
    values,
    missing_values: single.filter((code) => !values.some((value) => value.code === code)),
    missing_range: span,
  }) as unknown as Column;
}

/**
 * Reads the variables of a statistical file (SPSS, Stata or SAS) into a profile.
 *
 * `input` is the variables as `statfmt` delivers them (see `StatVariable` and section 15 of the specification). Value
 * labels do not make a list closed: SPSS and Stata allow codes without a label.
 */
export function fromReadstat(input: StatVariable[] | { variables: StatVariable[] }): Profile {
  const listed = Array.isArray(input) ? input : input.variables;
  if (!listed?.length) throw new Error('no variables found');
  return { columns: listed.map(columnOf) };
}
