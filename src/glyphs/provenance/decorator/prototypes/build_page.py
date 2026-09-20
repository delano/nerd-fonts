import html, sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nfprov_html
vs = open(os.path.join(HERE, 'example-selector.txt'), encoding='utf-8').read()
pua = open(os.path.join(HERE, '..', '..', 'example-marked.txt'), encoding='utf-8').read()
def paras(t): return [p for p in t.split('\n\n') if p.strip()][:2]
raw = ''.join(f'<p>{html.escape(p)}</p>' for p in paras(vs))
server = ''.join(f'<p>{nfprov_html.to_html(p)}</p>' for p in paras(vs))
client_pua = ''.join(f'<p>{html.escape(p)}</p>' for p in paras(pua))
open(os.path.join(HERE, 'test.html'), 'w', encoding='utf-8').write(f'''<!doctype html><meta charset="utf-8"><title>nfprov css test</title>
<style>
body{{font:15px/1.5 system-ui, sans-serif; margin:16px}} section{{margin-bottom:18px}} h2{{font-size:13px;margin:0 0 4px;color:#666}}
.prov-ai{{background:#fff0c2; text-decoration: underline wavy #c77d00; text-decoration-skip-ink:none}}
.prov-human{{background:#e3f3e3}} .prov-unknown{{text-decoration: underline dashed #888}}
</style>
<section id="raw"><h2>1. Raw selector text, system font, no script (control)</h2>{raw}</section>
<section id="server"><h2>2. Server-side spans (Python), selector encoding, selectors retained</h2>{server}</section>
<section id="client"><h2>3. Client-side spans (JS), selector encoding</h2>{raw}</section>
<section id="clientpua"><h2>4. Client-side spans (JS), PUA encoding decoded to base</h2>{client_pua}</section>
<p id="probe"><span id="a">T</span><span id="b">T&#x{0xE0101:x};</span></p>
<script src="nfprov.js"></script>
<script>
window.__counts = {{ client: nfprov.render(document.getElementById('client')), clientpua: nfprov.render(document.getElementById('clientpua')) }};
</script>''')
