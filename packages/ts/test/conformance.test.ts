import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';
import { run } from '../src/index.ts';

const ROOT = join(import.meta.dirname, '../../../conformance');
const read = (...parts: string[]): string => readFileSync(join(ROOT, ...parts), 'utf8');

for (const command of readdirSync(ROOT)) {
  for (const name of readdirSync(join(ROOT, command))) {
    test(`${command}/${name}`, () => {
      const files = readdirSync(join(ROOT, command, name))
        .filter((file) => file.startsWith('in'))
        .sort();
      const { stdout, code } = run(
        [command, ...files],
        Object.fromEntries(files.map((file) => [file, read(command, name, file)])),
      );
      assert.equal(stdout, read(command, name, 'out'));
      assert.equal(code, existsSync(join(ROOT, command, name, 'code')) ? Number(read(command, name, 'code')) : 0);
    });
  }
}
