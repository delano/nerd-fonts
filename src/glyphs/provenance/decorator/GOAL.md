# Goal

Let anyone render provenance-marked text on a page they control, on any
browser, without the reader installing a font and without changing the
producer.

## Why

Marked text depends today on a P+ font and a shaper that honours it. That
excludes every mobile browser, every iOS browser, and every page whose author
controls the markup but not the reader's fonts. See HTML-RENDERING.md for the
measurements that show a decorator pass closes that gap.

## What this directory is

The consumer-side contract for the decorator, in the form that lets a third
party implement it in an afternoon and prove it correct:

| File | Role |
| --- | --- |
| DECORATOR.md | The contract: input, algorithm, output markup, options. |
| fixtures.json | Conformance cases. An implementation is correct if it reproduces every `runs` entry. |
| mapping.json | Copy of `../mapping.json`, the code point registry an implementation vendors. The source of truth stays one level up. |
| HTML-RENDERING.md | The measurements behind the approach. |

## Rollout

1. Fix the contract and fixture here. Nothing else depends on a package.
2. JavaScript on npm: DOM decorator, rehype plugin, markdown-it plugin. npm
   gives a CDN script tag, so the smallest integration is one script tag and
   one stylesheet.
3. Python on PyPI: `nfprov render`, next to the marker.
4. Ruby gem: kramdown hook for Jekyll and GitHub Pages.

Each port is one file plus the fixture runner and carries no dependencies. Ship
the JavaScript port and wait for one breakage report before porting further.
Extend the fixture on every report.

## Non-goals

- Visual style. Implementations emit a class and an attribute. CSS is the
  integrator's. A shared stylesheet may ship alongside but is not the contract.
- Producing marks. The marker in `bin/scripts/nfprov.py` does that.
- Editor decorations. The same run detection can drive VS Code or CodeMirror
  decoration APIs; that is a separate deliverable.
- Inferring provenance from unmarked text.

## Status

Two prototypes, Python and JavaScript, pass all cases in fixtures.json.
Neither is in this repository. The fixture was generated from the Python
prototype and checked by hand; the JavaScript prototype was then run against it.
