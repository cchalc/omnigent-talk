# Run of show: "google dev - omnigent" (20 min)

The 22-slide Google deck stays the spine. Four new slides (N1–N4) bring in what this repo built.
Content is still settling, so `[GAP]` marks what's open. The full list is in `gaps.md`.

**Shape:** about 11 min of story, 7 min of live demo, 1 min close, 1 min buffer. Q&A comes after.
**Acts:** the deck's three questions (Compose · Collaborate · Control) frame the story and name
the demo's three acts. The new slides sit inside **Control**, because that's where Databricks
earns its place: request-level governance underneath Omnigent's run-level control.

| # | Slide | Act | Time | Status | Note |
|---|---|---|---|---|---|
| 1 | Title | Open | 0:15 | keep | Seed the wink: built with an assistant inside Omnigent |
| N1 | **Receipts** | Open | 0:45 | **new** | `sections/01-receipts.md`. Git-log beat is optional (+0:20 if used) |
| 2 | Wall of harnesses | Problem | 0:45 | keep | Show of hands. DHH "decades / weeks" line |
| 3 | Three questions: Compose · Collaborate · Control | Problem | 0:30 | keep | "Remember these three: they're the demo's acts" |
| 4 | Not a 14th harness: an open layer above | Problem | 0:20 | trim | Absorbs slide 5's "So, Omnigent." |
| 5 | "So, Omnigent." | — | 0:00 | **cut** | Say it on slide 4 |
| 6 | What it looks like | Omnigent | 0:20 | trim | One breath. The demo shows the UI |
| 7 | Architecture: clients / server / host / runner | Omnigent | 1:00 | keep | Plant "runner" here; N2 pays it off. "Agents love the Unix philosophy" |
| 8–10 | Composition · Collaboration · Control | Omnigent | 0:30 | **trim** | One beat, three clicks, ~10 s each |
| 11 | 18 harnesses, picker | Compose | 0:30 | keep | Label Antigravity *community-supported* if it's in the picker shot |
| N2 | **Antigravity + Gemini on Unity Gateway** | Compose | 1:00 | **new** | `sections/02-gemini-agy.md`. 15 s slide + 45 s cutaway (the only terminal switch before the demo) |
| 12 | Team in one YAML | Compose | 0:40 | keep | On-slide quote: "The agents are at once both too fast and too slow." |
| 13 | Contextual policies | Control | 0:40 | keep | "Guardrails it can't talk its way around" |
| 14 | Two layers | Control | 0:45 | keep | The hinge for N3/N4 |
| N3 | **Route the work, not the vendor** | Control | 0:45 | **new** | `sections/03-routing-usage.md`. Pre-captured `just ask` still **on the slide**, no terminal switch. On-slide quote: "At this moment in time, we are all token limited." |
| 15 | Share a live session | Collaborate | 0:15 | trim | Act 2 shows it, so just point forward |
| 16 | OSS vs managed on Databricks | Databricks | 0:30 | keep | "Start managed, drop to OSS when you need custom control." Label managed *Beta* |
| 17 | OSS picture | Databricks | 0:15 | trim | |
| 18 | Managed picture | Databricks | 0:15 | trim | Label *Beta*; Databricks Sandbox *Beta, AWS only* |
| N4 | **One audit trail** | Databricks | 0:45 | **new** | `sections/03-routing-usage.md`. Pre-captured, requester-filtered table on the slide, no live query |
| 20 | Scenario: Auto-Refund | Demo | 0:30 | **moved** | Before slide 19 now, so the room knows the scenario before the demo starts. On-slide quote: "Software is product management" |
| 19 | Live demo | Demo | 7:00 | **trim** | Act 1 Debby 3:00 · Act 2 share 1:30 · Act 3 Polly + close laptop 2:00 · close line 0:30 |
| 21 | Who should use it, close | Close | 0:45 | keep | Closer from `dhh-phrases.md` §5. Cross-cloud footer line (prep-reference wants one honesty slide; this is it) |
| 22 | End | Close | 0:00 | keep | Receipt payoff line (see N1) |
| | **Total** | | **19:00** | | 1:00 buffer. Optional git beat uses 0:20 of it |

## Timing authority

This file sets the timings and the still-vs-cutaway choices. Where a section file gives a longer
estimate (N1 75 s, N2 75 s, N3/N4 60–75 s plus a 30 s cutaway), the outline wins: N1 0:45 without
the git beat, N2 0:15 slide + 0:45 cutaway, N3 and N4 0:45 each as **stills** (no terminal switch).
The sections keep their full demo beats as options for a longer slot.

## What got trimmed, and why

- **Slide 5 is cut, and slides 8–10 collapse into one 30 s beat.** Slide 3 already names the three Cs, and the demo acts deliver them. That frees about 1:30.
- **Slides 6, 15, 17, 18 are trimmed** to 15–20 s each. The demo shows the UI and sharing, and slide 16 carries the OSS/managed story. That frees about 1:30.
- **The demo goes from ~10:00 to 7:00.** Act 1 runs a single round, using the "1 round" fallback the deck already lists. Act 3 is just kick-off plus close the laptop; the build result is already in the pre-run session.
- **N3 and N4 use stills, not cutaways.** Live usage rows lag (about 20 min observed; the repo says up to an hour), the table is account-wide, and N4's workspace isn't the demo's. Stills save about 1:00 and avoid all three problems.
- **Moved to `appendix.md`:** memory, Sandbox API, budgets, `ug` managed config, Smart Routing, Skills, unified trace table, behavior evals, CEL policies. None is stage-ready (readiness table in the appendix).

## Two workspaces, one sentence

The Auto-Refund demo (slide 19) runs on a different workspace from the repo's FEVM demos (N2–N4).
Say it once, at N4: *"Everything so far ran on my demo workspace. The live demo runs on a second
workspace. Same platform, same gateway story."* `[GAP: confirm the Auto-Refund workspace routes
through Unity Gateway the same way, or soften that line.]`

## Placement alternatives (if the timing slips)

- **Running long:** drop the N1 git beat, cut N4 to its key line on slide 18, and fold N3 into slide 14's notes. That saves about 1:15 (N3 0:45 + most of N4).
- **Running short:** add N2b (the Argon sub-slide, 0:15) and do the N1 git beat live.
