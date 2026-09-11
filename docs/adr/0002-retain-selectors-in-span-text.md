# 0002. Retain selectors inside span text so copy round-trips

Status: accepted. Date: 2026-09-11.

## Context

A reader may copy from a decorated page into an editor that has a P+ font.
The selectors are default-ignorable and render at zero width in every engine
tested.

## Decision

Span text keeps the original selectors. A `strip` option removes them for
integrators who need find-in-page, at the cost of copy round-trip. Default off.

## Evidence

Selecting the decorated sections in Chromium and WebKit yielded all 322
selectors present in the source, identical to the undecorated control. Width
of a letter plus selector equalled the bare letter in both engines.

Find-in-page was tested 2026-09-11 and the concern did not materialise.
`window.find('fork')` succeeds in both Chromium and WebKit against
`f<VS>o<VS>r<VS>k<VS>`, where the DOM text contains no literal `fork`
substring. The selection returned is the full interleaved range. A search for
an absent string returns false, so the match is not spurious. Both engines
ignore default-ignorable selectors when matching.

## Consequences

- Plain-text clipboard carries the selector encoding into HarfBuzz hosts.
- Find-in-page is not a reason to strip. `strip` remains for integrators who
  need clean text for other reasons, such as a plain-text export.
- Measured in browser find-in-page only. Search in other consumers, such as
  editors, greps, and site search indexes, is untested and will not ignore
  the selectors unless it normalises them away.
- A physical paste into a P+ editor was not performed; only the selection
  string was read.
