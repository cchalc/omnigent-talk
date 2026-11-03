from omnigent_talk.gateway import Reply
from omnigent_talk.routing import format_tally, tally


def reply(status: int, model: str | None = None) -> Reply:
    return Reply(status, model, "", None if status == 200 else "x")


def test_tally_counts_models_and_failures():
    counts = tally([reply(200, "a"), reply(200, "a"), reply(200, "b"), reply(429)])
    assert counts == {"a": 2, "b": 1, "HTTP 429": 1}


def test_format_tally_orders_by_count():
    lines = format_tally(tally([reply(200, "b"), reply(200, "a"), reply(200, "a")])).splitlines()
    assert lines[0].split()[:2] == ["a", "2"]
    assert "66.7%" in lines[0]
