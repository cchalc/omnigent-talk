from omnigent_talk.budget import EVERYONE_ELSE_USD, unity_gateway_budget


def alert(body: dict) -> dict:
    (only,) = body["budget"]["alert_configurations"]
    return only


def test_budget_is_per_user_on_unity_gateway_and_blocks():
    body = unity_gateway_budget("acct", 123, per_user_usd=0.5)
    assert body["budget"]["resource_type"] == "BUDGET_RESOURCE_TYPE_UNITY_AI_GATEWAY"
    assert body["budget"]["filter"]["workspace_id"]["values"] == [123]
    a = alert(body)
    assert a["scope_type"] == "ALERT_CONFIGURATION_SCOPE_TYPE_PER_USER"
    assert a["quantity_threshold"] == "0.50"
    assert a["action_configurations"] == [{"action_type": "BLOCK_USAGE"}]


def test_only_principal_gets_the_low_cap_and_everyone_else_a_high_one():
    a = alert(unity_gateway_budget("acct", 1, per_user_usd=0.5, only_principal=42))
    assert a["quantity_threshold"] == f"{EVERYONE_ELSE_USD:.2f}"
    assert a["principal_overrides"] == [{"principal_id": 42, "override_threshold": "0.50"}]


def test_alert_only_budget_has_no_block_action():
    a = alert(unity_gateway_budget("acct", 1, block=False, notify="team@example.com"))
    assert a["action_configurations"] == [
        {"action_type": "EMAIL_NOTIFICATION", "target": "team@example.com"}
    ]
