// Runs nfprov.js against ../fixtures.json. Usage: node check_fixtures.mjs
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const src = fs.readFileSync(path.join(here, 'nfprov.js'), 'utf8').replace('})(window);', '})(globalThis);');
(0, eval)(src);
const fx = JSON.parse(fs.readFileSync(path.join(here, '..', 'fixtures.json'), 'utf8'));
let fail = 0;
for (const c of fx.cases) {
  const got = nfprov.runs(c.input, c.options);
  const ok = JSON.stringify(got) === JSON.stringify(c.runs);
  if (!ok) { fail++; console.log('FAIL', c.name, '\n got', JSON.stringify(got), '\n exp', JSON.stringify(c.runs)); }
}
console.log(`${fx.cases.length - fail}/${fx.cases.length} pass`);
process.exit(fail ? 1 : 0);
