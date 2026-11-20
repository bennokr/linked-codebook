import {
  evaluateCondition,
  isBlank,
  parseCondition,
  type Condition,
  type EvaluateOptions,
  type Row,
} from './condition.ts';
import type { Column, Profile } from './generated/types.ts';
import { isNumeric } from './infer.ts';
import { clean } from './jsonld.ts';

/** Column name to cells: the data that `missingness` reads. */
export type Data = Record<string, unknown[]>;
type Declared = [codes: Set<string>, column: Column];

const BLANK_KINDS: Record<string, string> = {
  true: 'blank_applicable',
  false: 'blank_not_applicable',
  null: 'blank_unknown',
};

function declaredCodes(column: Column): Set<string> {
  const labelled = (column.values ?? []).filter((value) => value.missing).map((value) => value.code);
  return new Set([...(column.missing_values ?? []), ...labelled]);
}

/** True for a code that is declared to mean no value, or a number in the declared range. */
function isDeclared(cell: unknown, [codes, column]: Declared): boolean {
  const limits = column.missing_range;
  const inRange =
    limits !== undefined && isNumeric(cell as string) && limits.low <= Number(cell) && Number(cell) <= limits.high;
  return codes.has(String(cell)) || inRange;
}

function rowsOf(data: Data): Row[] {
  const count = Math.max(0, ...Object.values(data).map((cells) => cells.length));
  return Array.from({ length: count }, (_unused, index) =>
    Object.fromEntries(Object.entries(data).map(([name, cells]) => [name, cells[index] ?? null])),
  );
}

/** The rows as a rule sees them: a declared missing code is no answer, so it becomes null. */
function answersOf(profile: Profile, rows: Row[]): Row[] {
  const columns = new Map<string, Declared>(
    profile.columns.map((column) => [column.name, [declaredCodes(column), column]]),
  );
  return rows.map((row) =>
    Object.fromEntries(
      Object.entries(row).map(([name, cell]) => {
        const declared = columns.get(name);
        return [name, declared && isDeclared(cell, declared) ? null : cell];
      }),
    ),
  );
}

/** For each row whether the column applies, or undefined if it has no rule; the error if the rule fails. */
function applicability(
  column: Column,
  rows: Row[],
  options: EvaluateOptions,
): { applies?: (boolean | null)[]; error?: string } {
  if (!column.applies_when) return {};
  try {
    const tree = parseCondition(column.applies_when);
    return { applies: rows.map((row) => evaluateCondition(tree, row, options)) };
  } catch (error) {
    return { error: (error as Error).message };
  }
}

/** What a cell is: blank (and, if the column has a rule, why), a declared missing code, or an answer. */
function kindOf(cell: unknown, state: boolean | null | undefined, ruled: boolean, declared: Declared): string {
  if (isBlank(cell)) return ruled ? (BLANK_KINDS[String(state)] as string) : 'blank';
  if (isDeclared(cell, declared)) return 'declared';
  return state === false ? 'answered_not_applicable' : 'present';
}

/** Adds a cell of the given kind to the counts. A blank_* cell is also blank; an unwanted answer is still present. */
function tally(counts: Record<string, number>, codes: Record<string, number>, cell: unknown, kind: string): void {
  const add = (key: string): void => {
    counts[key] = (counts[key] ?? 0) + 1;
  };
  if (kind === 'declared') {
    codes[String(cell)] = (codes[String(cell)] ?? 0) + 1;
    return;
  }
  add(kind);
  if (kind.startsWith('blank_')) add('blank');
  if (kind === 'answered_not_applicable') add('present');
}

function columnReport(column: Column, rows: Row[], answers: Row[], options: EvaluateOptions): Record<string, unknown> {
  const declared: Declared = [declaredCodes(column), column];
  const { applies, error } = applicability(column, answers, options);
  const counts: Record<string, number> = { present: 0, blank: 0 };
  const codes: Record<string, number> = {};
  rows.forEach((row, index) => {
    const cell = row[column.name];
    tally(counts, codes, cell, kindOf(cell, applies?.[index], applies !== undefined, declared));
  });
  return clean({ ...counts, declared: codes, rule_error: error });
}

/**
 * Counts, for each column of the profile that the data has, how its values divide.
 *
 * `data` is `{ name: cells }`. `present` is a value; `declared` counts the codes that mean no value; `blank` is an
 * empty cell, divided by the rule `applies_when` into `blank_not_applicable` (skipped by design), `blank_applicable`
 * (missing although the question applied) and `blank_unknown` (the rule cannot be decided). `answered_not_applicable`
 * counts values in rows where the rule says the question does not apply.
 *
 * `options.blank` is how rules treat a blank, as in `evaluateCondition`. With 'value' (the default, as in REDCap) a
 * declared missing code is an ordinary value in a rule; with 'unknown' it is a blank and makes the rule unknown.
 */
export function missingness(profile: Profile, data: Data, options: EvaluateOptions = {}): Record<string, unknown> {
  const rows = rowsOf(data);
  const answers = (options.blank ?? 'value') === 'value' ? rows : answersOf(profile, rows);
  const columns = profile.columns.filter((column) => column.name in data);
  return {
    rows: rows.length,
    columns: Object.fromEntries(columns.map((c) => [c.name, columnReport(c, rows, answers, options)])),
  };
}

/** The parsed `applies_when` of every column that has one, or the reason it could not be parsed. */
export function conditions(profile: Profile): Record<string, { condition: Condition } | { error: string }> {
  const found: Record<string, { condition: Condition } | { error: string }> = {};
  for (const column of profile.columns.filter((candidate) => candidate.applies_when)) {
    try {
      found[column.name] = { condition: parseCondition(column.applies_when as string) };
    } catch (error) {
      found[column.name] = { error: (error as Error).message };
    }
  }
  return found;
}
