#!/usr/bin/env python3
"""Report how a patched or subset webfont differs from its upstream source.

Usage:
    compare-font-derivation.py ORIGINAL STAGED [STAGED ...]

ORIGINAL is the unpatched upstream face (TTF/OTF). Each STAGED file is a
patched and/or subset build (TTF/OTF/WOFF/WOFF2).

Exit codes:
    0  every staged font is clean or a format-only conversion (OFL-safe)
    1  at least one staged font is a Modified Version by the signals below
    2  a staged font could not be read, or its glyph names no longer line up
       with the upstream's (post table dropped) so the verdict is inconclusive

Scope: this compares the glyph *set* (added/dropped by name), the container
format, and the cmap subtables present. It does NOT diff the outlines,
metrics, kerning, or hinting of glyphs the two fonts share, so a "no changes
detected" verdict means "none of the checked signals fired," not "byte
equivalent." That is enough for the provenance patcher, which only adds
variant glyphs and leaves the base outlines untouched.

Requires: fonttools, plus brotli to read WOFF2.
"""

from __future__ import annotations

import argparse
import sys

from fontTools.ttLib import TTFont

# Glyph-name suffixes the provenance patcher appends to each base glyph.
PROVENANCE_SUFFIXES = ("ai", "human", "unknown")

# Name IDs that make up the font's public identity. ID 1 is the one OFL
# clause 3 calls "the primary font name as presented to the users".
NAME_IDS = {
    1: "family",
    3: "unique ID",
    4: "full name",
    6: "PostScript",
    16: "typographic family",
}


def is_provenance_variant(glyph_name: str) -> bool:
    # Require the dotted-suffix form (A.ai), so a glyph merely *named*
    # "ai"/"human"/"unknown" is not misread as a provenance variant.
    return "." in glyph_name and glyph_name.rsplit(".", 1)[-1] in PROVENANCE_SUFFIXES


def codepoints(font: TTFont) -> set[int]:
    """Unicode codepoints the font's best cmap maps, or empty if it has none."""
    best = font.getBestCmap()
    return set(best) if best else set()


def cmap_formats(font: TTFont) -> set[int]:
    return {table.format for table in font["cmap"].tables}


def describe_new_outlines(
    font: TTFont, added: list[str]
) -> list[tuple[str, int]]:
    """Added glyphs that carry their own contours rather than reusing existing ones.

    A provenance variant such as A.ai is a composite of the base glyph plus a
    mark, so the mark is where the genuinely new drawing lives.
    """
    if "glyf" not in font:
        return []
    glyf = font["glyf"]
    drawn = []
    for name in added:
        if name not in glyf:
            continue
        glyph = glyf[name]
        if not glyph.isComposite() and glyph.numberOfContours:
            drawn.append((name, glyph.numberOfContours))
    return drawn


def composite_breakdown(font: TTFont, name: str) -> list[str] | None:
    if "glyf" not in font or name not in font["glyf"]:
        return None
    glyph = font["glyf"][name]
    if not glyph.isComposite():
        return None
    return [component.glyphName for component in glyph.components]


def compare(original_path: str, staged_path: str) -> str:
    """Print a report. Return a status: "modified", "inconclusive",
    "format-only", or "clean"."""
    original = TTFont(original_path, lazy=True)
    staged = TTFont(staged_path, lazy=True)

    original_glyphs = set(original.getGlyphOrder())
    staged_glyphs = set(staged.getGlyphOrder())

    added = sorted(staged_glyphs - original_glyphs)
    dropped = sorted(original_glyphs - staged_glyphs)

    # The added/dropped sets above are matched by glyph NAME. A build that drops
    # the post table loses the real names, and fontTools rebuilds them from cmap
    # (uniXXXX etc.), so a glyph can show as "dropped" under one name and "added"
    # under another while its outline never moved. Cross-check against actual
    # cmap codepoint coverage: if names churn heavily but coverage barely moves,
    # the name diff is an artifact and any verdict from it is meaningless.
    original_cps = codepoints(original)
    staged_cps = codepoints(staged)
    coverage_lost = original_cps - staged_cps
    names_unreliable = len(dropped) > 0.05 * max(len(original_glyphs), 1) and (
        len(coverage_lost) < 0.2 * len(dropped)
    )
    variants = [g for g in added if is_provenance_variant(g)]
    other_added = [g for g in added if not is_provenance_variant(g)]

    original_format = original.flavor or "sfnt"
    staged_format = staged.flavor or "sfnt"
    format_changed = original_format != staged_format

    new_cmap = cmap_formats(staged) - cmap_formats(original)
    new_outlines = describe_new_outlines(staged, added)

    print("=" * 72)
    print("original: %s" % original_path)
    print("staged:   %s" % staged_path)
    print("-" * 72)
    if names_unreliable:
        print(
            "WARNING: glyph names churn but cmap coverage barely moves - a build"
        )
        print(
            "         dropped the post table, so the glyph-name diff is unreliable."
        )
    print(
        "glyph count            %d -> %d"
        % (len(original_glyphs), len(staged_glyphs))
    )
    print(
        "glyphs added           %d  (%d provenance variants, %d other)"
        % (len(added), len(variants), len(other_added))
    )
    if other_added:
        preview = ", ".join(other_added[:12])
        print(
            "  other added:         %s%s"
            % (preview, " ..." if len(other_added) > 12 else "")
        )
    print("original glyphs dropped %d" % len(dropped))
    if dropped:
        preview = ", ".join(dropped[:12])
        print(
            "  dropped:             %s%s"
            % (preview, " ..." if len(dropped) > 12 else "")
        )

    if new_outlines:
        print("added glyphs with their own contours: %d" % len(new_outlines))
        for name, contours in new_outlines[:6]:
            print("  %-28s %d contour(s), upstream: no" % (name, contours))

    # Show one variant's construction, since it demonstrates that the mark is
    # overlaid on the untouched base glyph.
    sample = next((g for g in variants if g.endswith(".ai")), None)
    if sample:
        components = composite_breakdown(staged, sample)
        if components:
            print("%-30s composite of %s" % (sample, " + ".join(components)))

    print(
        "font format            %s -> %s%s"
        % (
            original_format,
            staged_format,
            "  (changed)" if format_changed else "",
        )
    )
    if new_cmap:
        print(
            "cmap subtables added   %s"
            % ", ".join("format %d" % f for f in sorted(new_cmap))
        )

    staged_names = staged["name"]
    original_names = original["name"]
    print("-" * 72)
    copyright_notice = original_names.getDebugName(0) or ""
    reserved = "Reserved Font Name" in copyright_notice
    print(
        "upstream copyright declares a Reserved Font Name: %s"
        % ("yes" if reserved else "no")
    )
    if reserved:
        print("  %s" % copyright_notice.strip())
    for name_id, label in sorted(NAME_IDS.items()):
        value = staged_names.getDebugName(name_id)
        if value:
            print("  staged name ID %-2d (%-18s) %s" % (name_id, label, value))

    # A container swap (TTF -> WOFF/WOFF2) repackages the same font data; OFL
    # treats that as a format conversion, not a modification of the font, so it
    # does not by itself trip the Reserved Font Name clause. Only changes to the
    # font data proper do.
    data_changed = bool(added or dropped or new_cmap)
    print("-" * 72)
    if names_unreliable:
        print(
            "VERDICT: inconclusive - glyph names no longer match upstream, cannot"
        )
        print(
            "         judge the glyph set. Rebuild retaining the post table so the"
        )
        print("         names survive, then re-run.")
        return "inconclusive"
    if data_changed or format_changed:
        reasons = []
        if added:
            reasons.append("%d glyphs added" % len(added))
        if dropped:
            reasons.append("%d glyphs removed" % len(dropped))
        if new_cmap:
            reasons.append("cmap subtable added")
        if format_changed:
            reasons.append(
                "format %s -> %s" % (original_format, staged_format)
            )
        if data_changed:
            print(
                "VERDICT: Modified Version under OFL 1.1 (%s)."
                % "; ".join(reasons)
            )
            if reserved:
                print(
                    "         Upstream reserves its name, so clause 3 requires a family"
                )
                print(
                    "         name that does not contain it, or written permission."
                )
            return "modified"
        print(
            "VERDICT: format conversion only (%s -> %s), same font data."
            % (original_format, staged_format)
        )
        print(
            "         Not a Modified Version; the Reserved Font Name clause is"
        )
        print("         not triggered by repackaging alone.")
        return "format-only"
    print("VERDICT: no glyph, format, or cmap changes detected.")
    return "clean"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report how a patched/subset webfont differs from its upstream source."
    )
    parser.add_argument("original", help="unpatched upstream face (TTF/OTF)")
    parser.add_argument(
        "staged", nargs="+", help="patched and/or subset build(s)"
    )
    args = parser.parse_args(argv)

    statuses: list[str] = []
    had_error = False
    for staged in args.staged:
        try:
            statuses.append(compare(args.original, staged))
        except Exception as error:  # noqa: BLE001 - report and continue to the next file
            print("error comparing %s: %s" % (staged, error), file=sys.stderr)
            had_error = True
    if had_error or "inconclusive" in statuses:
        return 2
    if "modified" in statuses:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
