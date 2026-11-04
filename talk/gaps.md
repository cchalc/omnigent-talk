# Gaps and open threads

These are still open, deliberately. Each section file has its own detailed `## Gaps`. This page
collects the ones that change what gets said or shown, and what closes them.

## Presenter decisions

| # | Decision | Default in the draft | Where |
|---|---|---|---|
| D1 | Closer: regret question (A) or fun close (C) | A | `dhh-phrases.md` §5 |
| D2 | Say "Isaac" on the N1 receipt, or "a coding agent" | "a coding agent" | `sections/01-receipts.md` |
| D3 | Keep N2b (Argon sub-slide) or a one-line mention | One line | `sections/02-gemini-agy.md` |
| D4 | `just ask` live or as a still on N3 | Still | `sections/03-routing-usage.md` |
| D5 | Keep the Smart Routing line on N3 | Keep, labelled Beta, one line | `sections/03-routing-usage.md` |
| D6 | Rust "acid in my eyes" laugh line (risky for a Google room) | Skip | `dhh-phrases.md` |
| D7 | Rename `databricks-gemini-*` destinations in `resources/model_services.yml`, or keep the file off screen | Off screen | `sections/02-gemini-agy.md` gap 2 |
| D8 | What "pickling cool cucumbers" refers to | Unused | `dhh-phrases.md` |

## Must close before rehearsal

1. **Two workspaces.** The Auto-Refund demo and the FEVM demos run on different workspaces. Confirm the Auto-Refund workspace also routes through Unity Gateway, or soften the N4 transition line.
2. **Payoff line on slide 22.** The repo shows only one build session running inside Omnigent. Confirm the sessions behind the commits, or use the safer line in `sections/01-receipts.md`.
3. **Fallback assets.** `talk/fallbacks/` doesn't exist. Needed: `antigravity-setup.mov` (N2), `router-ask.txt` or a still (N3), `usage-query.txt` plus `routing-dashboard.png` (N4), and the trailer output (N1). All redacted.
4. **The N4 query.** Nothing in the repo filters on `requester = current_user()`. Save the query from `sections/03-routing-usage.md` and capture its output at least an hour ahead.
5. **Demo runbook.** The deck cites `DEMO_SCRIPT.md` for slide 19, but it isn't in this repo. Write `talk/runbook.md` (plan Task 14, step 4) without workspace names.
6. **Collaboration teammate** for Act 2 (plan "Still Open").
7. **Timed dry run.** Every timebox is an estimate. Log the overruns in `lessons.md`, which doesn't exist yet. Neither do `tasks.md` and `checkpoint.md`.

## `prep-reference.md` conflicts (existing file, not edited here)

- Line 13 lists `omni agy --model gemini-3.8-flash`, but `--model` is dropped on this build. Use `/model` in agy (`sections/02-gemini-agy.md`).
- It asks for one Argon release-note *slide*. This draft makes it a spoken line (D3). It also says "a model-name change, not a new integration", which is UNVERIFIED.
- It points to `talk/fallbacks/antigravity-setup.mov`, which doesn't exist yet.
- It asks for a cross-cloud recap slide. In this draft that's a one-sentence footer on slide 21.

## Deck wording fixes (Google deck, not in this repo)

- "Unity AI Gateway" → **Unity Gateway** (slides 14, 16, 17 notes and any on-slide text).
- Slide 11 says "13+ harnesses". Facts say 18 in 3 tiers. Pick one.
- Slides 9 and 15: inline comments aren't documented (facts: *Collaboration*). Drop the feature or label the screenshot.
- Slide 12: the Panickssery et al. 2024 self-preference claim and the Terminal-Bench line need facts rows.
- Slide 14: Simon Willison's "lethal trifecta" needs a facts row. "Cost attribution" isn't sourced, because the usage table has no cost column.
- Move slide 20 (Scenario) before slide 19 (Demo).
- `talk/routing-architecture-slide.md` has 10 corrections, all verified against the code. They're listed in `sections/03-routing-usage.md`, and the file hasn't been changed.

## Room to explore (content still evolving)

- **Narrow waist / "the gateway sees tokens, Omnigent sees the run."** This is a strong framing for slide 7 and N4, from the Omnigent team's own pitch. Find a public source (docs, blog, or talk) before using it as their phrase. Otherwise say it in your own words.
- **Omnigent's own OpenTelemetry story.** Server, runner, and harness telemetry would complement N4's gateway view. Not sourced or built yet.
- **Fire-and-forget and SDLC agents.** Issue → fix PR → review agent. This could deepen Act 3's "close the laptop". Needs a public source.
- **Appendix items to promote** if one gets stage-ready before the talk: memory (A1) and Sandbox API (A2) are closest. See the readiness table in `appendix.md`.
- **Audio check** for the three 🟡 DHH lines (terminal, "more fun", the full "two years" line).
- **Smart Routing preview** on the account (plan Task 7). If it's enabled, N3 could show the platform version too.

## Facts to add (for `docs/research/facts.md`)

The full rows, in facts.md format, are in each file's `## Facts to add` block. This page doesn't
copy them, to avoid drift. Add a row before its claim reaches a slide.

| From | Rows | Must have before stage |
|---|---|---|
| `dhh-phrases.md` | 3 DHH quotes (token limited, too fast and too slow, product management), transcript-verified | All 3. These are on-slide quotes |
| `sections/01-receipts.md` | Harness traffic matrix, co-author trailer count, hermetic scrub (61 vars), gateway probes all 200, usage lag conflict, Qwen destination, codex reply ≠ row | Matrix, trailers, scrub |
| `sections/02-gemini-agy.md` | agy usage row, `/model` pick, `--model` drop, runner origin, two layers, base-URL override, streaming route, split and probe results, budgets scope, Argon "model-name change", Gemini-specific governance, "Google product", build versions, model-preselect conflict | agy usage row, `/model` pick |
| `sections/03-routing-usage.md` | Model services (Beta) doc URL, split and fallback mechanics, 16/4 split, 3.5 fallback config, task router, classifier 9/9, Qwen service, usage lag, account-wide usage, pi table, agy lands, Claude/Codex no row, agy discovery, no rate limit, dashboard shape, bundle names conflict | Model services URL, task router, account-wide usage |
| `appendix.md` | Budget fields, memory and Sandbox SDK signatures, cross-process memory run, Sandbox output, `ug` probe and sync, preview name, Smart Routing coverage, eval corpus | Only if an appendix slide is promoted |

**Settle these conflicts first:** usage lag (about 20 min observed vs "up to an hour" in the repo),
and `databricks-gemini-*` bundle names vs the 403 note in facts.
