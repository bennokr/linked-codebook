import { canonical } from './canonical.ts';
import { commands as spec } from './constants.ts';
import type { Profile } from './generated/types.ts';
import { infer } from './infer.ts';
import { build } from './jsonld.ts';
import { merge } from './merge.ts';
import { parse } from './read.ts';
import { toFrictionless } from './frictionless.ts';
import { fromSssom, toSssom } from './sssom.ts';
import { validate } from './validate.ts';

export interface Result {
  stdout: string;
  code: number;
}

const done = (stdout: string): Result => ({ stdout, code: 0 });

/** A profile, read from profile JSON or from DSV JSON-LD. */
function load(text: string): Profile {
  const document = JSON.parse(text) as Record<string, unknown>;
  return Object.keys(document).some((key) => key.startsWith('@')) || 'datasetSchema' in document
    ? parse(document)
    : (document as unknown as Profile);
}

const commands: Record<string, (...texts: string[]) => Result> = {
  normalize: (profile) => done(canonical(load(profile))),
  build: (profile) => done(canonical(build(load(profile)))),
  'to-frictionless': (profile) => done(canonical(toFrictionless(load(profile)))),
  'to-sssom': (profile) => done(toSssom(load(profile))),
  'from-sssom': (sssom, profile) => done(canonical(fromSssom(sssom, load(profile)))),
  merge: (base, incoming) => done(canonical(merge(load(base), load(incoming)))),
  infer: (data) => done(canonical(infer(JSON.parse(data) as Record<string, never[]>))),
  validate: (document) => {
    const errors = validate(JSON.parse(document));
    return { stdout: errors.length ? `${errors.join('\n')}\n` : 'ok\n', code: errors.length ? 1 : 0 };
  },
};

const usage = `usage: linked-codebook <command> <file>...\n\n${Object.entries(spec)
  .map(([name, { files, summary }]) => `  ${[name, ...files.map((file) => `<${file}>`)].join(' ')}\n      ${summary}\n`)
  .join('')}`;

/** Runs a command on the texts of the files it names. It does no input or output itself. */
export function run(args: string[], texts: Record<string, string>): Result {
  const [name = '', ...files] = args;
  const command = commands[name];
  if (!command || (spec as Record<string, { files: string[] }>)[name]?.files.length !== files.length) {
    return { stdout: usage, code: 2 };
  }
  try {
    return command(
      ...files.map((file) => {
        const text = texts[file];
        if (text === undefined) throw new Error(`no such file: ${file}`);
        return text;
      }),
    );
  } catch (error) {
    return { stdout: `error: ${(error as Error).message}\n`, code: 2 };
  }
}
