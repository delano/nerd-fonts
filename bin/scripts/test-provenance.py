#!/usr/bin/env python3
# Nerd Fonts Version: 3.5.1
# Script Version: 1.0.0
# CI validator for provenance-patched fonts
#
### DEPENDENCY:
#     fontTools Python library
#       ==> https://github.com/fonttools/fonttools
#       ==> Install: pip install fonttools
#
### USAGE:
#     test-provenance.py [--mapping PATH] [--reference REFERENCE_FONT] FONT
#     test-provenance.py --selftest
#
#     Exits 1 if any check fails.

import argparse
import json
import os
import sys
import tempfile

from fontTools.ttLib import TTFont

MAPPING_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "src", "glyphs", "provenance", "mapping.json")

FAILURES = []


def report(ok, name, detail=""):
    print("{}: {}{}".format("PASS" if ok else "FAIL", name,
                            " ({})".format(detail) if detail else ""))
    if not ok:
        FAILURES.append(name)
    return ok


def load_mapping(path):
    with open(path, encoding="utf-8") as handle:
        mapping = json.load(handle)
    selectors = {name: int(value[2:], 16)
                 for name, value in mapping["variation_selectors"].items()}
    pua = {int(key[2:], 16): int(entry["base"][2:], 16)
           for key, entry in mapping["pua"].items()}
    return selectors, pua


def find_format14(font):
    for table in font["cmap"].tables:
        if table.format == 14:
            return table
    return None


def check_font(font_path, mapping_path, reference_path):
    selectors, pua = load_mapping(mapping_path)
    font = TTFont(font_path)

    uvs_table = find_format14(font)
    if not report(uvs_table is not None, "format 14 cmap subtable",
                  font_path):
        return
    uvs = uvs_table.uvsDict
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    checked = 0
    absent = 0
    pua_ok = vs_ai_ok = vs_human_ok = vs_unknown_ok = width_ok = True
    problems = []

    def variant_glyph(base, selector):
        for base_cp, glyph_name in uvs.get(selector, []):
            if base_cp == base:
                return glyph_name, True
        return None, False

    for pua_cp, base_cp in sorted(pua.items()):
        base_name = cmap.get(base_cp)
        if base_name is None:
            absent += 1
            continue
        checked += 1
        pua_name = cmap.get(pua_cp)
        if pua_name is None:
            pua_ok = False
            problems.append("U+{:06X} not in cmap".format(pua_cp))
            continue
        for state in ("ai", "human", "unknown"):
            name, present = variant_glyph(base_cp, selectors[state])
            # fontTools stores "use the default glyph" as None; we require a
            # dedicated variant glyph for every state.
            if not present or name is None:
                problems.append("U+{:04X}+{} has no dedicated variant".format(
                    base_cp, state))
                if state == "ai":
                    vs_ai_ok = False
                elif state == "human":
                    vs_human_ok = False
                else:
                    vs_unknown_ok = False
                continue
            if state == "ai" and name != pua_name:
                vs_ai_ok = False
                problems.append("U+{:04X}+ai is {} but PUA is {}".format(
                    base_cp, name, pua_name))
            if hmtx[name][0] != hmtx[base_name][0]:
                width_ok = False
                problems.append("{} width differs from {}".format(name, base_name))

    detail = "; ".join(problems[:5]) + ("; ..." if len(problems) > 5 else "")
    report(pua_ok, "PUA code points map to glyphs", detail if not pua_ok else "")
    report(vs_ai_ok, "base+VS_AI resolves to the PUA glyph",
           detail if not vs_ai_ok else "")
    report(vs_human_ok, "base+VS_HUMAN resolves to a glyph",
           detail if not vs_human_ok else "")
    report(vs_unknown_ok, "base+VS_UNKNOWN resolves to a glyph",
           detail if not vs_unknown_ok else "")
    report(width_ok, "variant advance widths match base",
           detail if not width_ok else "")

    if reference_path:
        check_metrics(font, TTFont(reference_path))
    else:
        print("SKIP: metric comparison (no --reference given)")

    print("bases checked: {}".format(checked))
    print("bases absent from font: {}".format(absent))


def check_metrics(font, reference):
    fields = [("head", "yMin"), ("head", "yMax"),
              ("hhea", "ascent"), ("hhea", "descent"),
              ("OS/2", "sTypoAscender"), ("OS/2", "sTypoDescender"),
              ("OS/2", "usWinAscent"), ("OS/2", "usWinDescent")]
    bad = []
    for table, field in fields:
        got = getattr(font[table], field)
        want = getattr(reference[table], field)
        if got != want:
            bad.append("{}.{} {} != {}".format(table, field, got, want))
    report(not bad, "vertical metrics match reference", "; ".join(bad))


def selftest(mapping_path):
    """Build a tiny in-memory font with provenance tables and validate it."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

    selectors, pua = load_mapping(mapping_path)
    base_cp, pua_cp = 0x0041, 0x100041
    names = [".notdef", "A", "A.ai", "A.human", "A.unknown"]
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(names)
    builder.setupCharacterMap({base_cp: "A", pua_cp: "A.ai"})
    builder.setupGlyf({name: TTGlyphPen(None).glyph() for name in names})
    builder.setupHorizontalMetrics({name: (600, 0) for name in names})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Test", "styleName": "Regular"})
    builder.setupOS2()
    builder.setupPost()

    sub = CmapSubtable.newSubtable(14)
    sub.platformID, sub.platEncID, sub.language = 0, 5, 0xFFFFFFFF
    sub.cmap = {}
    sub.uvsDict = {selectors["ai"]: [[base_cp, "A.ai"]],
                   selectors["human"]: [[base_cp, "A.human"]],
                   selectors["unknown"]: [[base_cp, "A.unknown"]]}
    builder.font["cmap"].tables.append(sub)

    with tempfile.TemporaryDirectory(prefix="test-provenance-") as workdir:
        font_path = os.path.join(workdir, "test-provenance.ttf")
        map_path = os.path.join(workdir, "test-provenance-mapping.json")
        builder.save(font_path)
        limited = {"U+{:06X}".format(pua_cp): {"base": "U+{:04X}".format(base_cp),
                                               "provenance": "ai"}}
        with open(map_path, "w", encoding="utf-8") as handle:
            json.dump({"version": 1,
                       "variation_selectors": {k: "U+{:04X}".format(v)
                                               for k, v in selectors.items()},
                       "pua": limited}, handle)
        check_font(font_path, map_path, None)
    return 1 if FAILURES else 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="test-provenance.py")
    parser.add_argument("font", nargs="?", help="patched font to validate")
    parser.add_argument("--mapping", default=MAPPING_PATH,
                        help="path to mapping.json")
    parser.add_argument("--reference",
                        help="same font built without --provenance")
    parser.add_argument("--selftest", action="store_true",
                        help="validate a synthetic in-memory font and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest(args.mapping)
    if not args.font:
        parser.error("no FONT given")
    try:
        check_font(args.font, args.mapping, args.reference)
    except OSError as error:
        sys.stderr.write("test-provenance.py: {}\n".format(error))
        return 1
    if FAILURES:
        print("FAILED checks: {}".format(", ".join(FAILURES)))
        return 1
    print("All checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
