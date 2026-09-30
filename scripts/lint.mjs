import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
const files = ['src/server.js', 'test/server.test.js'];
for (const file of files) {
  const text = await readFile(file, 'utf8');
  if (text.includes('\t')) throw new Error(`Tab em ${file}`);
  if (!text.endsWith('\n')) throw new Error(`Falta newline em ${file}`);
}
if (!(await readdir(path.join('src', 'public'))).includes('index.html')) throw new Error('Front-end ausente');
console.log('Lint de estrutura e estilo: OK');
