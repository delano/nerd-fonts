# 0006. Decorator packages per ecosystem, protocol in its own repository

Status: proposed. Date: 2026-09-11.

## Context

Adoption of MCP and ACP followed a pattern: a short spec, a shared
conformance test, one reference implementation, thin SDKs in the languages
people already use. The fixture (0004) is the shared test.

## Proposal

- JavaScript on npm first: DOM decorator, rehype plugin, markdown-it plugin.
  npm gives a CDN script tag, so the smallest integration is one script tag
  and one stylesheet.
- Python on PyPI second: `nfprov render`, beside the marker.
- Ruby gem third: kramdown hook for Jekyll and GitHub Pages, and dogfooding
  in Onetime Secret.
- Ship the JavaScript port and wait for one breakage report before porting
  further.
- Each package vendors mapping.json, has no dependencies, exposes `runs` and
  `to_html` or `decorate`, and accepts only `strip`, `merge_whitespace` and a
  class prefix.
- Move the marker, decorators, mapping.json, fixture and spec to their own
  repository. The font patcher stays here and consumes mapping.json from
  there.
- A browser extension built on the client-side pass is the delivery for pages
  the author does not control. iOS Safari and Android Firefox allow
  extensions.

## Open

No package exists. The repository split is not started. Nothing here is
measured.
