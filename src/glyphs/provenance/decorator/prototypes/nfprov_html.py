"""Server-side: in-band provenance text -> HTML spans. Reuses nfprov.cluster_end."""
import html, json, sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', '..', 'bin', 'scripts'))
import nfprov
MAP = json.load(open(os.path.join(HERE, '..', 'mapping.json')))
SEL = {int(v[2:], 16): k for k, v in MAP['variation_selectors'].items()}
SEL_OF = {k: chr(int(v[2:], 16)) for k, v in MAP['variation_selectors'].items()}
PUA = {int(k[2:], 16): (chr(int(v['base'][2:], 16)), v['provenance']) for k, v in MAP['pua'].items()}

def runs(text, strip=False):
    chars = list(text); items = []; i = 0
    while i < len(chars):
        cp = ord(chars[i])
        if cp in PUA:
            base, state = PUA[cp]; out = base if strip else base + SEL_OF[state]; i += 1
        elif chars[i].isspace():
            state = 'ws'; out = chars[i]; i += 1
        else:
            end = nfprov.cluster_end(chars, i, set(SEL))
            cluster = ''.join(chars[i:end]); state = None; out = cluster; i = end
            if i < len(chars) and ord(chars[i]) in SEL:
                state = SEL[ord(chars[i])]
                if not strip: out += chars[i]
                i += 1
        if items and items[-1][0] == state: items[-1][1] += out
        else: items.append([state, out])
    merged = []
    for k, (state, out) in enumerate(items):
        nxt = items[k + 1][0] if k + 1 < len(items) else None
        if state == 'ws' and merged and merged[-1][0] and merged[-1][0] == nxt:
            merged[-1][1] += out; continue
        if state == 'ws': state = None
        if merged and merged[-1][0] == state: merged[-1][1] += out
        else: merged.append([state, out])
    return merged

def to_html(text, strip=False):
    parts = []
    for state, out in runs(text, strip):
        e = html.escape(out)
        parts.append(f'<span class="prov prov-{state}" data-prov="{state}">{e}</span>' if state else e)
    return ''.join(parts)

if __name__ == '__main__':
    text = open(sys.argv[1], encoding='utf-8').read()
    paras = [p for p in text.split('\n\n') if p.strip()]
    print('\n'.join(f'<p>{to_html(p)}</p>' for p in paras))
