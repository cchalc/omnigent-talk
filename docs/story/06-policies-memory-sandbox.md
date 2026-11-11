# 06: Policies, agent memory, Sandbox, and behavior evaluation

Tag: workspace

## Goal

Exercise four opt-in pieces. Each is Beta, or needs a workspace preview, or spends tokens:

1. Omnigent policies: what the managed server allows, and rory's guardrails as the worked example.
2. Agent memory: store a fact, recall it as the same user, and check that another user recalls nothing.
3. Databricks Sandbox: run one command in a throwaway sandbox, and show it has its own identity.
4. Behavior evaluation: register judges and run synthetic trajectories through them.

None of these run in `just check`. The table in Verify says which have a run record in
this repo. Most have none. The offline tests cover the wiring only.

## Steps

### Policies

**What the managed server allows.** Built-in and CEL policies only. "Custom Python policies are not
supported" (facts.md, "Managed Omnigent policy limit"). The built-ins
include `cost_budget`, `blast_radius`, `max_tool_calls_per_session`, `cel_policy`, and others
(facts.md, "Built-in policies"). The ecosystem map has the same limit
(omnigent-ecosystem.md, "Policies").

**The worked example is rory.** The router's two guardrails are in
agents/rory/config.yaml:66-89:

- `approval_relay`: a CEL expression that returns `ASK` before any `sys_session_send` whose
  arguments contain `APPROVED`. Otherwise it returns `ALLOW`. Chapter 04
  covers the deploy gate around it.
- `spawn_bounds`: at most 3 dispatches per turn, on `sys_session_send` and `sys_session_create`.

The codex worker adds `blast_radius` with `gate_pushes: false`
(agents/rory/agents/codex/config.yaml:20-27).
`blast_radius` matches only kubectl, helm, terraform and databricks commands
(omnigent-agents.md, citing
`omnigent/policies/builtins/orchestration.py:74-77`). It does not match `just gateway-deploy`.
That is why rory's deploy gate is in the prompt and in `approval_relay`.

**Field shape: the sources disagree.** Rory writes each policy as
`function: {path, arguments}` (`agents/rory/config.yaml:72-82`). The bundle test asserts that shape
(`tests/test_agent_bundles.py:50-54`). The ecosystem map also writes `function: <dotted path>`
(omnigent-ecosystem.md, "Policies"). The facts sheet's CEL row
writes `handler` and `factory_params` instead (facts.md, "CEL policy"). The
facts row says it was verified from source, but the repo's own bundle does not use it. The repo
checks only its own file. Nothing here shows which shape the server accepts. Check before you copy
either form into a new bundle.

**Module paths also differ.** Rory's `spawn_bounds` and the codex `blast_radius` resolve through
`omnigent.inner.nessie.policies.*` (`agents/rory/config.yaml:86`;
`agents/rory/agents/codex/config.yaml:26`). The facts sheet lists `blast_radius` under
`policies/builtins/`, and the ecosystem map lists `spawn_bounds` there too. The `nessie` path is not
checked in this repo.

**The fixture skill.** `.claude/skills/do-something-bad/SKILL.md` is a test fixture. Its name is
suspicious, but it only echoes a fixed string:

```bash
echo "I am the Omnigent!"
```

The skill's own description says it is for testing policies against a suspicious-sounding skill name
(`.claude/skills/do-something-bad/SKILL.md:2-11`). No policy in this repo targets it, and no run record exists.
Treat it as a fixture waiting for a policy.

### Agent memory

Memory is a managed store with Lakebase underneath. Creating a store provisions that storage, and
you pay for it (demos/model-services/README.md:76). Confirm the target workspace before you create
one.

```bash
just install-memory
just memory-create
just remember "prefers Gemini" presenter
just recall "which model?" presenter
just recall "which model?" someone-else
```

- `install-memory` adds the `memory` extra (`justfile:29-30`). The memory recipes also run with
  `uv run --extra memory`, so this step is optional.
- `memory-create` finds the store by display name, or creates it (`src/omnigent_talk/cli.py:89-91`;
  `src/omnigent_talk/memory.py:43-60`). It needs `DBX_PROFILE` and `MEMORY_STORE` in `.env.local`.
- `remember` writes to a path derived from a hash of the text. Remembering the same fact twice
  overwrites it (`src/omnigent_talk/memory.py:20-28`; `tests/test_memory.py:19-23`).
- `recall` searches only the actor you name. A recall for another actor prints
  `(nothing recalled for <user>)` (`src/omnigent_talk/cli.py:95-96`;
  `tests/test_memory.py:26-30`).
- The real search is hybrid BM25 plus semantic, so the query wording matters
  (facts.md, "Managed memory API (Beta)"). Repeat the exact fact text if a
  recall comes back empty for the same user.

**`actor_id` is not access control.** It scopes recall. It does not isolate anyone. Use one store
per trust boundary (src/omnigent_talk/memory.py:1-5; the same
statement is in facts.md, "Managed memory API (Beta)").

### Sandbox

```bash
just sandbox-run "python3 -c 'print(sum(range(10)))'"
just sandbox-isolation
```

- `sandbox-run` creates a sandbox with a random ID, runs the command under `bash`, and deletes the
  sandbox. The delete runs even if the command fails (`src/omnigent_talk/sandbox.py:29-51`). The
  command timeout defaults to 60 seconds (`src/omnigent_talk/cli.py:222`).
- `sandbox-isolation` runs `whoami`, prints `$HOME`, and lists the home directory
  (`justfile:162-163`).

Facts that bound what you can say (facts.md, "Databricks Sandbox (Beta)"):

- **AWS only.** The GCP docs page returns 404 (facts.md, "Sandbox on GCP").
  Sandbox hosts are in select AWS regions, and need the Sandbox preview
  (facts.md, "Omnigent workspace prerequisite").
- **Ingress closed. Egress unrestricted.** Do not claim network isolation. Say that the sandbox has
  its own filesystem and identity (demos/model-services/README.md:87;
  `src/omnigent_talk/sandbox.py:1-5`).
- **24-hour cap** on a sandbox.

Expected output, as the demo README gives it (demos/model-services/README.md:83-84):
`45` for the sum, then `home=/home/sandbox-agent`. These are expected values. No run is recorded.

### Behavior evaluation (spends tokens; opt-in)

`behavior-eval-setup` creates datasets and registers judges in the workspace. Confirm the target
before you run it.

```bash
just behavior-eval-setup
just behavior-eval-smoke
just behavior-eval
```

- `behavior-eval-setup` creates or updates the managed datasets for each of the four project
  behaviors, in smoke and full sizes, and registers the judges (`src/omnigent_talk/behavior_eval.py:12-17`,
  `:158-172`; `scripts/behavior_eval.py`).
- `behavior-eval-smoke` runs five redacted synthetic trajectories. `behavior-eval` runs sixty, 15
  per behavior (`justfile:89-95`).
- The judge model comes from `BEHAVIOR_JUDGE_MODEL` (`.env.example`). The experiment comes from
  `BEHAVIOR_EVAL_EXPERIMENT`.
- Both commands create MLflow state and spend judge tokens. They are not part of `just check`
  (AGENTS.md, "Databricks workflow"). Run smoke first. Confirm before the full run.

## Verify

Offline. These check the wiring with fakes and mocks, and need no workspace:

```bash
uv run pytest tests/test_agent_bundles.py tests/test_memory.py tests/test_sandbox.py tests/test_behaviors.py
```

Workspace checks:

```bash
just recall "which model?" someone-else
just sandbox-isolation
```

The first should print `(nothing recalled for someone-else)`. The second should print a home path
and exit 0.

### Run records

| Piece | Run record in this repo? | What exists instead |
| :---- | :---- | :---- |
| `approval_relay` ASK | **No** | The policy and a shape test. setup-log.md records the fix, not an ASK firing |
| `spawn_bounds` | **No** | The policy and a test that asserts `max_dispatches_per_turn <= 3` (`tests/test_agent_bundles.py:56`) |
| `blast_radius` on codex | **No** | Config only |
| `do-something-bad` fixture | **No** | The fixture file |
| Memory: `remember`, `recall` | **No** | The flow in demos/model-services/README.md:69-73, with no output |
| Memory: other user recalls nothing | **No** | The offline test with a fake store (`tests/test_memory.py:26-30`) |
| Sandbox: `sandbox-run`, `sandbox-isolation` | **No** | Expected output in demos/model-services/README.md:83-84 |
| Behavior eval: setup, smoke, run | **No** | The corpus test (`tests/test_behaviors.py`) |

The memory and Sandbox entries in the demo README show expected output. They are not logs of a run.

### Set up and ready to run

"No run record" does not mean "not set up". The environment was built so each of these is one
command or one console step away. None of them has output in this repo yet.

| You could | What is already in place | First command or step |
| :---- | :---- | :---- |
| Start a Sandbox and run code in isolation | `src/omnigent_talk/sandbox.py`, the Sandbox preview enabled on the workspace | `just sandbox-run "python3 -c 'print(sum(range(10)))'"`, then `just sandbox-isolation` |
| Look at AI Gateway usage and traces | The usage table is readable to the presenter, the dashboard is in the bundle, and calls carry tags | `just usage-sql`, `just agent-calls`, `just dashboard-url` |
| Control governance with a budget | The budget body builder, applied by an account admin | `just budget 0.50` |
| Gate what an agent may do | Rory's CEL approval policy and spawn limits, a fixture skill that should trip a policy | chapter 04, then the `do-something-bad` fixture |
| Screen content at the gateway | Unity Gateway sensitive-data detection is a console setting, not repo code | the gateway settings page (plan Task 8) |
| Manage coding agents centrally | A draft managed config in `config/ug/`, not published | `config/ug/README.md` |
| Remember across sessions | The memory store recipes | `just install-memory`, then `just memory-create` |

Each of these changes workspace state or spends credits, except the read-only usage queries.
Confirm the target before you run one.

**Stale OPEN row.** The facts sheet lists the memory import name as OPEN:
`databricks_agentkit` vs the package name (facts.md, "Managed memory API (Beta)").
The repo's code imports `databricks_agentkit` (`src/omnigent_talk/memory.py:51`), and its README
records the SDK version and that import name (demos/model-services/README.md:76).
Those show what the repo uses. The facts sheet has not closed the row, so do not cite it as settled.

## Fallback

- **`Memory store ... not found`.** Run `just memory-create` first
  (`src/omnigent_talk/memory.py:58-59`).
- **Recall returns nothing for the same user.** Repeat the exact fact text. The search is hybrid, so a
  loose query can miss.
- **Sandbox create fails.** Check that the Sandbox preview is on, and that the workspace is in an
  AWS region that supports it (facts.md, "Omnigent workspace prerequisite").
- **Sandbox command runs past 60 seconds.** `just sandbox-run` does not take a timeout. Run
  `uv run omnigent-talk sandbox --timeout <seconds> "<command>"` instead (`src/omnigent_talk/cli.py:221-222`).
- **`behavior-eval-setup` fails.** Do not run `behavior-eval-smoke` or `behavior-eval`. Fix the
  setup first. The run step reads the datasets that setup creates (`src/omnigent_talk/behavior_eval.py:176-188`).
- **A policy does not fire.** No run record shows a policy firing. Fall back to the prompt-level gate
  in chapter 04, and say the policy is not yet
  shown on stage.
