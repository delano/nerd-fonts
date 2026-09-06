#!/usr/bin/env python3
# Nerd Fonts Version: 3.5.1
# Script Version: 1.1.0
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
    # The profile version is what font-patcher announces as ";NFProv <n>"
    return selectors, pua, mapping["version"]


def find_format14(font):
    for table in font["cmap"].tables:
        if table.format == 14:
            return table
    return None


def check_font(font_path, mapping_path, reference_path, check_naming=True):
    selectors, pua, profile = load_mapping(mapping_path)
    font = TTFont(font_path)
    reference = TTFont(reference_path) if reference_path else None

    # Names are checked before the cmap gate so a font built without
    # --provenance reports the missing suffix/tag, not just the missing table.
    if check_naming:
        check_names(font, profile, reference)
    else:
        print("SKIP: name table checks (synthetic font)")

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

    if reference is not None:
        check_metrics(font, reference)
    else:
        print("SKIP: metric comparison (no --reference given)")

    print("bases checked: {}".format(checked))
    print("bases absent from font: {}".format(absent))


def name_record(font, name_id):
    """Return name ID as str, preferring Windows/en-US; None if absent."""
    table = font["name"]
    record = table.getName(name_id, 3, 1, 0x409)
    if record is None:
        for candidate in table.names:
            if candidate.nameID == name_id:
                record = candidate
                break
    return record.toUnicode() if record is not None else None


def check_names(font, profile, reference=None):
    """Assert the naming conventions font-patcher --provenance applies."""
    suffix = " P+"
    family = name_record(font, 1) or ""
    full = name_record(font, 4) or ""
    postscript = name_record(font, 6) or ""
    unique = name_record(font, 3) or ""
    version = name_record(font, 5) or ""
    typo_family = name_record(font, 16)

    report(family.endswith(suffix), "ID 1 family ends with P+", family)
    report(" P+" in full, "ID 4 full name contains P+", full)
    report("P+" in postscript.split("-", 1)[0],
           "ID 6 PostScript name has P+ before the hyphen", postscript)
    if typo_family is not None:
        report(typo_family.endswith(suffix), "ID 16 typographic family ends with P+",
               typo_family)

    # ID 1 must fit the 31 character legacy limit. The only accepted overflow is
    # the " Propo P+" form at exactly 32 (JetBrainsMono Nerd Font Propo P+).
    if len(family) == 32 and family.endswith(" Propo P+"):
        print("INFO: ID 1 family is 32 chars, accepted Propo overflow ({})".format(
            family))
    else:
        report(len(family) <= 31, "ID 1 family length <= 31",
               "{} chars: {}".format(len(family), family))

    # ID 5 segments: [...;][fork;]NFProv <profile>;Nerd Fonts <ver>
    segments = version.split(";")
    prov_tag = "NFProv {}".format(profile)
    prov_index = segments.index(prov_tag) if prov_tag in segments else -1
    report(prov_index >= 0, "ID 5 version carries {}".format(prov_tag), version)
    report(segments[-1].startswith("Nerd Fonts "),
           "ID 5 version ends with the Nerd Fonts segment", segments[-1])
    report(prov_index == len(segments) - 2,
           "ID 5 NFProv segment directly precedes the Nerd Fonts segment", version)
    fork = [i for i, seg in enumerate(segments) if seg.endswith("/nerd-fonts")]
    if not fork:
        print("INFO: ID 5 has no fork segment (projectFork blank)")
    elif prov_index >= 0:
        report(fork[-1] < prov_index, "ID 5 fork segment precedes NFProv", version)

    # rename_font() derives the UniqueID from the last token of the Version name
    last_token = version.split()[-1] if version.split() else ""
    report(bool(last_token) and unique.endswith(last_token),
           "ID 3 unique ID ends with last Version token",
           "{!r} vs {!r}".format(unique, last_token))

    if reference is None:
        print("SKIP: untouched name IDs comparison (no --reference given)")
        return
    bad = []
    for name_id in (0, 7, 8, 9, 10, 11, 12, 13, 14):
        got = name_record(font, name_id)
        want = name_record(reference, name_id)
        if got != want:
            bad.append("ID {}".format(name_id))
    got_vendor = font["OS/2"].achVendID
    want_vendor = reference["OS/2"].achVendID
    if got_vendor != want_vendor:
        bad.append("achVendID {!r} != {!r}".format(got_vendor, want_vendor))
    report(not bad, "untouched name IDs and vendor match reference", "; ".join(bad))


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

    selectors, pua, _profile = load_mapping(mapping_path)
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
        check_font(font_path, map_path, None, check_naming=False)
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
