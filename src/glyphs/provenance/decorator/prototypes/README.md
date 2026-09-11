# Decorator prototypes

The two implementations that pass `../fixtures.json`, plus the rig that
measured them. Kept as prototypes: the JavaScript belongs in an npm package
and the Python in `nfprov.py render` (ADR 0006), and neither move has
happened. Nothing here is a dependency of the font build.

| File | Role |
| --- | --- |
| `nfprov.js` | Client-side. `runs(text, opts)` per DECORATOR.md using `Intl.Segmenter`; `render(root)` walks text nodes and wraps runs in spans. No dependencies. |
| `nfprov_html.py` | Server-side. `runs(text, strip)` and `to_html(text, strip)`. Reuses `cluster_end` from `bin/scripts/nfprov.py` and reads `../mapping.json`. |
| `check_fixtures.mjs`, `check_fixtures.py` | Fixture runners. Exit non-zero on any failing case. |
| `gen_fixtures.py` | Generates `../fixtures.json` from the Python implementation. Run only to add cases; the fixture is checked by hand and never edited to fit an implementation. |
| `build_page.py` | Writes `test.html` from `example-selector.txt` and `../../example-marked.txt`. |
| `test.html` | Four sections: raw selector text, Python spans, JS spans on selector text, JS spans on PUA text. Inline CSS: sawtooth underline for `ai`, dashed for `unknown`. |
| `run.mjs` | Headless Chromium and WebKit: span counts, selector width, screenshots. |
| `copy.mjs` | Selects each section and counts selectors in the selection text. |

## Run

```sh
node check_fixtures.mjs
../../../../../.venv/bin/python check_fixtures.py
node run.mjs
node copy.mjs
```

The Python needs fontTools only transitively through `nfprov.py`; use the
repo `.venv`.

## Results, 2026-09-11

Both fixture runners: 18/18.

`run.mjs`, Chromium 1243 and WebKit 2358 (WebKit 26.5), 420 px viewport at
2x, system font:

- 7 spans per section in every path, identical between engines.
- Selector width delta 0: a retained selector adds no advance in either
  engine.
- Client-side span text still contains the selector; PUA input is re-emitted
  as base plus selector.

`copy.mjs`: 322 selectors in the selection text of every section in both
engines, so selection of decorated text round-trips the marks (ADR 0002). The
`*TextEqualsRaw` flags are false only because each section's heading differs.

Not measured: find-in-page, paste into an editor, screen readers, a real
device. See the Open sections of ADRs 0002 and 0008.

## Playwright setup on this machine

There is no global Playwright. `run.mjs` and `copy.mjs` import
`playwright-core` 1.63.0-alpha from the npx cache; override with
`PLAYWRIGHT_CORE=/path/to/playwright-core/index.mjs`. That package expects
`chromium-1243` and `webkit-2358` under `~/Library/Caches/ms-playwright`.
The older cached `webkit-2203` launched but never answered the first time and
had to be killed, so a fresh WebKit was installed with

```sh
node /Users/d/.npm/_npx/9833c18b2d85bc59/node_modules/playwright-core/cli.js install webkit
```

Do not pass `executablePath` to a mismatched cached build. Firefox is not
installed for this package; the cached `firefox-1490` hangs with it. Headless
WebKit is the only local proxy for iOS Safari.
