// Opens the built page in a browser, runs an example with both libraries and expects the same output.
// Needs `node site/build.ts` first and network access for Pyodide.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join } from 'node:path';
import { after, before, test } from 'node:test';
import { chromium, type Browser } from 'playwright';

const dist = join(import.meta.dirname, 'dist');
const types: Record<string, string> = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
};
const server = createServer((request, response) => {
  const path = join(dist, request.url === '/' ? 'index.html' : (request.url ?? ''));
  readFile(path).then(
    (body) => response.writeHead(200, { 'content-type': types[extname(path)] ?? 'application/octet-stream' }).end(body),
    () => response.writeHead(404).end(),
  );
});
let browser: Browser;

before(async () => {
  await new Promise<void>((resolve) => server.listen(0, resolve));
  browser = await chromium.launch({ executablePath: process.env['CHROMIUM_PATH'] });
});
after(async () => {
  await browser.close();
  server.close();
});

test('both libraries print the same for an example', async () => {
  const page = await browser.newPage();
  const address = server.address();
  await page.goto(`http://localhost:${typeof address === 'object' && address ? address.port : 0}/`);
  await page.selectOption('#example', { label: 'merge/two' });
  await page.click('button[type=submit]');
  await page.waitForFunction(() => document.getElementById('status')?.textContent?.startsWith('Same'), undefined, {
    timeout: 120_000,
  });
  assert.match((await page.textContent('#py')) ?? '', /"title": "Base"/);
});
