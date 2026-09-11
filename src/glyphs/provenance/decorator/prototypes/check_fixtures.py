"""Runs nfprov_html.py against ../fixtures.json. Usage: .venv/bin/python check_fixtures.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nfprov_html as N
fx = json.load(open(os.path.join(HERE, '..', 'fixtures.json'), encoding='utf-8'))
fail = 0
for c in fx['cases']:
    got = [{'state': s, 'text': t} for s, t in N.runs(c['input'], strip=c['options'].get('strip', False))]
    if got != c['runs']:
        fail += 1
        print('FAIL', c['name'], '\n got', got, '\n exp', c['runs'])
print(f"{len(fx['cases']) - fail}/{len(fx['cases'])} pass")
sys.exit(1 if fail else 0)
