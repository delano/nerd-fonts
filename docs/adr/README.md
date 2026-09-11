# Architecture decision records

One file per decision. Status is `accepted` only when the decision is
implemented or measured; otherwise `proposed`. Superseded records stay in
place with a pointer to their replacement.

| ADR | Status | Title |
| --- | --- | --- |
| [0001](0001-render-marks-as-html-spans.md) | accepted | Render provenance marks as HTML spans, independent of the font |
| [0002](0002-retain-selectors-in-span-text.md) | accepted | Retain selectors inside span text so copy round-trips |
| [0003](0003-decode-pua-to-base-plus-selector.md) | accepted | Decode PUA input to base plus selector |
| [0004](0004-shared-fixture-for-conformance.md) | accepted | One fixture file defines decorator conformance |
| [0005](0005-serve-p-plus-as-woff2-subset.md) | proposed | Serve the P+ font as a woff2 subset for HarfBuzz browsers |
| [0006](0006-decorator-packages-and-repository.md) | proposed | Decorator packages per ecosystem, protocol in its own repository |
| [0007](0007-coretext-via-ccmp-ligature.md) | accepted | Reach variants under CoreText through a ccmp ligature |
| [0008](0008-do-not-publish-pua-to-the-web.md) | proposed | Do not publish PUA-encoded text to the web |
| [0009](0009-editor-decoration-apis.md) | proposed | Editor decoration APIs as a third consumer path |
| [0010](0010-contributor-identity-is-out-of-band.md) | accepted | Contributor identity is out of band; states stay the in-band vocabulary |
