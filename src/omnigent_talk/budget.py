"""An account budget that blocks a user's Unity Gateway usage past a small monthly spend.

Budgets are account-level, so applying one needs an account admin and an account profile:
`databricks account budgets create --json @<file> --profile <account-profile>`. This module
only builds the request body, so it can be reviewed (and tested) before anything is created.
"""

from __future__ import annotations

from typing import Any


def unity_gateway_budget(
    account_id: str,
    workspace_id: int,
    *,
    per_user_usd: float = 1.0,
    block: bool = True,
    notify: str | None = None,
    name: str = "omnigent-talk: Unity Gateway per-user cap",
) -> dict[str, Any]:
    actions: list[dict[str, str]] = []
    if block:
        actions.append({"action_type": "BLOCK_USAGE"})
    if notify:
        actions.append({"action_type": "EMAIL_NOTIFICATION", "target": notify})
    return {
        "budget": {
            "account_id": account_id,
            "display_name": name,
            "resource_type": "BUDGET_RESOURCE_TYPE_UNITY_AI_GATEWAY",
            "filter": {"workspace_id": {"operator": "IN", "values": [workspace_id]}},
            "alert_configurations": [
                {
                    "time_period": "MONTH",
                    "trigger_type": "CUMULATIVE_SPENDING_EXCEEDED",
                    "quantity_type": "LIST_PRICE_DOLLARS_USD",
                    "quantity_threshold": f"{per_user_usd:.2f}",
                    "scope_type": "ALERT_CONFIGURATION_SCOPE_TYPE_PER_USER",
                    "action_configurations": actions,
                }
            ],
        }
    }
