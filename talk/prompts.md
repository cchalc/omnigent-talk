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
| 1 | Write a SQL query for the top 5 customers by total revenue from an orders table. | qwen | _pending_ |
| 2 | Explain the difference between a LEFT JOIN and a FULL OUTER JOIN with a small example. | qwen | _pending_ |
| 3 | Review the diff on this branch against its base and list real bugs only. | codex | _pending_ |
| 4 | Deploy the gateway bundle. | codex, stops at the confirmation gate | _pending_ |
