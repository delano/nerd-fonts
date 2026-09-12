// Runs the shipped css/nfprov.js against fixtures.json and checks the tables
// it embeds (nfprov.mapping) against mapping.json, which it never loads at
// runtime. Also checks that the two mapping.json copies are identical.
// Usage: node check_fixtures.mjs [path/to/nfprov.js]
// Exits non-zero on any failing case, version mismatch, or table drift.
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const target = path.resolve(process.argv[2] || path.join(here, '..', '..', '..', '..', 'css', 'nfprov.js'));
const nfprov = createRequire(import.meta.url)(target);
const fx = JSON.parse(fs.readFileSync(path.join(here, 'fixtures.json'), 'utf8'));

let fail = 0;

// mapping.json: the two copies must match, and the embedded tables must match it.
const mapPath = path.join(here, 'mapping.json');
const mapText = fs.readFileSync(mapPath, 'utf8');
if (mapText !== fs.readFileSync(path.join(here, '..', 'mapping.json'), 'utf8')) {
  fail++;
  console.log('FAIL decorator/mapping.json differs from ../mapping.json');
}
const map = JSON.parse(mapText);
const cp = s => parseInt(s.slice(2), 16);
const selectors = {};
for (const [name, value] of Object.entries(map.variation_selectors)) selectors[name] = cp(value);
const ranges = [];
for (const [key, entry] of Object.entries(map.pua).sort((a, b) => cp(a[0]) - cp(b[0]))) {
  const point = cp(key);
  if (point - 0x100000 !== cp(entry.base) || (entry.provenance || 'ai') !== 'ai') {
    fail++;
    console.log(`FAIL mapping.json ${key}: nfprov.js assumes PUA = 0x100000 + base and state ai`);
  }
  const last = ranges[ranges.length - 1];
  if (last && last[1] === point - 1) last[1] = point; else ranges.push([point, point]);
}
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
if (!same(nfprov.mapping.selectors, selectors)) {
  fail++;
  console.log('FAIL selectors: nfprov.js', JSON.stringify(nfprov.mapping.selectors), 'mapping.json', JSON.stringify(selectors));
}
if (!same(nfprov.mapping.puaRanges, ranges)) {
  fail++;
  console.log('FAIL puaRanges: nfprov.js', JSON.stringify(nfprov.mapping.puaRanges), 'mapping.json', JSON.stringify(ranges));
}
if (nfprov.mapping.version !== map.version) {
  fail++;
  console.log(`FAIL mapping version: nfprov.js ${nfprov.mapping.version}, mapping.json ${map.version}`);
}

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
