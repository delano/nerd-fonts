# 0006. Protocol repository and ecosystem packages

Status: proposed. Date: 2026-09-11.

## Context

The decorator will have implementations in more than one language. ADR 0004
makes the shared fixture the conformance test. A separate repository would
hold the protocol material and the reference implementations without making
them part of the font patcher.

## Proposed repository boundary

The new repository would contain the protocol and code used to consume it:

- The protocol specification. It does not exist as a standalone file yet. Its
  title depends on the unresolved protocol name.
- One canonical `mapping.json` code-point registry. The two current copies,
  in `src/glyphs/provenance/mapping.json` and
  `src/glyphs/provenance/decorator/mapping.json`, are byte-identical. The
  split would replace them with one source registry.
- `fixtures.json`, the conformance suite defined by ADR 0004.
- The JavaScript decorator and stylesheet, currently `css/nfprov.js` and
  `css/nfprov.css`.
- The Python shared core and HTML renderer from `bin/scripts/nfprov.py`:
  `load_mapping`, `is_combining`, `cluster_end`, `do_runs`, `to_html`, and
  the decorator form of `strip`.
- Fixture runners for the JavaScript and Python implementations.
- Protocol documentation that is not specific to the font fork:
  `DECORATOR.md`, `HTML-RENDERING.md`, `GOAL.md`, and ADRs 0001–0009.

Each published package would vendor a copy of `mapping.json`; packages would
not depend on one another. The source registry and fixture would remain in the
new repository.

This font fork would keep the work that builds or verifies fonts:

- `font-patcher` and its `--provenance` option. After the split, it would read
  the registry supplied by the protocol repository.
- `bin/scripts/test-provenance.py`, which verifies built fonts and requires
  `fontTools`.
- The encoder operations in `bin/scripts/nfprov.py`: `do_mark`,
  `do_mark_added`, and `do_convert`.
- `do_inspect`, which is diagnostic tooling for the font workflow.
- `src/glyphs/provenance/README.md`, limited to how this fork wires the
  feature into the patcher and its build.
- Fork-specific material: `zed-about.md`, examples, `ROLLOUT.txt`, and
  prototype screenshots.

## Python extraction

`bin/scripts/nfprov.py` currently combines encoder, renderer, shared parsing,
and diagnostics. The shared parsing boundary is already explicit: every
`do_*` function receives `selectors`, `pua2base`, and `base2pua` as arguments
instead of using mutable module state.

The proposed extraction is the shared core plus the decoder and renderer. The
fork would keep a thin encoder and use the extracted package. This keeps
`cluster_end` with the fixture that tests its effect on decorator output.

The existing `selftest` must be divided as part of this work. Its fixture loop
covers `do_runs` and belongs with the package. Its mark/convert round trips
cover the fork-side encoder. Tests for cluster handling should remain with the
shared core. No files should move until this test ownership is explicit.

This resolves an ambiguity in the earlier wording, “`nfprov render`, beside
the marker.” It should not mean that the entire marker CLI moves. This is a
proposal, not a completed extraction.

## Packages and rollout

1. Publish the JavaScript package first. It would provide the DOM decorator,
   a rehype plugin, and a markdown-it plugin. A browser integration can use a
   script and stylesheet.
2. Wait for one breakage report and add its case to `fixtures.json` before
   starting another port.
3. Publish the Python decoder and renderer on PyPI.
4. Publish a Ruby gem with a kramdown hook for Jekyll and GitHub Pages, then
   test it in Onetime Secret.

Every package would expose `runs` and either `to_html` or `decorate`. The only
options would be `strip`, `merge_whitespace`, and a class prefix.

A browser extension based on the client-side decorator is the proposed route
for pages whose author cannot add a decorator pass. The extension does not
exist yet.

## Naming

No protocol name, organisation, repository name, package name, or domain has
been chosen. The protocol name must be decided before the specification is
published.

The current names have different roles:

- `nfprov` is the in-fork Python tool name and the names of the current
  JavaScript and CSS files.
- `prov` is the default and shipped CSS class prefix. The decorator emits
  `prov`, `prov-STATE`, and `data-prov`.

A name decision should use one term for the organisation or namespace,
repository role suffixes, package names, class prefix, and specification title.
Role suffixes are the only allowed variation. The term must not be specific to
fonts or derived from Nerd Fonts; the protocol is also used by HTML spans and
editor decoration APIs. It must cover generated and reserved states, not only
AI. Changing `prov` would be a compatibility change for existing CSS users.

Whether `prov` is suitable as a public protocol name, whether the public
property is called provenance or attribution, and whether a single namespace
is available on GitHub, npm, PyPI, RubyGems, and a domain are open questions.
Availability must be checked before the name is adopted.

## Status

No package has been published, no browser extension exists, and the repository
split has not started.
