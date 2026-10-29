// Builds the test page into site/dist: the bundle, the wheel of the Python library and the examples.
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { build } from 'esbuild';

const root = join(import.meta.dirname, '..');
const dist = join(root, 'site/dist');
mkdirSync(dist, { recursive: true });

await build({
  entryPoints: [join(root, 'site/main.ts')],
  bundle: true,
  format: 'esm',
  target: 'es2022',
  outfile: join(dist, 'main.js'),
});
for (const file of ['index.html', 'style.css']) cpSync(join(root, 'site', file), join(dist, file));

execFileSync('uv', ['build', '--wheel', '--out-dir', join(dist, 'wheel'), 'packages/py'], {
  cwd: root,
  stdio: 'inherit',
});
cpSync(
  join(dist, 'wheel', readdirSync(join(dist, 'wheel')).find((file) => file.endsWith('.whl')) ?? ''),
  join(dist, 'linked_codebook.whl'),
);

const conformance = join(root, 'conformance');
const examples = readdirSync(conformance).flatMap((command) =>
  readdirSync(join(conformance, command)).map((name) => {
    const directory = join(conformance, command, name);
    const inputs = readdirSync(directory).filter((file) => file.startsWith('in'));
    return {
      name: `${command}/${name}`,
      command,
      files: Object.fromEntries(inputs.map((file) => [file, readFileSync(join(directory, file), 'utf8')])),
    };
  }),
);
writeFileSync(join(dist, 'examples.json'), JSON.stringify(examples));
