// Runs the prototype nfprov.js against ../fixtures.json. Usage: node check_fixtures.mjs
// The shipped css/nfprov.js is checked by ../check_fixtures.mjs.
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const src = fs.readFileSync(path.join(here, 'nfprov.js'), 'utf8').replace('})(window);', '})(globalThis);');
(0, eval)(src);
const fx = JSON.parse(fs.readFileSync(path.join(here, '..', 'fixtures.json'), 'utf8'));
let fail = 0, skip = 0;
for (const c of fx.cases) {
  if ('merge_whitespace' in c.options) { skip++; continue; } // the prototype predates this option
  const got = nfprov.runs(c.input, c.options);
  const ok = JSON.stringify(got) === JSON.stringify(c.runs);
  if (!ok) { fail++; console.log('FAIL', c.name, '\n got', JSON.stringify(got), '\n exp', JSON.stringify(c.runs)); }
}
console.log(`${fx.cases.length - fail - skip}/${fx.cases.length} pass, ${skip} skipped (merge_whitespace)`);
process.exit(fail ? 1 : 0);
