import assert from 'node:assert/strict';
import { test } from 'node:test';
import { evaluateCondition, missingness, parseCondition, type Profile } from '../src/index.ts';

const cases: [string, Record<string, unknown>, boolean | null][] = [
  ['[a] = 1', { a: '1' }, true],
  ['[a] = 1', { a: 1 }, true],
  ['[a] = 1', { a: '' }, null],
  ['[a] <> 1', { a: null }, null],
  ["[a] = '' ", { a: ' ' }, true],
  ['[a] = 1 and [b] = 1', { a: '2' }, false],
  ['[a] = 1 and [b] = 1', { a: '1' }, null],
  ['[a] = 1 or [b] = 1', { a: '1' }, true],
  ['[a] = 1 or [b] = 1', { a: '2' }, null],
  ['not [a] = 1', { a: '2' }, true],
  ['a in (1, 2)', { a: '2' }, true],
  ['a in (1, 2)', {}, null],
  ['a IS NULL', {}, true],
  ['a < 10', { a: '9' }, true],
  ['a < 10', { a: '007' }, true],
  ["d >= '2020-01-01'", { d: '2021-05-05' }, true],
];

test('evaluation is three-valued', () => {
  for (const [text, row, expected] of cases) {
    assert.equal(evaluateCondition(parseCondition(text), row), expected, text);
  }
});

test('a missing code of the controlling question makes the rule unknown', () => {
  const profile = {
    columns: [
      { name: 'smoker', missing_values: ['9'] },
      { name: 'cigs', applies_when: "[smoker] = '1'" },
    ],
  } as Profile;
  const report = missingness(profile, { smoker: ['1', '0', '9', ''], cigs: ['', '', '', ''] }) as {
    columns: Record<string, unknown>;
  };
  assert.deepEqual(report.columns['cigs'], {
    blank: 4,
    blank_applicable: 1,
    blank_not_applicable: 1,
    blank_unknown: 2,
    present: 0,
  });
  assert.deepEqual(report.columns['smoker'], { blank: 1, declared: { '9': 1 }, present: 2 });
});
