import { canonical } from './canonical.ts';
import { commands as spec } from './constants.ts';
import type { Profile } from './generated/types.ts';
import { parseCondition } from './condition.ts';
import { infer } from './infer.ts';
import { build } from './jsonld.ts';
import { merge } from './merge.ts';
import { conditions, missingness } from './missingness.ts';
import { parse } from './read.ts';
import { fromRedcap } from './redcap.ts';
import { toFrictionless } from './frictionless.ts';
import { fromReadstat } from './readstat.ts';
import { fromSssom, toSssom } from './sssom.ts';
import { fromTables, tableWarnings, toTables } from './table.ts';
import { validate } from './validate.ts';

/** What `run` returns: the output text and the exit code. */
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
  'parse-condition': (text) => done(canonical(parseCondition(text))),
  conditions: (profile) => done(canonical(conditions(load(profile)))),
  missingness: (profile, data) => done(canonical(missingness(load(profile), JSON.parse(data)))),
  'from-readstat': (variables) => done(canonical(fromReadstat(JSON.parse(variables)))),
  'from-redcap': (dictionary) => done(canonical(fromRedcap(dictionary))),
  'from-tables': (tables) => done(canonical(fromTables(JSON.parse(tables)))),
  'to-tables': (profile) => done(canonical(toTables(load(profile)))),
  'check-tables': (tables) => {
    const warnings = tableWarnings(JSON.parse(tables));
    return done(warnings.length ? `${warnings.join('\n')}\n` : 'ok\n');
  },
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

/**
 * The command line as a function: runs a command on the texts of the files it names.
 *
 * It returns `{ stdout, code }` and does no input or output itself. See [Command
 * line](https://bennokr.github.io/linked-codebook/docs/cli).
 */
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
