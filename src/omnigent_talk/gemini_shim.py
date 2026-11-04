"""Point native agy at a custom Unity Gateway model service.

Omnigent's own agy adapter only discovers `system.ai.gemini-*` services
(`omnigent/models/databricks_model_discovery.py`). This shim is the same idea pinned to one
service: agy talks to it on 127.0.0.1 with a key, and it forwards every generateContent call
to `<service>` with the profile's Databricks auth, whatever model agy asked for.

Two modes:
- `wrap`: run one command (e.g. a bare `agy`) with `GEMINI_API_KEY` and
  `GOOGLE_GEMINI_BASE_URL` pointing at a per-run shim. Fine for agy alone. It does not reach
  `omni agy --server`, because the host daemon launches agy, not this shell.
- `serve`: listen on a fixed port with a fixed key until stopped, so an Omnigent `key`
  provider for the gemini family can point at it (see `just agy-provider`).

Both modes stamp Unity Gateway attribution on every forwarded call, read from the environment
at startup (`attribution_headers`): `AI_GATEWAY_REQUEST_TAGS` (a JSON object of strings, merged
over `DEFAULT_REQUEST_TAGS`) becomes `Databricks-Ai-Gateway-Request-Tags`, which lands in
`request_tags` in `system.ai_gateway.usage`. `AI_GATEWAY_CODING_AGENT` and
`AI_GATEWAY_CLIENT_SURFACES`, when set, become the coding-agent and client-surface headers
Omnigent itself sends for the harnesses it drives (`omnigent/databricks_ai_gateway.py`).
"""

from __future__ import annotations

import asyncio
import contextlib
import hmac
import json
import os
import re
import secrets
import signal
import socket
import sys
from collections.abc import Mapping
from pathlib import Path

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

from omnigent_talk.gateway import REQUEST_TAGS_HEADER, AuthHeaders, gemini_url

GENERATE_PATH = re.compile(r"/v1beta/models/([^/:]+):(generateContent|streamGenerateContent)")
RESPONSE_HEADERS = {"content-type", "content-encoding", "content-length"}
# agy's endpoint override; Omnigent uses the same name (`onboarding/gemini_gateway.py`).
BASE_URL_ENV = "GOOGLE_GEMINI_BASE_URL"
# Attribution settings, and the headers they become. Header names match Omnigent's.
REQUEST_TAGS_ENV = "AI_GATEWAY_REQUEST_TAGS"
CODING_AGENT_ENV = "AI_GATEWAY_CODING_AGENT"
CLIENT_SURFACES_ENV = "AI_GATEWAY_CLIENT_SURFACES"
CODING_AGENT_HEADER = "Databricks-Custom-Coding-Agent"
CLIENT_SURFACES_HEADER = "Databricks-Custom-Client-Surfaces"
# Every shim call is findable in usage, even when nothing else tagged it.
DEFAULT_REQUEST_TAGS = {"client": "omnigent-talk-gemini-shim"}
# Omnigent's budget for the tag header.
MAX_REQUEST_TAGS_LENGTH = 4096


def log(message: str) -> None:
    print(f"[gemini-shim] {message}", file=sys.stderr, flush=True)


def attribution_headers(env: Mapping[str, str]) -> dict[str, str]:
    """Gateway attribution headers from the environment. A malformed tag setting fails loudly."""
    tags = dict(DEFAULT_REQUEST_TAGS)
    raw = env.get(REQUEST_TAGS_ENV, "").strip()
    if raw:
        try:
            extra = json.loads(raw)
        except json.JSONDecodeError:
            extra = None
        if not isinstance(extra, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in extra.items()
        ):
            raise SystemExit(f"{REQUEST_TAGS_ENV} must be a JSON object of strings.")
        tags.update(extra)
    encoded = json.dumps(tags, separators=(",", ":"))
    if len(encoded) > MAX_REQUEST_TAGS_LENGTH:
        raise SystemExit(f"{REQUEST_TAGS_ENV} is over {MAX_REQUEST_TAGS_LENGTH} characters.")
    headers = {REQUEST_TAGS_HEADER: encoded}
    for name, header in (
        (CODING_AGENT_ENV, CODING_AGENT_HEADER),
        (CLIENT_SURFACES_ENV, CLIENT_SURFACES_HEADER),
    ):
        if value := env.get(name, "").strip():
            headers[header] = value
    return headers


class GeminiShim:
    def __init__(
        self,
        host: str,
        service: str,
        auth: AuthHeaders,
        client: httpx.AsyncClient,
        key: str | None = None,
        lite_service: str | None = None,
        attribution: Mapping[str, str] | None = None,
    ) -> None:
        self.host = host
        self.service = service
        self.lite_service = lite_service
        self.auth = auth
        self.client = client
        self.key = key or secrets.token_urlsafe(32)
        self.attribution = dict(attribution or {})
        self.app = Starlette(routes=[Route("/{path:path}", self.forward, methods=["POST"])])

    def target(self, requested: str) -> str:
        """agy sends background work (titles, summaries) to a `*-lite` model; route it apart."""
        if self.lite_service and "lite" in requested:
            return self.lite_service
        return self.service

    async def forward(self, request: Request) -> JSONResponse | StreamingResponse:
        supplied = request.headers.get("x-goog-api-key") or request.query_params.get("key", "")
        if not hmac.compare_digest(supplied, self.key):
            return JSONResponse({"error": {"message": "Invalid shim key"}}, 401)
        match = GENERATE_PATH.fullmatch(request.url.path)
        if match is None:
            return JSONResponse({"error": {"message": "Unsupported Gemini operation"}}, 404)
        requested, operation = match[1], match[2]
        service = self.target(requested)
        try:
            headers = await asyncio.to_thread(self.auth)
            upstream = await self.client.send(
                self.client.build_request(
                    "POST",
                    gemini_url(self.host, service, operation),
                    params=[(k, v) for k, v in request.query_params.multi_items() if k != "key"],
                    headers={**self.attribution, **headers, "Content-Type": "application/json"},
                    content=await request.body(),
                ),
                stream=True,
            )
        except Exception:
            # Auth and transport errors can carry tokens or URLs, so don't echo them.
            log("upstream request failed; try `databricks auth login --profile <profile>`")
            return JSONResponse({"error": {"message": "Databricks gateway request failed"}}, 502)
        log(f"{requested} -> {service} {operation}: HTTP {upstream.status_code}")
        return StreamingResponse(
            upstream.aiter_raw(),
            status_code=upstream.status_code,
            headers={k: v for k, v in upstream.headers.items() if k in RESPONSE_HEADERS},
            background=BackgroundTask(upstream.aclose),
        )


class _Server(uvicorn.Server):
    @contextlib.contextmanager
    def capture_signals(self):
        # In wrap mode the child owns Ctrl-C and we stop when it exits.
        yield


def _client() -> httpx.AsyncClient:
    timeout = httpx.Timeout(connect=15, read=None, write=60, pool=15)
    return httpx.AsyncClient(timeout=timeout, follow_redirects=False)


async def serve(
    host: str, service: str, auth: AuthHeaders, port: int, key: str, lite: str | None = None
) -> None:
    """Serve until interrupted. agy (or Omnigent's host daemon) connects with `key`."""
    async with _client() as client:
        attribution = attribution_headers(os.environ)
        shim = GeminiShim(host, service, auth, client, key, lite, attribution)
        log(
            f"listening on 127.0.0.1:{port}, forwarding to {service}"
            + (f" (lite: {lite})" if lite else "")
            + f", tags {attribution[REQUEST_TAGS_HEADER]}"
        )
        config = uvicorn.Config(shim.app, host="127.0.0.1", port=port, log_level="error")
        await uvicorn.Server(config).serve()


async def wrap(
    host: str, service: str, auth: AuthHeaders, argv: list[str], lite: str | None = None
) -> int:
    """Serve the shim on a free port exactly as long as the child command runs."""
    async with _client() as client:
        attribution = attribution_headers(os.environ)
        shim = GeminiShim(host, service, auth, client, lite_service=lite, attribution=attribution)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            server = _Server(uvicorn.Config(shim.app, log_level="error", lifespan="off"))
            serving = asyncio.create_task(server.serve(sockets=[listener]))
            try:
                async with asyncio.timeout(10):
                    while not server.started:
                        if serving.done():
                            await serving
                            raise RuntimeError("Gemini shim did not start")
                        await asyncio.sleep(0.01)
                env = {
                    **{k: v for k, v in os.environ.items() if not k.startswith("DATABRICKS_")},
                    "GEMINI_API_KEY": shim.key,
                    BASE_URL_ENV: f"http://127.0.0.1:{port}",
                }
                log(
                    f"listening on 127.0.0.1:{port}, forwarding to {service}"
                    + (f" (lite: {lite})" if lite else "")
                    + f", tags {attribution[REQUEST_TAGS_HEADER]}"
                )
                child = await asyncio.create_subprocess_exec(*argv, env=env)
                loop = asyncio.get_running_loop()
                for sig in (signal.SIGTERM, signal.SIGHUP):
                    loop.add_signal_handler(sig, child.send_signal, sig)
                return await child.wait()
            finally:
                server.should_exit = True
                try:
                    await asyncio.wait_for(serving, 5)
                except TimeoutError:
                    serving.cancel()


def agy_gemini_dir(root: Path) -> Path:
    """An isolated agy `--gemini_dir` whose settings select API-key auth.

    agy ignores `GEMINI_API_KEY` while `modelProvider` is unset and keeps using its Google
    login. Omnigent's bridge writes the same setting into its per-session dir; this does it
    for a bare `agy`, without touching `~/.gemini`.
    """
    gemini_dir = root / ".gemini"
    settings = gemini_dir / "antigravity-cli" / "settings.json"
    settings.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    current = json.loads(settings.read_text()) if settings.exists() else {}
    current.update({"modelProvider": "gemini", "showFeedbackSurvey": False})
    settings.write_text(json.dumps(current, indent=2) + "\n")
    return gemini_dir
