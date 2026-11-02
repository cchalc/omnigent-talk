# Omnigent Meta-Harness Talk — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this repo into both (a) the live demo environment and (b) the build log for a Google developer conference talk: *"One harness to rule them all: Omnigent as a meta-harness, with Gemini on Databricks."*

**Architecture:** The repo holds checked-in, secret-free Omnigent config (providers, agents, routing, policies), small demo scripts for the Databricks pieces (Unity AI Gateway tracing, agent memory on Lakebase, serverless sandbox), the talk itself (outline, speaker notes, demo runbook), and a tracking layer (tasks / checkpoints / lessons) so the build process can be shown on stage too. Every demo has a scripted happy path, a verification command, and a pre-recorded fallback.

**Tech Stack:** Omnigent (`omni` CLI, server, web UI, Android app), harnesses: Claude Code, Codex, Pi, Antigravity (`agy`); Databricks on GCP: Unity AI Gateway (Gemini 4 "Argon" + others), `system.ai_gateway.usage`, inference tables, MLflow tracing, Lakebase agent memory, serverless sandbox; Python via `uv`; Databricks CLI v1.17+.

**Spec:** No separate spec doc. The source brief is copied into the "Source Brief" section below. Executors should treat it as the spec.

## Source Brief (from the user, 2026-11-01)

- Talk at a **Google developer conference**. The repo tracks everything done and gets presented alongside the coding agents and techniques used to build it.
- Central theme: **set up and configure Omnigent as a meta-harness** to switch between harnesses and models, with smart routing and more (https://omnigent.ai/docs/use/coding-agents), including Omnigent features beyond coding agents.
- Cover the **full scope** of Omnigent, with a focus on: **harness engineering, smart routing, contextual policies, usability (collaboration, mobile app)**.
- Highlight **Gemini as a foundation model on Databricks**, and Databricks itself running **on GCP**. Cite https://docs.databricks.com/gcp/en/release-notes/unity-gateway/#google-gemini-4-argon-is-now-available-on-unity-gateway.
- Set up **Antigravity**: https://omnigent.ai/docs/build/harnesses/configuration#antigravity and #configure-native-agy-credentials. Walk through what the setup looks like and how to configure Omnigent to run it well.
- Show **tracing of model calls with Unity AI Gateway** and **skill usage on Databricks**.
- Show **agent memory** (https://docs.databricks.com/aws/en/agents/custom-agents/stateful-agents) and **serverless sandbox** (https://docs.databricks.com/aws/en/compute/serverless/sandbox).
- Soft theme throughout: **Databricks platform features and why they matter to Google developers**.
- Track tasks, checkpoints, and lessons the way `/Users/christopher.chalcraft/Projects/Databricks/ai-kitchen-dbx` does.

## Global Constraints

- **Never use Homebrew.** Install with `uv`, `uv tool`, `npm`, `nix`, or the official curl installers (see `~/.agents/behaviors/package-management/BEHAVIOR.md`).
- **Never auto-select a Databricks profile.** All commands use `--profile "$DBX_PROFILE"`. The presenter sets `DBX_PROFILE` once in `.env.local`, which is gitignored. The talk workspace must be a **GCP** workspace.
- **No secrets in git.** Tokens, API keys, OAuth files, and workspace hostnames you don't want public go in `.env.local` or `~/.omnigent/`, never in tracked files. Run `scripts/check.sh` (Task 1), which greps for token patterns, before every commit.
- **Shared agent config:** do not edit `~/.omnigent`, `~/.agents`, or skill dirs in place. Repo config is the source of truth, applied with `scripts/apply-config.sh`, which snapshots first (`~/.agents/behaviors/shared-config-edits/BEHAVIOR.md`).
- **Every on-stage claim carries a source URL** in `docs/research/facts.md`. Unverified claims are tagged `[UNVERIFIED]` and must not reach slides.
- Commit messages end with `Co-authored-by: Isaac <no-reply@databricks.com>`.
- Talk length assumption: **40 min** (30 talk/demo + 10 Q&A). Adjust in Task 14 once the slot is confirmed.

## Review Focus

1. **Conference Wi-Fi fails or a workspace or endpoint is slow.** Each demo must have a recorded fallback (`talk/fallbacks/`), and the runbook must say when to switch to it (Task 14 dry run).
2. **Model or endpoint names change before the talk.** Gemini endpoint names, harness model IDs, and Omnigent versions are pinned in `config/versions.env` and checked by `scripts/preflight.sh` (Task 13), which fails loudly instead of failing live.
3. **Secrets leaking on screen or into git.** This covers OAuth files, `~/.databrickscfg`, and terminal history. `scripts/check.sh` guards git (Task 1). The runbook has a "screen hygiene" checklist (Task 14).
4. **The routing demo picks an unexpected harness or model.** The routing demo prompts are written to have one obvious winner. The test in Task 7 asserts the router's choice for each scripted prompt before stage time.
5. **A policy blocks the presenter mid-demo.** The cost budget and the data-residency policy are tested so the happy-path prompts pass and the "deny" prompt is denied (Task 8 unit tests and a smoke test).

---

## Research Status (read first)

The planning session could not fetch docs directly (WebFetch was denied). The facts below come from web-search summaries and **must be verified in Task 2** before anyone builds on them.

| Claim | Source to verify | Status |
|---|---|---|
| Omnigent is a meta-harness over Claude Code, Codex, Pi, Antigravity, etc. It has Direct and Native-TUI harness modes | omnigent.ai/docs/build/harnesses/supported | UNVERIFIED |
| Antigravity harness: `pip install "omnigent[antigravity]"`, `harness: antigravity`, aliases `agy`, `google-antigravity` | omnigent.ai/docs/build/harnesses/configuration#antigravity, github omnigent-ai/omnigent docs/AGENT_YAML_SPEC.md | UNVERIFIED |
| Native agy creds: macOS Keychain (agy ≥1.1.7), `~/.gemini/oauth_creds.json` (macOS), `~/.gemini/antigravity-cli/antigravity-oauth-token` (Linux). The native harness needs a gateway exposing the **native Gemini API**, not an OpenAI-compatible route | omnigent.ai/docs/build/harnesses/configuration#configure-native-agy-credentials | UNVERIFIED |
| `omni setup` with a Databricks profile writes a provider like `databricks-gemini-<profile>` with `native_gemini: true` | omnigent.ai/docs/build/models | UNVERIFIED |
| Smart routing: server `llm:` block (judge model, `fallback_models`) or `routing: {provider: external, base_url, router_name, ...}`, plus an "Auto · smart routing" option in the UI | omnigent.ai/docs/reference/configuration/routing | UNVERIFIED |
| Policies: `policies:` in server config or agent YAML. Each has `type: function`, `handler: <dotted path>`, `factory_params`. Builtins include `cost.cost_budget`, `safety.max_tool_calls_per_session`, `github.github_policy`. `PolicyEvent` includes `conversation_id` | github omnigent-ai/omnigent docs/POLICIES.md | UNVERIFIED |
| Collaboration: share a live session by URL, comment inline, steer. The same session runs across terminal, web, and mobile. An Android app is on Google Play | omnigent.ai/docs/collaborate, /docs/interact/mobile | UNVERIFIED |
| `omni diagnose` prints a secret-free environment snapshot | omnigent.ai/releases | UNVERIFIED |
| Databricks docs host an Omnigent quickstart on GCP | docs.databricks.com/gcp/en/omnigent/quickstart | UNVERIFIED |
| Gemini 4 "Argon" is available on Unity Gateway (GCP) | user-supplied release-note anchor | user-supplied, confirm date and endpoint name |
| `system.ai_gateway.usage` includes coding-agent session metadata and invocation source. Inference tables log payloads | docs.databricks.com/gcp/en/ai-gateway/usage-tracking | UNVERIFIED |
| Agent memory: Lakebase-backed short-term memory (LangGraph `CheckpointSaver`) and long-term memory (`DatabricksStore`) in `databricks-langchain[memory]` | user-supplied stateful-agents URL | confirm API names |
| Serverless sandbox: isolated serverless Linux env for agent-generated code | user-supplied sandbox URL | confirm API, GCP availability, and preview status |

## Talk Narrative (target shape — finalized in Task 14)

| # | Segment | Min | Live demo | Databricks "why it matters to Google devs" beat |
|---|---|---|---|---|
| 1 | Hook: "I built this talk with 4 agents and 6 models. Here's the receipt." Show the repo's LESSONS and CHECKPOINTS | 2 | repo tour | — |
| 2 | Problem: harness lock-in. Each agent CLI has its own config, auth, skills, and policies | 3 | — | — |
| 3 | Omnigent as a meta-harness: architecture (server, harnesses, providers, policies, UI) | 4 | `omni` overview | — |
| 4 | Harness engineering: one agent spec, four harnesses (Claude Code, Codex, Pi, **Antigravity**) | 5 | switch harness live | One credential (a Databricks profile) for all of them |
| 5 | **Gemini on Databricks on GCP**: Unity AI Gateway, Gemini 4 Argon, native Gemini API for `agy` | 4 | agy driven by Databricks Gemini | Governance (UC permissions, rate limits, budgets) applied to Gemini |
| 6 | Smart routing: Auto mode picks harness and model per task | 3 | 3 scripted prompts | Gateway-side routing and fallbacks |
| 7 | Contextual policies: budget, GitHub write scope, data residency | 3 | allowed and denied action | Data stays governed by Unity Catalog |
| 8 | Observability: every call and skill traced | 3 | `system.ai_gateway.usage` and MLflow traces | One SQL-queryable audit trail across vendors |
| 9 | Agents that remember and act safely: Lakebase memory and serverless sandbox | 4 | recall across sessions, run code in sandbox | Managed Postgres plus isolated compute, no infra |
| 10 | Usability: collaborate on a live session, continue on an Android phone | 2 | join from phone | — |
| 11 | Recap, how to try it (links, QR to repo) | 1 | — | — |

## File Structure

```
README.md                          # talk abstract, repo map, how to reproduce
TASKS.md                           # live task board (mirrors this plan's checkboxes at a glance)
CHECKPOINTS.md                     # dated "working state" snapshots (what works, how to resume)
LESSONS.md                         # dated lessons learned (feeds the talk's "receipts" segment)
.gitignore                         # .env.local, .venv, fallbacks/*.mp4 if large, etc.
.env.example                       # DBX_PROFILE=, GEMINI_ENDPOINT=, LAKEBASE_INSTANCE=, ... (no values)
config/
  versions.env                     # pinned omnigent / agy / CLI versions and endpoint names
  omnigent/
    config.yaml                    # providers (databricks profile via env), defaults
    server_config.yaml             # routing + server-wide policies
    agents/
      talk-coder.yaml              # the single agent spec reused across harnesses
      talk-coder.antigravity.yaml  # harness override for agy
policies/
  pyproject.toml                   # uv project for custom policies
  talk_policies/__init__.py
  talk_policies/residency.py       # data-residency policy: pure core + omnigent adapter
  tests/test_residency.py
demos/
  01-harness-switch/run.sh
  02-antigravity/README.md         # step-by-step agy native-creds walkthrough (on-stage script)
  03-routing/prompts.md + test_routing.sh
  04-policies/run.sh
  05-tracing/usage.sql, traces.md
  06-skills/README.md
  07-memory/memory_demo.py
  08-sandbox/sandbox_demo.py
  09-collab-mobile/README.md
scripts/
  check.sh                         # secret scan + yaml lint + policy tests
  apply-config.sh                  # snapshot ~/.omnigent then link/copy repo config
  preflight.sh                     # day-of checks: versions, endpoints, auth, warehouses
docs/
  research/facts.md                # every on-stage claim + source URL + verified date
  superpowers/plans/               # this plan
talk/
  outline.md                       # final segment plan with timings
  speaker-notes.md
  runbook.md                       # exact demo keystrokes, fallbacks, screen hygiene
  slides/                          # deck source or link (Google Slides via fe-google-tools:google-slides)
  fallbacks/                       # recorded demo clips / screenshots
```

---

### Task 1: Repo scaffold and tracking layer

**Files:**
- Create: `TASKS.md`, `CHECKPOINTS.md`, `LESSONS.md`, `.gitignore`, `.env.example`, `scripts/check.sh`
- Modify: `README.md`

**Interfaces:**
- Produces: `scripts/check.sh`, which exits non-zero on secret patterns, invalid YAML, or failing policy tests. Every later task runs it before committing. `LESSONS.md` entry format: `## YYYY-MM-DD — <title>` followed by **Context / Lesson / Talk-worthy? (y/n)**.

- [ ] **Step 1: Reconcile with ai-kitchen-dbx conventions.** Open `/Users/christopher.chalcraft/Projects/Databricks/ai-kitchen-dbx` (the planning session could not read it). Note its task, checkpoint, and lesson file names, formats, and any hooks or skills that write them. If they differ from this task's names, **use ai-kitchen-dbx's names and formats** and update the File Structure section of this plan to match. Record the decision in `LESSONS.md`.
- [ ] **Step 2: Write `.gitignore`**

```gitignore
.env.local
.venv/
__pycache__/
*.pyc
.isaac/
mtime-test-*/
talk/fallbacks/*.mov
```

- [ ] **Step 3: Write `.env.example`** (names only, no values)

```bash
DBX_PROFILE=            # GCP workspace profile from ~/.databrickscfg — presenter chooses
GEMINI_ENDPOINT=        # Unity AI Gateway endpoint name for Gemini 4 Argon (Task 3)
GEMINI_FLASH_ENDPOINT=  # cheaper Gemini endpoint for routing contrast (Task 3)
LAKEBASE_INSTANCE=      # Lakebase instance for agent memory (Task 11)
EMBEDDING_ENDPOINT=     # embeddings endpoint for long-term memory (Task 11)
WAREHOUSE_ID=           # SQL warehouse for usage queries (Task 9)
```

- [ ] **Step 4: Write `scripts/check.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
# 1. secret scan over tracked + staged files
if git ls-files -z --cached --others --exclude-standard \
   | xargs -0 grep -nIE '(dapi[0-9a-f]{32}|AIza[0-9A-Za-z_-]{35}|sk-[A-Za-z0-9]{20,}|ya29\.[0-9A-Za-z_-]+|"refresh_token")' 2>/dev/null; then
  echo "check: possible secret found (above)"; fail=1
fi
# 2. yaml parses
for f in $(git ls-files --cached --others --exclude-standard '*.yaml' '*.yml'); do
  uv run --quiet --with pyyaml python -c "import sys,yaml; yaml.safe_load(open(sys.argv[1]))" "$f" \
    || { echo "check: invalid yaml $f"; fail=1; }
done
# 3. policy tests (once policies/ exists)
if [ -f policies/pyproject.toml ]; then
  (cd policies && uv run --quiet pytest -q) || fail=1
fi
exit $fail
```

- [ ] **Step 5: Verify that check.sh catches a planted secret**

Run: `printf 'x=dapi%032d\n' 0 > ./leak.txt && bash scripts/check.sh; echo "exit=$?"; rm leak.txt`
Expected: prints `check: possible secret found` and `exit=1`. Then `bash scripts/check.sh; echo "exit=$?"` gives `exit=0`.

- [ ] **Step 6: Write `TASKS.md`** with one line per task in this plan (`- [ ] Task N: <name>`). Write `CHECKPOINTS.md` with its first entry (`## 2026-11-01 — Plan written; nothing executed yet. Resume at Task 1.`). Write `LESSONS.md` with the first lesson: *"Planning session had no Bash/WebFetch/out-of-repo read permission. Research came from search summaries, hence the Research Status table. Talk-worthy? y (permission modes as a safety feature)."*
- [ ] **Step 7: Update `README.md`** with the talk title, a 3-sentence abstract (from the Goal and Source Brief), the repo map (File Structure), and a link to this plan.
- [ ] **Step 8: Commit**

```bash
bash scripts/check.sh && git add -A && git commit -m "chore: scaffold talk repo and tracking layer

Co-authored-by: Isaac <no-reply@databricks.com>"
```

### Task 2: Fact verification pass

**Files:**
- Create: `docs/research/facts.md`
- Modify: this plan's Research Status table (flip statuses)

**Interfaces:**
- Produces: `docs/research/facts.md`, a table with columns `claim | exact quote | URL | verified (YYYY-MM-DD) | slide #`. Later tasks look up config keys and commands here, not from memory.

- [ ] **Step 1:** For each row in Research Status, open the URL and copy the **exact** config keys, commands, and quotes into `facts.md`. Use the `databricks-docs` skill for Databricks pages and WebFetch for omnigent.ai and GitHub.
- [ ] **Step 2:** Also capture what's missing from the Omnigent docs: the full feature list beyond coding agents (e.g. scheduled tasks, inbox/async calls, browser tools, skills loading, sys_* tools, agent download/registry). These feed the "full scope" slide.
- [ ] **Step 3:** Confirm on the GCP docs: the Gemini 4 Argon release-note date, the endpoint name pattern, whether Unity AI Gateway exposes the **native Gemini API** route that `agy` needs, and whether **agent memory** and **serverless sandbox** are available on **GCP** (the user's links are AWS docs). If either is unavailable on GCP, record it and decide in Task 11/12 whether to demo on an AWS workspace and say so on stage.
- [ ] **Step 4:** Flip each row's status in this plan to VERIFIED or WRONG (with the correction).
- [ ] **Step 5: Verify:** `grep -c "| UNVERIFIED |" docs/superpowers/plans/2026-11-01-omnigent-meta-harness-talk.md` → `0`.
- [ ] **Step 6:** Commit (`docs: verify talk facts against primary sources`).

### Task 3: Databricks GCP workspace and Unity AI Gateway (Gemini)

**Files:**
- Create: `config/versions.env`, `demos/05-tracing/smoke.sh`

**Interfaces:**
- Produces: `GEMINI_ENDPOINT` and `GEMINI_FLASH_ENDPOINT` values (in `.env.local`, and in `config/versions.env` if the names aren't sensitive). Usage tracking and inference tables are enabled on those endpoints.

- [ ] **Step 1:** Load skills `databricks-core` and `databricks-model-serving`. The presenter chooses the GCP profile and sets `DBX_PROFILE` in `.env.local`. Confirm it is GCP: `databricks auth describe --profile "$DBX_PROFILE"` shows a `*.gcp.databricks.com` host.
- [ ] **Step 2:** Find the Gemini endpoints: `databricks serving-endpoints list --profile "$DBX_PROFILE" -o json | jq -r '.[].name' | grep -i gemini`. Record the names in `.env.local` and `config/versions.env`.
- [ ] **Step 3:** In the Unity AI Gateway UI or API, enable **usage tracking** and **inference tables** for those endpoints, plus a rate limit, so they can be shown on stage. Screenshot the settings to `talk/fallbacks/gateway-settings.png`.
- [ ] **Step 4: Write `demos/05-tracing/smoke.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../../.env.local"
databricks serving-endpoints query "$GEMINI_ENDPOINT" --profile "$DBX_PROFILE" \
  --json '{"messages":[{"role":"user","content":"Reply with exactly: pong"}],"max_tokens":10}' \
  | jq -r '.choices[0].message.content'
```

- [ ] **Step 5: Verify:** `bash demos/05-tracing/smoke.sh` → output contains `pong`.
- [ ] **Step 6:** Add a `LESSONS.md` entry and commit (`feat: gemini via unity ai gateway smoke test`).

### Task 4: Omnigent install and base config

**Files:**
- Create: `config/omnigent/config.yaml`, `config/omnigent/server_config.yaml` (routing and policies are added later), `scripts/apply-config.sh`

**Interfaces:**
- Consumes: `DBX_PROFILE` (Task 3)
- Produces: provider name **`dbx`** (kind `databricks`), which every agent YAML references. `scripts/apply-config.sh` installs repo config into `~/.omnigent/`.

- [ ] **Step 1:** Install with no brew: `uv tool install "omnigent[databricks,antigravity]"` (or the curl installer in facts.md). Record `omni --version` in `config/versions.env` as `OMNIGENT_VERSION=`.
- [ ] **Step 2:** Run `omni setup` interactively. Choose **Databricks — workspace** with `$DBX_PROFILE`. Then diff the generated `~/.omnigent/config.yaml` against the facts.md key names.
- [ ] **Step 3: Write `config/omnigent/config.yaml`** by templating the generated file. Key names must match what `omni setup` produced. Expected shape:

```yaml
providers:
  dbx:
    kind: databricks
    profile: ${DBX_PROFILE}
    default: true
```

If env interpolation isn't supported for `profile`, `apply-config.sh` renders the file with `envsubst`.
- [ ] **Step 4: Write `scripts/apply-config.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .env.local
ts=$(date +%Y%m%d-%H%M%S)
[ -d ~/.omnigent ] && tar czf "$HOME/.omnigent.backup-$ts.tgz" -C "$HOME" .omnigent
mkdir -p ~/.omnigent
for f in config.yaml server_config.yaml; do
  envsubst < "config/omnigent/$f" > "$HOME/.omnigent/$f"
done
mkdir -p ~/.omnigent/agents && cp config/omnigent/agents/*.yaml ~/.omnigent/agents/ 2>/dev/null || true
echo "applied; backup at ~/.omnigent.backup-$ts.tgz"
```

Before writing to `~/.omnigent`, check `~/.agents/AGENT-ENVIRONMENT.md`. If `~/.omnigent` (or part of it) is a symlink to a canonical location, write there instead.
- [ ] **Step 5: Verify:** `bash scripts/apply-config.sh && omni diagnose` shows provider `dbx` healthy with no secrets printed. Save the output (redacted) to `talk/fallbacks/omni-diagnose.txt`.
- [ ] **Step 6:** Commit (`feat: omnigent base config with databricks provider`).

### Task 5: Harness engineering — one agent, four harnesses

**Files:**
- Create: `config/omnigent/agents/talk-coder.yaml`, `demos/01-harness-switch/run.sh`, `demos/01-harness-switch/task.md`

**Interfaces:**
- Consumes: provider `dbx`
- Produces: agent `talk-coder`, and harness IDs `claude-code`, `codex`, `pi`, `antigravity` (exact IDs from facts.md).

- [ ] **Step 1: Write `talk-coder.yaml`.** Confirm the field names against facts.md and AGENT_YAML_SPEC.md.

```yaml
name: talk-coder
prompt: |
  You are a careful coding assistant working in the omnigent-talk repo.
  Keep changes minimal and explain them in one paragraph.
executor:
  harness: claude-code
  model: databricks-claude-sonnet-4-6   # replace with exact id from facts.md
  auth:
    type: databricks
    profile: ${DBX_PROFILE}
```

- [ ] **Step 2: Write `demos/01-harness-switch/task.md`**, a tiny deterministic task that can be run on stage: *"Add a `--json` flag to `scripts/preflight.sh` that prints results as JSON."* (Pick a task that exists once Task 13 is done, or a toy file under `demos/01-harness-switch/sandbox/`.)
- [ ] **Step 3: Write `run.sh`** to run the same agent and task across harnesses. Use the documented CLI override flag from facts.md:

```bash
#!/usr/bin/env bash
set -euo pipefail
harness=${1:?usage: run.sh <claude-code|codex|pi|antigravity>}
omni run talk-coder --harness "$harness" --prompt-file "$(dirname "$0")/task.md"
```

- [ ] **Step 4: Verify:** run each of the four harnesses. Each completes the task, and the session is visible in the web UI. Record per-harness wall time and model in `CHECKPOINTS.md`.
- [ ] **Step 5:** Note per-harness differences (skills support, native TUI vs direct, auth quirks) in `LESSONS.md`. This becomes the "harness engineering" slide content.
- [ ] **Step 6:** Commit (`feat: single agent spec across four harnesses`).

### Task 6: Antigravity with native agy credentials via Databricks Gemini

**Files:**
- Create: `config/omnigent/agents/talk-coder.antigravity.yaml`, `demos/02-antigravity/README.md`

**Interfaces:**
- Consumes: `GEMINI_ENDPOINT`, provider `dbx`
- Produces: a working `antigravity` harness whose model calls go through Unity AI Gateway (visible in Task 9 usage).

- [ ] **Step 1:** Install `agy` per facts.md, with no brew (use the official installer or npm). Record the version in `config/versions.env` as `AGY_VERSION=` and confirm it is ≥1.1.7 if Keychain creds are used.
- [ ] **Step 2:** Configure native agy credentials following #configure-native-agy-credentials exactly. Path A: `omni setup` → Antigravity → *Configure native agy API key / gateway* → Databricks profile, which should register a `databricks-gemini-<profile>` provider with `native_gemini: true`. Path B (fallback): agy's own OAuth login.
- [ ] **Step 3:** Confirm that the gateway route used is the **native Gemini API**, not OpenAI-compatible. If the Databricks gateway doesn't expose it for Argon, record that in LESSONS and use the closest supported route. Do not fake it on stage.
- [ ] **Step 4: Write `talk-coder.antigravity.yaml`**

```yaml
name: talk-coder-agy
extends: talk-coder          # if extends unsupported, duplicate prompt from talk-coder.yaml
executor:
  harness: antigravity
  model: ${GEMINI_ENDPOINT}
```

- [ ] **Step 5: Write `demos/02-antigravity/README.md`**, the on-stage walkthrough: (1) where creds live (Keychain, `~/.gemini/...`, never shown on screen), (2) the `omni setup` screens, (3) the generated provider block (redacted), (4) running `demos/01-harness-switch/run.sh antigravity`, (5) the matching row in `system.ai_gateway.usage`.
- [ ] **Step 6: Verify:** `bash demos/01-harness-switch/run.sh antigravity` succeeds. Within about 15 minutes, a usage row for `$GEMINI_ENDPOINT` with an agent/invocation-source column appears (Task 9 query).
- [ ] **Step 7:** Record the screen flow (`talk/fallbacks/antigravity-setup.mov`, gitignored if large) and commit (`feat: antigravity harness on databricks gemini`).

### Task 7: Smart routing

**Files:**
- Modify: `config/omnigent/server_config.yaml`
- Create: `demos/03-routing/prompts.md`, `demos/03-routing/test_routing.sh`

**Interfaces:**
- Consumes: provider `dbx`, both Gemini endpoints, harness IDs from Task 5
- Produces: `routing`/`llm` config, plus three scripted prompts each with an expected `(harness, model)` pair.

- [ ] **Step 1:** Add routing config using the exact keys from facts.md. Expected shape (built-in judge on Databricks Gemini Flash):

```yaml
llm:
  model: ${GEMINI_FLASH_ENDPOINT}
  profile: ${DBX_PROFILE}
  fallback_models: [${GEMINI_ENDPOINT}]
```

If the Databricks gateway offers an external router (`routing: provider: external`), evaluate it as option B and pick one in `LESSONS.md`.
- [ ] **Step 2: Write `prompts.md`** with three prompts that have an obvious winner each:
  1. "Rename this variable across the repo" → cheap, fast model.
  2. "Design a migration plan for this 40-file refactor" → strongest reasoning model.
  3. "Use Gemini-native tools to …" / multimodal (screenshot-to-code) → Antigravity + Gemini Argon.
  Write the expected `(harness, model)` next to each.
- [ ] **Step 3: Write `test_routing.sh`.** It runs each prompt in Auto mode with a dry-run/explain flag if one exists (check facts.md), extracts the chosen harness and model from session info (`omni` CLI or `sys_session_get_info`), and diffs against expected. It exits 1 on any mismatch.
- [ ] **Step 4: Verify:** `bash demos/03-routing/test_routing.sh` exits 0 on three consecutive runs. Routers are nondeterministic, so if it flaps, tighten the prompts rather than the test.
- [ ] **Step 5:** Commit (`feat: smart routing config and deterministic demo prompts`).

### Task 8: Contextual policies (including a custom data-residency policy)

**Files:**
- Create: `policies/pyproject.toml`, `policies/talk_policies/__init__.py`, `policies/talk_policies/residency.py`, `policies/tests/test_residency.py`, `demos/04-policies/run.sh`
- Modify: `config/omnigent/server_config.yaml`

**Interfaces:**
- Produces: `talk_policies.residency.decide(model: str, cwd: str, sensitive_globs: list[str], allowed_prefixes: list[str]) -> Decision`, where `Decision` is a dataclass `(allow: bool, reason: str)`. Also `talk_policies.residency.data_residency_policy(**factory_params)`, the Omnigent factory adapter. Its exact callable signature is copied from the builtins in the installed `omnigent/policies/builtins/` package.

- [ ] **Step 1: Write `policies/pyproject.toml`**

```toml
[project]
name = "talk-policies"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
pythonpath = ["."]
```

- [ ] **Step 2: Write the failing tests** `policies/tests/test_residency.py`

```python
from talk_policies.residency import Decision, decide

GLOBS = ["*/customer-data/*", "*/pii/*"]
PREFIXES = ["databricks-"]

def test_sensitive_path_blocks_non_databricks_model():
    d = decide("gpt-5.5", "/work/customer-data/etl", GLOBS, PREFIXES)
    assert d == Decision(False, "model gpt-5.5 not allowed for sensitive path /work/customer-data/etl")

def test_sensitive_path_allows_databricks_hosted_model():
    assert decide("databricks-gemini-4-argon", "/work/pii/x", GLOBS, PREFIXES).allow

def test_non_sensitive_path_allows_anything():
    assert decide("gpt-5.5", "/work/omnigent-talk", GLOBS, PREFIXES).allow

def test_empty_model_is_denied_on_sensitive_path():
    assert not decide("", "/work/pii/x", GLOBS, PREFIXES).allow

def test_trailing_slash_and_case_do_not_bypass():
    assert not decide("GPT-5.5", "/work/PII/x/", GLOBS, PREFIXES).allow
```

- [ ] **Step 3: Verify they fail:** `cd policies && uv run pytest -q` → FAIL with `ModuleNotFoundError: talk_policies.residency`.
- [ ] **Step 4: Write `talk_policies/residency.py`** (pure core)

```python
from dataclasses import dataclass
from fnmatch import fnmatch


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str


def decide(model: str, cwd: str, sensitive_globs: list[str], allowed_prefixes: list[str]) -> Decision:
    path = cwd.lower().rstrip("/") + "/"
    if not any(fnmatch(path, g.lower()) for g in sensitive_globs):
        return Decision(True, "non-sensitive path")
    if model and any(model.lower().startswith(p.lower()) for p in allowed_prefixes):
        return Decision(True, f"model {model} is governed by Unity AI Gateway")
    return Decision(False, f"model {model} not allowed for sensitive path {cwd}")
```

and an empty `talk_policies/__init__.py`.
- [ ] **Step 5: Verify:** `cd policies && uv run pytest -q` → `5 passed`.
- [ ] **Step 6: Add the Omnigent adapter.** Read the installed builtin `cost_budget` (`python -c "import omnigent.policies.builtins.cost as m; print(m.__file__)"`) and copy its factory → handler shape exactly. Add `data_residency_policy(sensitive_globs, allowed_prefixes)` to `residency.py`. It returns a handler that pulls the model and cwd off the policy event, calls `decide`, and returns deny/allow in Omnigent's result type. Add one adapter test that constructs a real `PolicyEvent` (as builtin tests do) for the deny case.
- [ ] **Step 7: Wire it into `server_config.yaml`** alongside the builtins:

```yaml
policy_modules:
  - talk_policies
policies:
  session_budget:
    type: function
    handler: omnigent.policies.builtins.cost.cost_budget
    factory_params: {max_cost_usd: 5.00, ask_thresholds_usd: [2.00]}
  data_residency:
    type: function
    handler: talk_policies.residency.data_residency_policy
    factory_params:
      sensitive_globs: ["*/customer-data/*", "*/pii/*"]
      allowed_prefixes: ["databricks-"]
```

Make `talk_policies` importable by the Omnigent server: `uv pip install -e policies` into the omni tool env, or follow the policy_modules path documented in facts.md.
- [ ] **Step 8: Write `demos/04-policies/run.sh`.** It creates `/tmp/talk/customer-data/` and runs `talk-coder` there twice: with a non-Databricks model (expected: denied, with the reason shown) and with `$GEMINI_ENDPOINT` (expected: allowed).
- [ ] **Step 9: Verify:** `bash scripts/check.sh` passes (it runs the pytest suite). `bash demos/04-policies/run.sh` shows one deny and one allow.
- [ ] **Step 10:** Commit (`feat: data-residency policy keeping sensitive paths on databricks-governed models`).

### Task 9: Tracing and usage via Unity AI Gateway

**Files:**
- Create: `demos/05-tracing/usage.sql`, `demos/05-tracing/traces.md`

**Interfaces:**
- Consumes: Tasks 5–8 traffic, `WAREHOUSE_ID`
- Produces: three saved queries used on stage (optionally a small AI/BI dashboard).

- [ ] **Step 1:** Load `databricks-unity-catalog` and `databricks-dbsql`. Run `DESCRIBE system.ai_gateway.usage` and write the real column names into facts.md.
- [ ] **Step 2: Write `usage.sql`** with three queries. Adjust column names to Step 1's output:

```sql
-- Q1: calls per harness/agent and model, last 24h
SELECT invocation_source, model_name, count(*) AS calls, sum(tokens_total) AS tokens
FROM system.ai_gateway.usage
WHERE event_time > now() - INTERVAL 24 HOURS
GROUP BY ALL ORDER BY calls DESC;

-- Q2: one coding-agent session end to end
SELECT event_time, invocation_source, model_name, tokens_total, latency_ms
FROM system.ai_gateway.usage
WHERE session_id = :session_id ORDER BY event_time;

-- Q3: Gemini share of traffic
SELECT model_name LIKE '%gemini%' AS is_gemini, count(*) FROM system.ai_gateway.usage
WHERE event_time > now() - INTERVAL 24 HOURS GROUP BY ALL;
```

- [ ] **Step 3:** Optionally, build a 3-tile AI/BI dashboard with the `databricks-aibi-dashboards` skill (test every query first, per that skill).
- [ ] **Step 4: Write `traces.md`.** Explain how to open the MLflow/gateway trace for a session, which shows model calls plus tool and skill spans. Take screenshots into `talk/fallbacks/`.
- [ ] **Step 5: Verify:** each query returns ≥1 row from today's Task 5–8 runs, including at least one antigravity/Gemini row.
- [ ] **Step 6:** Commit (`feat: unity ai gateway usage and trace queries`).

### Task 10: Skills on Databricks

**Files:**
- Create: `demos/06-skills/README.md`, plus one small demo skill (location decided in Step 1)

**Interfaces:**
- Produces: one skill loaded by at least two harnesses through Omnigent, and visible as a span or usage record on Databricks.

- [ ] **Step 1:** Read `~/.agents/AGENT-ENVIRONMENT.md` to find the canonical skills location. Decide whether the demo skill lives there (shared) or under `demos/06-skills/skills/` (repo-local, loaded by Omnigent). Prefer repo-local so the repo stays reproducible for attendees.
- [ ] **Step 2:** Write a tiny skill, `gcp-databricks-facts`. It answers "how do I call Gemini on Databricks" using `docs/research/facts.md`.
- [ ] **Step 3:** Run it from `claude-code` and `antigravity` via Omnigent (the `load_skill` path). Confirm the skill load shows up in the Databricks trace or usage (Task 9 Q2). If skill spans aren't captured on Databricks, say so honestly in LESSONS and show the Omnigent-side record instead.
- [ ] **Step 4:** Write the README with the demo steps and expected output. Commit (`feat: shared skill demo across harnesses`).

### Task 11: Agent memory on Lakebase

**Files:**
- Create: `demos/07-memory/pyproject.toml`, `demos/07-memory/memory_demo.py`, `demos/07-memory/README.md`

**Interfaces:**
- Consumes: `LAKEBASE_INSTANCE`, `EMBEDDING_ENDPOINT`, `GEMINI_ENDPOINT`, `DBX_PROFILE`
- Produces: `memory_demo.py remember "<fact>" --user <id>` and `memory_demo.py recall "<question>" --user <id>`, run in separate processes to prove persistence.

- [ ] **Step 1:** Load the `databricks-lakebase` and `databricks-agent-bricks` skills. Using Task 2's GCP availability finding, create or choose a Lakebase instance (the presenter approves cost) and set `LAKEBASE_INSTANCE`.
- [ ] **Step 2:** Confirm the API names on the stateful-agents page. The expected shape is `databricks_langchain.CheckpointSaver(instance_name=...)` for short-term memory and `databricks_langchain.DatabricksStore(instance_name=..., embedding_endpoint=..., embedding_dims=...)` for long-term memory. Write the confirmed signatures into facts.md.
- [ ] **Step 3: Write `pyproject.toml`** with dependencies `databricks-langchain[memory]`, `langgraph`, `databricks-sdk`.
- [ ] **Step 4: Write `memory_demo.py`.** Long-term memory only, kept small enough for a slide:

```python
import argparse, hashlib, os
from databricks_langchain import DatabricksStore

def store() -> DatabricksStore:
    s = DatabricksStore(
        instance_name=os.environ["LAKEBASE_INSTANCE"],
        embedding_endpoint=os.environ["EMBEDDING_ENDPOINT"],
        embedding_dims=1024,  # match the embedding endpoint; confirm in facts.md
    )
    s.setup()
    return s

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["remember", "recall"])
    p.add_argument("text")
    p.add_argument("--user", required=True)
    a = p.parse_args()
    ns = ("users", a.user, "memories")
    s = store()
    if a.cmd == "remember":
        s.put(ns, hashlib.sha256(a.text.encode()).hexdigest()[:16], {"text": a.text})
        print("stored")
    else:
        for item in s.search(ns, query=a.text, limit=3):
            print(item.value["text"])

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Verify:** `uv run memory_demo.py remember "My talk is at the Google dev conference and I prefer Gemini" --user chris`, then a **new process**: `uv run memory_demo.py recall "which model do I prefer?" --user chris` prints the stored fact. Running `recall` with `--user someone-else` prints nothing (scoping).
- [ ] **Step 6:** In the README, show how an Omnigent agent uses this as an MCP tool or skill, so memory follows the user across harnesses. If wiring it as a tool is out of time-scope, show it as a separate demo and note that in LESSONS.
- [ ] **Step 7:** Commit (`feat: lakebase-backed agent memory demo`).

### Task 12: Serverless sandbox

**Files:**
- Create: `demos/08-sandbox/sandbox_demo.py`, `demos/08-sandbox/README.md`

**Interfaces:**
- Consumes: `DBX_PROFILE`
- Produces: `sandbox_demo.py "<python code>"`, which runs model-generated code in the Databricks serverless sandbox and prints stdout. Plus one "agent writes code → sandbox runs it" flow.

- [ ] **Step 1:** From the sandbox doc (Task 2), record in facts.md: the API or SDK entry point, the GCP availability and preview status, the network and filesystem isolation guarantees, and the time and size limits.
- [ ] **Step 2:** Implement `sandbox_demo.py` using the documented SDK call. It takes code from argv, creates or reuses a sandbox, executes the code, prints stdout and exit status, and tears down. Keep it under 40 lines.
- [ ] **Step 3: Verify the happy path:** `uv run sandbox_demo.py "print(sum(range(10)))"` → `45`.
- [ ] **Step 4: Verify isolation** (the on-stage "why it matters" beat): `uv run sandbox_demo.py "import os; print(os.listdir(os.path.expanduser('~')))"` shows the sandbox home, not the laptop's. A network call to a blocked host fails, if egress is restricted per the docs.
- [ ] **Step 5:** Connect it to an agent. Have `talk-coder-agy` write a data-analysis snippet, then execute it via `sandbox_demo.py`, either as a tool or by hand for the demo. Document this in the README.
- [ ] **Step 6:** Commit (`feat: serverless sandbox demo for agent-generated code`).

### Task 13: Collaboration, mobile, and preflight

**Files:**
- Create: `demos/09-collab-mobile/README.md`, `scripts/preflight.sh`

**Interfaces:**
- Consumes: everything above
- Produces: `scripts/preflight.sh`, which exits 0 only when every demo's dependencies are healthy.

- [ ] **Step 1:** Collaboration demo. Start a `talk-coder` session, share its URL, have a second account or browser join, leave an inline comment, and steer the agent. Write the exact steps in the README.
- [ ] **Step 2:** Mobile demo. Install the Omnigent Android app (Google Play, a nice touch for this audience), sign in, open the same live session, and send a steering message from the phone. Plan screen mirroring for the phone (e.g. `scrcpy` via nix or npm, not brew).
- [ ] **Step 3:** Briefly show other non-coding Omnigent features from Task 2 Step 2, e.g. a scheduled task that runs `usage.sql` Q1 every morning and posts a summary, or the async inbox. Pick one and document it.
- [ ] **Step 4: Write `scripts/preflight.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
source .env.local; source config/versions.env
ok=0; check() { if eval "$2" >/dev/null 2>&1; then echo "PASS $1"; else echo "FAIL $1"; ok=1; fi; }
check "omnigent version"   '[ "$(omni --version | grep -oE "[0-9.]+" | head -1)" = "$OMNIGENT_VERSION" ]'
check "omni diagnose"      'omni diagnose'
check "databricks auth"    'databricks current-user me --profile "$DBX_PROFILE"'
check "gemini endpoint"    'bash demos/05-tracing/smoke.sh | grep -q pong'
check "routing"            'bash demos/03-routing/test_routing.sh'
check "policies"           'bash scripts/check.sh'
check "memory"             '(cd demos/07-memory && uv run memory_demo.py recall "model" --user chris | grep -qi gemini)'
check "sandbox"            '(cd demos/08-sandbox && uv run sandbox_demo.py "print(45)" | grep -q 45)'
exit $ok
```

- [ ] **Step 5: Verify:** `bash scripts/preflight.sh` → all PASS. Then break one thing (e.g. a bad `GEMINI_ENDPOINT`) and confirm it prints `FAIL gemini endpoint` and exits 1.
- [ ] **Step 6:** Commit (`feat: collaboration/mobile demo and day-of preflight`).

### Task 14: Talk content, runbook, and dry run

**Files:**
- Create: `talk/outline.md`, `talk/speaker-notes.md`, `talk/runbook.md`, `talk/slides/` (or a link in README)

- [ ] **Step 1:** Confirm the slot length and audience level with the presenter, then rebalance the Talk Narrative timings into `talk/outline.md`.
- [ ] **Step 2:** Write `speaker-notes.md` per segment: the key line, the demo command, the Databricks "why it matters" beat (governance, one audit trail, managed Postgres memory, isolated compute, runs on GCP), and the source URL from facts.md.
- [ ] **Step 3:** Build the slides with the `fe-google-tools:google-slides` or `databricks-slides:slide-deck` skill. Include a "receipts" slide built from `LESSONS.md` (talk-worthy = y) and git history: which harness or model wrote which part of this repo.
- [ ] **Step 4: Write `runbook.md`.** Per demo: the pre-opened terminal or tab, the exact keystrokes, the expected output, the fallback clip, and a "switch to fallback if no output in N seconds" rule. Screen hygiene: hide `~/.databrickscfg`, clear shell history, use a demo-only browser profile, turn on notifications DND, and make the workspace URL safe to show.
- [ ] **Step 5:** Record a fallback for every demo into `talk/fallbacks/`.
- [ ] **Step 6: Full dry run** with a timer. Run preflight, then the whole talk. Log overruns and failures in `LESSONS.md` and fix them. Repeat until it runs clean twice.
- [ ] **Step 7:** Final `CHECKPOINTS.md` entry and commit (`docs: talk outline, notes, runbook`).

---

## Open Questions for the Presenter

1. Which Databricks **GCP** profile or workspace will host the demo? (Of the profiles seen, `fevm-cjc` or a new FEVM GCP workspace seem likely. Your call.)
2. Talk slot length, and the audience mix (app devs vs ML/data folks)?
3. If agent memory or serverless sandbox isn't available on GCP yet, is a separate AWS workspace OK for that segment (stated openly), or should it be cut?
4. Should the attendee-facing repo be public on GitHub at talk time? This affects how much workspace detail stays in tracked files.
5. Do you have an Android device for the mobile demo, and a second account for the collaboration demo?
