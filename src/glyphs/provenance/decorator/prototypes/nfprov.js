/* nfprov.js: render in-band provenance marks as HTML spans. No font needed. */
(function (global) {
  const VS = { 0xE0100: 'human', 0xE0101: 'ai', 0xE0102: 'unknown', 0xE0103: 'edited', 0xE0104: 'mixed' };
  const PUA_AI = 0x100000; // ai plane: U+100000 + base (mapping.json v1)
  const seg = new Intl.Segmenter(undefined, { granularity: 'grapheme' });

  // text -> [{state, text}], whitespace between equal states is absorbed
  function runs(text, opts) {
    const strip = !!(opts && opts.strip);
    const items = [];
    for (const { segment } of seg.segment(text)) {
      const cps = Array.from(segment);
      const last = cps[cps.length - 1].codePointAt(0);
      const cp0 = cps[0].codePointAt(0);
      let state = null, out = segment;
      if (VS[last] !== undefined && cps.length > 1) {
        state = VS[last];
        if (strip) out = cps.slice(0, -1).join('');
      } else if (cps.length === 1 && cp0 >= PUA_AI && cp0 <= 0x10FFFF) {
        state = 'ai';
        out = String.fromCodePoint(cp0 - PUA_AI) + (strip ? '' : String.fromCodePoint(0xE0101)); // PUA is unreadable without the font; re-emit as selector encoding
      } else if (/^\s+$/.test(segment)) {
        state = 'ws';
      }
      const prev = items[items.length - 1];
      if (prev && prev.state === state) prev.text += out; else items.push({ state, text: out });
    }
    // absorb whitespace between two runs of the same non-null state
    const merged = [];
    for (let i = 0; i < items.length; i++) {
      const it = items[i], prev = merged[merged.length - 1], next = items[i + 1];
      if (it.state === 'ws' && prev && next && prev.state === next.state && prev.state) { prev.text += it.text; continue; }
      if (it.state === 'ws') it.state = null;
      if (prev && prev.state === it.state) prev.text += it.text; else merged.push(it);
    }
    return merged;
  }

  function render(root, opts) {
    root = root || document.body;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: n => /[\u{E0100}-\u{E0104}\u{100000}-\u{10FFFF}]/u.test(n.nodeValue) &&
        !n.parentNode.closest('script,style,textarea,.prov') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
    });
    const nodes = []; let n; while ((n = walker.nextNode())) nodes.push(n);
    let count = 0;
    for (const node of nodes) {
      const frag = document.createDocumentFragment();
      for (const r of runs(node.nodeValue, opts)) {
        if (!r.state) { frag.appendChild(document.createTextNode(r.text)); continue; }
        const span = document.createElement('span');
        span.className = 'prov prov-' + r.state; span.dataset.prov = r.state;
        span.textContent = r.text; frag.appendChild(span); count++;
      }
      node.parentNode.replaceChild(frag, node);
    }
    return count;
  }
  global.nfprov = { runs, render };
})(window);
