"""Smart Routing preview: the routes:select request Omnigent sends, and parsing its answer."""

import json

import httpx
import pytest

from omnigent_talk import smart_routing
from omnigent_talk.gateway import GeminiGateway


def gateway_answering(handler) -> GeminiGateway:
    return GeminiGateway(
        "https://ws.example",
        lambda: {"Authorization": "Bearer t"},
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.parametrize("family", ["claude", "codex"])
def test_body_offers_the_full_menu_for_one_family(family):
    body = smart_routing.select_body("fix a typo", family)
    assert [o["model"] for o in body["route_options"]] == list(smart_routing.MENUS[family])
    assert {o["harness"] for o in body["route_options"]} == {family}
    assert body["route_selector"] == {"router_name": "task_v1"}


def test_body_truncates_the_prompt_like_omnigent():
    assert len(smart_routing.select_body("x" * 5000, "claude")["task"]["prompt"]) == 4000


def test_select_posts_to_the_router_and_reads_pick_and_rationale():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "route_selection": [
                    {"route_option": {"model": "claude-sonnet-5", "harness": "claude"}}
                ],
                "rationale": "trivial task -> cheapest arm",
            },
        )

    pick = smart_routing.select(gateway_answering(handler), "fix a typo", "claude")
    assert seen["url"] == "https://ws.example/ai-gateway/routing/v1/routes:select"
    assert seen["auth"] == "Bearer t"
    assert seen["body"]["task"]["prompt"] == "fix a typo"
    assert pick == smart_routing.Pick(200, "claude-sonnet-5", "trivial task -> cheapest arm")


def test_router_error_is_reported_not_raised():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403, json={"message": "Enhanced Unity Gateway preview is not enabled"}
        )

    pick = smart_routing.select(gateway_answering(handler), "fix a typo", "codex")
    assert pick.model is None
    assert pick.status == 403
    assert "preview" in (pick.error or "")


def test_empty_selection_is_an_error():
    pick = smart_routing.parse_pick(httpx.Response(200, json={"route_selection": []}))
    assert pick.model is None
    assert pick.error == "router returned no route selection"


def test_server_info_keeps_only_the_smart_routing_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/2.0/omnigent/v1/info"
        return httpx.Response(
            200,
            json={
                "smart_routing_enabled": True,
                "smart_routing_sources": {"external": True, "oss": True},
                "login_url": "https://ws.example/login",
            },
        )

    info = smart_routing.server_info(
        gateway_answering(handler), "https://ws.example/api/2.0/omnigent"
    )
    assert info == {
        "smart_routing_enabled": True,
        "smart_routing_sources": {"external": True, "oss": True},
    }
