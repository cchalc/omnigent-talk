# Prompt log

Every prompt that drives a demo or a build step goes here verbatim. The talk quotes from this
file, and a presenter can paste from it on stage. Newest session last. Each entry has a date
(UTC), the agent or harness that received it, and what happened.

## 2026-11-03 · Curating Omnigent agents and building `rory`

### Build prompt (Claude Code, through the Omnigent claude-native-ui agent)

> I want to curate all my custom agents that are available in omnigent. Right now I see quite a
> few but I don't understand how they are listed in the workspace. Make sure to track some of
> these prompts so we can include them in the omnigent talk/demo. Log them and make sure to use
> jj, worktrunk, commit and push early and often. Try and work with some subagents as well and
> understand other sessions that are running. There is polly and debby listed as custom built
> in. Let's create something custom to use codex when doing code reviews or deployments but use
> qwen through the gemini router set up in the omnigent-talk schema for more simplistic tasks
> like sql queries.

What happened:
- The agent read `sys_agent_list` and `sys_session_list` to inventory the picker. Results are in
  `docs/omnigent-agents.md`.
- It read the other running sessions without interrupting them, using
  `sys_session_get_history`. A Codex session was setting up jj and Worktrunk guidance in the
  primary worktree, and an Antigravity session was drafting a routing slide. To avoid
  collisions, the work moved to a Worktrunk child worktree (`cchalcraft/custom-agents`).
- It found that `qwen_code` already existed in the bundle but was not yet deployed.
- It asked four questions before planning: the Qwen route, the agent's name and registration,
  whether to clean up stale sessions, and how to integrate the work.

Talk point: the meta-harness can inspect its own fleet. One prompt lists every agent and
session, reads what the other harnesses are doing, and plans around them.

### Demo prompts for `rory`

`rory` sends review and deploy work to a Codex worker, and SQL and simple tasks to a Qwen worker
on the `qwen_code` model service. Paste these into a rory session in order.

| # | Prompt | Expected worker | Outcome |
|---|---|---|---|
| 1 | Write a SQL query for the top 5 customers by total revenue from an orders table. | qwen | 2026-11-03: `route: sql -> qwen`. One `SUM ... GROUP BY ... LIMIT 5` query plus its assumed columns |
| 2 | Explain the difference between a LEFT JOIN and a FULL OUTER JOIN with a small example. | qwen | _pending_ |
| 3 | Review the diff on this branch against its base and list real bugs only. | codex | 2026-11-03: `route: review -> codex`. Three findings, all fixed on the branch: path traversal in `render-agent`, a headless deploy that can't answer the CLI's confirmation, and a destroy path with no plan. The Claude reviewer found the traversal too, plus a prompt-only gate. Both vendors caught the same top bug |
| 4 | Deploy the gateway bundle. | codex, stops at the confirmation gate | 2026-11-03: `route: deploy -> codex`, plan step only. Validation passed, but `just gateway-plan` was missing: the worker runs in the session's cwd, on the base branch, before this branch merged. Codex refused to substitute another command and deployed nothing. Rerun after the merge to reach the approval question |

### Build-session prompts sent to agents

These went from the build session to other agents. They are kept because they show the
meta-harness driving itself.

- To the `qwen-spike` bundle (openai-agents on `qwen_code`, launched with
  `sys_session_create(config_path=...)`): "Write a SQL query for the top 5 customers by total
  revenue from an orders table. Reply with only the SQL." It returned one SQL block. This proved
  the wiring before rory existed.
- To rory (prompt 3, as sent): "Review the branch cchalcraft/custom-agents against its base
  cchalcraft/model-services-demo (use `git diff cchalcraft/model-services-demo...cchalcraft/custom-agents`;
  the branch is checked out in another worktree, so read files with
  `git show cchalcraft/custom-agents:<path>`). Real bugs, leaks and broken recipes only."
  Rory replied `route: review -> codex` and sent codex a `REVIEW:` brief.
- In parallel, a Claude Code reviewer subagent read the same diff, so two vendors reviewed the
  same change. In the session tree, Claude Code's own subagents show up as Omnigent sub-agents
  of the build session.

Talk point: two vendors reviewed the same diff, Codex through rory and Claude through a Claude
Code subagent. They agreed on the worst bug, and each found one the other missed. Codex found
that the headless deploy couldn't answer a confirmation prompt. Claude found that the deploy
gate was enforced only by the prompt. Both are fixed: a CEL `approval_relay` policy now ASKs
before any approval reaches the worker, and destroy belongs to the presenter alone.

## 2026-11-04 · Smart Routing (Beta)

### Build prompt (Claude Code, through the Omnigent claude-native-ui agent)

> I want to work through the smart routing demo https://docs.databricks.com/aws/en/ai-gateway/coding-agent-model-selection#use-smart-routing-in-omnigent

### Stage prompt (`omni-fevm claude --smart-routing`, and again in the UI Smart Routing harness)

```
Use three subagents, one per task, and run them in parallel. Change no files. (1) In README.md, say in one sentence what this repo is for. (2) Explain what `parse_label` in src/omnigent_talk/router.py does and what it returns for an empty answer. (3) Review how gateway.py, router.py and routing.py handle 429s and retries across the whole package, and list the three riskiest gaps. When all three finish, tell me which model each subagent used.
```

Not yet run live (rehearsal pending).

### Preview corpus outcome (`just smart-routing-preview`, 2026-11-04)

| Prompt (from `demos/smart-routing/prompts.txt`) | claude pick | codex pick |
| :---- | :---- | :---- |
| Fix a typo in README.md line 3 | claude-opus-4-8 | gpt-5-6-sol |
| Rename a variable in a named file | claude-opus-4-8 | gpt-5-6-sol |
| Add a unit test in a named file | claude-opus-4-8 | gpt-5-6-sol |
| Why does this TypeError fail (trace) | claude-sonnet-5 | gpt-5-6-sol |
| Flaky pytest run | claude-sonnet-5 | gpt-5-6-sol |
| Cross-file gateway refactor | claude-sonnet-5 | gpt-5-6-sol |
| Cross-cutting rate-limit migration | claude-sonnet-5 | gpt-5-6-sol |

Rationale for the escalations: "[not_crosscutting AND not_mixed_change AND low_ambiguity] all
hold -> escalate up to claude-opus-4-8". The rest: "not all hold -> default claude-sonnet-5".
The router uses an LLM extraction step, so a rerun can differ. One run.
