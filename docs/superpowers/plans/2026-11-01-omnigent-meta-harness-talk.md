# Omnigent Meta-Harness Talk — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this repo into both (a) the live demo environment and (b) the build log for a Google developer conference talk: *"One harness to rule them all: Omnigent as a meta-harness, with Gemini on Databricks."*

**Architecture:** The repo holds secret-free Omnigent agent specs and policies, small demo scripts for the Databricks pieces (Unity Gateway usage and tracing, Skills, agent memory, Databricks Sandbox), the talk itself (outline, speaker notes, demo runbook), and a tracking layer (`tasks.md` / `checkpoint.md` / `lessons.md`, the ai-kitchen-dbx convention) so the build process can be shown on stage too. Demos run against the presenter's **existing Databricks-hosted Omnigent server** (AWS workspace). Every demo has a scripted happy path, a verification command, and a pre-recorded fallback.

**Tech Stack:** Omnigent ≥ v0.20.0 (`omni` CLI, managed server on Databricks, web UI, Android app). Harnesses: Claude Code (`claude-sdk`), Codex, Pi, Antigravity (`antigravity-native`, `omni agy`). Databricks: **Unity Gateway** (Gemini 3.8 Flash live via `system.ai.gemini-3-8-flash`; Gemini 4 Argon mentioned from the release note; Smart Routing, service policies, Skills), `system.ai_gateway.usage`, the built-in usage dashboard, the unified trace table, agent memory (`databricks-agentbricks`), and Databricks Sandbox. Python via `uv`. Databricks CLI ≥ v1.17.

**Spec:** No separate spec doc. The source brief is below. Verified facts live in `docs/research/facts.md`.

## Source Brief (from the user, 2026-11-01)

- Talk at a **Google developer conference**. The repo tracks everything done and gets presented alongside the coding agents and techniques used to build it.
- Central theme: **set up and configure Omnigent as a meta-harness** to switch between harnesses and models, with smart routing and more (https://omnigent.ai/docs/use/coding-agents), including Omnigent features beyond coding agents.
- Cover the **full scope** of Omnigent, with a focus on **harness engineering, smart routing, contextual policies, and usability (collaboration, mobile app)**.
- Highlight **Gemini as a foundation model on Databricks**, and Databricks itself running **on GCP**. Cite https://docs.databricks.com/gcp/en/release-notes/unity-gateway/#google-gemini-4-argon-is-now-available-on-unity-gateway.
- Set up **Antigravity**: https://omnigent.ai/docs/build/harnesses/configuration#antigravity and #configure-native-agy-credentials.
- Show **tracing of model calls through the gateway** and **skill usage on Databricks**.
- Show **agent memory** (https://docs.databricks.com/aws/en/agents/custom-agents/stateful-agents) and **serverless sandbox** (https://docs.databricks.com/aws/en/compute/serverless/sandbox).
- Soft theme throughout: **Databricks platform features and why they matter to Google developers**.
- Track tasks, checkpoints, and lessons the way `/Users/christopher.chalcraft/Projects/Databricks/ai-kitchen-dbx` does.

## Global Constraints

- **Never use Homebrew.** Install with `uv`, `uv tool`, `npm`, `nix`, or official curl installers (`~/.agents/behaviors/package-management/BEHAVIOR.md`).
- **Never auto-select a Databricks profile.** Commands use `--profile "$DBX_PROFILE"` (or `$DBX_GCP_PROFILE`). The presenter sets these in `.env.local`, which is gitignored.
- **Never modify `~/.omnigent`.** It is the presenter's live, daily-use config. Demo scripts pass `--server "$OMNI_SERVER"`. If a repo-local `.omnigent/config.yaml` is used, it may only contain `server:` / `harness:` keys. Project config replaces every non-`harness` key wholesale, so a repo `providers:` block would hide the presenter's providers.
- **No secrets in git.** Tokens, keys, and OAuth files stay in `.env.local`, the OS keychain, or `~/.omnigent/`. Run `scripts/check.sh` before every commit.
- **The repo is public at talk time.** Nothing in git may contain workspace hostnames or URLs (including `OMNI_SERVER`), workspace or org IDs, user emails, warehouse IDs, or screenshots that show any of these. Generic model names (`system.ai.*`, `databricks-gemini-*`) are fine.
- **Every on-stage claim carries a source URL** in `docs/research/facts.md`. Unverified claims are tagged `[UNVERIFIED]` and must not reach slides.
- Commit messages end with `Co-authored-by: Isaac <no-reply@databricks.com>`.
- Talk length: **60 min slot** (45 talk/demo + 15 Q&A).
- **Cross-cloud honesty.** The Omnigent server and Databricks Sandbox run on the AWS workspace (Sandbox is AWS-only today). The Gemini, Unity Gateway, and agent-memory story is shown with the GCP docs, and on a GCP workspace if one is available (`DBX_GCP_PROFILE`, optional). Say this openly on one slide.

## Review Focus

1. **Conference Wi-Fi fails or an endpoint is slow.** Each demo has a recorded fallback (`talk/fallbacks/`), and the runbook says when to switch (Task 14).
2. **Versions or model names drift.** Omnigent, agy, and model names are pinned in `config/versions.env` and checked by `scripts/preflight.sh` (Task 13).
3. **Secrets on screen or in git.** `scripts/check.sh` (Task 1) and the runbook's screen-hygiene checklist (Task 14) cover this.
4. **Smart Routing is nondeterministic and has no dry-run.** Routing assertions check "routing happened, and the models used are within the expected set", never exact picks (Task 7).
5. **A policy blocks the presenter mid-demo.** CEL policies are unit-tested offline against the real `cel_policy` factory, then smoke-tested (Task 8).
6. **Beta features.** Smart Routing, Skills API, agent memory, Sandbox, the unified trace table, and Omnigent on Databricks are all Beta, and Antigravity is a *community-supported* Omnigent harness. Label them as such on slides. Each needs a fallback.

---

## Research Status

Verified 2026-11-02 against primary sources (docs.databricks.com/gcp unless noted; omnigent.ai; github.com/omnigent-ai/omnigent; installed package source). Exact quotes and URLs are in `docs/research/facts.md`.

| Claim | Status | Correct detail |
|---|---|---|
| Gemini 4 Argon on Unity Gateway | VERIFIED | Oct 13 2026, available via Foundation Model APIs. No endpoint name or region given, and **not served on the FEVM demo workspace**, so it's mentioned only, never demoed (decision 11). Live demos use Gemini 3.8 Flash (Sep 2), as `system.ai.gemini-3-8-flash`. |
| Product name | CORRECTED | It's **Unity Gateway** (CLI `ug`), not "Unity AI Gateway". The system table stays `system.ai_gateway.usage`. |
| `system.ai_gateway.usage` coding-agent metadata | VERIFIED | `session_metadata{client_session_id, client_subagent_id, coding_agent, agent_version, surface, reasoning_effort, smart_router_name}`, `invocation_metadata.source`, `destination_model`, `endpoint_name`, `requester`, `input/output/total_tokens`, `latency_ms`, `routing_information`, `mcp_metadata`, `request_tags`. No cost column. Built-in usage dashboard has Overview / Spend / Coding Agents / MCPs / **Skills** / Performance tabs. |
| Tracing | CORRECTED | The **unified trace table** (Beta) puts every gateway request and response in one UC table. Coding-agent tracing goes through `ug`. Inference tables can be attached per service. Not "MLflow traces". |
| Skills on Databricks | VERIFIED | Unity Gateway Skills REST API (Beta, Oct 12), central org config of skills, the dashboard **Skills** tab (downloads and loads by user), and audit-log service `aiGatewaySkills` (list, load, file fetch). |
| Smart Routing | CORRECTED | This is Unity Gateway **Smart Routing (Beta)**. It picks the lowest-cost capable `system.ai.*` model, and each subagent is routed independently. It covers Claude Code + Codex only. It needs the *Enhanced Unity Gateway* account preview. In Omnigent ≥0.8, pick **Smart Routing** as the harness in the UI, or run `omni claude --smart-routing`. Gemini/Antigravity are not routed harnesses (Gemini can still be a routed *model*). Omnigent's own `llm:` / `routing: {provider: external, ...}` blocks enable the Auto picker. No dry-run. |
| Policies | CORRECTED | **Databricks-hosted Omnigent supports only built-in policies and CEL custom policies. Custom Python policies are not supported.** CEL: `handler: omnigent.policies.builtins.cel.cel_policy`, `factory_params: {expression, reason}`. The expression sees `event.type`, `event.target`, `event.data.{name, arguments}`, `event.context.{model, harness, usage, labels}` and returns `{"result": "DENY"\|"ASK"\|"ALLOW", "reason": ...}`. `PolicyEvent` has **no cwd**. Platform side: UC **service policies** on Unity Gateway (Sensitive Data Detection guardrail, request-tag checks, MCP prompt-injection screening, external guardrail vendors). |
| Harness modes | VERIFIED | Direct mode (Omnigent runs model + tools) vs Native TUI (`*-native`). 18 harnesses in 3 support tiers; Antigravity is **community-supported**. |
| Antigravity harness | CORRECTED | Harness `antigravity-native`, launched by `omni agy` (aliases `agy`, `google-antigravity`; added in v0.12). Install agy with `curl -fsSL https://antigravity.google/cli/install.sh \| bash`, **≥ 1.1.13**. |
| Native agy credentials | VERIFIED | `omni setup` → Antigravity → *Configure native agy API key / gateway* → *Databricks profile* writes `native_gemini: true`. **The native Gemini API is required.** OpenAI-compatible and Bearer/token-refresh gateways are unsupported. Creds: macOS Keychain (agy ≥1.1.7), `~/.gemini/oauth_creds.json`, `~/.gemini/antigravity-cli/antigravity-oauth-token` (Linux). Databricks lists Gemini CLI (`ug gemini`) as a supported agent, which suggests a native Gemini route exists. Confirm it in Task 6. |
| Collaboration and mobile | CORRECTED | Share with Read or Edit. With Edit, collaborators "co-drive": their messages run on the owner's machine and are labeled with their email. `omni attach <session_id>`. **Inline comments are not documented, so they're dropped.** Android `ai.omnigent.android` on Google Play, plus iOS and an installable PWA. |
| `omni diagnose` / `omni usage` / `omni sandbox` | VERIFIED | `omni diagnose [--json]`, `omni usage [--json]`, `omni sandbox create/connect` (modal / daytona / islo). |
| Agent YAML | CORRECTED | `name`, `prompt`, `executor.{harness, model, auth}`, `policies`. **There is no `extends`.** The local 0.9 parser reads `executor.type` + `executor.config`, while the docs show `executor.harness`. Re-check after upgrading. |
| Omnigent on Databricks | VERIFIED | Managed server (Beta) with workspace IdP and models via FMAPI / Unity Gateway. Hosts are a Databricks Sandbox (select AWS regions) or a self-registered machine (`omni login <ws>`, `omni host --server <ws>`). A GCP page exists (`/gcp/en/omnigent/`). |
| Agent memory | CORRECTED | "Agent memory and sessions" (Beta; GCP page exists). `pip install databricks-agentbricks` (≥0.6.0). `AgentKitClient(WorkspaceClient()).memory_stores.create(id)`, `.add/.put(actor_id, path, content, description)`, `.search(actor_id, query, limit)`. Lakebase-backed with no separate setup. **`actor_id` scopes recall but is not access control**; isolate with one store per boundary. The old `DatabricksStore` / `CheckpointSaver` approach is not what the docs show. The doc's install name (`databricks-agentbricks`) and import (`databricks_agentkit`) differ, so verify on install. |
| Serverless sandbox | CORRECTED | **Databricks Sandbox** (Beta, opt-in on the Previews page). **AWS only** (the GCP page 404s). 4 vCPU / 8 GB, 100 GB persistent home, 24 h runtime cap, ingress closed, **egress unrestricted**. SDK: `w.sandbox.create_sandbox(sandbox_id=...)`, `w.sandbox.execute_command_sync(..., args=[...], execution_timeout=Duration(...))`, `w.sandbox.delete_sandbox("sandboxes/<id>")`. CLI: `databricks sandbox create / ssh`. Agent Bricks: `agentbricks tools add sandbox --scope ...`. |
| Latest Omnigent | VERIFIED | **v0.20.0 (2026-10-28)**. Local install is 0.9.0.dev0 (2026-08-10), so upgrade. Relevant changes: v0.12 `omni agy`; v0.17 period budgets and `conversation_id`; v0.19 MCP gateway with policy checks; v0.20 restricts unregistered policy handlers in uploaded bundles. |
| Omnigent full scope | VERIFIED | Polly (multi-agent orchestrator) and Debby (brainstorming) bundled agents, scheduled tasks, inbox / async calls, browser tools, skills, Slack integration (`omni integration slack`), cloud sandboxes, REST API, macOS app, mobile. |

## Talk Narrative (target shape — finalized in Task 14)

60-min slot: 45 min of content (below) + 15 min Q&A.

| # | Segment | Min | Live demo | Databricks "why it matters to Google devs" beat |
|---|---|---|---|---|
| 1 | Hook: "I built this talk with 4 harnesses and N models. Here's the receipt." Show `lessons.md` and git history | 2 | repo tour | — |
| 2 | Problem: harness lock-in. Each agent CLI has its own config, auth, skills, and policies | 3 | — | — |
| 3 | Omnigent as a meta-harness: server, harnesses, providers, policies, UI, plus a full-scope tour (Polly/Debby, scheduled tasks, Slack, sandboxes). *Omnigent on Databricks* is the managed server | 5 | `omni` overview, web UI | Managed server behind your workspace IdP |
| 4 | Harness engineering: one agent YAML across four harnesses (Claude Code, Codex, Pi, **Antigravity**). Direct vs Native TUI | 7 | switch harness live | One credential (a Databricks profile) for all of them |
| 5 | **Gemini on Databricks**: live on Gemini 3.8 Flash through Unity Gateway's native Gemini API; one slide on **Gemini 4 Argon** (Oct 13 release note: it's on Unity Gateway, and new Gemini models land there as they ship); full Antigravity setup walkthrough | 6 | `omni agy --model gemini-3.8-flash` on Databricks-served Gemini | UC permissions, rate limits, and budgets apply to Gemini like any other model |
| 6 | Smart Routing: Unity Gateway picks the cheapest capable model per subagent | 4 | Smart Routing session; show the per-subagent models | Routing as a governed platform service |
| 7 | Contextual policies, two layers: Omnigent (budget + CEL residency) and Unity Gateway service policies (sensitive-data guardrail) | 4 | an allowed and a denied action | Governance enforced at the gateway, whatever the harness |
| 8 | Observability: built-in usage dashboard (Coding Agents + **Skills** tabs), `system.ai_gateway.usage`, unified trace table | 5 | dashboard + one SQL query | One SQL-queryable audit trail across vendors and harnesses |
| 9 | Agents that remember and act safely: agent memory + Databricks Sandbox (AWS, disclosed) | 5 | recall across sessions; run agent code in Sandbox | Managed Lakebase-backed memory, isolated compute, no infra |
| 10 | Usability: share a live session (Edit = co-drive), continue on the Android phone | 3 | join and steer from the phone | — |
| 11 | Recap, cross-cloud honesty note, how to try it (QR code to the public repo) | 1 | — | — |

## File Structure

```
README.md                          # talk abstract, repo map, how to reproduce
tasks.md                           # rolling work list: In Progress / Next, with resume steps
checkpoint.md                      # single snapshot, overwritten each session: Last session / Current state / Next action
lessons.md                         # append-only, newest first: ### YYYY-MM-DD — title / What / Why it matters / Tags
.gitignore                         # existing GitHub template + appended talk entries
.env.example                       # variable names only
config/
  versions.env                     # pinned omnigent / agy / CLI versions and model names
  omnigent/agents/talk-coder.yaml  # the single agent spec reused across harnesses
  omnigent/policies.yaml           # built-in + CEL policies attached to talk-coder
policies/
  pyproject.toml                   # uv project: offline tests for the CEL expressions
  tests/test_cel_policies.py
demos/
  01-harness-switch/run.sh, task.md
  02-antigravity/README.md         # step-by-step agy native-creds walkthrough (on-stage script)
  03-routing/prompts.md, check_routing.sql
  04-policies/run.sh
  05-tracing/smoke.sh, usage.sql, traces.md
  06-skills/README.md, skills/gcp-databricks-facts/SKILL.md
  07-memory/pyproject.toml, memory_demo.py, README.md
  08-sandbox/pyproject.toml, sandbox_demo.py, README.md
  09-collab-mobile/README.md
scripts/
  check.sh                         # secret/hostname scan + yaml lint + policy tests
  preflight.sh                     # day-of checks: versions, endpoints, auth
docs/
  research/facts.md                # every on-stage claim + exact quote + URL + verified date
  superpowers/plans/               # this plan
talk/
  prep-reference.md               # presenter reference: model choices (3.8 Flash live, Argon mentioned), framing rules
  outline.md, speaker-notes.md, runbook.md
  slides/                          # deck source or link
  fallbacks/                       # recorded demo clips / screenshots
```

---

### Task 1: Repo scaffold and tracking layer

**Files:**
- Create: `tasks.md`, `checkpoint.md`, `lessons.md`, `.env.example`, `scripts/check.sh`
- Modify: `README.md`, `.gitignore` (append only)

**Interfaces:**
- Produces: `scripts/check.sh`, which exits non-zero on secret patterns, workspace hostnames, invalid YAML, or failing policy tests. Tracking formats follow ai-kitchen-dbx (`tasks.md` / `checkpoint.md` / `lessons.md`). Talk-worthy lessons get a `#talk` tag.

- [ ] **Step 1: Append to `.gitignore`.** Do not overwrite it: the existing file is GitHub's Python template and already covers `.venv/`, `__pycache__/`, and similar. `.isaac/` stays tracked.

```gitignore
# talk repo
.env.local
talk/fallbacks/*.mov
talk/fallbacks/*.mp4
```

- [ ] **Step 2: Write `.env.example`** (names only, no values)

```bash
DBX_PROFILE=            # AWS workspace profile hosting the Omnigent server + Sandbox — presenter chooses (fevm-cjc)
DBX_GCP_PROFILE=        # optional GCP workspace profile for Gemini/memory demos — presenter chooses
OMNI_SERVER=            # Omnigent server URL (<workspace>/api/2.0/omnigent); never commit
OMNIGENT_CONFIG_HOME=   # isolated Omnigent home, same as the omni-fevm wrapper ($HOME/.omnigent-fevm)
OMNIGENT_DATA_DIR=      # same dir; keeps auth tokens / host daemon separate from ~/.omnigent
GEMINI_MODEL=           # main live Gemini model (system.ai.gemini-3-8-flash on FEVM; Argon is GCP-only)
GEMINI_FLASH_MODEL=     # cheaper Gemini for contrast (system.ai.gemini-3-1-flash-lite)
WAREHOUSE_ID=           # SQL warehouse for usage queries (Task 9)
MEMORY_STORE=           # agent memory store id (Task 11)
```

- [ ] **Step 3: Write `scripts/check.sh`.** The secret scan excludes `scripts/check.sh` and `docs/superpowers/plans/`, because both contain the literal patterns.

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
files() { git ls-files -z --cached --others --exclude-standard -- . ':!scripts/check.sh' ':!docs/superpowers/plans/'; }
# 1. secret scan over tracked + untracked-not-ignored files
if files | xargs -0 grep -nIE '(dapi[0-9a-f]{32}|AIza[0-9A-Za-z_-]{35}|sk-[A-Za-z0-9]{20,}|ya29\.[0-9A-Za-z_-]+|"refresh_token")' 2>/dev/null; then
  echo "check: possible secret found (above)"; fail=1
fi
# 2. public repo: no workspace hostnames (docs.databricks.com links are fine)
if files | xargs -0 grep -nIE '[a-z0-9-]+\.(cloud|gcp)\.databricks\.com|adb-[0-9]+\.[0-9]+\.azuredatabricks\.net|databricksapps\.com' 2>/dev/null \
   | grep -v 'docs\.databricks\.com'; then
  echo "check: workspace hostname found (above) — move it to .env.local"; fail=1
fi
# 3. yaml parses
while IFS= read -r -d '' f; do
  uv run --quiet --with pyyaml python -c "import sys,yaml; yaml.safe_load(open(sys.argv[1]))" "$f" \
    || { echo "check: invalid yaml $f"; fail=1; }
done < <(git ls-files -z --cached --others --exclude-standard -- '*.yaml' '*.yml')
# 4. policy tests (once policies/ exists)
if [ -f policies/pyproject.toml ]; then
  (cd policies && uv run --quiet pytest -q) || fail=1
fi
exit $fail
```

- [ ] **Step 4: Verify that check.sh catches planted problems.** Run `printf 'x=dapi%032d\n' 0 > leak.txt && bash scripts/check.sh; echo "exit=$?"; rm leak.txt`. Expected: `check: possible secret found` and `exit=1`. Repeat with `printf 'h=foo-1.2.%s.databricks.com\n' gcp > leak.txt` and expect the hostname failure. A clean run should give `exit=0`.
- [ ] **Step 5: Write the tracking files** in ai-kitchen-dbx format (see `/Users/christopher.chalcraft/Projects/Databricks/ai-kitchen-dbx/{tasks,checkpoint,lessons}.md`):
  - `tasks.md`: `# Tasks` / "Rolling work list. Updated each session." / `## In Progress` / `## Next`, with one `- [ ] **Task N: <name>.**` line per task in this plan.
  - `checkpoint.md`: `# Checkpoint` / `**Last session:** <date>.` / `**Current state:**` / `**Next action (resume point):**`. Overwrite it at each session end.
  - `lessons.md`: header + format block, then the entries listed under *Lessons to seed* at the end of this plan.
- [ ] **Step 6: Update `README.md`** with the talk title, a 3-sentence abstract, the repo map, and a link to this plan.
- [ ] **Step 7: Commit** (`chore: scaffold talk repo and tracking layer`), after `bash scripts/check.sh` passes.

### Task 2: Fact sheet completion

**Files:**
- Modify: `docs/research/facts.md` (seeded 2026-11-02)

- [ ] **Step 1:** For each row of `facts.md`, re-open the URL and replace any paraphrase with the **exact** quote. WebFetch returns summaries, so slide quotes must be checked by eye or with `curl`.
- [ ] **Step 2:** Fill the items still marked open in `facts.md`: native Gemini route on Unity Gateway, Omnigent CEL policy docs page (404 on 2026-11-02), the `extends`/`executor.harness` schema after upgrading, `databricks-agentbricks` import name, and Sandbox region list.
- [ ] **Step 3: Verify:** `grep -c "OPEN" docs/research/facts.md` → `0`, or each remaining item has a stated reason and a slide-safe fallback wording.
- [ ] **Step 4:** Commit (`docs: complete talk fact sheet`).

### Task 3: Unity Gateway and Gemini models

**Files:**
- Create: `config/versions.env`, `demos/05-tracing/smoke.sh`

**Interfaces:**
- Produces: `GEMINI_MODEL` and `GEMINI_FLASH_MODEL` (generic `system.ai.*` / `databricks-gemini-*` names may also go in `config/versions.env`).

- [ ] **Step 0: BLOCKED until the presenter confirms which profile(s) to use** (`DBX_PROFILE`, optional `DBX_GCP_PROFILE`).
- [ ] **Step 1:** Load skills `databricks-core` and `databricks-model-serving`. Run `databricks auth describe --profile "$DBX_PROFILE"` to confirm the profile (do not print the token).
- [ ] **Step 2:** Confirm the Gemini model services. Done 2026-11-02 on `fevm-cjc`: `system.ai.gemini-3-8-flash` (live) and `system.ai.gemini-3-1-flash-lite` (contrast). Legacy `databricks-gemini-*` endpoints return 403. Record both names in `config/versions.env` (generic names are safe to commit).
- [ ] **Step 3:** Confirm Unity Gateway usage tracking is on (it's on by default since Jul 17 2026). Optionally attach an inference table and a rate limit to show on stage. Screenshot the settings to `talk/fallbacks/gateway-settings.png` and redact the hostname.
- [ ] **Step 4: Write `demos/05-tracing/smoke.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../../.env.local"
# Native Gemini route, the same one omni agy's adapter uses. Brace ${m}: zsh/bash treat $m:g as a modifier.
m=${1:-$GEMINI_MODEL}
host=$(databricks auth describe --profile "$DBX_PROFILE" -o json | jq -r '.details.host')
token=$(databricks auth token --profile "$DBX_PROFILE" | jq -r '.access_token')
curl -fsS -X POST "${host}/ai-gateway/gemini/v1beta/models/${m}:generateContent" \
  -H "Authorization: Bearer ${token}" -H 'Content-Type: application/json' \
  -d '{"contents":[{"role":"user","parts":[{"text":"Reply with exactly: pong"}]}]}' \
  | jq -r '.candidates[0].content.parts[0].text'
```

- [ ] **Step 5: Verify:** `bash demos/05-tracing/smoke.sh` → output contains `pong`. Repeat with `bash demos/05-tracing/smoke.sh "$GEMINI_FLASH_MODEL"`. (`.details.host` from `auth describe` was verified 2026-11-02; `auth env` is deprecated.)
- [ ] **Step 6:** Add a `lessons.md` entry and commit (`feat: gemini via unity gateway smoke test`).

### Task 4: Omnigent upgrade and server connection

**Files:**
- Modify: `config/versions.env`

**Interfaces:**
- Consumes: `OMNI_SERVER`, `DBX_PROFILE`
- Produces: `OMNIGENT_VERSION=` pin. Every demo script connects with `--server "$OMNI_SERVER"`.

- [ ] **Step 1:** `omni upgrade` (local is 0.9.0.dev0; target ≥ v0.20.0). Record `omni --version` as `OMNIGENT_VERSION=`. If `omni upgrade` misbehaves, use `uv tool upgrade omnigent`. Never use brew.
- [ ] **Step 2:** Confirm the server connection: `omni login "$OMNI_SERVER"` if needed, then `omni diagnose --server "$OMNI_SERVER" --json`. Save a redacted copy to `talk/fallbacks/omni-diagnose.txt` (hostname removed).
- [ ] **Step 3:** Confirm the laptop is registered as a host (`omni host --server "$OMNI_SERVER"`) and check the managed server's preview prerequisites: the Omnigent preview, and the Sandbox preview for Task 12.
- [ ] **Step 4:** Re-check the agent YAML schema against the upgraded package (`executor.harness` vs `executor.type`/`config`) and update `facts.md`.
- [ ] **Step 5:** `lessons.md` entry (e.g. "stale 0.9 install had no `omni agy`") and commit (`chore: pin omnigent version`).

### Task 5: Harness engineering — one agent, four harnesses

**Files:**
- Create: `config/omnigent/agents/talk-coder.yaml`, `demos/01-harness-switch/run.sh`, `demos/01-harness-switch/task.md`

**Interfaces:**
- Produces: agent `talk-coder`. Harness IDs come from the upgraded `omni run --help`: `claude-sdk`, `codex`, `pi`, `antigravity` (direct) / `antigravity-native` (`omni agy`).

- [ ] **Step 1: Write `talk-coder.yaml`** using the schema confirmed in Task 4 Step 4:

```yaml
name: talk-coder
prompt: |
  You are a careful coding assistant working in the omnigent-talk repo.
  Keep changes minimal and explain them in one paragraph.
executor:
  harness: claude-sdk
  model: system.ai.claude-sonnet-5-5   # replace with the exact name from Task 3
```

- [ ] **Step 2: Write `task.md`**, a tiny deterministic task on a toy file under `demos/01-harness-switch/sandbox/` (e.g. "add a `--json` flag to `sandbox/greet.py`").
- [ ] **Step 3: Write `run.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source ../../.env.local
harness=${1:?usage: run.sh <claude-sdk|codex|pi|antigravity> [model]}
omni run ../../config/omnigent/agents/talk-coder.yaml --server "$OMNI_SERVER" \
  --harness "$harness" ${2:+--model "$2"} -p "$(cat task.md)"
```

- [ ] **Step 4: Verify:** run all four harnesses. Each completes the task, and each session is visible in the web UI. Record per-harness wall time and model in `checkpoint.md`.
- [ ] **Step 5:** Record per-harness differences (direct vs native TUI, skills support, auth quirks, Antigravity community tier) in `lessons.md` (`#talk`). These feed the harness-engineering slide.
- [ ] **Step 6:** Commit (`feat: single agent spec across four harnesses`).

### Task 6: Antigravity with native agy credentials via Databricks Gemini

**Files:**
- Create: `demos/02-antigravity/README.md`

**Interfaces:**
- Consumes: `GEMINI_MODEL`, `DBX_PROFILE`
- Produces: a working `omni agy` session whose model calls go through Unity Gateway and show up in Task 9 usage.

- [ ] **Step 1:** Install agy: `curl -fsSL https://antigravity.google/cli/install.sh | bash`. Read the script before running it. Require **agy ≥ 1.1.13** and record `AGY_VERSION=` in `config/versions.env`.
- [ ] **Step 2:** `omni setup` → Antigravity → *Configure native agy API key / gateway* → *Add a credential* → *Databricks profile* (`$DBX_PROFILE`). Confirm that a provider with `native_gemini: true` was written. Show it on stage redacted; never show the file raw.
- [ ] **Step 3: Go/no-go.** Confirm Unity Gateway serves Gemini through the **native Gemini API** (the route `ug gemini` uses), not only OpenAI-compatible chat. If it doesn't, or if it needs Bearer/token-refresh (unsupported by agy), fall back to agy's own Google OAuth (`~/.gemini/oauth_creds.json` already exists) and say on stage that the gateway route is pending. Do not fake it.
- [ ] **Step 4:** Run `omni agy --server "$OMNI_SERVER"` with `task.md`, and `bash demos/01-harness-switch/run.sh antigravity "$GEMINI_MODEL"` for the direct mode.
- [ ] **Step 5: Write `demos/02-antigravity/README.md`**, the on-stage walkthrough: (1) where creds live (Keychain / `~/.gemini/...`, never on screen), (2) the `omni setup` screens, (3) the redacted provider block with `native_gemini: true`, (4) `omni agy` running the task, (5) the matching row in `system.ai_gateway.usage`.
- [ ] **Step 6: Verify:** within about 15 minutes, a usage row appears with the Gemini `destination_model` and a `session_metadata.coding_agent` value for the run (Task 9 Q2).
- [ ] **Step 7:** Record `talk/fallbacks/antigravity-setup.mov` (gitignored) and commit (`feat: antigravity harness on databricks gemini`).

### Task 7: Smart Routing

**Files:**
- Create: `demos/03-routing/prompts.md`, `demos/03-routing/check_routing.sql`

**Interfaces:**
- Consumes: `OMNI_SERVER`, the Enhanced Unity Gateway preview (account admin), and `EXECUTE` on every candidate `system.ai.*` model.

- [ ] **Step 1:** Confirm the Enhanced Unity Gateway preview is enabled on the account. If it isn't, ask the presenter: it's an account-admin action, so don't toggle it yourself.
- [ ] **Step 2: Write `prompts.md`.** Use one prompt that naturally fans out to subagents with mixed difficulty (e.g. "rename X across the repo, then design a migration plan for Y"). List the *set* of models that may be chosen. Live: start a session with **Smart Routing** as the harness in the web UI, or with `omni claude --smart-routing --server "$OMNI_SERVER"`. The agent shows the model it chose for each subagent, with the reason when available.
- [ ] **Step 3: Write `check_routing.sql`**, which shows that routing happened for a session:

```sql
SELECT event_time, session_metadata.client_subagent_id, destination_model,
       session_metadata.smart_router_name, routing_information
FROM system.ai_gateway.usage
WHERE session_metadata.client_session_id = :session_id
ORDER BY event_time;
```

- [ ] **Step 4: Verify:** run the prompt three times. Each run has a non-null `smart_router_name`, and every `destination_model` is in the expected set. Don't assert exact picks (it's nondeterministic, with no dry-run). If no subagent is routed, rework the prompt.
- [ ] **Step 5 (optional):** Show Omnigent's own Auto picker: configure `routing: {provider: external, base_url, router_name, profile}` on the server, if the managed server allows server config. Skip it if not, and note that in `lessons.md`.
- [ ] **Step 6:** Commit (`feat: smart routing demo`).

### Task 8: Contextual policies (Omnigent CEL + Unity Gateway service policy)

**Files:**
- Create: `config/omnigent/policies.yaml`, `policies/pyproject.toml`, `policies/tests/test_cel_policies.py`, `demos/04-policies/run.sh`
- Modify: `config/omnigent/agents/talk-coder.yaml` (attach policies)

**Interfaces:**
- Produces: two CEL expressions in `policies.yaml` that are also loaded by the tests, so the tests and the deployed policy are the same text. The managed server only supports built-in and CEL policies; Python policies are rejected.

- [ ] **Step 1: Write `config/omnigent/policies.yaml`.** It holds the residency rule as CEL, plus built-in budgets. `PolicyEvent` has no cwd, so residency is keyed on the *paths in tool-call arguments*.

```yaml
policies:
  session_budget:
    type: function
    handler: omnigent.policies.builtins.cost.cost_budget
    factory_params: {max_cost_usd: 5.00, ask_thresholds_usd: [2.00]}
  data_residency:
    type: function
    handler: omnigent.policies.builtins.cel.cel_policy
    factory_params:
      expression: >
        event.type == "tool_call"
        && string(event.data.arguments).lowerAscii().contains("customer-data/")
        && !(has(event.context.model) && string(event.context.model).startsWith("system.ai."))
          ? {"result": "DENY", "reason": "customer-data/ is restricted to Databricks-governed models"}
          : {"result": "ALLOW"}
      reason: Data residency
```

Check that `string(map)` and `lowerAscii()` are supported by the `cel-python` version Omnigent pins. If not, match on specific argument keys (`event.data.arguments.path`, `.command`) and record what worked in `lessons.md`.
- [ ] **Step 2: Write `policies/pyproject.toml`** (uv project with dev deps `pytest>=8`, `pyyaml`, `omnigent`).
- [ ] **Step 3: Write the failing tests first.** `policies/tests/test_cel_policies.py` loads `data_residency.factory_params.expression` from `policies.yaml`, builds it with `omnigent.policies.builtins.cel.cel_policy`, and asserts:
  - a `tool_call` with `arguments={"path": "demo/customer-data/x.csv"}` and `context.model="gpt-5.5"` → DENY;
  - the same call with `context.model="system.ai.gemini-3-8-flash"` → ALLOW;
  - a non-sensitive path with any model → ALLOW;
  - a missing model on a sensitive path → DENY;
  - an upper-case `Customer-Data/` path → DENY (case doesn't bypass).
  Run `cd policies && uv run pytest -q` and confirm they fail before Step 1's expression is finalized.
- [ ] **Step 4: Verify:** `bash scripts/check.sh` passes; it runs pytest.
- [ ] **Step 5:** Attach the policies to `talk-coder.yaml`, using the schema confirmed in Task 4, inline or by reference.
- [ ] **Step 6: Unity Gateway layer.** In Unity Catalog, attach the **Sensitive Data Detection** guardrail service policy (Beta) to the Gemini service. Demo: a prompt containing a fake credit-card number is blocked. Blocked calls return HTTP 200 with the block reason. Screenshot this to `talk/fallbacks/`.
- [ ] **Step 7: Write `demos/04-policies/run.sh`.** Create `demos/04-policies/customer-data/sample.csv` with fake data, then ask `talk-coder` to summarize it twice: with a non-`system.ai.*` model (expect DENY plus the reason) and with `$GEMINI_MODEL` (expect ALLOW).
- [ ] **Step 8: Verify:** the run shows one deny and one allow, and the guardrail demo blocks.
- [ ] **Step 9:** Commit (`feat: CEL data-residency policy and gateway guardrail`).

### Task 9: Observability via Unity Gateway

**Files:**
- Create: `demos/05-tracing/usage.sql`, `demos/05-tracing/traces.md`

**Interfaces:**
- Consumes: Tasks 5–8 traffic, `WAREHOUSE_ID`

- [ ] **Step 1:** Load `databricks-unity-catalog` and `databricks-dbsql`. Run `DESCRIBE system.ai_gateway.usage` and confirm it matches the columns in Research Status.
- [ ] **Step 2: Write `usage.sql`**

```sql
-- Q1: calls and tokens per coding agent and model, last 24h
SELECT session_metadata.coding_agent AS agent, destination_model,
       count(*) AS calls, sum(total_tokens) AS tokens
FROM system.ai_gateway.usage
WHERE event_time > now() - INTERVAL 24 HOURS
GROUP BY ALL ORDER BY calls DESC;

-- Q2: one coding-agent session end to end
SELECT event_time, session_metadata.client_subagent_id, destination_model,
       total_tokens, latency_ms, invocation_metadata.source
FROM system.ai_gateway.usage
WHERE session_metadata.client_session_id = :session_id ORDER BY event_time;

-- Q3: Gemini share of traffic
SELECT lower(destination_model) LIKE '%gemini%' AS is_gemini, count(*) AS calls
FROM system.ai_gateway.usage
WHERE event_time > now() - INTERVAL 24 HOURS GROUP BY ALL;
```

- [ ] **Step 3:** Show the **built-in usage dashboard** instead of building one: the Overview, Coding Agents (harness usage, sessions, subagents) and Skills tabs. Screenshot each to `talk/fallbacks/`.
- [ ] **Step 4: Write `traces.md`**, covering how to find a session's requests in the **unified trace table** (Beta) and in inference tables, plus coding-agent tracing (`ai-gateway/coding-agent-observability#tracing`).
- [ ] **Step 5: Verify:** each query returns ≥1 row from today's runs, including at least one Gemini/Antigravity row.
- [ ] **Step 6:** Commit (`feat: unity gateway usage and trace queries`).

### Task 10: Skills on Databricks

**Files:**
- Create: `demos/06-skills/README.md`, `demos/06-skills/skills/gcp-databricks-facts/SKILL.md`

**Interfaces:**
- Produces: one skill registered with Unity Gateway Skills, loaded by at least two harnesses, and visible in the dashboard Skills tab and the `aiGatewaySkills` audit logs.

- [ ] **Step 1:** Write a tiny skill, `gcp-databricks-facts`, that answers "how do I call Gemini on Databricks" from `docs/research/facts.md`. Keep the source repo-local so attendees can reproduce it.
- [ ] **Step 2:** Register it through the **Unity Gateway Skills REST API** (Beta; `ai-gateway/skill-reference`) or the central coding-agent configuration (`ai-gateway/coding-agent-configure-govern`). Record the exact calls in the README.
- [ ] **Step 3:** Load it from `claude-sdk` and `antigravity` via Omnigent. Confirm the loads appear in the usage dashboard **Skills** tab and in `system.access.audit` with `service_name = 'aiGatewaySkills'`.
- [ ] **Step 4:** If a harness can't load gateway skills, show Omnigent's `load_skill` path instead and record that honestly in `lessons.md`.
- [ ] **Step 5:** Commit (`feat: databricks-governed skill across harnesses`).

### Task 11: Agent memory

**Files:**
- Create: `demos/07-memory/pyproject.toml`, `demos/07-memory/memory_demo.py`, `demos/07-memory/README.md`

**Interfaces:**
- Consumes: `MEMORY_STORE`, `DBX_GCP_PROFILE` (preferred, to show it on GCP) or `DBX_PROFILE`
- Produces: `memory_demo.py remember "<fact>" --user <id>` and `memory_demo.py recall "<question>" --user <id>`, run in separate processes to prove persistence.

- [ ] **Step 1:** Load `databricks-agent-bricks`. Confirm the memory Beta is enabled on the chosen workspace. Note that you pay for the underlying Lakebase.
- [ ] **Step 2: Write `pyproject.toml`** with dependencies `databricks-agentbricks>=0.6.0`, `databricks-sdk`. Confirm the import name (docs: `databricks_agentkit`) after install.
- [ ] **Step 3: Write `memory_demo.py`**

```python
import argparse, hashlib, os
from databricks.sdk import WorkspaceClient
from databricks_agentkit import AgentKitClient


def store():
    client = AgentKitClient(WorkspaceClient(profile=os.environ["MEMORY_PROFILE"]))
    return client.memory_stores.get(os.environ["MEMORY_STORE"])  # confirm get vs create in facts.md


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["remember", "recall"])
    p.add_argument("text")
    p.add_argument("--user", required=True)
    a = p.parse_args()
    s = store()
    if a.cmd == "remember":
        path = f"/facts/{hashlib.sha256(a.text.encode()).hexdigest()[:16]}.md"
        s.put(actor_id=a.user, path=path, content=a.text, description=a.text[:80])
        print("stored")
    else:
        for item in s.search(actor_id=a.user, query=a.text, limit=3):
            print(item.content)  # confirm field name in facts.md


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Verify:** `uv run memory_demo.py remember "My talk is at a Google dev conference and I prefer Gemini" --user chris`. Then, in a **new process**, `uv run memory_demo.py recall "which model do I prefer?" --user chris` prints the fact, and `--user someone-else` prints nothing. On stage, say that `actor_id` scopes recall but is not access control.
- [ ] **Step 5:** In the README, show how an Omnigent agent uses this (as an MCP tool or skill) so memory follows the user across harnesses. If that's out of time-scope, run it as a standalone demo and note that in `lessons.md`.
- [ ] **Step 6:** Commit (`feat: agent memory demo`).

### Task 12: Databricks Sandbox

**Files:**
- Create: `demos/08-sandbox/pyproject.toml`, `demos/08-sandbox/sandbox_demo.py`, `demos/08-sandbox/README.md`

**Interfaces:**
- Consumes: `DBX_PROFILE` (AWS; Sandbox is AWS-only, so disclose this)
- Produces: `sandbox_demo.py "<shell command>"`, which runs in a Databricks Sandbox and prints the exit code and stdout. Also an Omnigent session hosted in a Sandbox.

- [ ] **Step 1:** Enable the **Databricks Sandbox** preview on the workspace (presenter action) and confirm the region is supported.
- [ ] **Step 2: Implement `sandbox_demo.py`** (under 40 lines) with `databricks-sdk`: `w.sandbox.create_sandbox(sandbox_id=...)`, then `w.sandbox.execute_command_sync(..., args=["-c", cmd], execution_timeout=Duration(seconds=60))` (no shell is implied, so run `/bin/bash -c`), print `exit_code` and `stdout`, then `w.sandbox.delete_sandbox("sandboxes/<id>")`. Copy the exact signatures from the quickstart into `facts.md`.
- [ ] **Step 3: Verify the happy path:** `uv run sandbox_demo.py "python3 -c 'print(sum(range(10)))'"` → `45`.
- [ ] **Step 4: Verify isolation:** `uv run sandbox_demo.py "whoami; ls ~"` shows `sandbox-agent` and the sandbox home, not the laptop's. Note that **egress is unrestricted**, so don't claim network isolation; claim ingress closed and a separate filesystem and identity instead.
- [ ] **Step 5: Agent flow.** Start an Omnigent session hosted in a Databricks Sandbox from the web UI (the managed server supports Sandbox hosts; model access is forced through Unity Gateway). Have it write and run a data-analysis snippet. Document the steps in the README. Mention `omni sandbox create/connect` (modal/daytona/islo) as the OSS equivalent.
- [ ] **Step 6:** Commit (`feat: databricks sandbox demo for agent-generated code`).

### Task 13: Collaboration, mobile, a non-coding feature, and preflight

**Files:**
- Create: `demos/09-collab-mobile/README.md`, `scripts/preflight.sh`

- [ ] **Step 1: Collaboration.** Start a `talk-coder` session, click **Share** → *Edit*, and have a second account co-drive. Their messages appear labeled with their identity. Also show `omni attach <session_id>` from a second terminal. Inline comments are not a documented feature, so don't demo them.
- [ ] **Step 2: Mobile.** Open the same live session in the Omnigent Android app (`ai.omnigent.android`, Google Play) and send a steering message. Mirror the phone with `scrcpy` via nix (not brew).
- [ ] **Step 3: One non-coding feature.** Pick a scheduled task that runs `usage.sql` Q1 every morning and posts a summary, or the Slack integration (`omni integration slack`). Document it in the README.
- [ ] **Step 4: Write `scripts/preflight.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
source .env.local; source config/versions.env
ok=0; check() { if eval "$2" >/dev/null 2>&1; then echo "PASS $1"; else echo "FAIL $1"; ok=1; fi; }
check "omnigent version" '[ "$(omni --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -1)" = "$OMNIGENT_VERSION" ]'
check "agy version"      '[ "$(agy --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -1)" = "$AGY_VERSION" ]'
check "omni diagnose"    'omni diagnose --server "$OMNI_SERVER"'
check "databricks auth"  'databricks current-user me --profile "$DBX_PROFILE"'
check "gemini endpoint"  'bash demos/05-tracing/smoke.sh | grep -q pong'
check "policies"         'bash scripts/check.sh'
check "memory"           '(cd demos/07-memory && uv run memory_demo.py recall "model" --user chris | grep -qi gemini)'
check "sandbox"          '(cd demos/08-sandbox && uv run sandbox_demo.py "echo 45" | grep -q 45)'
exit $ok
```

- [ ] **Step 5: Verify:** `bash scripts/preflight.sh` → all PASS. Then set a bad `GEMINI_MODEL` and confirm `FAIL gemini endpoint` with exit 1.
- [ ] **Step 6:** Commit (`feat: collaboration/mobile demo and day-of preflight`).

### Task 14: Talk content, runbook, and dry run

**Files:**
- Create: `talk/outline.md`, `talk/speaker-notes.md`, `talk/runbook.md`, `talk/slides/` (or a link in README)

- [ ] **Step 1:** Confirm the audience level with the presenter, then rebalance the Talk Narrative timings into `talk/outline.md`.
- [ ] **Step 2:** Read `talk/prep-reference.md` first; its say / don't-say rules are binding. Write `speaker-notes.md` per segment: the key line, the demo command, the Databricks "why it matters" beat, the source URL from `facts.md`, and a **Beta / community-supported** label where it applies.
- [ ] **Step 3:** Build slides with `databricks-slides:slide-deck` or `fe-google-tools:google-slides`. Include a "receipts" slide from `lessons.md` (`#talk`) and git history (which harness or model wrote which part), plus the cross-cloud honesty slide.
- [ ] **Step 4: Write `runbook.md`.** Per demo: the pre-opened terminal or tab, exact keystrokes, expected output, the fallback clip, and a "switch to fallback after N seconds" rule. Screen hygiene: hide `~/.databrickscfg` and `~/.omnigent`, clear shell history, use a demo-only browser profile, turn on DND, and keep the workspace URL off screen (it's in `.env.local`).
- [ ] **Step 5:** Record a fallback for every demo into `talk/fallbacks/`.
- [ ] **Step 6: Full dry run** with a timer: preflight, then the whole talk. Log overruns and failures in `lessons.md` and fix them. Repeat until it runs clean twice.
- [ ] **Step 7:** Overwrite `checkpoint.md` and commit (`docs: talk outline, notes, runbook`).

### Task 15: Project agent guidance and behavior evaluation

**Files:**
- Modify: `AGENTS.md`; keep `CLAUDE.md` as `@AGENTS.md`
- Create: `.config/wt.toml`, `.agents/behaviors/*/BEHAVIOR.md`, MLflow evaluation runner

**Interfaces:**
- Worktrunk owns child worktrees and runs `just check` before merge. JJ 0.45.1 is used only in
  the primary worktree because it cannot initialize inside Git worktrees.
- Four Agent Behavior specs govern Databricks data processing, infrastructure deployment,
  evidence-backed talk content, and rehearsal-ready demos.
- `just behavior-eval-setup`, `just behavior-eval-smoke`, and `just behavior-eval` use the
  user-selected `DBX_PROFILE` and opt-in Databricks MLflow experiment/model settings.

- [x] **Step 1:** Make AGENTS.md the concise source of truth and preserve CLAUDE.md's import.
- [x] **Step 2:** Add the Worktrunk pre-merge check and document the JJ/worktree boundary.
- [x] **Step 3:** Add the four behavior specs in the agentbehavior.dev format.
- [x] **Step 4:** Add a public-safe 60-case synthetic trajectory corpus, managed MLflow datasets,
  and registered `make_judge()` scorers. Keep workspace runs outside `just check`.
- [ ] **Step 5:** Run the five-case smoke evaluation, then the full evaluation. Record run IDs and
  scorer agreement on the talk's receipts slide without exposing the experiment URL.
- [ ] **Step 6:** Rehearse the behaviors as a short build-log beat: show one passing trajectory and
  one caught failure, citing agentbehavior.dev from the fact sheet.

---

## Decisions (presenter)

2026-11-01:
1. **Profiles:** to be provided later. Task 3 onward is blocked until then. Tasks 1–2 can proceed. *Superseded by 11:* `fevm-cjc`, given 2026-11-02.
2. **Slot:** 60 min (45 content + 15 Q&A).
3. **AWS workspace:** OK for agent memory / Sandbox if they're unavailable on GCP. Disclose this on stage.
4. **Repo:** public at talk time.
5. **Android:** the presenter has a device and uses the app. The mobile demo stays in.

2026-11-02:
6. **Omnigent server:** use the presenter's existing Databricks-hosted server (AWS workspace) rather than standing up a GCP one. Consequences: CEL/built-in policies only, Sandbox available, cross-cloud honesty slide. *Refined by 11:* that server is now the FEVM workspace's managed Omnigent.
7. **Tracking:** follow ai-kitchen-dbx conventions (`tasks.md` / `checkpoint.md` / `lessons.md`).
8. **Plan lives on `main`** (merged from `worktree-87fc0046`).

2026-11-02 (later):
9. **Upgraded:** omnigent CLI → `0.22.0.dev0` (git `08b7d804`, tracks `omnigent-ai/omnigent` main; extras `antigravity, databricks`). The remote server reports `0.21.0.dev0`. `omni agy` is available. agy `1.4.12` is installed at `~/.local/bin/agy` (official installer, SHA-512 verified). Its `agy install` shell-config step was **skipped**, because the rc files are home-manager symlinks and `~/.local/bin` is already on PATH. Task 4 Step 1 and Task 6 Step 1 are done; pin these in `config/versions.env` during Task 1.

10. **Antigravity profile:** `fevm-cjc` (AWS FEVM workspace) is the Databricks profile for `omni agy`. Probed 2026-11-02: the native Gemini route `POST <ws>/ai-gateway/gemini/v1beta/models/system.ai.gemini-3-8-flash:generateContent` returns 200 with `thoughtSignature`, so the **Task 6 go/no-go passes**. Served Gemini models: `system.ai.gemini-3-1-flash-lite`, `-3-5-flash`, `-3-7-flash`, `-3-8-flash`. **No Gemini 4 Argon** on this workspace; find a workspace that has it, or present Argon from the release note only. Legacy `databricks-gemini-*` endpoints return 403 *"no longer available. Use Unity Catalog model services."* All Gemini names in this plan should be `system.ai.gemini-*`, and Task 3's `smoke.sh` must use the native route (or `system.ai.*` names), not `serving-endpoints query databricks-gemini-*`.

2026-11-02 (night):
11. **FEVM is the single demo workspace, driven by `omni-fevm`.** Logfood couldn't show gateway traces (no BROWSE on `system`, no `unity_gateway_otel_spans`). On FEVM (`fevm-cjc`) the presenter is a workspace admin and *can* read `system.ai_gateway.usage`. Details are in `docs/omni-fevm.md`.
    - **Wrapper:** `omni-fevm` is a home-manager fish function next to `omni-dev` / `omni-gtm`. It's **plain `omni`, not `isaac omni`**, with `OMNIGENT_CONFIG_HOME` = `OMNIGENT_DATA_DIR` = `~/.omnigent-fevm`, `OMNIGENT_SERVER` = FEVM's `/api/2.0/omnigent` mount, and `DATABRICKS_CONFIG_PROFILE=fevm-cjc`. Isaac would pre-configure harnesses against the ai-devtools gateway, so usage would land in the wrong workspace. Demo scripts must export the same two `OMNIGENT_*` vars (now in `.env.example`) so they never touch `~/.omnigent`.
    - **Gemini:** every live demo uses `system.ai.gemini-3-8-flash`. Argon gets a GCP-only release-note slide (wording in `talk/prep-reference.md`). This supersedes the "find a workspace with Argon" option in 10.
    - **Blocker:** FEVM's `/api/2.0/omnigent/v1/me` returned **404** (2026-11-02), so the *Omnigent* workspace preview must be enabled (FEVM Settings → Previews), along with the *Databricks Sandbox* preview for Task 12. Then run `omni-fevm setup`, `omni-fevm login <ws>`, and `omni-fevm host`.
    - **Harness traffic matrix (to fill in after setup):** org-managed Claude Code settings pin `ANTHROPIC_BASE_URL` / `apiKeyHelper` to the ai-devtools gateway, and `~/.codex/config.toml` does the same for Codex. So the native Claude/Codex TUIs probably won't show up in FEVM usage. pi and agy (Omnigent provider) and direct `claude-sdk` should. Verify with the query in `docs/omni-fevm.md` and record the results here.

## Lessons to seed (`lessons.md`, Task 1 Step 5)

- **2026-11-01 — Planning without tools produces a plausible but wrong plan.** *What:* the first planning session had no Bash/WebFetch, so 12/12 facts were unverified, and on 2026-11-02 most needed correction (product name, smart routing layer, memory API, sandbox cloud, policy support). *Why it matters:* verify against primary docs before building. *Tags:* #research #talk
- **2026-11-02 — Managed Omnigent rejects Python policies.** *What:* Databricks-hosted Omnigent supports built-in and CEL policies only, and `PolicyEvent` has no cwd. *Why it matters:* residency is expressed in CEL over tool-call arguments and tested offline with the real factory. *Tags:* #omnigent #policies #talk
- **2026-11-02 — Project `.omnigent/config.yaml` replaces non-harness keys wholesale.** *What:* only `harness:` deep-merges, so a repo `providers:` block would hide the user's providers. *Why it matters:* demos use `--server`, and `~/.omnigent` is never touched. *Tags:* #omnigent #config
- **2026-11-02 — `omni upgrade --dry-run` upgraded for real.** *What:* on a git-tracking install, `--dry-run` printed the resolution and then installed it. *Why it matters:* use `--check` to look without changing anything. *Tags:* #omnigent #talk
- **2026-11-02 — agy's installer edits shell rc files.** *What:* the final `agy install` step configures the shell, but on a nix/home-manager machine the rc files are read-only store symlinks. *Why it matters:* strip that step and rely on `~/.local/bin` already being on PATH. *Tags:* #nix #antigravity
- **2026-11-02 — zsh `$var:g` is a modifier.** *What:* `"$HOST/.../$m:generateContent"` was mangled into `.../nerateContent` because zsh treats `:g` as a history modifier. *Why it matters:* always brace (`${m}:generateContent`) in Gemini URLs. *Tags:* #shell
- **2026-11-02 — "Same wrapper, different server" isn't enough for traces.** *What:* `omni-gtm`-style wrappers only change the Omnigent *server*. Model calls follow the harness's own gateway config: isaac pre-config, org-managed Claude Code settings, and `~/.codex/config.toml` all pin the ai-devtools gateway. *Why it matters:* the server (session state, UI, mobile) and the model gateway (usage, traces) are separate layers. Check where usage actually lands before claiming "it's all traced". *Tags:* #omnigent #harness-engineering #talk
- **2026-11-02 — Isolate Omnigent per workspace with `OMNIGENT_CONFIG_HOME` + `OMNIGENT_DATA_DIR`.** *What:* the data dir also holds `auth_tokens.json` and the host daemon pidfile, so `~/.omnigent-fevm` separates FEVM completely from the daily-use `~/.omnigent`. *Why it matters:* demo setup can't break the presenter's real config. *Tags:* #omnigent #config
- **2026-11-03 — Each harness speaks a different gateway dialect, so model names differ.** *What:* direct pi on a `kind: databricks` provider uses `/serving-endpoints` (needs `databricks-claude-sonnet-5-5`; `system.ai.*` → 404), claude-sdk uses the Anthropic surface (`system.ai.claude-sonnet-5-5`), and native agy uses the native Gemini route through Omnigent's adapter. All four FEVM surfaces returned 200 when probed directly. *Why it matters:* "the gateway is broken" was wrong every time. Probe the surface before blaming it. *Tags:* #harness-engineering #gateway #talk
- **2026-11-03 — `omni agy --model` was dropped on the remote path.** *What:* on 0.22.0.dev0 the runner logged `model_override=None`, so agy asked for its default `gemini-3.1-pro-preview` and the Databricks adapter refused it as "not unambiguous". `/model` → Gemini 3.8 Flash inside agy fixed it. *Why it matters:* the demo picks the model in-TUI. It may be worth an upstream issue. *Tags:* #antigravity #omnigent #bug
- **2026-11-03 — Agent sessions leak routing env into everything they launch.** *What:* a shell inside Claude Code (itself under an Omnigent runner) exports about 60 vars (`ANTHROPIC_BASE_URL`, `OMNIGENT_SERVER`, `OMNIGENT_DATABRICKS_ORG_PIN`, `OMNIGENT_CREDENTIAL_SERVICE_*`, …). A FEVM host daemon started there sent claude-sdk calls to the *other* workspace's gateway, despite `profile=fevm-cjc`. *Why it matters:* nested meta-harnesses need hermetic launchers. `omni-fevm` now `env -u`s those prefixes. *Tags:* #harness-engineering #omnigent #talk
- **2026-11-03 — Logs show intent; usage rows show truth.** *What:* after the env fix, claude-sdk's runner log said `base_url=<fevm>`, yet no FEVM usage row ever appeared, for claude-sdk or native Claude. Likely cause: org-managed Claude Code settings (`env.ANTHROPIC_BASE_URL`, `apiKeyHelper`, policy precedence) applied by the `claude` CLI underneath both. *Why it matters:* on the presenter's laptop, only Antigravity/Gemini and pi demonstrably land on FEVM. Build the "traced on this workspace" demo around agy, and present the Claude pinning as device-level governance. *Tags:* #observability #governance #talk
- **2026-11-03 — `system.ai_gateway.usage` lags about 20 min and is account-wide.** *What:* the newest row was 22 min old, and the table held other users' traffic. Filter with `requester = current_user()`. *Why it matters:* on stage, show a query over calls made *before* the talk, or use the unified trace table if it's enabled. *Tags:* #observability #talk
- **2026-11-02 — A research subagent was blocked by auto mode.** *What:* the Databricks-docs research subagent was refused, so the docs were fetched inline instead. *Why it matters:* permission modes are a visible safety feature, and plans should not depend on a single delegation path. *Tags:* #permissions #talk

## Still Open

- Audience mix (app devs vs ML/data folks). This affects how deep segments 8–9 go. Confirm in Task 14.
- A second account or person for the collaboration demo (Task 13 Step 1).
- Whether a GCP workspace (`DBX_GCP_PROFILE`) is available for the Gemini/memory demos, or everything runs on the AWS workspace.
- Whether the Enhanced Unity Gateway preview (Smart Routing) is enabled on the account (Task 7 Step 1).
- **FEVM previews:** enable *Omnigent* (currently 404) and *Databricks Sandbox*, then run `omni-fevm setup` / `login` / `host` (Decision 11).
- **FEVM unified trace table:** try AI Gateway → Govern → Traces. If that needs metastore admin (FEVM shares `metastore_aws_us_east_1`), fall back to `system.ai_gateway.usage` plus inference tables.
- **Harness traffic matrix:** which harnesses' model calls show up in FEVM usage (Decision 11).
