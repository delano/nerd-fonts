# 0010. Contributor identity is out of band; states stay the in-band vocabulary

Status: accepted. Date: 2026-09-11.

## Context

A mark is one code point after one grapheme cluster. It says what kind of
author produced that cluster: explicit human, AI, unknown, edited, or mixed
(`mapping.json` `variation_selectors`). Unmarked text is assumed human.

The question was whether the protocol could name contributors instead:
H1, H2, AI1, AI2, and so on. The capacity to do so exists in one place and
not in the others.

| Layer | Used | Free |
| --- | --- | --- |
| Selectors `U+E0100`–`U+E01EF` | 5 | 235 (`VS1`–`VS16` are Unicode's) |
| PUA plane 16 | all | 0 (`PUA_AI(cp) = 0x100000 + cp` reserves the plane for AI) |
| Font glyphs | 3 variants per base | one glyph per base per generated state; CJK fonts reach the 65,535 cap quickly |
| Marks a reader can tell apart | 3 (bar, sawtooth, none) | about 2 |
| Decorator, `data-prov`, CSS | 5 states | unbounded |

Two facts decide it. First, a numbered contributor is an identity, not a
state. The table that says who AI2 is cannot fit in a code point and would
have to live outside the text. Second, the protocol's value is that a mark is
self-describing and survives copy and paste. An ordinal slot loses that at the
document boundary: AI2 in one file is not AI2 in another.

## Decision

1. The in-band vocabulary is the state set in `mapping.json`. New entries may
   be states (kinds of author). They may not be identities (particular
   authors, models, sessions, or accounts).
2. Identity, when wanted, is carried out of band by the container: an
   attribute on a wrapping element in HTML, a header line or sidecar in plain
   text, a field in an editor's metadata. The protocol does not define that
   channel. It defines only that unmarked text is assumed human and marked
   text has the state its selector names.
3. If per-contributor granularity is ever needed in band, it is added as
   slots, not states: an optional `mapping.json` section in which each slot
   selector names the state it belongs to. A decoder that does not know the
   slot table reports the state. A decoder that does reports the state and
   the slot ordinal. The meaning of an ordinal is declared by the container
   under point 2. This is a contract version bump and is not scheduled.

## Evidence

The capacity table is read from the code as of this date: `mapping.json`
version 1, `font-patcher` glyph generation (three variants per base plus mark
glyphs), and `css/nfprov.js`. The decorator is table driven in both
languages, so the software cost of a new state is one registry entry; the
font cost is one glyph per base; the visual cost is a stroke pattern a reader
must distinguish at 12 to 14 px. None of those budgets holds identities.

Slots were checked for cost without being built: 16 slot selectors use 16 of
235 free selectors and zero new glyphs, because a format 14 cmap may map
several selectors to the same variant glyph.

## Consequences

- `human`, `ai`, `unknown`, `edited`, and `mixed` remain the whole in-band
  set. `edited` and `mixed` still need glyphs (README, reserved selectors).
- A page that wants per-contributor colour styles by container, not by
  mark. The decorator's `data-prov` stays a state name.
- Selector allocation for slots would raise collisions with registered
  ideographic variation sequences on Han bases, the same exposure issue #20
  already carries. Slots would not reach CoreText through PUA; only the ccmp
  route in issue #24 applies.
- Copy and paste carries state and drops identity. That is by design.

## Related: document-level defaults

The same principle answers whether text can declare "unmarked here means
mixed" or "unmarked here means AI". It can, but only out of band and only as
a statement about the container.

- In band there is no code point for a default, and there will not be one. A
  default marker would have to persist until the next marker, which
  `CRITERIA.md` rejected because a partial copy would carry the wrong state
  or none. Unmarked text is assumed human wherever it lands.
- Out of band a container may declare a default, for example an attribute on
  the wrapping element in HTML. Presentation may style unmarked text inside
  it accordingly. The decorator does not read it: runs with no state stay
  `null`, so the declaration is lost on copy exactly as identity is.
- The useful case is a document that is mostly AI with human edits marked
  explicitly. That works today by marking the AI text and leaving the human
  edits unmarked, or by marking both. Declaring a default instead saves
  bytes and loses the property that every character answers for itself.
  The protocol prefers the marks.
