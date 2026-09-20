// Renders test.html in headless Chromium and WebKit, reports span counts and
// selector width, writes shot-<engine>.png. See README.md for the Playwright setup.
// Usage: node run.mjs            (PLAYWRIGHT_CORE overrides the package path)
import http from 'http'; import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const PW = process.env.PLAYWRIGHT_CORE || `${process.env.HOME}/.npm/_npx/9833c18b2d85bc59/node_modules/playwright-core/index.mjs`;
const { chromium, webkit } = await import(PW);
const dir = path.dirname(fileURLToPath(import.meta.url));
const srv = http.createServer((q, r) => { const f = path.join(dir, q.url === '/' ? 'test.html' : q.url); r.setHeader('content-type', f.endsWith('.js') ? 'text/javascript' : 'text/html; charset=utf-8'); r.end(fs.readFileSync(f)); }).listen(8765);
for (const [name, engine] of [['chromium', chromium], ['webkit', webkit]]) {
  try {
    const b = await engine.launch(); const p = await b.newPage({ viewport: { width: 420, height: 1100 }, deviceScaleFactor: 2 });
    const errs = []; p.on('pageerror', e => errs.push(String(e)));
    await p.goto('http://localhost:8765/');
    const r = await p.evaluate(() => ({
      counts: window.__counts, serverSpans: document.querySelectorAll('#server .prov').length,
      selectorWidthDelta: document.getElementById('b').getBoundingClientRect().width - document.getElementById('a').getBoundingClientRect().width,
      clientCopyHasVS: /\u{E0101}/u.test(document.querySelector('#client .prov-ai').textContent),
      puaDecoded: document.querySelector('#clientpua .prov-ai').textContent.slice(0, 8),
    }));
    await p.screenshot({ path: path.join(dir, `shot-${name}.png`), fullPage: true });
    console.log(name, JSON.stringify(r), errs.length ? errs : '');
    await b.close();
  } catch (e) { console.log(name, 'FAILED', e.message.split('\n')[0]); }
}
srv.close();
