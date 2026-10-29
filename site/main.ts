import { commands } from '../packages/ts/src/constants.ts';
import { run } from '../packages/ts/src/index.ts';

interface Example {
  name: string;
  command: string;
  files: Record<string, string>;
}
interface Outcome {
  stdout: string;
  code: number;
}
interface Pyodide {
  toPy: (value: unknown) => unknown;
  unpackArchive: (data: ArrayBuffer, format: string) => void;
  pyimport: (name: string) => { run: (args: unknown, texts: unknown) => { toJs: () => [string, number] } };
}
declare function loadPyodide(): Promise<Pyodide>;

const spec = commands as Record<string, { files: string[] }>;
const element = <T extends HTMLElement>(id: string): T => document.getElementById(id) as T;
const example = element<HTMLSelectElement>('example');
const command = element<HTMLSelectElement>('command');
const files = element('files');
const status = element('status');

const examples: Example[] = (await (await fetch('examples.json')).json()) as Example[];

/** The Python library, loaded when it is first needed. */
let python: Promise<(args: string[], texts: Record<string, string>) => Outcome> | undefined;
function loadPython(): Promise<(args: string[], texts: Record<string, string>) => Outcome> {
  python ??= (async () => {
    const pyodide = await loadPyodide();
    pyodide.unpackArchive(await (await fetch('linked_codebook.whl')).arrayBuffer(), 'wheel');
    const library = pyodide.pyimport('linked_codebook');
    return (args, texts) => {
      const [stdout, code] = library.run(pyodide.toPy(args), pyodide.toPy(texts)).toJs();
      return { stdout, code };
    };
  })();
  return python;
}

function showFiles(): void {
  const names = spec[command.value]?.files ?? [];
  files.replaceChildren(
    ...names.map((name) => {
      const label = document.createElement('label');
      label.append(`${name} `, Object.assign(document.createElement('textarea'), { name, spellcheck: false }));
      return label;
    }),
  );
}

function showExample(): void {
  const chosen = examples[Number(example.value)];
  if (!chosen) return;
  command.value = chosen.command;
  showFiles();
  const areas = Array.from(files.querySelectorAll('textarea'));
  Object.keys(chosen.files)
    .sort()
    .forEach((file, index) => {
      const area = areas[index];
      if (area) area.value = chosen.files[file] ?? '';
    });
}

const outcome = ({ stdout, code }: Outcome): string => `${stdout}\n[exit code ${code}]`;

async function runBoth(): Promise<void> {
  const texts = Object.fromEntries(
    Array.from(files.querySelectorAll('textarea')).map((area) => [area.name, area.value]),
  );
  const args = [command.value, ...Object.keys(texts)];
  element('ts').textContent = outcome(run(args, texts));
  status.textContent = 'Loading Python…';
  const result = (await loadPython())(args, texts);
  element('py').textContent = outcome(result);
  const same = element('ts').textContent === element('py').textContent;
  status.textContent = same ? 'Same output' : 'The outputs differ';
}

command.replaceChildren(...Object.keys(spec).map((name) => new Option(name)));
example.replaceChildren(...examples.map((item, index) => new Option(item.name, String(index))));
command.addEventListener('change', showFiles);
example.addEventListener('change', showExample);
element('form').addEventListener('submit', (event) => {
  event.preventDefault();
  void runBoth();
});
showExample();
