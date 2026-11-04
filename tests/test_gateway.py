import json

import httpx
import pytest

from omnigent_talk import gateway


def test_bare_service_is_qualified_from_env(monkeypatch):
    monkeypatch.setenv("CATALOG", "cat")
    monkeypatch.setenv("SCHEMA", "sch")
    assert gateway.service_name("gemini_router") == "cat.sch.gemini_router"
    assert gateway.service_name("system.ai.gemini-3-8-flash") == "system.ai.gemini-3-8-flash"


def test_missing_setting_names_the_variable(monkeypatch):
    monkeypatch.delenv("CATALOG", raising=False)
    with pytest.raises(SystemExit, match="CATALOG"):
        gateway.service_name("gemini_router")


def test_reply_drops_thought_parts():
    response = httpx.Response(
        200,
        json={
            "modelVersion": "gemini-3-8-flash",
            "candidates": [
                {"content": {"parts": [{"text": "thinking", "thought": True}, {"text": "pong"}]}}
            ],
        },
    )
    reply = gateway.Reply.from_response(response)
    assert (reply.status, reply.model_version, reply.text) == (200, "gemini-3-8-flash", "pong")


def test_reply_keeps_error_message():
    reply = gateway.Reply.from_response(httpx.Response(429, json={"error": {"message": "slow"}}))
    assert (reply.status, reply.error) == (429, "slow")


def test_generate_posts_native_route_with_tags():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"modelVersion": "m", "candidates": []})

    gw = gateway.GeminiGateway(
        "https://ws.example",
        lambda: {"Authorization": "Bearer t"},
        httpx.Client(transport=httpx.MockTransport(handler)),
    )
    gw.generate("c.s.router", "hi", tags={"demo": "split"})
    (request,) = seen
    assert (
        str(request.url)
        == "https://ws.example/ai-gateway/gemini/v1beta/models/c.s.router:generateContent"
    )
    assert request.headers["Authorization"] == "Bearer t"
    assert json.loads(request.headers[gateway.REQUEST_TAGS_HEADER]) == {"demo": "split"}


def test_shim_options_before_the_separator_are_not_swallowed():
    from omnigent_talk.cli import parser

    a = parser().parse_args(["shim", "router", "--lite", "fast", "--agy", "--", "-p", "hi"])
    assert (a.lite, a.agy, a.command) == ("fast", True, ["-p", "hi"])


def test_chat_posts_unified_route_with_tags():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200, json={"model": "c.s.qwen_code", "choices": [{"message": {"content": "ok"}}]}
        )

    gw = gateway.GeminiGateway(
        "https://ws.example",
        lambda: {"Authorization": "Bearer t"},
        httpx.Client(transport=httpx.MockTransport(handler)),
    )
    reply = gw.chat("c.s.qwen_code", [{"role": "user", "content": "hi"}], tags={"route": "sql"})
    (request,) = seen
    assert request.url.path == "/ai-gateway/mlflow/v1/chat/completions"
    assert json.loads(request.content)["model"] == "c.s.qwen_code"
    assert json.loads(request.headers[gateway.REQUEST_TAGS_HEADER]) == {"route": "sql"}
    assert (reply.status, reply.text) == (200, "ok")


def test_chat_reply_keeps_text_parts_and_drops_reasoning():
    content = [
        {"type": "reasoning", "summary": [{"type": "summary_text", "text": "thinking"}]},
        {"type": "text", "text": "SELECT 1;"},
    ]
    response = httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
    assert gateway.Reply.from_chat(response).text == "SELECT 1;"


def test_chat_reply_keeps_error_message():
    response = httpx.Response(403, json={"error": {"message": "no EXECUTE"}})
    reply = gateway.Reply.from_chat(response)
    assert (reply.status, reply.error) == (403, "no EXECUTE")
