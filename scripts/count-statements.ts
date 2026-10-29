// Prints the number of statements in the TypeScript files under the given directories.
// Declarations of types are not counted: they are erased and have no counterpart in Python.
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import ts from 'typescript';

const TYPE_ONLY = new Set([ts.SyntaxKind.InterfaceDeclaration, ts.SyntaxKind.TypeAliasDeclaration]);

function count(node: ts.Node): number {
  let total = ts.isStatement(node) && !TYPE_ONLY.has(node.kind) && !ts.isBlock(node) ? 1 : 0;
  ts.forEachChild(node, (child) => {
    total += count(child);
  });
  return total;
}

const files = process.argv.slice(2).flatMap((directory) =>
  readdirSync(directory, { recursive: true, encoding: 'utf8' })
    .filter((file) => file.endsWith('.ts') && !file.includes('generated'))
    .map((file) => join(directory, file)),
);
const total = files.map((file) => count(ts.createSourceFile(file, readFileSync(file, 'utf8'), ts.ScriptTarget.ES2022, true))).reduce((a, b) => a + b, 0);
console.log(total);
