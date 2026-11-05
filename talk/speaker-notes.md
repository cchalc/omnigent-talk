# Speaker notes: "google dev - omnigent"

These follow the run order in `outline.md`. For existing slides, the deck's own notes are
condensed, then extended with **Repo tie-in** (what this repo built), **DHH** (a line from
`dhh-phrases.md`, with its status), and **Deck fix** (wording to change in the Google deck before
the talk). New slides summarise their section file, which holds the full notes, demo beat, and
sources.

Rules (from `prep-reference.md`): the product is **Unity Gateway**, models are `system.ai.gemini-*`,
Beta and community-supported labels go on the slide, and no hostnames, workspace names, or IDs
appear on screen. Only ✅ quotes go on slides.

---

## Open

### 1 · Title (0:15)
- Welcome, plus one line on who you are. "About eleven minutes of story, then a live demo you'll watch me drive."
- Seed the wink: "This deck was built by coding agents running inside Omnigent. Hold me to that."

### N1 · Receipts (0:45, new): `sections/01-receipts.md`
- **Key line:** "On the title slide I said an assistant built this deck inside Omnigent. That's a claim you can check, so here's the receipt."
- **Receipt to pick (say one, maybe two):** 16 of 18 commits carry a coding-agent co-author trailer. Every gateway surface returned 200 on a direct probe, but only some harness calls left usage rows. *Logs show intent, usage rows show truth.* The agent's own shell leaked about 60 routing variables, so I built a hermetic launcher.
- **DHH (🟡, notes only):** "The modern terminal is just a good-looking place to work."
- Optional 20 s git beat. The command and expected output are in the section file.
- `[GAP: "Isaac" appears in the trailer output. Decide whether to say the tool's name or "a coding agent".]`

## Problem

### 2 · Wall of harnesses (0:45)
- "Harness" means the app around a model: Claude Code, Codex, Cursor, Antigravity (community-supported in Omnigent), and more. `[GAP: the wall's logos need a facts row; facts list 18 Omnigent harnesses.]` Everyone shipped their own.
- Show of hands: "Who uses one of these? More than one? Keep your hand up if one of them is making you wait."
- **DHH (✅, notes only; the 3 on-slide quotes are on 12, N3, 20):** "There are decades where nothing happens and weeks where decades happen." Say "DHH quoted it on Lex Fridman". He credits Lenin, so don't put Lenin on the slide.
- **Riff:** "Harness lock-in is a bet on this year's CLI."

### 3 · Three questions (0:30)
- Compose agents across harnesses on one task. Collaborate: humans and agents in one session. Control: cost and security across every agent.
- "Remember these three. They're the demo's three acts."

### 4 · An open layer, not a 14th harness (0:20), and slide 5 is cut
- "The fix isn't a fourteenth harness. It's an open layer above them all: a meta-harness. So, Omnigent."
- **Riff:** "The harness will change. The session doesn't have to."

## Omnigent

### 6 · What it looks like (0:20)
- Web UI (sessions, chat, live diff `[GAP: facts row]`) and mobile. "It feels like a coding assistant. The value is the layer underneath." You'll see it live.

### 7 · Architecture (1:00)
- Clients on top are thin views onto one session: terminal, web, mobile, REST.
- The server in the middle is the shared brain: history, agent catalog, policies, MCP, skills, sign-in, sharing.
- The host is where agents run: your laptop, or a managed cloud sandbox. The runner wraps each harness in a uniform, sandboxed session. `[GAP: facts row for the runner/sandbox wording, from the Omnigent architecture docs]`
- **Plant for N2:** "Remember the runner. In a minute you'll see it launch Antigravity on my laptop and send its Gemini calls through Unity Gateway."
- **Framing (theme from the Omnigent team, not quoted):** the server is the *narrow waist*. Every harness's inputs and outputs pass through one place. `[GAP: find a public source before saying "narrow waist" as Omnigent's own phrase.]`
- **DHH (✅, notes):** "Agents love the Unix philosophy." Riff: "Small harnesses, with one session layer composing them. That's the Unix idea one layer up."

### 8–10 · Composition · Collaboration · Control (0:30 for all three)
- Click, click, click: "Combine agents across harnesses. Co-drive a live session. Policies for cost and security, plus a sandbox `[GAP: facts row]`. That's the product on one slide."
- **Deck fix:** slide 9 says "comment on files/docs". Inline comments aren't documented (facts: *Collaboration*), so drop "comment".

## Compose

### 11 · Harnesses out of the box (0:30)
- No migration. It uses what's already on your machine, and the Harness Plugin SDK covers the rest. `[GAP: facts row for the Plugin SDK]`
- **Deck fix:** change "13+" to **18, in three support tiers** (facts: *Harness tiers and modes*). If Antigravity is in the picker shot, label it community-supported.

### N2 · Antigravity + Gemini on Unity Gateway (1:00, new): `sections/02-gemini-agy.md`
- **Key line:** "Antigravity is still Antigravity. Its Gemini calls now go through Unity Gateway, so they land in the gateway's usage table." (Not "everything else": Claude Code and Codex didn't land there; see N1/N4.)
- **On-slide labels:** *Community-supported Omnigent harness · Omnigent on Databricks (Beta)*.
- **Cutaway (45 s):** pre-opened `omni-fevm agy` with `/model` already set to Gemini 3.8 Flash off stage. Type `Reply with exactly: fevm-agy-ok`. Switch to fallback after 15 s with no output, or on any error text. `[GAP: fallback clip not recorded.]`
- Disclosure, said once: "This is an AWS workspace. The Gemini docs I'm citing are GCP."
- **Why it matters to Google devs:** Budgets and rate limits are *available* on Unity Gateway (facts: *Budgets / rate limits*). None is configured on these services, so don't say "applied", and don't claim Gemini-specific governance until it has a facts row.
- **Argon (one line, optional):** "Gemini 4 Argon is also on Unity Gateway, as of the October 13 release notes. Same gateway." Never show it.

### 12 · Team in one YAML (0:40)
- Define the whole team in one YAML: roles, models, tools, harnesses. Two reasons. Cross-vendor build and review: one vendor writes, another checks it against the spec (the Polly pattern in Act 3). And multi-perspective debate, which is the Act 1 pattern.
- **On-slide quote (✅, 01:33:15):** *"The agents are at once both too fast and too slow."* Riff: "So you run several, in one session, and stop waiting on any one of them."
- **Deck fix:** the Panickssery et al. 2024 self-preference claim and the Terminal-Bench line need facts rows before they're spoken. `[GAP]`

## Control

### 13 · Contextual policies (0:40)
- What the run touched (PII or public) × the action (email, Salesforce, publish) gives ALLOW / ASK / DENY. Touched customer PII, then tries to publish externally: DENY.
- **Line:** "Guardrails the agent can't talk its way around. Not a system prompt that asks nicely." `[GAP: facts row for contextual policies (ALLOW/ASK/DENY over the run) before saying it as a product claim]`
- **Repo tie-in:** managed Omnigent on Databricks runs built-in and **CEL** policies only, not custom Python (facts: *Managed Omnigent policy limit*, *CEL policy*). The CEL demo isn't built yet; it's in the appendix.

### 14 · Two layers (0:45)
- Omnigent covers the trajectory: cumulative spend, tool calls, running risk, and local actions no gateway sees. Unity Gateway covers each request: usage tracking and budgets (facts: *Usage table columns*, *Budgets / rate limits*). `[GAP: facts rows for "local actions" and UC permissions on model services]`
- Refunds example: reading the table is fine and opening a public issue is fine, but the two together are a leak. Optional: Simon Willison's "lethal trifecta" `[GAP: facts row]`.
- **Line:** "Execution-level control on top, request-level governance underneath." N3 and N4 are the underneath.
- **Deck fix:** "Unity AI Gateway" → **Unity Gateway** here and on slides 16–17. "Cost attribution": the usage table has no cost column, so say "spend caps and usage" until the Spend tab's method is sourced.

### N3 · Route the work, not the vendor (0:45, new): `sections/03-routing-usage.md`
- **On-slide quote (✅, 01:01:16):** *"At this moment in time, we are all token limited."*
- **Key line:** "A model service never reads the prompt. It splits at random by weight. So the decision happens before the gateway, in one cheap call, and the gateway records what we decided."
- Flash-Lite labels each prompt. Code and SQL go to a Qwen service `[GAP: Qwen route unprobed; say "a code model" until it has a facts row]`, general to Gemini 3.8 Flash, and every call is tagged with its route. Show the pre-captured `just ask` line on the slide.
- **Say:** "This is client-side routing, our code. The platform's version is Unity Gateway Smart Routing, which is Beta and covers Claude Code and Codex."
- **Honest half:** the classifier is itself a call on every prompt, so it has to cost less than it saves. Don't claim quality or cost savings, because neither has been measured.

## Collaborate

### 15 · Share a live session (0:15)
- "Not screenshots in Slack: the same live session. You'll see it in Act 2."
- **Deck fix:** the inline-comments screenshot shows a feature the docs don't cover. Swap it for the share dialog, or label it.

## Databricks

### 16 · OSS vs managed (0:30)
- Same codebase, two deployments. OSS: you run the server and host (Databricks Apps + Lakebase `[GAP: facts row]`), Unity Gateway governs, and you bring your own sandbox (`omni sandbox`: modal / daytona / islo, facts: *Full scope*). Managed (**Beta**): workspace IdP, Databricks Sandbox host (**Beta, AWS only**), and Unity Gateway wired in.
- **Line:** "Start managed, drop to OSS when you need custom control."

### 17 · OSS picture: cut, folded into 16
- Say on 16: "Route the LLM and MCP calls through Unity Gateway and they're governed by Unity Catalog. One control plane." (Not "every call": device settings can pin a harness elsewhere; see N4.)
### N5 · Configure once, pick the gateway (0:45, new): `sections/04-agent-config.md`
- **Key line:** "The config is the part you keep. The gateway is a setting."
- **On-slide text:** *Managed config (Beta): one JSON, applied by `ug`, for Claude Code and Codex. Omnigent: one layer over every supported harness, with providers for your gateways.*
- **Databricks side:** an admin publishes one coding-agent config per workspace. It sets models, defaults, MCP servers and skills, gated by Unity Catalog grants, and `ug` applies it at launch. It's Beta, needs the Managed Configuration preview, and the schema covers **two agents**, Claude Code and Codex. (`ug` itself launches more, e.g. `ug gemini`.)
- **Omnigent side:** four credential types (API key, subscription, a gateway with base URL and key, a Databricks profile), and the agent YAML picks the harness and auth. "Unity Gateway is a strong default. It isn't the only door."
- **Receipt:** this laptop already runs two gateways at once. Device settings keep Claude Code and Codex on the org gateway, while Antigravity and pi reach the demo workspace.
- **Honest limits:** "any gateway" is documented, not demonstrated here. Antigravity needs a gateway that speaks the native Gemini API.

### 18 · Managed picture (0:15)
- Label *Beta*; Sandbox *AWS only*: "Managed server and Databricks Sandbox, wired to the gateway and workspace identity. Not a walled garden."

### N4 · One audit trail (0:45, new): `sections/03-routing-usage.md`
- **Key line:** "Omnigent tells you what the run did. The gateway tells you what every request did, and you can ask it in SQL."
- The pre-captured table is on the slide: service, served model, route, attempts, tokens. No requester column.
- **Honest coverage:** native agy lands in `system.ai_gateway.usage`, and direct pi lands in the serving endpoint usage table. Claude Code and Codex didn't show up on this workspace, likely because org-managed device settings send them to another gateway. Call that device-level governance either way.
- **Transition, and the two-workspace sentence:** "Everything so far ran on my demo workspace. The live demo runs on a second one. Same platform, same story. Enough slides."

## Demo

### 20 · Scenario: Auto-Refund (0:30, now before 19)
- You're a PM on the Orders team at a food-delivery app. When an order fails, the refund is instant and automatic. The catch: Orders detects the failure, Payments moves the money, and their contract is a draft with open questions.
- **On-slide quote (✅, 00:53:16):** *"Software is product management."* Riff: "Auto-Refund is a product question before it's a code question."

### 19 · Live demo (7:00)
Pre-flight, setup, and fallbacks come from the deck's slide-19 notes and its `DEMO_SCRIPT.md`. `[GAP: that script isn't in this repo. Bring a public-safe copy into talk/runbook.md.]`
- **Act 1, Compose (3:00).** Debby debate on the Auto-Refund repo, **one round**. Then "Turn this into a one-page PRD, under 250 words, ending 'Open questions for the Payments team.'" Governance beat: show live session cost, then Add policy.
  - **DHH (✅, notes):** "I'm telling it the problem I have. I'm telling it the fuzzy, vague idea I have." Riff: "I didn't hand the debate a spec. The first pass shows me what I actually wanted."
- **Act 2, Collaborate (1:30).** Share, then a teammate opens the *same* live session and types the Payments answer. "Same session, their device, the permission I set." `[GAP: teammate not confirmed.]`
- **Act 3, Control (2:00).** Polly in Databricks Sandbox (Beta) on the same repo. Claude Code implements, Codex reviews. Then close the laptop and reopen the session from the phone.
  - Riff on "too fast and too slow": "It's building while I'm not watching. That's how you stop waiting."
- **Close line (0:30):** "More brains, more people, no laptop. Swap the model, share the session, keep it running in the sandbox, no rewrite."

## Close

### 21 · Who should use it (0:45)
- Quick self-check. You use more than one harness, you're on Databricks, you want to share live sessions, you need guardrails, or you want agents that keep running with the laptop closed.
- **Closer (pick one from `dhh-phrases.md` §5).** Default is A. Quote only the ✅ prefix, *"Are you gonna look at yourself two years from now…"*, then your own words, "…and be proud you leaned in?" Then "The harness will change. The session doesn't have to. Shake off the AI psychosis and just have fun."
- Alternative C uses "more fun with computers in the last three months" (🟡, check the audio first).

### 22 · End
- **Payoff (safe default):** "The assistant that wrote our setup log ran inside Omnigent, and you just saw where that showed up in the usage table."
- **Payoff (if the build sessions are confirmed under Omnigent):** "Remember the receipt? The assistant that built this demo has been inside Omnigent the whole time." `[GAP: confirm first; see gaps.md]`
- Cross-cloud footer, one sentence: "The demo workspace and Sandbox are AWS; the Gemini docs I cited are GCP."
- Then Q&A. Backup slides exist in `appendix.md`; none is stage-tested yet.
