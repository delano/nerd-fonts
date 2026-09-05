# Inline Typographic Provenance

> **Status: implementation plan.** This directory currently contains the plan only.
> `mapping.json`, `font-patcher --provenance`, `nfprov.py`, and
> `test-provenance.py` are proposed additions; they are not in this checkout.

This document turns the external proposal _Inline Typographic Provenance for
Nerd Fonts_ into practical changes for this repository. The source proposal
describes the protocol as “a lightweight convention for distinguishing
human-written and AI-written text using Unicode code points embedded directly in
the text.” It defines the provenance states, encodings, fallback behavior, and
editor semantics. This plan defines the Nerd Fonts implementation, tooling, and
release work.

It is for contributors implementing the feature, not for users of the current
`font-patcher`.

## Proposed behavior

A provenance-aware patched font would render marked text using variants derived
from the source font's glyphs. Unlike existing glyph sets in `src/glyphs/`, it
would not copy symbols from a separate symbol font.

The proposed encodings are:

| Encoding               | Text                        | Font with provenance glyphs | Font without provenance glyphs |
| ---------------------- | --------------------------- | --------------------------- | ------------------------------ |
| Variation selector     | `<base>` followed by `VS_*` | Variant glyph               | Plain base glyph               |
| Private Use Area (PUA) | `PUA_AI_<base>`             | `.ai` glyph                 | Missing-glyph display          |

## Proposed files

- `mapping.json`: versioned registry of allocated code points.
- `README.md`: this proposal and implementation guide.
- `bin/scripts/nfprov.py`: reference encoder and decoder.
- `bin/scripts/test-provenance.py`: CI-only validator for patched fonts.

`bin/scripts/archive-font-patcher.sh` already archives all of `src/glyphs/`.
Once `mapping.json` exists, that script will include it in `FontPatcher.zip`.

## Code-point allocation

### Variation selectors

| State           | Selector           | Status                  |
| --------------- | ------------------ | ----------------------- |
| Explicit human  | `U+E0100` (`VS17`) | Generated               |
| AI              | `U+E0101` (`VS18`) | Generated               |
| Unknown         | `U+E0102` (`VS19`) | Generated               |
| Human-edited AI | `U+E0103` (`VS20`) | Reserved; not generated |
| Mixed or other  | `U+E0104` (`VS21`) | Reserved; not generated |

These selectors would be a private convention shared by encoders, decoders, and
patched fonts. They are not registered Unicode variation sequences.

### PUA counterparts

Do not allocate provenance glyphs in Supplementary PUA-A
(`U+F0000`–`U+FFFFD`). The current `Material` patch set occupies
`U+F0001`–`U+F1AF0` in that range (`font-patcher`, `setup_patch_set`). For
example, the illustrative `U+F0041` allocation would collide with that set.

Use Supplementary PUA-B (plane 16) instead, with this fixed allocation:

```text
PUA_AI(cp) = 0x100000 + cp    for 0x0020 <= cp <= 0xFFFD
```

This allocates a PUA counterpart for every Basic Multilingual Plane (BMP) base
character without a lookup formula. In the current patch-set definitions,
Supplementary PUA-B does not overlap an allocated glyph range.

The initial profile (`"version": 1`) would list non-whitespace Basic Latin
and Latin-1 Supplement base characters (`U+0020`–`U+00FF`) that are present in
the source font. This covers the initial proposal's practical Latin,
punctuation, and symbol subset. The formula reserves the remaining range; later
profiles must not give those code points a different meaning.

### Stability rules

The protocol specification should make the following compatibility rules
normative:

- Published `mapping.json` code points are never reassigned or removed.
- A profile that adds base characters or states increments `version` and appends
  entries only.
- Before changing an allocation range, check every `SymStart` and `SymEnd` in
  `font-patcher` and the [Codepoint Conflicts wiki page][wiki-conflicts].

## Proposed `mapping.json` format

```json
{
  "version": 1,
  "variation_selectors": {
    "human": "U+E0100",
    "ai": "U+E0101",
    "unknown": "U+E0102",
    "edited": "U+E0103",
    "mixed": "U+E0104"
  },
  "pua": {
    "U+100041": { "base": "U+0041", "provenance": "ai" }
  }
}
```

Although the PUA formula is fixed, consumers should read the `pua` table. A
future profile may restrict an entry or attach additional metadata.

## Proposed `font-patcher` integration

### Command-line option

Add this option to the `Symbol Fonts` argument group:

```text
--provenance[={identical|subtle|explicit}]
```

It should use the same optional-value pattern as `--braille`:

- If supplied without a value, it selects `identical`.
- It is not enabled by `--complete`.
- It warns and does nothing for the Symbols Only font, because variants require
  base glyphs from the source font.

Keeping the option separate from `--complete` makes it opt-in. Release builds
could pass `--provenance=subtle` through `NERDFONTS` after the project decides
whether such fonts need a distinct public family name.

### Patch order

Add provenance glyphs after the patch-set loop and the glyph-count check, but
before the `grave` fix-up in `font_patcher.patch()`:

```python
        if self.args.glyphcount:
            check_glyph_counts(glyphnum)

        self.add_provenance_glyphs()
```

This order matters because `set_sourcefont_glyph_widths()` has already
normalized glyph widths for `--mono`, and `copy_glyphs()` may rebuild the
encoding or clear `altuni` on overwritten slots.

Do not add provenance to `patch_set`. Existing `Filename` and `Font` patch-set
entries create a separate FontForge font, then copy, scale, and align its
glyphs. Provenance variants instead reference existing glyphs in
`self.sourceFont` and must retain their original scale.

### Glyph generation

The following is the proposed implementation shape:

```python
def add_provenance_glyphs(self):
    """Add VS and PUA variants derived from the source font's own glyphs."""
    if not self.args.provenance:
        return
    if self.symbolsonly:
        logger.warning("Provenance glyphs need base glyphs; skipping Symbols Only font")
        return

    mapping_file = os.path.join(self.args.glyphdir, "provenance", "mapping.json")
    with open(mapping_file, encoding="utf-8") as file:
        mapping = json.load(file)

    vs = {name: int(value[2:], 16) for name, value in mapping["variation_selectors"].items()}
    mark = self.create_provenance_mark() if self.args.provenance != "identical" else None

    added = 0
    for pua_string, entry in mapping["pua"].items():
        base = int(entry["base"][2:], 16)
        pua = int(pua_string[2:], 16)
        if base not in self.sourceFont:
            continue
        if self.args.careful and pua in self.sourceFont:
            continue

        base_glyph = self.sourceFont[base]
        ai = self.sourceFont.createChar(pua, base_glyph.glyphname + ".ai")
        self.derive_provenance_glyph(ai, base_glyph, mark)
        ai.altuni = ((base, vs["ai"], 0),)

        for state in ("human", "unknown"):
            glyph = self.sourceFont.createChar(-1, base_glyph.glyphname + "." + state)
            self.derive_provenance_glyph(glyph, base_glyph, None)
            glyph.altuni = ((base, vs[state], 0),)
        added += 1

    self.sourceFont.encoding = "UnicodeFull"
    logger.info("Added provenance variants for %d base glyphs (%s)", added, self.args.provenance)


def derive_provenance_glyph(self, glyph, base_glyph, mark):
    """Create a metric-identical base-glyph reference, optionally with a mark."""
    glyph.addReference(base_glyph.glyphname)
    if mark:
        dx = (base_glyph.width - mark.width) / 2
        glyph.addReference(mark.glyphname, (1, 0, 0, 1, dx, 0))
    glyph.width = base_glyph.width
    glyph.vwidth = base_glyph.vwidth
    glyph.manualHints = True
```

The implementation must verify the FontForge behavior on each supported
FontForge version:

- `createChar(-1, name)` creates the unencoded human and unknown variants.
- `altuni` entries with a selector produce the required format 14 `cmap`
  subtable.
- CFF output flattens references and TrueType output preserves composites.

Do not add `fontTools` as a runtime dependency of `font-patcher`. The patcher
archive is intended to run with FontForge; `fontTools` is only proposed for the
CI validator.

### Presentation styles

| Style       | `.human` and `.unknown` | `.ai`                                            |
| ----------- | ----------------------- | ------------------------------------------------ |
| `identical` | Reference to base glyph | Reference to base glyph                          |
| `subtle`    | Reference to base glyph | Base glyph with a small dot below the baseline   |
| `explicit`  | Reference to base glyph | Base glyph with a bar spanning its advance width |

`create_provenance_mark()` should create one unencoded glyph named
`provenance.mark`. It can use `glyphPen`, as the Braille generator does. The
implementation must maintain these invariants:

- The mark remains within `self.font_dim['ymin']` and `self.font_dim['ymax']`.
- After centering, the mark remains within the base glyph's advance width.
- For `--mono`, use `self.font_dim['width']` as that width.
- Scale the mark relative to `self.sourceFont.em`, not fixed font units.

### Font metadata

Record the profile version in the font's Version name (name ID 5). Insert the
profile tag before the Nerd Fonts version segment:

```python
prov = ";NFProv " + PROVENANCE_PROFILE if self.args.provenance else ""
self.sourceFont.version += prov + ";" + projectName + " " + version
```

The insertion order is important because `FontnameParser.rename_font()` derives
`UniqueID` from the last whitespace-separated Version token. The intended result
is, for example:

```text
Version 3.003;NFProv 1;Nerd Fonts 3.5.1
```

### Glyph-count check

Register generated glyphs so `--experimental check-glyph-count` does not report
them as unexplained:

```python
glyphnum.update({"Provenance": (None, added)})
```

`check_glyph_counts()` already skips entries with an `ish` value of `None`, so
no icon cheat-sheet file is required.

## Files that should remain unchanged

- `glyphnames.json`, `bin/scripts/lib/i_*.sh`, and `css/` describe icon glyphs.
  Provenance variants are source-font characters; `mapping.json` would be their
  registry.
- The icon-set table in `src/glyphs/README.md` has no suitable upstream or
  license row for this feature. Add only a one-line pointer to this directory.
- `Dockerfile` needs no new runtime dependency.
- `fonts.json`, the release matrix, family names, and archive layout should not
  change as part of the implementation.

## Proposed helper tools

### `bin/scripts/nfprov.py`

Implement a standard-library-only reference encoder and decoder. It should load
`mapping.json` relative to its own location and support:

```text
nfprov.py inspect FILE
nfprov.py mark --human|--unknown|--ai [--mode=vs|pua] FILE
nfprov.py convert --from=vs|pua --to=vs|pua FILE
nfprov.py strip FILE
```

`strip` must warn that it is lossy. Unrecognized code points should pass through
unchanged. Add the Nerd Fonts and script-version header lines required by
`version-bump.sh`, and list the tool in `bin/scripts/README.md` as `[4]`.

### `bin/scripts/test-provenance.py`

Implement a `fontTools`-based validator for CI. It should verify that:

- A format 14 `cmap` subtable exists.
- For each mapped base glyph present in the font, the PUA code point and
  `base + VS_AI` resolve to the same glyph.
- `base + VS_HUMAN` and `base + VS_UNKNOWN` resolve to glyphs.
- Each variant has the same advance width as its base glyph.
- `head.yMin`, `head.yMax`, and `hhea` ascender and descender match a build of
  the same font without `--provenance`.

List the validator in `bin/scripts/README.md` as `[1]`.

## Proposed CI and release changes

### Font-patcher workflow

`.github/workflows/font-patcher.yml` already runs when `src/glyphs/**` changes
and installs `fonttools`. After the existing Hack patch step, add a provenance
build and validator step:

```yaml
- name: Patch provenance font
  run: |
    fontforge --script ./font-patcher src/unpatched-fonts/Hack/Hack-Regular.ttf \
      --complete --provenance=subtle --quiet --no-progressbars \
      --outputdir "$GITHUB_WORKSPACE/temp/prov/"

- name: Validate provenance tables
  run: |
    python3 bin/scripts/test-provenance.py \
      "$GITHUB_WORKSPACE/temp/prov/HackNerdFont-Regular.ttf"
```

Also add a `--mono` provenance build, since width normalization precedes variant
generation.

### Release workflow

`gotta-patch-em-all-font-patcher!.sh` already forwards `NERDFONTS` to its
`font-patcher` calls. To distribute provenance-aware fonts, the release workflow
could set:

```yaml
env:
  NERDFONTS: "--provenance=subtle"
```

Do this only after deciding whether public distribution needs a distinct font
family name. That decision affects `projectName` and
`projectNameAbbreviation` in `font-patcher`.

## Implementation validation

After implementing the feature, use this proposed validation sequence for a Hack
build and, separately, a Fira Code build. It requires FontForge, HarfBuzz's
`hb-shape`, and the proposed validator:

```bash
# Hack: patch and validate the generated font.
fontforge --script ./font-patcher src/unpatched-fonts/Hack/Hack-Regular.ttf \
  --complete --provenance=subtle --debug 2 --outputdir /tmp/prov
python3 bin/scripts/test-provenance.py /tmp/prov/HackNerdFont-Regular.ttf

# The two inputs should shape to A.ai.
hb-shape /tmp/prov/HackNerdFont-Regular.ttf -u "0041,E0101"
hb-shape /tmp/prov/HackNerdFont-Regular.ttf -u "100041"

# Fira Code: create the file before testing its contextual alternatives.
fontforge --script ./font-patcher src/unpatched-fonts/FiraCode/FiraCode-Regular.ttf \
  --complete --provenance=subtle --debug 2 --outputdir /tmp/prov
hb-shape /tmp/prov/FiraCodeNerdFont-Regular.ttf --features=calt \
  -u "003D,E0101,003E,E0101"
```

Repeat the validation for `--mono`, `--variable-width-glyphs`, an OTF source,
and a font with `calt` ligatures. Do not commit generated test fonts.

Variation selectors have Unicode general category `Mn`. Contextual and ligature
lookups that do not use `IgnoreMarks` may not match across a selector. PUA
variants have no inherited kerning or ligatures. Confirm and document the
observed behavior per font during implementation.

[wiki-conflicts]: https://github.com/ryanoasis/nerd-fonts/wiki/Codepoint-Conflicts
