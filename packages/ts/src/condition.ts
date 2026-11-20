import { condition as spec } from './constants.ts';
import { isNumeric } from './infer.ts';

/**
 * A node of the tree that `parseCondition` returns and `evaluateCondition` takes.
 *
 * It is a variable, a value, or an operator with its operands (see section 13 of the specification). The tree is shaped
 * like [JsonLogic](https://jsonlogic.com): `{ "==": [{ "var": "smoker" }, "1"] }`.
 */
export type Condition = string | number | Record<string, unknown>;
export type Row = Record<string, unknown>;

const TOKENS = spec.tokens.map(({ kind, pattern }) => ({ kind, pattern: new RegExp(pattern, 'y') }));
const OPERATORS = spec.operators as Record<string, string>;
const COMPARISONS = ['==', '!=', '<', '<=', '>', '>='];
const KEYWORDS = ['and', 'or', 'not', 'in', 'is', 'null'];

type Token = [kind: string, text: string];

function tokenize(text: string): Token[] {
  const found: Token[] = [];
  let position = 0;
  while (position < text.length) {
    const hit = TOKENS.map(({ kind, pattern }) => {
      pattern.lastIndex = position;
      return [kind, pattern.exec(text)?.[0]] as const;
    }).find(([, matched]) => matched !== undefined);
    if (!hit?.[1]) throw new Error(`unexpected '${text[position]}' at position ${position}`);
    position += hit[1].length;
    if (hit[0] !== 'space') found.push([hit[0], hit[1]]);
  }
  return found;
}

const unquote = (text: string): string => {
  const quote = text.charAt(0);
  return text.slice(1, -1).replaceAll(quote + quote, quote);
};

/** The variable of a bracketed field: [name], or [name(code)] for an option of a REDCap checkbox. */
function variable(field: string): Condition {
  const content = field.slice(1, -1).trim();
  const option = /^([^()]+)\((.*)\)$/s.exec(content);
  if (!option) return { var: content };
  const code = (option[2] ?? '').trim().toLowerCase().replace(new RegExp(spec.checkbox_other, 'g'), '_');
  return { var: spec.checkbox.replace('{name}', (option[1] ?? '').trim()).replace('{code}', code) };
}

const isValue = (node: Condition): boolean => typeof node !== 'object' || 'var' in node;

/** A comparison; comparing with the empty string asks whether the value is blank. */
function compare(operator: string, left: Condition, right: Condition): Condition {
  if (right === '' && (operator === '==' || operator === '!=')) {
    const test = { null: [left] };
    return operator === '==' ? test : { '!': [test] };
  }
  return { [operator]: [left, right] };
}

class Parser {
  private at = 0;
  private readonly tokens: Token[];

  constructor(tokens: Token[]) {
    this.tokens = tokens;
  }

  private peek(): Token {
    return this.tokens[this.at] ?? ['end', ''];
  }

  private take(): Token {
    const token = this.peek();
    this.at += 1;
    return token;
  }

  private isWord(...names: string[]): boolean {
    const [kind, text] = this.peek();
    return kind === 'word' && names.includes(text.toLowerCase());
  }

  /** True at the word `and` or `or`, or at a symbol that stands for it. */
  private isJoin(name: string): boolean {
    const [kind, text] = this.peek();
    return this.isWord(name) || (kind === 'join' && (spec.joins as Record<string, string>)[text] === name);
  }

  private isPunct(text: string): boolean {
    const [kind, found] = this.peek();
    return kind === 'punct' && found === text;
  }

  private expect(text: string): void {
    if (!this.isPunct(text)) throw new Error(`expected '${text}', found '${this.peek()[1] || 'the end'}'`);
    this.take();
  }

  parse(): Condition {
    const node = this.disjunction();
    if (this.at < this.tokens.length) throw new Error(`unexpected '${this.peek()[1]}'`);
    return node;
  }

  private chain(name: string, operand: () => Condition): Condition {
    const items = [operand()];
    while (this.isJoin(name)) {
      this.take();
      items.push(operand());
    }
    return items.length === 1 ? (items[0] as Condition) : { [name]: items };
  }

  private disjunction(): Condition {
    return this.chain('or', () => this.conjunction());
  }

  private conjunction(): Condition {
    return this.chain('and', () => this.negation());
  }

  private negation(): Condition {
    if (!this.isWord('not')) return this.comparison();
    this.take();
    return { '!': [this.negation()] };
  }

  private comparison(): Condition {
    const left = this.operand();
    const [kind, text] = this.peek();
    if (kind === 'op') {
      this.take();
      return compare(OPERATORS[text] as string, left, this.operand());
    }
    const test = this.wordTest(left);
    if (test) return test;
    if (isValue(left)) throw new Error('expected a comparison');
    return left;
  }

  /** The test that follows a value as a word: IN (...), IS [NOT] NULL. Nothing if the next token is not one. */
  private wordTest(left: Condition): Condition | undefined {
    if (this.isWord('in')) {
      this.take();
      return { in: [left, this.options()] };
    }
    if (!this.isWord('is')) return undefined;
    this.take();
    return this.nullTest(left);
  }

  private nullTest(left: Condition): Condition {
    const negated = this.isWord('not');
    if (negated) this.take();
    if (!this.isWord('null')) throw new Error('expected NULL');
    this.take();
    const test = { null: [left] };
    return negated ? { '!': [test] } : test;
  }

  private options(): Condition[] {
    this.expect('(');
    const items = [this.literal()];
    while (this.isPunct(',')) {
      this.take();
      items.push(this.literal());
    }
    this.expect(')');
    return items;
  }

  private literal(): Condition {
    const [kind, text] = this.take();
    if (kind === 'number') return Number(text);
    if (kind === 'string') return unquote(text);
    throw new Error(`expected a value, found '${text || 'the end'}'`);
  }

  private operand(): Condition {
    const [kind] = this.peek();
    if (kind === 'number' || kind === 'string') return this.literal();
    if (!this.isPunct('(')) return this.name();
    this.take();
    const node = this.disjunction();
    this.expect(')');
    return node;
  }

  private name(): Condition {
    const [kind, text] = this.take();
    if (kind === 'field') {
      if (this.peek()[0] === 'field') throw new Error('references to events are not supported');
      return variable(text);
    }
    if (kind === 'word' && !KEYWORDS.includes(text.toLowerCase())) {
      if (this.isPunct('(')) throw new Error(`function ${text} is not supported`);
      return { var: text };
    }
    throw new Error(`expected a field or a value, found '${text || 'the end'}'`);
  }
}

/**
 * Parses a condition of skip logic (REDCap branching logic or a SQL `WHERE` subset) into a tree.
 *
 * Throws an error for text that is not one, or that uses what the language does not have.
 */
export const parseCondition = (text: string): Condition => new Parser(tokenize(text)).parse();

export const isBlank = (cell: unknown): boolean =>
  cell === null || cell === undefined || (typeof cell === 'string' && !cell.trim());

function valueOf(node: unknown, row: Row): unknown {
  if (typeof node === 'object' && node !== null && 'var' in node) {
    const cell = row[(node as { var: string }).var];
    return isBlank(cell) ? null : cell;
  }
  return node;
}

/** Numbers are compared as numbers (so 1 and "1" are alike), everything else as text. */
const same = (left: unknown, right: unknown): boolean =>
  isNumeric(left as string) && isNumeric(right as string)
    ? Number(left) === Number(right)
    : String(left) === String(right);

function order(left: unknown, right: unknown): number {
  const numeric = isNumeric(left as string) && isNumeric(right as string);
  const [a, b] = numeric ? [Number(left), Number(right)] : [String(left), String(right)];
  if (a === b) return 0;
  return a > b ? 1 : -1;
}

/** A comparison where a side is blank. With a blank that is a value, two blanks are equal and a blank differs from any value. */
function compareBlank(operator: string, left: unknown, right: unknown, blankIsValue: boolean): boolean | null {
  if (!blankIsValue || (operator !== '==' && operator !== '!=')) return null;
  return (left === null && right === null) === (operator === '==');
}

function compared(operator: string, left: unknown, right: unknown, blankIsValue: boolean): boolean | null {
  if (left === null || right === null) return compareBlank(operator, left, right, blankIsValue);
  if (operator === '==' || operator === '!=') return same(left, right) === (operator === '==');
  const sign = order(left, right);
  return { '<': sign < 0, '<=': sign <= 0, '>': sign > 0, '>=': sign >= 0 }[operator] as boolean;
}

/** `decisive` settles the result when present (false for and, true for or); unknown wins over the other value. */
function combine(results: (boolean | null)[], decisive: boolean): boolean | null {
  if (results.includes(decisive)) return decisive;
  return results.includes(null) ? null : !decisive;
}

function membership(args: unknown[], row: Row, blankIsValue: boolean): boolean | null {
  const left = valueOf(args[0], row);
  if (left === null) return blankIsValue ? false : null;
  return (args[1] as unknown[]).some((option) => same(left, option));
}

/** The third argument of `evaluateCondition` and `missingness`. */
export interface EvaluateOptions {
  /**
   * What a blank is. With "value" (the default, as in REDCap) a blank equals another blank and differs from anything
   * else, so `[a] <> 1` is true when `a` is blank; only ordering a blank is unknown. With "unknown" (as in SQL) every
   * comparison with a blank is unknown.
   */
  blank?: 'value' | 'unknown';
}

function evaluateNode(node: Condition, row: Row, blankIsValue: boolean): boolean | null {
  const [operator, args] = Object.entries(node as Record<string, unknown[]>)[0] ?? ['', []];
  if (COMPARISONS.includes(operator)) {
    return compared(operator, valueOf(args[0], row), valueOf(args[1], row), blankIsValue);
  }
  if (operator === 'in') return membership(args, row, blankIsValue);
  if (operator === 'null') return valueOf(args[0], row) === null;
  if (operator === '!') {
    const inner = evaluateNode(args[0] as Condition, row, blankIsValue);
    return inner === null ? null : !inner;
  }
  const results = args.map((arg: unknown) => evaluateNode(arg as Condition, row, blankIsValue));
  return combine(results, operator === 'or');
}

/**
 * Evaluates a condition tree for a row `{ name: cell }`: true, false or null (unknown).
 *
 * `node` is a tree from `parseCondition`. `options.blank` says what a blank value is. With 'value' (the default, as in
 * REDCap) a blank is the empty value: it equals another blank and differs from anything else, so `[a] <> 1` is true
 * when `a` is blank; only ordering a blank is unknown. With 'unknown' (as in SQL) every comparison with a blank is
 * unknown.
 */
export function evaluateCondition(node: Condition, row: Row, options: EvaluateOptions = {}): boolean | null {
  const blank = options.blank ?? 'value';
  if (blank !== 'value' && blank !== 'unknown') throw new Error(`blank must be 'value' or 'unknown', not '${blank}'`);
  return evaluateNode(node, row, blank === 'value');
}
