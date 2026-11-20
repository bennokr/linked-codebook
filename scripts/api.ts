// Prints the public API of the TypeScript package as JSON for scripts/generate.py: every export of index.ts that
// is not generated from the data model, with its parameters, the text of its type and its TSDoc.
import { join } from 'node:path';
import ts from 'typescript';

interface Entry {
  name: string;
  doc: string;
  file: string;
  kind: 'function' | 'constant' | 'type';
  signature?: string;
  definition?: string;
}

const directory = join(import.meta.dirname, '../packages/ts');
const entry = join(directory, 'src/index.ts');
const config = ts.parseJsonConfigFileContent(
  ts.readConfigFile(join(directory, 'tsconfig.json'), ts.sys.readFile).config,
  ts.sys,
  directory,
);
const program = ts.createProgram([entry], { ...config.options, noEmit: true, allowImportingTsExtensions: true });
const checker = program.getTypeChecker();

const text = (node: ts.Node): string => node.getText().replace(/\s+/g, ' ').trim();

function parameters(declaration: ts.SignatureDeclaration): string {
  return declaration.parameters
    .map((parameter) => `${text(parameter.name)}${parameter.questionToken || parameter.initializer ? '?' : ''}`)
    .join(', ');
}

function isFunction(node: ts.Node | undefined): node is ts.ArrowFunction | ts.FunctionExpression {
  return node !== undefined && (ts.isArrowFunction(node) || ts.isFunctionExpression(node));
}

function variable(name: string, declaration: ts.VariableDeclaration): Pick<Entry, 'kind' | 'signature'> {
  const { initializer } = declaration;
  return isFunction(initializer)
    ? { kind: 'function', signature: `${name}(${parameters(initializer)})` }
    : { kind: 'constant', signature: name };
}

function members(declaration: ts.InterfaceDeclaration): string {
  return `{ ${declaration.members.map((member) => text(member).replace(/;$/, '')).join('; ')} }`;
}

function detail(name: string, declaration: ts.Declaration): Pick<Entry, 'kind' | 'signature' | 'definition'> {
  if (ts.isFunctionDeclaration(declaration))
    return { kind: 'function', signature: `${name}(${parameters(declaration)})` };
  if (ts.isVariableDeclaration(declaration)) return variable(name, declaration);
  if (ts.isTypeAliasDeclaration(declaration)) return { kind: 'type', definition: text(declaration.type) };
  if (ts.isInterfaceDeclaration(declaration)) return { kind: 'type', definition: members(declaration) };
  return { kind: 'constant', signature: name };
}

function describe(name: string, symbol: ts.Symbol): Entry | undefined {
  const declaration = symbol.declarations?.[0];
  const file = declaration?.getSourceFile().fileName;
  if (!declaration || !file || file.includes('/generated/')) return undefined;
  const doc = ts.displayPartsToString(symbol.getDocumentationComment(checker)).trim();
  return { name, doc, file, ...detail(name, declaration) };
}

const source = program.getSourceFile(entry);
const module = source && checker.getSymbolAtLocation(source);
if (!module) throw new Error(`Cannot read the exports of ${entry}`);
const exports = checker
  .getExportsOfModule(module)
  .map((symbol) =>
    describe(symbol.name, symbol.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(symbol) : symbol),
  );
console.log(JSON.stringify(exports.filter(Boolean), null, 1));
