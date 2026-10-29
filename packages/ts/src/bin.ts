#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { run } from './cli.ts';

const args = process.argv.slice(2);
const texts = Object.fromEntries(args.slice(1).map((file) => [file, readFileSync(file, 'utf8')]));
const { stdout, code } = run(args, texts);
process.stdout.write(stdout);
process.exitCode = code;
