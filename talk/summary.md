# Summary: "google dev - omnigent"

## The one sentence

> Don't bet on this year's harness. Put one open session layer above all of them, govern every
> request underneath it on Databricks, and go have fun with the agents.

## The arc (20 min)

1. **Open with a receipt (N1).** This talk was built by coding agents, the git trailers show it, and the usage table shows part of the route. That makes the talk a demo of its own subject.
2. **Problem.** A wall of harnesses, each with its own config, auth, skills, and policies. Three questions no single harness answers: **Compose · Collaborate · Control**.
3. **Omnigent.** An open meta-harness, not a fourteenth harness. Clients, server, host, and runner give one uniform session over every harness.
4. **Compose.** 18 harnesses in three tiers. Antigravity runs on Gemini 3.8 Flash through Unity Gateway (N2). Then a whole team in one YAML.
5. **Control, two layers.** Omnigent sees the trajectory (contextual ALLOW/ASK/DENY policies). Unity Gateway sees each request: routing (N3) and one SQL audit trail (N4).
6. **Databricks.** OSS or managed, same codebase. Managed means workspace identity, Databricks Sandbox, and the gateway wired in. Config comes from Databricks managed config (Claude Code and Codex) or Omnigent providers (every harness, any gateway): *the config is the part you keep, the gateway is a setting* (N5).
7. **Live demo, three acts.** Debby debates the Auto-Refund PRD (Compose). A teammate co-drives the same session (Collaborate). Polly builds it in Databricks Sandbox while the laptop is closed (Control).
8. **Close.** The regret question, then "the harness will change, the session doesn't have to", then have fun.

## Where this repo's work lands

| Built here | Shows up as | Readiness |
|---|---|---|
| Hermetic `omni-fevm` launcher, harness traffic matrix, build lessons, co-author trailers | N1 Receipts | Evidence recorded. Payoff line needs a check (see gaps) |
| `omni-fevm agy` on Gemini 3.8 Flash via the native Gemini route; `gemini_shim.py`; model services | N2 | Native path verified once. Shim's `omni agy` path unverified |
| `router.py` client-side task router; `gemini_router` 80/20 split with fallback; Qwen route | N3 | Split measured once (16/4). Classifier 9/9 before deploy. Qwen route unrecorded |
| `config/ug/coding-agent-config.json` draft; the two-gateway laptop (org gateway + FEVM) | N5 | Schema verified from docs. Draft not published (preview off). "Any gateway" documented, not demonstrated |
| `system.ai_gateway.usage` queries, routing dashboard | N4 | Built. A requester-filtered query and captured stills are still needed |
| Memory, Sandbox, budgets, `ug` config, behavior evals, (CEL policies, Smart Routing, Skills, trace table not built) | `appendix.md` | None stage-ready |

## The tone

DHH on Lex Fridman #501: **joy, urgency without fear, a bit irreverent.** We're inviting people in,
not scolding them. Honesty is part of that voice too. Saying "this didn't land on the workspace,
here's why" lands harder than a clean claim. Full bank: `dhh-phrases.md`.

**Top lines**
- On slides (✅): *"At this moment in time, we are all token limited."* (N3) · *"The agents are at once both too fast and too slow."* (12) · *"Software is product management."* (20)
- In the notes (✅): "Agents love the Unix philosophy." · "the fuzzy, vague idea I have" · "Are you gonna look at yourself two years from now…" · "let your gut drive"
- Chris's own: "The harness will change. The session doesn't have to." · "Guardrails the agent can't talk its way around." · "Logs show intent. Usage rows show truth." · "Shake off the AI psychosis and just have fun."

## Files

`outline.md` (run of show) · `speaker-notes.md` (per slide) · `dhh-phrases.md` · `sections/01-receipts.md`
· `sections/02-gemini-agy.md` · `sections/03-routing-usage.md` · `sections/04-agent-config.md` · `appendix.md` · `gaps.md` (open threads and facts to add)
