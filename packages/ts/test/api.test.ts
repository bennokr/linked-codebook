import assert from 'node:assert/strict';
import { test } from 'node:test';
import { vocabulary } from '../src/constants.ts';
import { build, inferColumn, merge, parse, unmatchedSssom, validate, type Profile } from '../src/index.ts';

const profile: Profile = {
  title: 'Example',
  columns: [
    {
      name: 'sex',
      label: 'Sex',
      datatype: 'string',
      level: 'nominal',
      values: [
        { code: '1', label: 'Male' },
        { code: '9', label: 'Unknown', missing: true },
      ],
    },
  ],
};

test('a profile survives being written as JSON-LD and read back', () => {
  assert.deepEqual(parse(build(profile)), profile);
});

test('a written profile uses only defined terms', () => {
  assert.deepEqual(validate(build(profile)), []);
});

test('merging into itself changes nothing', () => {
  assert.deepEqual(merge(profile, profile), profile);
});

test('value labels make a column categorical', () => {
  const codes = Array.from({ length: 60 }, (_unused, index) => index % 30);
  assert.equal(inferColumn(codes).level, 'numerical');
  assert.equal(inferColumn(codes, { labelled: true }).level, 'categorical');
});

test('identifier names are not categories', () => {
  assert.equal(inferColumn(['a', 'b', 'a', 'b', 'a', 'b'], { name: 'patient_id' }).level, undefined);
});

test('every term is in its vocabulary', () => {
  assert.deepEqual(vocabulary.unverified, []);
});

test('limits can be raised', () => {
  const codes = Array.from({ length: 120 }, (_unused, index) => index % 12);
  assert.equal(inferColumn(codes).level, 'numerical');
  assert.equal(inferColumn(codes, { limits: { number: 12 } }).level, 'categorical');
});

test('unmatched rows are listed', () => {
  const tsv =
    'subject_id\tsubject_label\tpredicate_id\tobject_id\nx:1\tnope\tskos:exactMatch\thttp://e/1\nx:2\tsex\tskos:exactMatch\thttp://e/2\n';
  assert.deepEqual(unmatchedSssom(tsv, profile), ['nope']);
});

test('a known identifier overrides the name', () => {
  const codes = [1, 2, 1, 2, 1, 2];
  assert.equal(inferColumn(codes, { name: 'id', identifier: false }).level, 'categorical');
  assert.equal(inferColumn(codes, { name: 'group', identifier: true }).level, 'numerical');
});

test('statistics survive JSON-LD', () => {
  const counted: Profile = { rows: 3, columns: [{ name: 'a', completeness: 0.5 }] };
  assert.deepEqual(parse(build(counted)), counted);
  assert.deepEqual(validate(counted), []);
  assert.notDeepEqual(validate({ rows: 1.5, columns: [] }), []);
});

test('explicit keeps the variable IRIs that the library would write', () => {
  const written = build({ identifier: 'urn:x:1', columns: [{ name: 'a' }] });
  assert.equal(parse(written).columns[0]?.variable, undefined);
  assert.equal(parse(written, { explicit: true }).columns[0]?.variable, 'urn:x:1#variable-a');
});
