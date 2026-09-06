#!/usr/bin/env python3
"""Claude Code PostToolUse hook: mark model-written prose with AI provenance.

Claude Code passes the tool call as JSON on stdin after Write, Edit or
MultiEdit completes. Whatever the model wrote is run through
bin/scripts/nfprov.py so the P+ fonts render it as AI text. Code files are
left untouched; only the PROSE suffixes below are marked.

Environment:
  NFPROV_MODE   "vs" (default, variation selectors) or "pua". Use "pua" when
                the reader's editor shapes through CoreText (Zed, iTerm2,
                Ghostty), which drops selectors.
  NFPROV_DEBUG  set to any value to log decisions to stderr.
"""
import json
import os
import pathlib
import subprocess
import sys

PROSE = {".md", ".mdx", ".txt", ".rst"}
HERE = pathlib.Path(__file__).resolve().parent
NFPROV = HERE.parent.parent / "bin" / "scripts" / "nfprov.py"
MODE = os.environ.get("NFPROV_MODE", "vs")


def log(msg):
    if os.environ.get("NFPROV_DEBUG"):
        print(f"nfprov-hook: {msg}", file=sys.stderr)


def fail(msg):
    # Exit 2 feeds stderr back to Claude so a broken marker is visible.
    print(f"nfprov-hook: {msg}", file=sys.stderr)
    sys.exit(2)


def mark(text):
    if not text:
        return text
    out = subprocess.run(
        [sys.executable, str(NFPROV), "mark", "--ai", "--mode", MODE, "-"],
        input=text.encode("utf-8"), capture_output=True,
    )
    if out.returncode != 0:
        fail(f"nfprov.py failed: {out.stderr.decode('utf-8', 'replace').strip()}")
    return out.stdout.decode("utf-8")


def mark_added(old, new):
    """Return `new` with the model-added middle marked. An Edit's new_string
    usually repeats old_string's leading and trailing context, which the
    model did not write, so only the span between the common prefix and
    suffix is marked. A character-level diff is deliberately avoided: it
    treats shared letters inside a rewritten sentence as human."""
    if not old:
        return mark(new)
    pre = 0
    while pre < min(len(old), len(new)) and old[pre] == new[pre]:
        pre += 1
    suf = 0
    while (suf < min(len(old), len(new)) - pre
           and old[-1 - suf] == new[-1 - suf]):
        suf += 1
    end = len(new) - suf
    return new[:pre] + mark(new[pre:end]) + new[end:]


def mark_span(text, old, new, replace_all):
    """Mark the model-added part of `new` where it occurs in `text`. Marking
    is idempotent, so an already-marked occurrence is unchanged."""
    if not new or new not in text:
        log("inserted text not found in file, skipping")
        return text
    marked = mark_added(old, new)
    if replace_all:
        return text.replace(new, marked)
    return text.replace(new, marked, 1)


def main():
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        fail(f"bad JSON on stdin: {exc}")

    tool = event.get("tool_name", "")
    args = event.get("tool_input") or {}
    resp = event.get("tool_response")
    if isinstance(resp, dict) and resp.get("success") is False:
        log(f"{tool} reported failure, skipping")
        return

    path = pathlib.Path(args.get("file_path", ""))
    if path.suffix.lower() not in PROSE:
        log(f"{path} is not prose, skipping")
        return
    if not path.is_file():
        log(f"{path} does not exist, skipping")
        return
    if not NFPROV.is_file():
        fail(f"marker not found at {NFPROV}")

    if tool == "Write":
        # The model wrote the whole file, so mark all of it.
        path.write_text(mark(args.get("content", "")), encoding="utf-8")
        log(f"marked whole file {path}")
        return

    text = path.read_text(encoding="utf-8")
    if tool == "Edit":
        edits = [args]
    elif tool == "MultiEdit":
        edits = args.get("edits") or []
    else:
        log(f"unhandled tool {tool}")
        return

    for edit in edits:
        text = mark_span(text, edit.get("old_string", ""),
                         edit.get("new_string", ""),
                         bool(edit.get("replace_all")))
    path.write_text(text, encoding="utf-8")
    log(f"marked {len(edits)} edit(s) in {path}")


if __name__ == "__main__":
    main()
