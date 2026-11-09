import assert from 'node:assert/strict';
import { test } from 'node:test';
import { evaluateCondition, missingness, parseCondition, type Profile } from '../src/index.ts';

// text, row, result when a blank is a value (the default), result when a blank is unknown
const cases: [string, Record<string, unknown>, boolean | null, boolean | null][] = [
  ['[a] = 1', { a: '1' }, true, true],
  ['[a] = 1', { a: 1 }, true, true],
  ['[a] = 1', { a: '' }, false, null],
  ['[a] <> 1', { a: null }, true, null],
  ['[a] = [b]', {}, true, null],
  ["[a] = '' ", { a: ' ' }, true, true],
  ['[a] = 1 and [b] = 1', { a: '2' }, false, false],
  ['[a] = 1 and [b] = 1', { a: '1' }, false, null],
  ['[a] = 1 or [b] = 1', { a: '1' }, true, true],
  ['[a] = 1 or [b] = 1', { a: '2' }, false, null],
  ['not [a] = 1', { a: '2' }, true, true],
  ['a in (1, 2)', { a: '2' }, true, true],
  ['a in (1, 2)', {}, false, null],
  ['a IS NULL', {}, true, true],
  ['a < 10', { a: '9' }, true, true],
  ['a < 10', { a: '007' }, true, true],
  ['a < 10', {}, null, null],
  ["d >= '2020-01-01'", { d: '2021-05-05' }, true, true],
];

test('evaluation of a blank, as a value and as unknown', () => {
  for (const [text, row, asValue, asUnknown] of cases) {
    const tree = parseCondition(text);
    assert.equal(evaluateCondition(tree, row), asValue, text);
    assert.equal(evaluateCondition(tree, row, { blank: 'unknown' }), asUnknown, text);
  }
});

const profile = {
  columns: [
    { name: 'smoker', missing_values: ['9'] },
    { name: 'cigs', applies_when: "[smoker] = '1'" },
  ],
} as Profile;
const data = { smoker: ['1', '0', '9', ''], cigs: ['', '', '', ''] };
interface Report {
  columns: Record<string, unknown>;
}

test('a blank controlling answer is not applicable, as REDCap decides', () => {
  const report = missingness(profile, data) as unknown as Report;
  assert.deepEqual(report.columns['cigs'], { blank: 4, blank_applicable: 1, blank_not_applicable: 3, present: 0 });
  assert.deepEqual(report.columns['smoker'], { blank: 1, declared: { '9': 1 }, present: 2 });
});

test('a missing code of the controlling question makes the rule unknown when a blank is unknown', () => {
  const report = missingness(profile, data, { blank: 'unknown' }) as unknown as Report;
  assert.deepEqual(report.columns['cigs'], {
    blank: 4,
    blank_applicable: 1,
    blank_not_applicable: 1,
    blank_unknown: 2,
    present: 0,
  });
});
