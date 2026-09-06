# Provenance build: acceptance criteria

This document fixes what a provenance-enabled Nerd Font must do, what it may
do, and what is out of scope. It exists so that layout-level proposals (see
[issue #3](https://github.com/delano/nerd-fonts/issues/3)) can be judged
against a stable target instead of against each other. The protocol and
implementation are described in [README.md](README.md).

In one sentence: the font must "just work" the way people already expect a Nerd
Font to, and marked text must be visibly distinct in at least the mainstream
shaper stack. Marked text that renders as plain text in some hosts is
acceptable because it does not disrupt anyone. Marked text that renders as tofu
when the provenance font is absent is also acceptable, because the tofu itself
distinguishes marked from unmarked content.

## Must have

| #  | Criterion | Acceptance test |
| -- | --------- | --------------- |
| M1 | Unmarked text shapes identically to the ordinary Nerd Font build of the same source. Ligatures, kerning, real combining marks, icons and metrics are unchanged. | For a fixed corpus, `hb-shape` glyph names, advances and offsets are identical between the ordinary and provenance builds. |
| M2 | Marked text never disrupts the workflow in the provenance font. Every marked character renders as the correct base character with the same advance width as its unmarked form. No tofu, no wrong glyph, no cell misalignment. | `hb-shape` advances for marked and unmarked text are equal in `--mono` builds. |
| M3 | The provenance family installs alongside the ordinary family and is selectable like any other font. Family, full, PostScript and unique names are distinct for every face. | Both families install on macOS, Windows and Linux without one replacing the other. |
| M4 | Provenance is visibly distinct in at least one mainstream shaper. HarfBuzz is the required target; it covers VS Code and other Electron apps, Chrome, Firefox, JetBrains IDEs and most Linux terminals. | Rendered comparison in the verified-renderers table in the README. |
| M5 | Works through the generic patcher on any source font. No per-font authoring. | The existing CI matrix passes with `--provenance`. |
| M6 | Fallback without the provenance font is plain text or tofu, never a different character or reordered text. | Holds for both encodings today: a selector is default-ignorable, a PUA code point renders `.notdef`. |

## May have

- **S1. Ligatures survive in marked text.** Ligature loss inside a marked run
  is itself a visible provenance signal, and in a monospaced font it does not
  change advances, so it does not violate M2.
- **S2. Kerning survives in marked text.** Only observable in proportional
  (`Propo`) builds.
- **S3. Visible in CoreText and DirectWrite.** Native macOS terminals, Xcode,
  Safari, Windows Terminal, Visual Studio. CoreText currently renders marked
  text as plain text, which M4 and M6 permit.
- **S4. A ligature spanning a provenance boundary shows each component's
  state.**
- **S5. Unicode-conformant encoding.** Private variation sequences are not
  conformant; PUA code points are, but fall back to tofu. Both fallbacks are
  accepted, so this is a tooling and interchange concern rather than a
  rendering one.

## Non-goals

- Any change to a renderer, IDE or terminal.
- Provenance on text that carries no provenance code points. A font cannot
  infer authorship from ordinary Unicode.
- Universal renderer support.
- Provenance visible in the fallback rendering.

## Terms

- **Just works** means M1 and M2 together. Unmarked text is untouched; marked
  text is legible and aligned.
- **Backwards compatible** means M1 only. It says nothing about marked text.
- **No encoder changes** means the current per-cluster output of `nfprov.py
  mark` is the input the font must handle. Additive encoder modes are allowed.
- **Fallback** means rendering in a font that lacks the provenance glyphs.

## Approaches ruled out by these criteria

| Approach | Fails |
| -------- | ----- |
| Blanket `IgnoreMarks` on source lookups | M1: changes shaping of real combining marks. Also does not address the actual failure, which is a glyph-ID mismatch. |
| Normalize variants back to plain glyphs before source GSUB | M4: nothing is visible. |
| One family per state (`Hack Nerd Font AI`, `Hack Nerd Font Human`) | M4 in substance: records font choice, not code-point provenance. |
| Out-of-band spans drawn by the renderer | Non-goal: requires renderer changes. |
| Hand-authored per-font layout, slicing ligatures into per-cell halves, exhaustive variant enumeration | M5. |
| Provenance added upstream in each source font | M5. |
| Post-processing a released Nerd Font | M3 and M1: corrective renaming and a second FontForge round trip. |

## What remains

The current implementation (variant glyphs reached through a format 14 `cmap`
and PUA code points) meets M1, M2, M4, M5 and M6. The open must-have is **M3**:
only the version string is tagged today, and the family needs a first-class
naming variant.

Everything else in issue #3 concerns S1 and S2. Two candidates survive:

1. **Early `ccmp` split.** Substitute each variant back into its base glyph
   plus a zero-advance provenance marker glyph, classify the markers as marks
   in GDEF, and make the retained source lookups skip them with
   `UseMarkFilteringSet`. This is the only generic route to S1 and S2. It
   rewrites the GSUB and GPOS of arbitrary fonts, which is exactly where M1 is
   at risk: lookups that already use `IgnoreMarks`, an existing filtering set
   or attachment-type filtering each need handling, and a legacy `kern` table
   has no filtering mechanism at all.
2. **Run-boundary marking in `nfprov.py`.** Encoder-only. Restores ligatures
   strictly interior to a uniform run but not at its edges, because the
   boundary character still becomes a variant glyph. It also changes the
   protocol so that a state persists until the next marker, which weakens
   copy and paste of partial runs.

Decision: finish M3 and ship. Treat the `ccmp` split as a gated experiment
whose gate is the M1 acceptance test across the full font matrix. If it cannot
pass that test generically, drop S1 and document ligature loss as intended
provenance signalling. Do not adopt run-boundary marking; it buys a partial S1
at the cost of a protocol change.
