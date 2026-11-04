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
- Welcome, plus one line on who you are. "Ten minutes of story, then a live demo you'll watch me drive."
- Seed the wink: "This deck was built by coding agents running inside Omnigent. Hold me to that."

### N1 · Receipts (0:45, new): `sections/01-receipts.md`
- **Key line:** "On the title slide I said an assistant built this deck inside Omnigent. That's a claim you can check, so here's the receipt."
- **Receipt to pick (say one, maybe two):** 16 of 18 commits carry a coding-agent co-author trailer. Every gateway surface returned 200 on a direct probe, but only some harness calls left usage rows. *Logs show intent, usage rows show truth.* The agent's own shell leaked about 60 routing variables, so I built a hermetic launcher.
- **DHH (🟡, notes only):** "The modern terminal is just a good-looking place to work."
- Optional 20 s git beat. The command and expected output are in the section file.
- `[GAP: "Isaac" appears in the trailer output. Decide whether to say the tool's name or "a coding agent".]`

## Problem

### 2 · Wall of harnesses (0:45)
- "Harness" means the app around a model: Claude Code, Codex, Cursor, goose, Antigravity, and more. Everyone shipped their own.
- Show of hands: "Who uses one of these? More than one? Keep your hand up if one of them is making you wait."
- **DHH (✅, notes or slide):** "There are decades where nothing happens and weeks where decades happen." Say "DHH quoted it on Lex Fridman". He credits Lenin, so don't put Lenin on the slide.
- **Riff:** "Harness lock-in is a bet on this year's CLI."

### 3 · Three questions (0:30)
- Compose agents across harnesses on one task. Collaborate: humans and agents in one session. Control: cost and security across every agent.
- "Remember these three. They're the demo's three acts."

### 4 · An open layer, not a 14th harness (0:20), and slide 5 is cut
- "The fix isn't a fourteenth harness. It's an open layer above them all: a meta-harness. So, Omnigent."
- **Riff:** "The harness will change. The session shouldn't have to."

## Omnigent

### 6 · What it looks like (0:20)
- Web UI (sessions, chat, live diff) and mobile. "It feels like a coding assistant. The value is the layer underneath." You'll see it live.

### 7 · Architecture (1:00)
- Clients on top are thin views onto one session: terminal, web, mobile, REST.
- The server in the middle is the shared brain: history, agent catalog, policies, MCP, skills, sign-in, sharing.
- The host is where agents run: your laptop, or a managed cloud sandbox. The runner wraps each harness in a uniform, sandboxed session.
- **Plant for N2:** "Remember the runner. In a minute you'll see it launch Antigravity on my laptop and send its Gemini calls through Unity Gateway."
- **Framing (theme from the Omnigent team, not quoted):** the server is the *narrow waist*. Every harness's inputs and outputs pass through one place. `[GAP: find a public source before saying "narrow waist" as Omnigent's own phrase.]`
- **DHH (✅, notes):** "Agents love the Unix philosophy." Riff: "Small harnesses, with one session layer composing them. That's the Unix idea one layer up."

### 8–10 · Composition · Collaboration · Control (0:30 for all three)
- Click, click, click: "Combine agents across harnesses. Co-drive a live session. Policies for cost and security, plus a strong sandbox. That's the product on one slide."
- **Deck fix:** slide 9 says "comment on files/docs". Inline comments aren't documented (facts: *Collaboration*), so drop "comment".

## Compose

### 11 · Harnesses out of the box (0:30)
- No migration. It uses what's already on your machine, and the Harness Plugin SDK covers the rest.
- **Deck fix:** "13+" is a floor. Facts say 18 harnesses in 3 tiers (*Harness tiers and modes*). Pick one number. "18, in three support tiers" is sourced.

### N2 · Antigravity + Gemini on Unity Gateway (1:00, new): `sections/02-gemini-agy.md`
- **Key line:** "Antigravity is still Antigravity. Its Gemini calls now go through Unity Gateway, so they land in the same usage table as everything else in this talk."
- **On-slide labels:** *Community-supported Omnigent harness · Omnigent on Databricks (Beta)*.
- **Cutaway (45 s):** pre-opened `omni-fevm agy` with `/model` already set to Gemini 3.8 Flash off stage. Type `Reply with exactly: fevm-agy-ok`. Switch to fallback after 15 s with no output, or on any error text. `[GAP: fallback clip not recorded.]`
- Disclosure, said once: "This is an AWS workspace. The Gemini docs I'm citing are GCP."
- **Why it matters to Google devs:** Gemini is governed like any other model on Unity Gateway. Budgets and rate limits are *available*; none is configured on these services, so don't say "applied".
- **Argon (one line, optional):** "Gemini 4 Argon is also on Unity Gateway, as of the October 13 release notes. Same gateway, same controls." Never show it.

### 12 · Team in one YAML (0:40)
- Define the whole team in one YAML: roles, models, tools, harnesses. Two reasons. Cross-vendor build and review: Claude writes, Codex checks it against the spec. And multi-perspective debate, which is the Act 1 pattern.
- **On-slide quote (✅, 01:33:15):** *"The agents are at once both too fast and too slow."* Riff: "So you run several, in one session, and stop waiting on any one of them."
- **Deck fix:** the Panickssery et al. 2024 self-preference claim and the Terminal-Bench line need facts rows before they're spoken. `[GAP]`

## Control

### 13 · Contextual policies (0:40)
- What the run touched (PII or public) × the action (email, Salesforce, publish) gives ALLOW / ASK / DENY. Touched customer PII, then tries to publish externally: DENY.
- **Line:** "Guardrails the agent can't talk its way around. Not a system prompt that asks nicely."
- **Repo tie-in:** managed Omnigent on Databricks runs built-in and **CEL** policies only, not custom Python (facts: *CEL policy*). The CEL demo isn't built yet; it's in the appendix.

### 14 · Two layers (0:45)
- Omnigent covers the trajectory: cumulative spend, tool calls, running risk, and local actions no gateway sees. Unity Gateway covers each request: UC permissions, audit, spend caps.
- Refunds example: reading the table is fine and opening a public issue is fine, but the two together are a leak. Optional: Simon Willison's "lethal trifecta" `[GAP: facts row]`.
- **Line:** "Execution-level control on top, request-level governance underneath." N3 and N4 are the underneath.
- **Deck fix:** "Unity AI Gateway" → **Unity Gateway** here and on slides 16–17. "Cost attribution": the usage table has no cost column, so say "spend caps and usage" until the Spend tab's method is sourced.

### N3 · Route the work, not the vendor (0:45, new): `sections/03-routing-usage.md`
- **On-slide quote (✅, 01:01:16):** *"At this moment in time, we are all token limited."*
- **Key line:** "A model service never reads the prompt. It splits at random by weight. So the decision happens before the gateway, in one cheap call, and the gateway records what we decided."
- Flash-Lite labels each prompt. Code and SQL go to Qwen, general to Gemini 3.8 Flash, and every call is tagged with its route. Show the pre-captured `just ask` line on the slide.
- **Say:** "This is client-side routing, our code. The platform's version is Unity Gateway Smart Routing, which is Beta and covers Claude Code and Codex."
- **Honest half:** the classifier is itself a call on every prompt, so it has to cost less than it saves. Don't claim quality or cost savings, because neither has been measured.

## Collaborate

### 15 · Share a live session (0:15)
- "Not screenshots in Slack: the same live session. You'll see it in Act 2."
- **Deck fix:** the inline-comments screenshot shows a feature the docs don't cover. Swap it for the share dialog, or label it.

## Databricks

### 16 · OSS vs managed (0:30)
- Same codebase, two deployments. OSS: you run the server and host (Databricks Apps + Lakebase), Unity Gateway governs, and you bring your own sandbox. Managed: workspace IdP, Databricks Sandbox host, and Unity Gateway wired in.
- **Line:** "Start managed, drop to OSS when you need custom control."

### 17 · OSS picture (0:15) / 18 · Managed picture (0:15)
- 17: "Every LLM and MCP call goes through Unity Gateway. One control plane, governed by Unity Catalog."
- 18: "Managed server and Databricks Sandbox, wired to the gateway and workspace identity. Not a walled garden."

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
- **Close line (0:30):** "More brains, more people, no laptop. Swap the model, share the session, run it serverless, no rewrite."

## Close

### 21 · Who should use it (0:45)
- Quick self-check. You use more than one harness, you're on Databricks, you want to share live sessions, you need guardrails, or you want agents that keep running with the laptop closed.
- **Closer (pick one from `dhh-phrases.md` §5).** Default is A: "Two years from now… are you gonna look at yourself and be proud you leaned in?" (✅ prefix only), then "The harness will change. The session doesn't have to. Shake off the AI psychosis and just have fun."
- Alternative C uses "more fun with computers in the last three months" (🟡, check the audio first).

### 22 · End
- **Payoff:** "Remember the receipt? The assistant that built this demo has been inside Omnigent the whole time." `[GAP: the repo only backs this for one build session. Use the safer line in sections/01-receipts.md until confirmed.]`
- Then Q&A. The appendix slides are ready to pull up.
