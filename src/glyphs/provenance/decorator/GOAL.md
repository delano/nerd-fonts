# Goal

Let page authors show provenance-marked text without requiring readers to
install a font or changing the producer. A decorator detects marks in text,
wraps marked runs in HTML spans, and lets CSS display the state.

## When to use a decorator

A provenance font can display marks only when the reader has that font and a
compatible text shaper. A decorator works on a page whose author controls the
HTML or DOM. It does not need the reader's font. See
[HTML-RENDERING.md](HTML-RENDERING.md) for the measurements behind this
approach.

## Protocol material

This directory contains the consumer-facing protocol material.

| File | Purpose |
| --- | --- |
| [DECORATOR.md](DECORATOR.md) | Defines decorator input, output, options, and run detection. |
| `fixtures.json` | Defines conformance. A decorator must reproduce each recorded `runs` result. |
| `mapping.json` | A copy of the code-point registry currently held in `../mapping.json`. |
| [HTML-RENDERING.md](HTML-RENDERING.md) | Records the HTML rendering measurements and their limits. |

The duplicate mapping files are temporary. The proposed repository split in
[ADR 0006](../../../../docs/adr/0006-decorator-packages-and-repository.md)
would create one canonical registry and have each package vendor its own copy.

## Current implementation

The current, un-packaged implementations are:

- `css/nfprov.js`: the browser DOM decorator.
- `css/nfprov.css`: an optional stylesheet for the emitted classes.
- `bin/scripts/nfprov.py render`: the Python HTML renderer.

The `prototypes/` directory contains earlier implementations, fixture runners,
and the browser test rig. It is not part of the font build.

## Proposed packages

ADR 0006 proposes JavaScript first, then a Python decoder and renderer, then a
Ruby implementation. Every package would use the same fixture and vendor the
registry. The browser extension and editor integrations are separate future
work; neither exists yet.

## Non-goals

- Defining a visual style. The contract defines classes and an attribute; CSS
  is an integration choice.
- Adding marks to text. The encoder remains in `bin/scripts/nfprov.py`.
- Editor decorations. The same run detection may later support editor APIs.
- Inferring provenance from text that has no marks.

## Status

The JavaScript and Python implementations are in this repository but have not
been published as packages. The repository split and standalone specification
have not started.
