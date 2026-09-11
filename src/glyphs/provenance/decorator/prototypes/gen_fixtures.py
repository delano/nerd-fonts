import json, sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nfprov_html as N
H, A, U, E, M = '\U000E0100', '\U000E0101', '\U000E0102', '\U000E0103', '\U000E0104'
def mark(s, sel): return ''.join(c + sel if not c.isspace() else c for c in s)
def pua(s): return ''.join(chr(0x100000 + ord(c)) if not c.isspace() else c for c in s)
cases = [
 ("plain text, no marks", "The fork adds", {}),
 ("one ai word", mark("fork", A), {}),
 ("ai words joined across a space", mark("The fork", A), {}),
 ("ai then human, space between stays unmarked", mark("The", A) + " " + mark("fork", H), {}),
 ("human-edited first letter inside an ai word", "T" + mark("he", A), {}),
 ("unmarked text before and after a run", "The " + mark("fork", A) + " adds", {}),
 ("unknown, edited, mixed states", mark("a", U) + mark("b", E) + mark("c", M), {}),
 ("combining mark: selector follows the whole cluster", "é" + A + "x" + A, {}),
 ("emoji zwj sequence: selector follows the whole cluster", "\U0001F469‍\U0001F4BB" + A + " ok" , {}),
 ("pua input decodes to base plus ai selector", pua("Hi"), {}),
 ("pua and selector encodings in one string", pua("Hi") + " " + mark("there", A), {}),
 ("orphan selector with no base passes through unmarked", A + "x", {}),
 ("leading and trailing whitespace", "  " + mark("ai", A) + "  ", {}),
 ("newline is whitespace and joins equal states", mark("one", A) + "\n" + mark("two", A), {}),
 ("tab between different states", mark("a", A) + "\t" + mark("b", H), {}),
 ("strip: selectors removed, state kept", mark("fork", A), {"strip": True}),
 ("strip: pua decodes to bare base", pua("Hi"), {"strip": True}),
 ("punctuation marked, code span from sample", mark("`font-patcher --provenance`.", A), {}),
]
out = []
for name, text, opts in cases:
    runs = N.runs(text, strip=opts.get("strip", False))
    out.append({"name": name, "input": text, "options": opts, "runs": [{"state": s, "text": t} for s, t in runs]})
json.dump({"mapping_version": N.MAP["version"], "cases": out}, open(sys.argv[1], "w"), ensure_ascii=True, indent=1)
for c in out: print(c["name"], "->", [(r["state"], r["text"]) for r in c["runs"]])
