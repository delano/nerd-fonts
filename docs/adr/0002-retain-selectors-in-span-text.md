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

## Consequences

- Plain-text clipboard carries the selector encoding into HarfBuzz hosts.
- Find-in-page with selectors retained is untested.
- A physical paste into a P+ editor was not performed; only the selection
  string was read.
