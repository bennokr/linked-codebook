// Builds the site into site/dist: the test page (bundle and examples), the packages of both libraries, the JSON-LD
// contexts and the documentation (under docs/).
// The packages are named by version, so that other projects can install them from this site.
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
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
// The IRIs of the slots that no other vocabulary has (`lc:`) are those of this data model.
cpSync(join(root, 'spec/profile.yaml'), join(dist, 'profile.yaml'));

execFileSync('uv', ['build', '--wheel', '--out-dir', join(dist, 'wheel'), 'packages/py'], {
  cwd: root,
  stdio: 'inherit',
});
const wheel = readdirSync(join(dist, 'wheel')).find((file) => file.endsWith('.whl')) ?? '';
cpSync(join(dist, 'wheel', wheel), join(dist, 'linked_codebook.whl'));
cpSync(join(dist, 'wheel', wheel), join(dist, wheel));
rmSync(join(dist, 'wheel'), { recursive: true });
execFileSync('npm', ['run', 'build', '-w', 'linked-codebook'], { cwd: root, stdio: 'inherit' });
execFileSync('npm', ['pack', '-w', 'linked-codebook', '--pack-destination', dist], { cwd: root, stdio: 'inherit' });

// Released packages are kept in the repository, so that every version stays available to the projects that use it.
cpSync(join(root, 'releases'), dist, { recursive: true });

// The JSON-LD context, for documents that name it instead of embedding it: the current one, and one file per version
// (released versions come from `releases/` and are kept as they were).
execFileSync('uv', ['run', 'python', 'scripts/context.py', dist], { cwd: root, stdio: 'inherit' });

// The documentation, built with VitePress into `dist/docs`.
execFileSync('npx', ['vitepress', 'build', 'docs'], { cwd: root, stdio: 'inherit' });

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
