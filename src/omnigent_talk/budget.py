"""An account budget that blocks Unity Gateway usage past a small monthly spend.

Budgets are account-level, so applying one needs an account admin and an account profile:
`databricks account budgets create --json @<file> --profile <account-profile>`. This module
only builds the request body, so it can be reviewed (and tested) before anything is created.

A budget can't be narrowed to one model service (services carry no tags), only to a workspace.
On a shared workspace a per-user block would hit everyone, so by default the block only bites
one principal: everyone gets a threshold no demo reaches, and an override lowers it for the
presenter. The action (block or alert) belongs to the whole alert; overrides change only the
threshold.
"""

from __future__ import annotations

from typing import Any

# Monthly per-user spend that no one reaches in practice, so the block never fires for them.
EVERYONE_ELSE_USD = 100_000.0


def unity_gateway_budget(
    account_id: str,
    workspace_id: int,
    *,
    per_user_usd: float = 1.0,
    only_principal: int | None = None,
    block: bool = True,
    notify: str | None = None,
    name: str = "omnigent-talk: Unity Gateway per-user cap",
) -> dict[str, Any]:
    """Build the body. With `only_principal`, `per_user_usd` applies to that user alone."""
    actions: list[dict[str, str]] = []
    if block:
        actions.append({"action_type": "BLOCK_USAGE"})
    if notify:
        actions.append({"action_type": "EMAIL_NOTIFICATION", "target": notify})
    alert: dict[str, Any] = {
        "time_period": "MONTH",
        "trigger_type": "CUMULATIVE_SPENDING_EXCEEDED",
        "quantity_type": "LIST_PRICE_DOLLARS_USD",
        "quantity_threshold": f"{per_user_usd:.2f}",
        "scope_type": "ALERT_CONFIGURATION_SCOPE_TYPE_PER_USER",
        "action_configurations": actions,
    }
    if only_principal is not None:
        alert["quantity_threshold"] = f"{EVERYONE_ELSE_USD:.2f}"
        alert["principal_overrides"] = [
            {"principal_id": only_principal, "override_threshold": f"{per_user_usd:.2f}"}
        ]
    return {
        "budget": {
            "account_id": account_id,
            "display_name": name,
            "resource_type": "BUDGET_RESOURCE_TYPE_UNITY_AI_GATEWAY",
            "filter": {"workspace_id": {"operator": "IN", "values": [workspace_id]}},
            "alert_configurations": [alert],
        }
    }
