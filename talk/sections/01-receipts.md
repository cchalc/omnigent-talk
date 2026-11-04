# N1: Receipts

Slide N1 turns the title slide's wink into evidence. It's a new slide, inserted between slide 1 (Title) and slide 2 (Wall of harnesses). Draft 2026-11-03.

**Placement:** after slide 1, before slide 2.
**Timing:** 75 s in total (60–90 s window). The optional 20 s demo beat sits inside that window.
**Callback:** slide 1 notes say "this deck was built with an assistant running inside Omnigent — you'll see the same thing live." N1 is where we show it.

---

## Slide

**Title:** Receipts

**On-slide text (17 words):**

> Logs show intent. Usage rows show truth. 16 of 18 commits list a coding agent as co-author.

**Visual: two stacked receipts.**

1. **Top receipt, git strip.** Monospace, shaped like a till roll. Shows the trailer count from the demo beat (below), with the commit subjects as faint lines underneath.
2. **Bottom receipt, harness matrix.** Five rows, three columns. Text only: "Yes" or "No", no emoji. Source is the final matrix in `docs/omni-fevm.md`.

| Harness | Model | Usage row on the FEVM demo workspace? |
|---|---|---|
| Antigravity (native `agy`) | Gemini 3.8 Flash | Yes: `system.ai_gateway.usage` |
| pi (direct) | Claude Sonnet 5.5 (serving-endpoint name) | Yes: `system.serving.endpoint_usage` |
| claude-sdk (direct) | Claude Sonnet 5.5 | No: replied, no row |
| Claude Code (native TUI) | Claude | No: replied, no row |
| codex | [GAP: model not recorded] | No: default is the org gateway |

Footer line on the receipt, in small type: *"Checked with the usage table, 2026-11-03. Replies don't count, rows do."*

Labels on the slide: Antigravity carries **community-supported** (Omnigent harness tier). The receipt says **AWS demo workspace**, per cross-cloud honesty in `talk/prep-reference.md`.

---

## Speaker notes

**Key line:** "On the title slide I said an assistant built this deck inside Omnigent. That's a claim you can check, so here's the receipt."

**Receipt 1: the git log.** "Sixteen of the eighteen commits on this branch carry a co-author trailer from a coding agent. Two don't: the initial commit and the commit that added the prompt file. Anyone can run `git log` and see it."

**Receipt 2: logs show intent, usage rows show truth.** "Every FEVM gateway surface returned 200 when I probed it directly. But the harness calls that replied OK didn't all land. Claude Code replied twice and left no row. Only the usage table settles where a call went. Antigravity and pi did land."

**Receipt 3: the agent's own shell leaked.** "The test shell was itself inside an agent session, and it exported about sixty routing variables. A host daemon started from there inherited them and sent Claude calls to another workspace's gateway. The fix was a hermetic launcher: it drops those variables for the child process only. Nested meta-harnesses need that."

Do not add more than these three on the slide. Reserve lines are below.

**Reserve lines (Q&A or if the beat runs long):**
- "Each harness speaks its own gateway dialect. The gateway was never broken. We probed the surface before we blamed it." (Lesson, 2026-11-03.)
- "Planning without tools gave a plausible, wrong plan. On 2026-11-02, most of the first-pass facts needed correcting."
- "`omni upgrade --dry-run` upgraded for real on a git-tracking install. Use the check flag instead." [GAP: the check flag isn't verified in this repo.]

**Do not say on this slide:** behavior-eval scores, run IDs, or agreement numbers. There are none (see Gaps).

---

## Optional demo beat (20 s)

**Command** (run from the repo root, on the branch with the build history):

```bash
git log --format='%(trailers:key=Co-authored-by,valueonly)' | sed 's/ <[^>]*>//' | awk 'NF' | sort | uniq -c | sort -rn
```

The `sed` strips email addresses from the trailers, so none appear on screen. Don't print `%ae` or `%an` in this beat.

**Expected output (tested 2026-11-03; `uniq -c` pads the counts):**

```text
     15 Isaac
      1 omnigent
```

**Prerequisites:** local git only. No Databricks profile, no network.

**Timebox:** 20 s. Run it, say one line, move on.

**Fallback threshold:** if there's no output within 5 s, or the output differs from the block above, skip the command. Show the static top receipt on the slide and narrate the same numbers.

**Fallback asset:** [GAP: `talk/fallbacks/` doesn't exist, so there's no captured clip or screenshot of this output yet.]

**Screen hygiene:** [GAP: confirm the terminal prompt shows no username or absolute path before going on stage.]

**Rehearsal:** [GAP: no timed dry run recorded for this beat.]

---

## Sources

Rows in `docs/research/facts.md`, by label:

- **Harness tiers and modes**: 18 harnesses in 3 tiers. Antigravity tier is community-supported.
- **Antigravity tier** and **Antigravity harness**: `omni agy` and the aliases.
- **Claude Code org-managed settings pin the gateway**: the device-level pinning behind the "No" rows. Per-harness effect is still OPEN.
- **Omnigent on Databricks** (Beta): the managed server the demo runs on.
- **Native Gemini API route on Unity Gateway**: the route agy uses.
- **Gemini model names**: `system.ai.gemini-3-8-flash` on the FEVM demo workspace.
- **Usage table columns**: `session_metadata.coding_agent` and the other usage fields.
- **Legacy Gemini endpoints retired**: why the slide shows only `system.ai.gemini-*` names.
- **Agent Behavior format**: cited only if someone asks about the four behavior specs.

Proposed rows for the harness matrix, trailers, and probes are under **Facts to add**. Nothing here is sourced from a secondary summary.

---

## Payoff at the close

Slide 22 (End). Speaker notes, one line:

> "Remember the receipt on slide two? The assistant that built this demo has been inside Omnigent the whole time."

**Caution:** the record only backs this for one build session. The setup log, section 8, shows a Claude Code session running inside an Omnigent runner. Nothing in the repo shows that the sessions that wrote the commits ran under Omnigent. If that can't be confirmed before the talk, use this instead:

> "The assistant that wrote our setup log ran inside Omnigent. Here's where that showed up in the usage table."

---

## Facts to add

| Claim | Quote / detail | URL | Status |
|---|---|---|---|
| FEVM harness traffic matrix (2026-11-03) | Antigravity (native agy) → `system.ai.gemini-3-8-flash` in `system.ai_gateway.usage`. pi (direct) → `databricks-claude-sonnet-5-5` in `system.serving.endpoint_usage`. claude-sdk, native Claude Code: replies returned, no FEVM usage row in any round. codex: no FEVM row, default provider on the org gateway | docs/omni-fevm.md ("Final matrix"); probe 2026-11-03 | verified for this laptop; cause of the Claude rows OPEN (likely org-managed settings) |
| Co-author trailers on the build branch | 16 of 18 commits carry `Co-authored-by`: 15 name the Isaac coding-agent tool, 1 names Omnigent. No trailer on the initial commit or the `add prompt` commit | `git log` on branch `cchalcraft/model-services-demo` (2026-11-03) | verified; branch-specific (main holds 13 of the 18 commits) |
| Hermetic launcher scrub | A shell inside an agent session exports 61 routing variables. `omni-fevm` runs `env -u` on them for the child process. Check after scrub: 0 remain | docs/setup-log.md §8; docs/omni-fevm.md ("Hermetic environment") | verified (local check, 2026-11-03) |
| Gateway surfaces return 200 on direct probe | `/ai-gateway/anthropic/v1/messages` (`system.ai.claude-sonnet-5-5`); `/ai-gateway/mlflow/v1/chat/completions` (Claude Sonnet 5.5, Gemini 3.8 Flash); `/serving-endpoints/chat/completions` (`databricks-claude-sonnet-5-5`); `/ai-gateway/codex/v1/responses` (`system.ai.gpt-5-5`). All 200 | docs/setup-log.md §6; probe 2026-11-03 | verified (direct curl probe, not harness calls) |
| Usage row lag: conflicting figures | Newest row 22 min old during the 2026-11-03 probe. The demo README says rows can take up to an hour. Use "up to an hour" on slides | docs/setup-log.md §7; demos/model-services/README.md | conflicting; OPEN until a DESCRIBE/timing check |
| Router Qwen destination | Router sends code and SQL to `databricks-qwen35-122b-a10b` behind `qwen_code`. No served-model probe recorded | resources/model_services.yml; commit 5a630a7 | OPEN |
| codex reply vs codex row | setup-log §6 row 9 shows `fevm-codex-ok` (reply OK). Matrix says no FEVM row. Reply success doesn't prove routing | docs/setup-log.md §6, §9; docs/omni-fevm.md | verified; explain as "reply ≠ row" if asked |

---

## Gaps

- **[GAP: which model wrote which commit.]** The trailers name the Isaac tool and Omnigent. They don't name a harness or a model. Don't say "Claude wrote the router" or "agy built the budget" on stage without a record.
- **[GAP: the harness the build sessions ran in.]** The only record is setup-log §8: one Claude Code session under an Omnigent runner. The payoff line depends on this.
- **[GAP: the Isaac name.]** The trailer names an internal Databricks tool that wraps Claude Code and Codex (per `docs/omni-fevm.md`). The presenter decides whether to say the name on stage. The slide says "a coding agent" for that reason.
- **[GAP: codex model.]** Not recorded for the FEVM rows.
- **[GAP: Claude rows cause.]** "Likely org-managed settings" is unconfirmed. A run from a user or machine without managed settings would settle it. Until then, say "no row", not "blocked".
- **[GAP: `talk/fallbacks/` doesn't exist.]** No clip or screenshot of the matrix query or the trailer output.
- **[GAP: `lessons.md`, `tasks.md`, `checkpoint.md` don't exist.]** The lessons above come from the plan's "Lessons to seed" section. Quote the plan, not a tracked lessons file.
- **[GAP: `config/versions.env` doesn't exist.]** Plan decision 9 says to pin the Omnigent and agy versions there. The version numbers (Omnigent 0.22.0.dev0, agy 1.4.12) are only in plan prose and the setup log.
- **[GAP: behavior evals not run.]** Plan Task 15 Steps 5 and 6 are unchecked. The four behavior specs can be mentioned as written specs. Scores can't.
- **[GAP: Task 14 runbook and timed dry run don't exist.]** The 75 s timing is an estimate, not a rehearsal.

---

## Open threads

- Decide whether the trailer output goes on stage with "Isaac" in it or in the anonymized "coding agent" form on the slide.
- Confirm the sessions behind the commits, then keep or replace the payoff line.
- Test the Claude-row cause on a machine without org-managed settings. That turns "no row" into a settled finding.
- Re-run `git log` on the branch you present from. If the talk repo's `main` is the one that gets shown, the trailer count changes (13 commits on `main`).
- Keep the Gemini naming consistent with N2. The bundle's destination strings use `databricks-gemini-*` names, which the prep reference says not to show. The probe shows they work. Decide how N2 handles it.
