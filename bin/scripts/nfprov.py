#!/usr/bin/env python3
# Nerd Fonts Version: 3.5.1
# Script Version: 1.0.0
# Reference encoder/decoder for inline typographic provenance
#
### DEPENDENCY:
#     Python 3 standard library only
#
### USAGE:
#     nfprov.py inspect FILE
#     nfprov.py mark --human|--unknown|--ai [--mode=vs|pua] FILE
#     nfprov.py convert --from=vs|pua --to=vs|pua FILE
#     nfprov.py strip FILE
#     nfprov.py --selftest
#
#     FILE may be '-' for stdin. Output goes to stdout unless -o/--output.

import argparse
import io
import json
import os
import sys
import unicodedata

MAPPING_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "src",
    "glyphs",
    "provenance",
    "mapping.json",
)

PROG = "nfprov"
GENERATED_STATES = ("human", "ai", "unknown")
RESERVED_STATES = ("edited", "mixed")


def load_mapping(path=MAPPING_PATH):
    """Load mapping.json and return (mapping, selectors, pua2base, base2pua)."""
    with open(path, encoding="utf-8") as handle:
        mapping = json.load(handle)
    selectors = {
        name: int(value[2:], 16)
        for name, value in mapping["variation_selectors"].items()
    }
    pua2base = {}
    base2pua = {}
    for pua_string, entry in mapping["pua"].items():
        pua = int(pua_string[2:], 16)
        base = int(entry["base"][2:], 16)
        pua2base[pua] = (base, entry.get("provenance", "ai"))
        if entry.get("provenance", "ai") == "ai":
            base2pua[base] = pua
    return mapping, selectors, pua2base, base2pua


ZWJ = 0x200D
VS15, VS16 = 0xFE0E, 0xFE0F
SKIN_TONES = range(0x1F3FB, 0x1F400)  # emoji modifiers, category Sk
REGIONAL = range(0x1F1E6, 0x1F200)  # regional indicator symbols


def is_combining(char):
    """True for combining marks (Mn/Mc/Me) that attach to a base character."""
    return unicodedata.combining(char) != 0 or unicodedata.category(char) in (
        "Mn",
        "Mc",
        "Me",
    )


def cluster_end(chars, start, sel_cps):
    """Return the index just past the grapheme-ish cluster starting at `start`.

    A cluster is a base character plus everything that visually belongs to it:
    combining marks, the emoji variation selectors VS15/VS16, skin-tone
    modifiers, ZWJ joins (the ZWJ and whatever follows it), and the second half
    of a regional-indicator pair (a flag). A provenance selector always ends the
    cluster, because it is the mark we are about to place ourselves.
    """
    index = start + 1
    if (
        ord(chars[start]) in REGIONAL
        and index < len(chars)
        and ord(chars[index]) in REGIONAL
    ):
        index += 1  # flag: two regional indicators
    while index < len(chars):
        cp = ord(chars[index])
        if cp in sel_cps:
            break
        if cp == ZWJ:
            # The ZWJ and the character it joins stay in this cluster.
            index += 2 if index + 1 < len(chars) else 1
            continue
        if cp in (VS15, VS16) or cp in SKIN_TONES or is_combining(chars[index]):
            index += 1
            continue
        break
    return index


# --- transformations -------------------------------------------------------


def do_inspect(text, selectors, pua2base):
    """Return a plain-text 'key: value' report of provenance states."""
    sel2name = {cp: name for name, cp in selectors.items()}
    counts = dict.fromkeys(
        (
            "assumed_human",
            "explicit_human",
            "ai_vs",
            "ai_pua",
            "unknown",
            "edited",
            "mixed",
            "whitespace",
        ),
        0,
    )
    unrecognised_selectors = set()
    unrecognised_pua = set()

    chars = list(text)
    index = 0
    while index < len(chars):
        char = chars[index]
        cp = ord(char)
        index += 1
        if cp in sel2name:
            # A selector reached here has no base in front of it.
            unrecognised_selectors.add(cp)
            continue
        if 0xE0100 <= cp <= 0xE01EF:
            unrecognised_selectors.add(cp)
            continue
        if cp in pua2base:
            counts["ai_pua"] += 1
            continue
        if 0x100000 <= cp <= 0x10FFFD:
            unrecognised_pua.add(cp)
            continue
        if char.isspace():
            counts["whitespace"] += 1
            continue
        index = cluster_end(chars, index - 1, sel2name)
        if index < len(chars) and ord(chars[index]) in sel2name:
            name = sel2name[ord(chars[index])]
            index += 1
            counts[
                "explicit_human"
                if name == "human"
                else "ai_vs"
                if name == "ai"
                else name
            ] += 1
        else:
            counts["assumed_human"] += 1

    lines = [f"characters: {len(chars)}"]
    for key in (
        "assumed_human",
        "explicit_human",
        "ai_vs",
        "ai_pua",
        "unknown",
        "edited",
        "mixed",
        "whitespace",
    ):
        lines.append(f"{key}: {counts[key]}")
    lines.append(
        "unrecognised_selectors: {}".format(
            " ".join(f"U+{cp:04X}" for cp in sorted(unrecognised_selectors))
            or "-"
        )
    )
    lines.append(
        "unrecognised_pua: {}".format(
            " ".join(f"U+{cp:04X}" for cp in sorted(unrecognised_pua)) or "-"
        )
    )
    return "\n".join(lines) + "\n"


def do_mark(text, state, mode, selectors, pua2base, base2pua):
    """Attach the selector for `state` after every non-whitespace base.

    The selector goes after any combining marks, emoji variation selectors,
    skin-tone modifiers, ZWJ joins and regional-indicator pairs, so a cluster is
    marked once. Characters that already carry a provenance selector, selectors
    themselves, and PUA provenance characters are left alone (the operation is
    idempotent). With mode='pua' only single-code-point bases present in
    mapping.json are replaced by their PUA counterpart; every other base keeps
    the VS_AI encoding instead.
    """
    sel_cps = set(selectors.values())
    selector = chr(selectors[state])
    chars = list(text)
    out = []
    index = 0
    while index < len(chars):
        char = chars[index]
        cp = ord(char)
        if cp in sel_cps or cp in pua2base or char.isspace():
            out.append(char)
            index += 1
            continue
        start = index
        index = cluster_end(chars, index, sel_cps)
        cluster = chars[start:index]
        if index < len(chars) and ord(chars[index]) in sel_cps:
            out.extend(cluster)  # already marked
            continue
        if (
            mode == "pua"
            and state == "ai"
            and len(cluster) == 1
            and cp in base2pua
        ):
            out.append(chr(base2pua[cp]))
        else:
            out.extend(cluster)
            out.append(selector)
    return "".join(out)


def do_convert(text, from_mode, to_mode, selectors, pua2base, base2pua):
    """Convert the AI state between VS and PUA encodings; pass all else through."""
    if from_mode == to_mode:
        return text
    vs_ai = selectors["ai"]
    if from_mode == "vs":
        chars = list(text)
        out = []
        index = 0
        while index < len(chars):
            char = chars[index]
            index += 1
            if (
                index < len(chars)
                and ord(chars[index]) == vs_ai
                and ord(char) in base2pua
            ):
                out.append(chr(base2pua[ord(char)]))
                index += 1
            else:
                out.append(char)
        return "".join(out)
    out = []
    for char in text:
        entry = pua2base.get(ord(char))
        if entry and entry[1] == "ai":
            out.append(chr(entry[0]))
            out.append(chr(vs_ai))
        else:
            out.append(char)
    return "".join(out)


def do_strip(text, selectors, pua2base):
    """Remove all provenance selectors and map PUA entries back to their base."""
    sel_cps = set(selectors.values())
    out = []
    for char in text:
        cp = ord(char)
        if cp in sel_cps:
            continue
        entry = pua2base.get(cp)
        out.append(chr(entry[0]) if entry else char)
    return "".join(out)


# --- CLI -------------------------------------------------------------------


def read_input(path):
    """Read UTF-8 text verbatim; the locale encoding is never used."""
    if path == "-":
        stream = io.TextIOWrapper(
            sys.stdin.buffer, encoding="utf-8", newline=""
        )
        return stream.read()
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write_output(text, path):
    """Write UTF-8 text verbatim, keeping any CRLF line endings intact."""
    if path:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    else:
        stream = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", newline=""
        )
        stream.write(text)
        stream.flush()


class SelftestError(Exception):
    """Raised when a selftest expectation fails (works under python3 -O)."""


def check(condition, message):
    if not condition:
        raise SelftestError(message)


def selftest():
    """Round-trip the reference example through mark/convert/strip."""
    _, selectors, pua2base, base2pua = load_mapping()
    ai, human = chr(selectors["ai"]), chr(selectors["human"])

    def mark(text, state="ai", mode="vs"):
        return do_mark(text, state, mode, selectors, pua2base, base2pua)

    def convert(text, src, dst):
        return do_convert(text, src, dst, selectors, pua2base, base2pua)

    def strip(text):
        return do_strip(text, selectors, pua2base)

    source = "Written by a human. Generated by AI."
    vs_ai = mark(source)
    check(strip(vs_ai) == source, "strip must undo mark")
    check(mark(vs_ai) == vs_ai, "mark --mode=vs is not idempotent")
    pua = convert(vs_ai, "vs", "pua")
    check(pua != vs_ai, "vs->pua must change the text")
    check(convert(pua, "pua", "vs") == vs_ai, "pua->vs must be reversible")
    check(strip(pua) == source, "strip must undo the PUA encoding")
    direct = mark(source, mode="pua")
    check(direct == pua, "mark --mode=pua must equal mark + convert")
    check(
        mark(direct, mode="pua") == direct, "mark --mode=pua is not idempotent"
    )
    check(mark(direct) == direct, "mark must not re-mark PUA characters")

    marked_human = mark(source, state="human")
    check(strip(marked_human) == source, "strip must undo --human")
    check(
        convert(marked_human, "vs", "pua") == marked_human,
        "convert must pass non-AI states through",
    )

    report = do_inspect(vs_ai, selectors, pua2base)
    check("ai_vs: 30" in report, "unexpected inspect report: " + report)
    check("assumed_human: 0" in report, "unexpected inspect report: " + report)

    combining = "e\u0301x"
    check(mark(combining) == "e\u0301" + ai + "x" + ai, "combining mark split")
    check(strip(mark(combining)) == combining, "combining round trip")

    flag = "\U0001f1e8\U0001f1e6"  # regional indicator pair
    check(mark(flag) == flag + ai, "flag split into two marks")
    family = "\U0001f468\u200d\U0001f469\u200d\U0001f467"  # ZWJ sequence
    check(mark(family) == family + ai, "ZWJ sequence split")
    tone = "\U0001f44d\U0001f3fd"  # skin-tone modifier
    check(mark(tone) == tone + ai, "skin tone split")
    emoji_vs = "\u2764\ufe0f"  # VS16 presentation
    check(mark(emoji_vs) == emoji_vs + ai, "VS16 split")
    for text in (flag, family, tone, emoji_vs):
        check(
            mark(text, mode="pua") == text + ai,
            "multi-code-point cluster must fall back to VS",
        )
        check(strip(mark(text)) == text, "emoji round trip")

    check(mark("a\r\nb") == "a" + ai + "\r\nb" + ai, "CRLF must stay unmarked")

    reserved = "a" + chr(selectors["edited"]) + "b" + chr(selectors["mixed"])
    check(
        "edited: 1" in do_inspect(reserved, selectors, pua2base),
        "reserved selector not recognised",
    )
    check(strip(reserved) == "ab", "strip must remove reserved selectors")
    check(mark(reserved) == reserved, "reserved marks must be left alone")
    check(human != ai, "selector table is degenerate")

    print("nfprov: selftest OK")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog=PROG, description=__doc__)
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run internal round-trip tests and exit",
    )
    parser.add_argument(
        "--mapping", default=MAPPING_PATH, help="path to mapping.json"
    )
    subs = parser.add_subparsers(dest="command")

    def add_common(sub):
        sub.add_argument(
            "file", metavar="FILE", help="input file, or - for stdin"
        )
        sub.add_argument(
            "-o", "--output", help="write to this file instead of stdout"
        )

    add_common(subs.add_parser("inspect", help="report provenance states"))

    marker = subs.add_parser("mark", help="add provenance marks")
    group = marker.add_mutually_exclusive_group(required=True)
    for state in GENERATED_STATES:
        group.add_argument(
            "--" + state, dest="state", action="store_const", const=state
        )
    marker.add_argument("--mode", choices=("vs", "pua"), default="vs")
    add_common(marker)

    converter = subs.add_parser("convert", help="convert between encodings")
    converter.add_argument(
        "--from", dest="from_mode", choices=("vs", "pua"), required=True
    )
    converter.add_argument(
        "--to", dest="to_mode", choices=("vs", "pua"), required=True
    )
    add_common(converter)

    add_common(subs.add_parser("strip", help="remove all provenance (lossy)"))
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        try:
            return selftest()
        except SelftestError as error:
            sys.stderr.write(f"{PROG}: selftest failed: {error}\n")
            return 1
    if not args.command:
        parser.error("no subcommand given")
    if args.command == "mark" and args.mode == "pua" and args.state != "ai":
        parser.error(
            "--mode=pua is only valid with --ai "
            "(there is no PUA encoding for human or unknown)"
        )
    try:
        _, selectors, pua2base, base2pua = load_mapping(args.mapping)
    except (OSError, ValueError, KeyError) as error:
        sys.stderr.write(f"{PROG}: cannot load mapping: {error}\n")
        return 1
    try:
        text = read_input(args.file)
    except OSError as error:
        sys.stderr.write(f"{PROG}: cannot read input: {error}\n")
        return 1

    if args.command == "inspect":
        result = do_inspect(text, selectors, pua2base)
    elif args.command == "mark":
        result = do_mark(
            text, args.state, args.mode, selectors, pua2base, base2pua
        )
    elif args.command == "convert":
        result = do_convert(
            text, args.from_mode, args.to_mode, selectors, pua2base, base2pua
        )
    else:
        sys.stderr.write(
            f"{PROG}: strip is lossy: provenance cannot be recovered "
            "from the output\n"
        )
        result = do_strip(text, selectors, pua2base)

    try:
        write_output(result, args.output)
    except OSError as error:
        sys.stderr.write(f"{PROG}: cannot write output: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
