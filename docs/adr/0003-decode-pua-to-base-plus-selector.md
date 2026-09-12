# 0003. Decode PUA input to base plus selector

Status: accepted. Date: 2026-09-11.

## Context

PUA code points are tofu without the font, so a decorator must replace them.
Replacing with the bare base character loses provenance on copy, measured as
zero selectors in the selection of a PUA-decoded section.

## Decision

A PUA code point becomes its base character followed by the selector for its
state. With `strip`, the bare base character.

## Evidence

Both prototypes were changed and pass the PUA cases in
`src/glyphs/provenance/decorator/fixtures.json`.

## Consequences

- A page built from PUA text copies out in the selector encoding.
- The decorator never emits PUA. The selector encoding is the interchange form.
