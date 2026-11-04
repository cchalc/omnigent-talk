---
name: deploy
description: Run a gateway bundle deploy through the Codex worker with a two-phase approval gate. Use whenever the user asks to deploy, validate, redeploy or destroy the Unity Gateway bundle.
---

# deploy: plan, approve, then deploy

The workers are headless and can't answer approval prompts, so the approval happens in this
conversation.

1. **Plan.** Send `codex`: `PLAN: validate and plan the gateway bundle deploy`. It runs
   `just gateway-validate` and `just gateway-plan`.
2. **Show the user** three things:
   - the target, which is the profile in DBX_PROFILE (name only);
   - every create, update and delete from the plan;
   - the blast radius: what traffic or limits change, and whether anything is deleted.
3. **Ask** in one direct question: "Deploy these changes?" Wait for the user's reply.
4. **Deploy** only after a clear yes from the user in this conversation. Send `codex`
   `DEPLOY APPROVED` with the same title, then report its `just gateway-show` output.
5. If the user says no, or anything is unclear, stop and say nothing was deployed.

Destroy follows the same steps, with `DESTROY APPROVED` and `just gateway-destroy`. Never send
an approval phrase the user did not give.
