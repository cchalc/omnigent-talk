from omnigent_talk.budget import unity_gateway_budget


def test_budget_is_per_user_on_unity_gateway_and_blocks():
    body = unity_gateway_budget("acct", 123, per_user_usd=0.5)["budget"]
    assert body["resource_type"] == "BUDGET_RESOURCE_TYPE_UNITY_AI_GATEWAY"
    assert body["filter"]["workspace_id"]["values"] == [123]
    (alert,) = body["alert_configurations"]
    assert alert["scope_type"] == "ALERT_CONFIGURATION_SCOPE_TYPE_PER_USER"
    assert alert["quantity_threshold"] == "0.50"
    assert alert["action_configurations"] == [{"action_type": "BLOCK_USAGE"}]


def test_alert_only_budget_has_no_block_action():
    body = unity_gateway_budget("acct", 1, block=False, notify="team@example.com")["budget"]
    actions = body["alert_configurations"][0]["action_configurations"]
    assert actions == [{"action_type": "EMAIL_NOTIFICATION", "target": "team@example.com"}]
