import asyncio
import json

import httpx

from omnigent_talk.gemini_shim import GeminiShim, agy_gemini_dir


class Streamed(httpx.AsyncByteStream):
    """An unread body, like a real upstream; `Response(json=...)` arrives already consumed."""

    async def __aiter__(self):
        yield b'{"modelVersion": "gemini-3-8-flash"}'


def make_shim(seen: list[httpx.Request], lite: str | None = None) -> GeminiShim:
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
