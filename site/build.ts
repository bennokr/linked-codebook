// Builds the test page into site/dist: the bundle, the examples and the packages of both libraries.
// The packages are named by version, so that other projects can install them from this site.
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
const wheel = readdirSync(join(dist, 'wheel')).find((file) => file.endsWith('.whl')) ?? '';
cpSync(join(dist, 'wheel', wheel), join(dist, 'linked_codebook.whl'));
cpSync(join(dist, 'wheel', wheel), join(dist, wheel));
execFileSync('npm', ['run', 'build', '-w', 'linked-codebook'], { cwd: root, stdio: 'inherit' });
execFileSync('npm', ['pack', '-w', 'linked-codebook', '--pack-destination', dist], { cwd: root, stdio: 'inherit' });

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
