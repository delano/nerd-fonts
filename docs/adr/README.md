# Architecture decision records

One file per decision. Status is `accepted` only when the decision is
implemented or measured; otherwise `proposed`. Superseded records stay in
place with a pointer to their replacement.

| ADR | Status | Title |
| --- | --- | --- |
| [0005](0005-serve-p-plus-as-woff2-subset.md) | proposed | Serve the P+ font as a woff2 subset for HarfBuzz browsers |
| [0006](0006-decorator-packages-and-repository.md) | accepted | Decorator packages per ecosystem, protocol in its own repository |
| [0007](0007-coretext-via-ccmp-ligature.md) | accepted | Reach variants under CoreText through a ccmp ligature |

Consumer-side records live in the protocol repository,
<https://github.com/textprov/textprov/tree/main/docs/adr>: 0001 (spans
independent of the font), 0002 (selectors stay inside span text), 0003 (decode
PUA to base plus selector), 0004 (one fixture defines conformance), 0008 (do not
publish PUA to the web), 0009 (editor decoration APIs), and 0010 (contributor
identity is out of band), and 0011 (the producer is text processing, and a font
is a renderer). Numbering is shared across the two repositories, so a number
appears in one or the other, never both. ADR 0006 records the split and ADR
0011 corrects where it drew the producer boundary.
