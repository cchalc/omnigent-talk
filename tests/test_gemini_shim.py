import asyncio
import json

import httpx
import pytest

from omnigent_talk.gemini_shim import GeminiShim, agy_gemini_dir, attribution_headers

TAGS = "Databricks-Ai-Gateway-Request-Tags"


class Streamed(httpx.AsyncByteStream):
    """An unread body, like a real upstream; `Response(json=...)` arrives already consumed."""

    async def __aiter__(self):
        yield b'{"modelVersion": "gemini-3-8-flash"}'


def make_shim(
    seen: list[httpx.Request],
    lite: str | None = None,
    attribution: dict[str, str] | None = None,
) -> GeminiShim:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, stream=Streamed())

    upstream = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GeminiShim(
        "https://ws.example",
        "c.s.router",
        lambda: {"Authorization": "Bearer t"},
        upstream,
        lite_service=lite,
        attribution=attribution,
    )


def post(shim: GeminiShim, url: str, headers: dict[str, str] | None = None) -> httpx.Response:
    async def go() -> httpx.Response:
        transport = httpx.ASGITransport(app=shim.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://shim") as client:
            response = await client.post(url, headers=headers, content=b"{}")
            await response.aread()
            return response

    return asyncio.run(go())


def test_any_requested_model_goes_to_the_pinned_service():
    seen: list[httpx.Request] = []
    shim = make_shim(seen)
    r = post(
        shim,
        "/v1beta/models/gemini-3-pro:streamGenerateContent?alt=sse",
        {"x-goog-api-key": shim.key},
    )
    assert r.status_code == 200
    assert r.json() == {"modelVersion": "gemini-3-8-flash"}
    (request,) = seen
    assert request.url.path == "/ai-gateway/gemini/v1beta/models/c.s.router:streamGenerateContent"
    assert request.url.params["alt"] == "sse"
    assert request.headers["Authorization"] == "Bearer t"


def test_key_in_query_is_accepted_but_not_forwarded():
    seen: list[httpx.Request] = []
    shim = make_shim(seen)
    r = post(shim, f"/v1beta/models/m:generateContent?key={shim.key}")
    assert r.status_code == 200
    assert "key" not in seen[0].url.params


def test_wrong_key_is_rejected_before_any_upstream_call():
    seen: list[httpx.Request] = []
    r = post(make_shim(seen), "/v1beta/models/m:generateContent", {"x-goog-api-key": "nope"})
    assert r.status_code == 401
    assert seen == []


def test_other_operations_are_not_proxied():
    seen: list[httpx.Request] = []
    shim = make_shim(seen)
    r = post(shim, "/v1beta/models/m:countTokens", {"x-goog-api-key": shim.key})
    assert r.status_code == 404
    assert seen == []


def test_lite_calls_go_to_the_lite_service_when_set():
    seen: list[httpx.Request] = []
    shim = make_shim(seen, lite="c.s.fast")
    for model in ("gemini-3.1-flash-lite-preview", "gemini-3.1-pro-preview"):
        post(shim, f"/v1beta/models/{model}:generateContent", {"x-goog-api-key": shim.key})
    assert [r.url.path.rsplit("/", 1)[1] for r in seen] == [
        "c.s.fast:generateContent",
        "c.s.router:generateContent",
    ]


def test_agy_gemini_dir_selects_api_key_auth_and_keeps_other_settings(tmp_path):
    settings = tmp_path / ".gemini" / "antigravity-cli" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('{"model": "keep-me"}')
    assert agy_gemini_dir(tmp_path) == tmp_path / ".gemini"
    assert json.loads(settings.read_text()) == {
        "model": "keep-me",
        "modelProvider": "gemini",
        "showFeedbackSurvey": False,
    }


def test_default_tags_carry_the_whole_contract():
    headers = attribution_headers({})
    assert json.loads(headers[TAGS]) == {
        "demo": "bakehouse",
        "harness": "agy",
        "agent_spec": "unknown",
    }
    assert set(headers) == {TAGS}


def test_agent_spec_comes_from_env_and_request_tags_merge_over_the_defaults():
    env = {
        "AI_GATEWAY_AGENT_SPEC": "bakehouse-agy",
        "AI_GATEWAY_REQUEST_TAGS": '{"harness": "agy-bare", "stage": "rehearsal"}',
    }
    assert json.loads(attribution_headers(env)[TAGS]) == {
        "demo": "bakehouse",
        "harness": "agy-bare",
        "agent_spec": "bakehouse-agy",
        "stage": "rehearsal",
    }


def test_optional_agent_headers():
    headers = attribution_headers(
        {"AI_GATEWAY_CODING_AGENT": "antigravity", "AI_GATEWAY_CLIENT_SURFACES": "omnigent, ug"}
    )
    assert headers["Databricks-Custom-Coding-Agent"] == "antigravity"
    assert headers["Databricks-Custom-Client-Surfaces"] == "omnigent, ug"


@pytest.mark.parametrize(
    "value",
    [
        "agy\r\nAuthorization: Bearer stolen",
        "agy\nX-Injected: 1",
        "agy\x00",
        "agy\x7f",
        "agy\u2028",
        "caf\u00e9",
        "a" * 257,
    ],
)
@pytest.mark.parametrize("name", ["AI_GATEWAY_CODING_AGENT", "AI_GATEWAY_CLIENT_SURFACES"])
def test_header_values_with_control_or_non_ascii_characters_are_rejected(name, value):
    with pytest.raises(SystemExit, match=name):
        attribution_headers({name: value})


def test_tag_json_with_control_characters_stays_on_one_header_line():
    raw = json.dumps({"agent_spec": "x\r\nAuthorization: Bearer stolen"})
    encoded = attribution_headers({"AI_GATEWAY_REQUEST_TAGS": raw})[TAGS]
    assert "\r" not in encoded and "\n" not in encoded
    assert json.loads(encoded)["agent_spec"] == "x\r\nAuthorization: Bearer stolen"


@pytest.mark.parametrize("raw", ["not json", "[1]", '{"n": 1}', '{"k": "' + "x" * 5000 + '"}'])
def test_malformed_or_oversized_tags_fail_loudly(raw):
    with pytest.raises(SystemExit, match="AI_GATEWAY_REQUEST_TAGS"):
        attribution_headers({"AI_GATEWAY_REQUEST_TAGS": raw})


def test_attribution_is_forwarded_on_every_upstream_call():
    seen: list[httpx.Request] = []
    attribution = attribution_headers({"AI_GATEWAY_REQUEST_TAGS": '{"harness": "agy"}'})
    shim = make_shim(seen, lite="c.s.fast", attribution=attribution)
    for model in ("gemini-3.1-flash-lite-preview", "gemini-3.8-flash"):
        post(shim, f"/v1beta/models/{model}:generateContent", {"x-goog-api-key": shim.key})
    assert [json.loads(r.headers[TAGS])["harness"] for r in seen] == ["agy", "agy"]
    assert all(r.headers["Authorization"] == "Bearer t" for r in seen)


def test_incoming_headers_do_not_override_attribution():
    seen: list[httpx.Request] = []
    shim = make_shim(seen, attribution={TAGS: '{"demo": "bakehouse"}'})
    headers = {"x-goog-api-key": shim.key, TAGS: '{"demo": "spoofed"}'}
    post(shim, "/v1beta/models/m:generateContent", headers)
    assert json.loads(seen[0].headers[TAGS]) == {"demo": "bakehouse"}
