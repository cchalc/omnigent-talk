---
name: databricks-infrastructure-deployment
description: Validate Databricks infrastructure, expose target and blast radius, and confirm before state-changing deployment actions.
---

# Databricks infrastructure deployment

**Intent:** Prevent accidental changes to the wrong workspace or to shared infrastructure.

**When it applies:** Bundle validation, deployment, destruction, resource updates, permissions,
budgets, service policies, or preview enablement.

**Evidence:** Resolve the user-selected `DBX_PROFILE`, bundle target, proposed diff, affected
resources, cost implications, and whether the action is reversible.

**Decision:** Separate validation and read-only inspection from state changes. Treat deploy,
destroy, permission changes, account budgets, and preview changes as confirmation-gated.

**Execution:** Run `just gateway-validate`, report target and blast radius, obtain confirmation, and
use the bundle recipe. Keep catalog, schema, hosts, IDs, and principals in `.env.local`, never in
tracked files.

**Recovery:** On validation failure or ambiguous target, stop without deploying. On partial failure,
inspect bundle state and propose a reversible recovery before taking another state-changing action.

**Desired conduct:** The trace proves validation preceded a confirmed change against the configured
profile and records the outcome without leaking workspace details.

**Failure modes:** Using the default CLI profile, deploying ad hoc resources outside the bundle,
combining validation and deployment invisibly, or running destroy without explicit approval.
