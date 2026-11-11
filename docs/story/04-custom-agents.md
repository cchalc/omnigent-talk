# 04: Custom agents, the `rory` router

Tag: workspace

## Goal

Build and register `rory`, a router agent. Rory sends code review and deploys to a Codex worker,
and SQL and simple one-shot tasks to a Qwen worker. Then run the four demo prompts in order and
check the deploy gate. Steps 1, 2 and 4 need no workspace. Step 3 and the prompts do.

The bundle is in agents/rory. The design is in
omnigent-agents.md, and the recorded runs are in
talk/prompts.md.

## Steps

### 1. Read the bundle

| Path | What it is |
| :---- | :---- |
| `agents/rory/config.yaml` | The router. `claude-sdk` harness, the routing prompt, guardrails, `tools.agents` |
| `agents/rory/agents/codex/config.yaml` | Codex worker. `codex` harness, headless, a shell in the repo |
| `agents/rory/agents/qwen/config.yaml` | Qwen worker. `openai-agents` harness, no tools, model `${CATALOG}.${SCHEMA}.qwen_code` |
| `agents/rory/skills/review/SKILL.md` | How rory briefs codex for a review |
| `agents/rory/skills/deploy/SKILL.md` | The two-phase deploy gate |

Spec fields the bundle uses:

- `executor.type: omnigent`, with the harness under `executor.config.harness`
  (`agents/rory/config.yaml:12-15`). The bundle tests read that path
  (`tests/test_agent_bundles.py:23`). The facts sheet writes `executor.harness` and leaves the
  parser question OPEN (facts.md, "Agent YAML"). Follow the bundle.
- `prompt`: the routing rules, dispatch rules and deploy rules.
- `tools.agents`: `codex` and `qwen` (`agents/rory/config.yaml:91-94`). Each name needs a worker
  config with the same `name` (`tests/test_agent_bundles.py:26-29`).
- `guardrails.policies`: `approval_relay` and `spawn_bounds`. See step 4.
- `async: true` and `cancellable: true` (`agents/rory/config.yaml:63-64`).

### 2. Render the bundle (offline-safe)

```bash
just agent-render rory
```

The recipe runs `omnigent-talk render-agent`, which fills three placeholders and nothing else:
`CATALOG`, `SCHEMA` and `DBX_PROFILE` (`src/omnigent_talk/agent_bundle.py:16`). `just` loads the
values from `.env.local`. A missing value stops the render with a `KeyError`
(`src/omnigent_talk/agent_bundle.py:33-34`). The render makes no network call.

It writes to `.omnigent/rory/`, which is gitignored (`.gitignore:233`). Each run deletes that
directory and copies the bundle again (`src/omnigent_talk/agent_bundle.py:52-53`). Only `.yaml`,
`.yml` and `.md` files are rendered; other files are copied as they are
(`src/omnigent_talk/agent_bundle.py:61-68`).

The render is needed because `omnigent agent add` expands `${VAR}` only in connection, API-key
auth and MCP fields. It does not expand `executor.model` or `auth.profile`
(`src/omnigent_talk/agent_bundle.py:1-6`; facts.md, "Bundle env expansion is partial").

Check that no placeholder survives. This lists file names only, so no rendered values print:

```bash
grep -rl '\${CATALOG}\|\${SCHEMA}\|\${DBX_PROFILE}' .omnigent/rory || echo "no placeholders left"
```

### 3. Register the agent (changes the workspace; confirm first)

```bash
just agent-add rory
just agents
```

`just agent-add` renders the bundle, then runs `omnigent agent add .omnigent/rory` against
`$OMNI_SERVER`. Re-adding replaces the agent on the server
(omnigent-agents.md, "Making your own agent appear").
Confirm the target server with the presenter before you run it.

After upload, rory shows in `just agents` (user scope). It does not show in the builtins section
of `sys_agent_list`. Launch it by agent id (omnigent-agents.md,
and the 2026-11-03 entry in setup-log is the source for the id-launch note).

### 4. Guardrails

The router has two policies (`agents/rory/config.yaml:66-89`). The bundle test pins their shape
(`tests/test_agent_bundles.py:48-56`).

- **`approval_relay`** is the intended deploy gate. A CEL expression returns `ASK` for any
  `sys_session_send` whose arguments contain `APPROVED`, and `ALLOW` for everything else
  (`agents/rory/config.yaml:72-82`). The ASK is for a human, so a slip by the model cannot relay an
  approval on its own. No run in this repo shows it firing, and the test only checks the policy text, so treat it as
  unproven until you see an ASK. See chapter 06.
- **`spawn_bounds`** caps dispatches at 3 per turn, counting `sys_session_send` and
  `sys_session_create` (`agents/rory/config.yaml:83-89`).

The codex worker also has `blast_radius` with `gate_pushes: false`
(`agents/rory/agents/codex/config.yaml:20-27`). The codex config notes that a headless worker
cannot answer an ASK, so pushes are not gated there.

### 5. The two-phase deploy gate

The gate lives in rory's prompt, in the `deploy` skill, and in the codex prompt. It runs in three
steps.

1. **Plan.** Rory sends codex `PLAN:`. Codex runs `just gateway-validate` and `just gateway-plan`,
   reports every create, update and delete, and stops
   (`agents/rory/agents/codex/config.yaml:42-44`; `agents/rory/skills/deploy/SKILL.md:11-13`).
2. **Approval in this conversation.** Rory shows the target (the profile name in `DBX_PROFILE`),
   the changes and the blast radius. It asks one direct question. It sends the approval only after
   a clear yes from the user in this conversation (`agents/rory/config.yaml:50-57`;
   `agents/rory/skills/deploy/SKILL.md:13-18`).
3. **Deploy.** Rory sends codex `DEPLOY APPROVED` with the same title. Codex runs
   `just gateway-deploy`, then `just gateway-show <service>` for each changed service
   (`agents/rory/agents/codex/config.yaml:46-47`).

**Why there is no `--auto-approve`.** The workers are headless, so neither of them can answer a
confirmation prompt. The CLI asks for one when a change deletes or recreates a resource. If codex
passed `--auto-approve`, that prompt would be answered with no person in the loop. The codex
prompt therefore says never to add the flag. It tells codex to abort and leave the deploy to the
presenter (`agents/rory/agents/codex/config.yaml:47-50`; `agents/rory/skills/deploy/SKILL.md:22-24`).
The bundle test checks for that sentence (`tests/test_agent_bundles.py:65-66`).

**Destroy is not in the agent.** Codex never runs `just gateway-destroy`. Rory replies that the
presenter runs it, and says what it deletes
(`agents/rory/agents/codex/config.yaml:52-54`; `agents/rory/skills/deploy/SKILL.md:26-27`;
`tests/test_agent_bundles.py:67-68`).

The gate exists because of a review finding. Codex found that a headless deploy cannot answer the
CLI's confirmation prompt. Claude found that the approval rule existed only in the prompt. The
`approval_relay` policy and the destroy rule are the fixes (talk/prompts.md,
2026-11-03 talk point).

### 6. Run the recorded prompts, in order

Paste the four prompts from the "Demo prompts for `rory`" table in
talk/prompts.md. Each reply starts with a route line such as
`route: sql -> qwen`.

| # | Prompt | Expected | Recorded outcome |
| :-- | :---- | :---- | :---- |
| 1 | Top 5 customers by revenue, SQL | `route: sql -> qwen` | 2026-11-03: that route, one `GROUP BY` query with its assumed columns |
| 2 | LEFT JOIN vs FULL OUTER JOIN | qwen | Not yet recorded |
| 3 | Review the branch against its base, real bugs only | `route: review -> codex` | 2026-11-03: three findings, all fixed on the branch |
| 4 | Deploy the gateway bundle | Stops at the plan step | 2026-11-03: validation passed, but `just gateway-plan` was missing on the base branch. Codex deployed nothing |

Prompt 4 is expected to stop early. The worker runs on the session's base branch, which did not
yet have the plan recipe. Run it again after the branch merges to reach the approval question.

The qwen worker takes the SQL: it calls the `qwen_code` model service directly
(`agents/rory/agents/qwen/config.yaml:9-18`) and does not pass through the `gemini_router` split.
Rory itself does the planning and organizing. To confirm which model answered, read
`destination_model` with `just usage-sql`; the query needs account and metastore admin by default
(`demos/routing/usage.sql:3`).

## Verify

Offline. Checks the bundle wiring, the gate text and the renderer without a workspace:

```bash
uv run pytest tests/test_agent_bundles.py
```

Workspace. Rory is listed as a user agent:

```bash
just agents
```

Then send prompt 1 and confirm the first line of the reply is `route: sql -> qwen`.

## Fallback

- **Render fails with `KeyError`.** A placeholder is unset. Fill the name in `.env.local`. Names
  are in `.env.example`. Do not hardcode a value in the bundle.
- **`just agent-add` fails or is not confirmed.** Do not retry in a loop. Run `just agents` to see
  what is on the server. The recorded outputs in talk/prompts.md stand in
  for the live run.
- **Prompt 4 stops at the plan step.** That is the recorded result. Run it again after the merge.
- **The deploy stops on a confirmation prompt.** Codex has aborted, as designed. Tell the presenter
  to run `just gateway-deploy` themselves. Never send an approval phrase the user did not give.
- **Rory does not show a `route:` line.** The line is rory's rule (`agents/rory/config.yaml:38-39`),
  and the worker prompts do not ask for it. Check that the reply came from rory, and send the
  prompt again if it did not.
