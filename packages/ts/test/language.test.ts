import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';
import {
  build,
  infer,
  inferLanguage,
  isIdentifierName,
  parse,
  validate,
  type Cell,
  type Profile,
} from '../src/index.ts';

interface Doc {
  cases: { name: string; cells: Cell[]; expected: { language: string; share: number; cells: number } | null }[];
  identifier_names: Record<string, boolean>;
}
const doc = JSON.parse(readFileSync(join(import.meta.dirname, '../../../spec/cases/language.json'), 'utf8')) as Doc;

/** The stub of the shared cases: the tag before the first colon, or null for ?. */
const detect = (text: string): string | null => {
  const tag = text.split(':', 1)[0] ?? '';
  return tag === '?' ? null : tag;
};

for (const { name, cells, expected } of doc.cases) {
  test(`language: ${name}`, () => {
    assert.deepEqual(inferLanguage(cells, detect) ?? null, expected);
  });
}

for (const [name, expected] of Object.entries(doc.identifier_names)) {
  test(`identifier name: ${name}`, () => {
    assert.equal(isIdentifierName(name), expected);
  });
}

test('infer adds the language of text columns only', () => {
  const data: Record<string, Cell[]> = {
    review: Array.from(
      { length: 10 },
      (_, i) => `nl: een lange recensie met genoeg woorden om als tekst te tellen (${i})`,
    ),
    sex: ['nl: m', 'nl: f', 'nl: m', 'nl: f', 'nl: m', 'nl: f', 'nl: m', 'nl: f', 'nl: m', 'nl: f'],
    age: Array.from({ length: 10 }, (_, i) => String(20 + i)),
  };
  const columns = Object.fromEntries(infer(data, detect).columns.map((column) => [column.name, column]));
  assert.equal(columns.review?.language, 'nl');
  assert.equal(columns.sex?.language, undefined);
  assert.equal(columns.age?.language, undefined);
  assert.equal(infer(data).columns[0]?.language, undefined);
});

test('language survives JSON-LD and validates', () => {
  const profile: Profile = { title: 'Reviews', columns: [{ name: 'review', datatype: 'string', language: 'nl' }] };
  const document = build(profile);
  assert.deepEqual(parse(document), profile);
  assert.deepEqual(validate(document), []);
  const bad = { ...profile, columns: [{ name: 'review', language: 'Dutch!' }] };
  assert.deepEqual(validate(bad), ['/columns/0/language: Dutch! does not match ^[a-z]{2,3}(-[a-z0-9]{2,8})*$']);
});
