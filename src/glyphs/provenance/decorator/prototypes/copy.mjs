// Selection test: selects each section of test.html and counts selectors in
// the selection text, so copy round-trips are measured, not assumed.
// Usage: node copy.mjs            (PLAYWRIGHT_CORE overrides the package path)
import http from 'http'; import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const PW = process.env.PLAYWRIGHT_CORE || `${process.env.HOME}/.npm/_npx/9833c18b2d85bc59/node_modules/playwright-core/index.mjs`;
const { chromium, webkit } = await import(PW);
const dir = path.dirname(fileURLToPath(import.meta.url));
const srv = http.createServer((q, r) => { const f = path.join(dir, q.url === '/' ? 'test.html' : q.url); r.setHeader('content-type', f.endsWith('.js') ? 'text/javascript' : 'text/html; charset=utf-8'); r.end(fs.readFileSync(f)); }).listen(8766);
for (const [name, engine] of [['chromium', chromium], ['webkit', webkit]]) {
  const b = await engine.launch(); const p = await b.newPage();
  await p.goto('http://localhost:8766/');
  const r = await p.evaluate(() => {
    const count = s => (s.match(/[\u{E0100}-\u{E0104}]/gu) || []).length;
    const sel = id => { const range = document.createRange(); range.selectNodeContents(document.getElementById(id)); const s = getSelection(); s.removeAllRanges(); s.addRange(range); return s.toString(); };
    const raw = sel('raw'), server = sel('server'), client = sel('client'), pua = sel('clientpua');
    return { rawSelectors: count(raw), serverSelectors: count(server), clientSelectors: count(client), puaDecodedSelectors: count(pua), serverTextEqualsRaw: server === raw, clientTextEqualsRaw: client === raw };
  });
  console.log(name, JSON.stringify(r)); await b.close();
}
srv.close();
