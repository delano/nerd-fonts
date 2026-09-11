# 0004. One fixture file defines decorator conformance

Status: accepted. Date: 2026-09-11.

## Context

The decorator will be ported to several languages. Independent
implementations drift unless they share a test.

## Decision

`src/glyphs/provenance/decorator/fixtures.json` is the conformance suite. An
implementation conforms when `runs(input, options)` equals the recorded runs
for every case. The fixture is extended on every breakage report and never
edited to fit an implementation.

## Evidence

The fixture was generated from the Python prototype and checked by hand. The
JavaScript prototype, written independently with `Intl.Segmenter`, passes all
18 cases.

## Consequences

- A port is one file plus a fixture runner.
- Grapheme segmentation differences between hosts surface as fixture failures
  rather than silent divergence.
