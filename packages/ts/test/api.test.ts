import assert from 'node:assert/strict';
import { test } from 'node:test';
import { build, inferColumn, merge, parse, validate, type Profile } from '../src/index.ts';

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
