# Inline Typographic Provenance

This directory holds the mapping table that `font-patcher --provenance` uses to add
provenance-aware glyph variants to a font. The variants are derived from the source
font's own glyphs, not copied from a symbol font like the other sets in `src/glyphs/`.

The protocol itself (states, encodings, fallback behavior, editor semantics) is defined
in the design document "Inline Typographic Provenance for Nerd Fonts". This README only
covers how it is wired into this repository.

## Motivation

Text produced by AI tools and text written by people are indistinguishable once pasted.
The protocol marks provenance per character with Unicode code points, so it survives
copy and paste of any fragment without a sidecar. A patched font is the presentation
layer: it renders marked characters with `.human`, `.ai`, and `.unknown` glyph variants
that keep the base glyph's metrics.

Two encodings resolve to the same glyph:

| Encoding             | Text                       | Supporting font | Unsupported font |
|----------------------|----------------------------|-----------------|------------------|
| Variation selector   | `<base>` + `VS_*`          | variant glyph   | plain base glyph |
| Private Use Area     | `PUA_AI_<base>`            | `.ai` glyph     | tofu             |

## Contents

* `mapping.json`: The published, versioned mapping (see below). Shipped in `FontPatcher.zip`
  automatically because `archive-font-patcher.sh` zips all of `src/glyphs/`.
* `README.md`: This file.

## Code point allocation

### Variation selectors

| State           | Selector | Note                     |
|-----------------|----------|--------------------------|
| explicit human  | `U+E0100`| VS17                     |
| ai              | `U+E0101`| VS18                     |
| unknown         | `U+E0102`| VS19                     |
| human-edited ai | `U+E0103`| reserved, not generated  |
| mixed / other   | `U+E0104`| reserved, not generated  |

These are a private convention between encoders, decoders, and patched fonts. They are
not registered Unicode variation sequences.

### PUA counterparts

**Do not use Supplementary PUA-A (`U+F0000`-`U+FFFFD`).** Material Design Icons already
occupy `U+F0001`-`U+F1AF0` there (see the `Material` entry in `setup_patch_set`), so the
illustrative `U+F0041` example from the design document would collide with an icon.

The mapping uses Supplementary PUA-B (Plane 16) with a fixed offset:

```text
PUA_AI(cp) = 0x100000 + cp      for 0x0020 <= cp <= 0xFFFD
```

This covers every BMP base character without a lookup table and cannot overlap any glyph
set this project patches in (all of which live in the BMP PUA or Plane 15).

The initial profile (`"version": 1`) enumerates only Basic Latin and Latin-1 Supplement
(`U+0020`-`U+00FF`, whitespace excluded). Everything else is reserved by the formula and
must not be assigned to any other meaning later.

### Stability rules

* Once a code point is published in `mapping.json` it is never reassigned or removed.
* A profile that adds base characters or states bumps `version` and only appends.
* Any range change must be checked against every `SymStart`/`SymEnd` in `font-patcher`
  and the [Codepoint Conflicts wiki page][wiki-conflicts] before merging.

## `mapping.json` format

```json
{
  "version": 1,
  "variation_selectors": {
    "human":   "U+E0100",
    "ai":      "U+E0101",
    "unknown": "U+E0102",
    "edited":  "U+E0103",
    "mixed":   "U+E0104"
  },
  "pua": {
    "U+100041": { "base": "U+0041", "provenance": "ai" }
  }
}
```

The `pua` object is explicit even though the formula is fixed. Consumers must read the
table, not derive it, so that a future profile can restrict or annotate entries.

## `font-patcher` integration

### Command line

```
--provenance[={identical|subtle|explicit}]
```

* Lives in the `Symbol Fonts` argument group next to `--braille`, same `nargs='?'` plus
  `const` plus `choices` pattern. Default when the option is given: `identical`.
* Not implied by `--complete`. Release builds enable it via the `NERDFONTS` environment
  variable (see Release below). This keeps the option additive and the default patch
  result byte-identical to upstream.
* Ignored with a warning for the Symbols Only font (`self.symbolsonly`), because there
  are no Latin glyphs to derive from. Users on the fontconfig fallback route
  (`10-nerd-font-symbols.conf`) therefore do not get provenance glyphs.

### Where it runs

`font_patcher.patch()` gains one call **after** the `patch_set` loop and the
`check_glyph_counts` block, and **before** the `grave` fixup:

```python
        if self.args.glyphcount:
            check_glyph_counts(glyphnum)

        self.add_provenance_glyphs()
```

It has to run late because:

* `set_sourcefont_glyph_widths()` (run for `--mono`) must already have normalized the
  Latin widths that the variants inherit.
* `copy_glyphs()` may have cleared `altuni` on overwritten slots and rebuilt the encoding;
  provenance must add its own `altuni` after that, not before.

It does **not** go into the `patch_set` table. Both table styles (`Filename` and the
`Font` hook used by Braille) produce a *separate* FontForge font that `copy_glyphs()` pastes
from, then scales and aligns as icons. Provenance glyphs are references to glyphs already
in `self.sourceFont` and must not be scaled.

### Algorithm

```python
    def add_provenance_glyphs(self):
        """ Add provenance variants (VS and PUA) derived from the source font's own glyphs """
        if not self.args.provenance:
            return
        if self.symbolsonly:
            logger.warning("Provenance glyphs need base glyphs, skipping for Symbols Only font")
            return
        mapping_file = os.path.join(self.args.glyphdir, 'provenance', 'mapping.json')
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        vs = { k: int(v[2:], 16) for k, v in mapping['variation_selectors'].items() }
        mark = self.create_provenance_mark() if self.args.provenance != 'identical' else None

        added = 0
        for pua_s, entry in mapping['pua'].items():
            base = int(entry['base'][2:], 16)
            pua = int(pua_s[2:], 16)
            if base not in self.sourceFont:
                continue
            if self.args.careful and pua in self.sourceFont:
                continue
            base_glyph = self.sourceFont[base]
            # AI: encoded at the PUA code point, also reachable via base + VS_AI
            ai = self.sourceFont.createChar(pua, base_glyph.glyphname + '.ai')
            self.derive_provenance_glyph(ai, base_glyph, mark)
            ai.altuni = ((base, vs['ai'], 0),)
            # Explicit human and unknown: unencoded, reachable via VS only
            for state in ('human', 'unknown'):
                g = self.sourceFont.createChar(-1, base_glyph.glyphname + '.' + state)
                self.derive_provenance_glyph(g, base_glyph, None)
                g.altuni = ((base, vs[state], 0),)
            added += 1
        self.sourceFont.encoding = 'UnicodeFull' # Rebuild encoding table (needed after altuni changes)
        logger.info("Added provenance variants for %d base glyphs (%s)", added, self.args.provenance)

    def derive_provenance_glyph(self, glyph, base_glyph, mark):
        """ Make glyph a metric-identical copy of base_glyph, optionally with the provenance mark """
        glyph.addReference(base_glyph.glyphname)
        if mark:
            dx = (base_glyph.width - mark.width) / 2
            glyph.addReference(mark.glyphname, (1, 0, 0, 1, dx, 0))
        glyph.width = base_glyph.width
        glyph.vwidth = base_glyph.vwidth
        glyph.manualHints = True # No autohints for derived glyphs
```

Notes:

* `createChar(-1, name)` creates an unencoded glyph. Plane 16 code points are valid
  because `patch()` already switched the font to `'UnicodeFull'`.
* The format 14 `cmap` subtable comes for free: FontForge writes one for every
  `altuni` entry whose selector field is not `-1`. `font-patcher` already reads
  these `(unicode, selector, reserved)` tuples in `add_glyphrefs_to_essential()`.
  **fontTools is not required in the patcher** and must not become a dependency,
  because `FontPatcher.zip` is run on users' plain FontForge installs.
* References are flattened by FontForge when generating CFF (`.otf`) output and kept
  as composites for TrueType. Both keep the base outline and the advance width.
* Existing base glyphs are never modified. Their kerning and features are untouched.

### Presentation styles

| Style       | `.human` / `.unknown` | `.ai`                                 |
|-------------|-----------------------|---------------------------------------|
| `identical` | reference to base     | reference to base                     |
| `subtle`    | reference to base     | base + small dot below the baseline   |
| `explicit`  | reference to base     | base + bar spanning the advance width |

`create_provenance_mark()` draws the mark once, unencoded, named `provenance.mark`, with
a `glyphPen` in the same way `bin/scripts/braille/Braille.py` draws its dots. Invariants,
so line height and cell width do not change:

* Vertical extent stays within `[self.font_dim['ymin'], self.font_dim['ymax']]`.
  Place the mark in the descender zone, e.g. centered at `0.6 * ymin`.
* Horizontal extent stays within `[0, base.width]` after the centering transform.
  For `--mono` this is `self.font_dim['width']`.
* Mark size scales with `self.sourceFont.em`, not with fixed units.

### Font metadata

`setup_version()` records the profile version in the `Version` name (ID 5) because it is
the only field that survives into every consumer. `font.comment` and `font.fontlog` land
in FontForge's private `PfEd` table and are invisible to other tools.

The tag must be inserted **before** the `Nerd Fonts` segment:

```python
        prov = ";NFProv " + PROVENANCE_PROFILE if self.args.provenance else ""
        self.sourceFont.version += prov + ";" + projectName + " " + version
```

Reason: `FontnameParser.rename_font()` in `bin/scripts/name_parser/` builds `UniqueID`
from the *last whitespace-separated token* of the Version string. Appending `;NFProv 1` at
the end would turn every UniqueID into `Hack Nerd Font Regular 1`.

Result: `Version 3.003;NFProv 1;Nerd Fonts 3.5.1`.

### `--experimental check-glyph-count`

Register the added count so the check does not see an unexplained surplus:

```python
        glyphnum.update({'Provenance': (None, added)})
```

`check_glyph_counts()` skips entries whose `ish` file is `None`, which is intended: there
is no cheat-sheet file for these glyphs.

## What is *not* updated

* `glyphnames.json`, `bin/scripts/lib/i_*.sh`, `css/`: These are the icon cheat sheet.
  Provenance variants are letters, not icons. `mapping.json` is their registry.
* `src/glyphs/README.md` icon set table: Provenance has no upstream font and no license
  row. Add a one-line pointer to this directory below the table instead.
* `Dockerfile`: No new runtime dependency.

## Tooling

### `bin/scripts/nfprov.py`

Reference encoder/decoder from section 11 of the design document. Pure Python 3, standard
library only, reads `mapping.json` relative to its own location (same lookup pattern as
`font-patcher` uses for `glyphnames.json`, see `fetch_glyphnames()`).

```
nfprov.py inspect FILE
nfprov.py mark --human|--unknown|--ai [--mode=vs|pua] FILE
nfprov.py convert --from=vs|pua --to=vs|pua FILE
nfprov.py strip FILE
```

`strip` prints a warning that the operation is lossy. Unknown code points pass through
unchanged. Carry the `# Nerd Fonts Version:` and `# Script Version:` header lines so
`version-bump.sh` picks the file up, and add a row to `bin/scripts/README.md` marked `[4]`.

### `bin/scripts/test-provenance.py`

fontTools-based validator for a patched font, used by CI only:

* A format 14 `cmap` subtable exists.
* For every `pua` entry whose base is in the font: the PUA code point maps to a glyph,
  `base + VS_AI` maps to the same glyph, `base + VS_HUMAN` and `base + VS_UNKNOWN` map
  to glyphs.
* Every variant's advance width equals its base's.
* `head.yMin`/`yMax` and `hhea` ascender/descender equal the same font patched without
  `--provenance`.

Add it to `bin/scripts/README.md` marked `[1]`.

## CI and release

### `.github/workflows/font-patcher.yml`

Already triggers on `src/glyphs/**` and already runs `pip install fonttools`. Add after
the existing Hack steps:

```yaml
      - name: Patcher provenance
        run: |
          fontforge --script ./font-patcher src/unpatched-fonts/Hack/Hack-Regular.ttf \
          --complete --provenance=subtle --quiet --no-progressbars --outputdir $GITHUB_WORKSPACE/temp/prov/

      - name: Check provenance tables
        run: |
          python3 bin/scripts/test-provenance.py "$GITHUB_WORKSPACE/temp/prov/HackNerdFont-Regular.ttf"
```

Also run one `--mono` build with `--provenance`, because that is the path where width
normalization happens before the variants are derived.

### `.github/workflows/release.yml`

`gotta-patch-em-all-font-patcher!.sh` forwards `$NERDFONTS` to every `font-patcher` call
in all three variants. To ship provenance in `patched-fonts/`:

```yaml
      - name: Patch all the variations of the font family
        env:
          NERDFONTS: "--provenance=subtle"
        run: |
          cd -- "$GITHUB_WORKSPACE/bin/scripts"
          fontforge --script `pwd`/../../font-patcher --version
          ./gotta-patch-em-all-font-patcher\!.sh -jp "/${{ matrix.font }}"
```

No change to `fonts.json`, the font matrix, family names, or archive layout. If these
fonts are distributed publicly next to upstream Nerd Fonts, decide on a distinct family
name first (`projectName` and `projectNameAbbreviation` at the top of `font-patcher`).

## Manual testing

```bash
# Patch
fontforge --script ./font-patcher src/unpatched-fonts/Hack/Hack-Regular.ttf \
  --complete --provenance=subtle --debug 2 --outputdir /tmp/prov

# Shaping: expect glyph 'A.ai' for both inputs
hb-shape /tmp/prov/HackNerdFont-Regular.ttf -u "0041,E0101"
hb-shape /tmp/prov/HackNerdFont-Regular.ttf -u "100041"

# Ligature fonts: check that VS between letters does not break liga/calt
hb-shape /tmp/prov/FiraCodeNerdFont-Regular.ttf --features=calt -u "003D,E0101,003E,E0101"

# Tables
python3 bin/scripts/test-provenance.py /tmp/prov/HackNerdFont-Regular.ttf
```

Repeat for `--mono` and `--variable-width-glyphs`, and for at least one `.otf` source
(CFF flattens references) and one font with `calt` ligatures. Patched test fonts are
never committed.

Known limitation to verify per font: variation selectors are General Category `Mn`.
Contextual and ligature lookups that do not set `IgnoreMarks` will stop matching across
a selector, and PUA variants have no kerning or ligatures at all. This is a property of
the protocol, not of the patcher, and is documented rather than worked around.

[wiki-conflicts]: https://github.com/ryanoasis/nerd-fonts/wiki/Codepoint-Conflicts
