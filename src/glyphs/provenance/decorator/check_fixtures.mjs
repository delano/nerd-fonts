// Runs the shipped css/nfprov.js against fixtures.json.
// Usage: node check_fixtures.mjs [path/to/nfprov.js]
// Exits non-zero on any failing case or version mismatch.
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const target = path.resolve(process.argv[2] || path.join(here, '..', '..', '..', '..', 'css', 'nfprov.js'));
const nfprov = createRequire(import.meta.url)(target);
const fx = JSON.parse(fs.readFileSync(path.join(here, 'fixtures.json'), 'utf8'));

let fail = 0;
if (nfprov.contractVersion !== fx.contract_version) {
  fail++;
  console.log(`FAIL contract version: implementation ${nfprov.contractVersion}, fixture ${fx.contract_version}`);
}
if (nfprov.mappingVersion !== fx.mapping_version) {
  fail++;
  console.log(`FAIL mapping version: implementation ${nfprov.mappingVersion}, fixture ${fx.mapping_version}`);
}
for (const c of fx.cases) {
  const got = nfprov.runs(c.input, c.options);
  if (JSON.stringify(got) !== JSON.stringify(c.runs)) {
    fail++;
    console.log('FAIL', c.name, '\n got', JSON.stringify(got), '\n exp', JSON.stringify(c.runs));
  }
}
console.log(`${path.relative(process.cwd(), target)}: ${fx.cases.length - fail}/${fx.cases.length} pass`);
process.exit(fail ? 1 : 0);
