"""Call Unity Gateway model services through the native Gemini API.

Everything workspace-specific comes from the environment (`.env.local`, loaded by `just`), so
nothing identifying is committed. A missing setting fails loudly rather than defaulting.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

GEMINI_ROUTE = "/ai-gateway/gemini/v1beta/models"
REQUEST_TAGS_HEADER = "Databricks-Ai-Gateway-Request-Tags"

AuthHeaders = Callable[[], dict[str, str]]


def require_env(name: str) -> str:
    """Return a required setting, or exit with a message naming it."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is not set. Add it to .env.local (see .env.example).")
    return value


def service_name(service: str) -> str:
    """Qualify a bare service id with CATALOG.SCHEMA; leave `system.ai.*` and dotted names as is."""
    if "." in service:
        return service
    return f"{require_env('CATALOG')}.{require_env('SCHEMA')}.{service}"


def gemini_url(host: str, service: str, operation: str = "generateContent") -> str:
    return f"{host.rstrip('/')}{GEMINI_ROUTE}/{service}:{operation}"


def prompt_body(prompt: str, max_tokens: int = 256) -> dict[str, Any]:
    return {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }


@dataclass(frozen=True)
class Reply:
    status: int
    model_version: str | None
    text: str
    error: str | None

    @classmethod
    def from_response(cls, response: httpx.Response) -> Reply:
        try:
            payload: Any = response.json()
        except json.JSONDecodeError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        if response.is_success:
            parts = (payload.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            return cls(response.status_code, payload.get("modelVersion"), text.strip(), None)
        error = payload.get("error")
        message = error.get("message") if isinstance(error, dict) else response.text[:200]
        return cls(response.status_code, None, "", str(message))


@dataclass
class GeminiGateway:
    """A thin client for one workspace. `auth` returns fresh headers on every call."""

    host: str
    auth: AuthHeaders
    client: httpx.Client

    def generate(self, service: str, prompt: str, *, tags: dict[str, str] | None = None) -> Reply:
        headers = {**self.auth(), "Content-Type": "application/json"}
        if tags:
            headers[REQUEST_TAGS_HEADER] = json.dumps(tags)
        response = self.client.post(
            gemini_url(self.host, service), headers=headers, json=prompt_body(prompt)
        )
        return Reply.from_response(response)


def workspace_auth(profile: str) -> tuple[str, AuthHeaders]:
    """Host and a header factory for a CLI profile. The SDK refreshes OAuth tokens itself."""
    from databricks.sdk import WorkspaceClient

    config = WorkspaceClient(profile=profile).config
    host = config.host
    if not host:
        raise SystemExit(f"Profile {profile!r} has no host.")
    return host, config.authenticate


def connect(profile: str | None = None) -> GeminiGateway:
    host, auth = workspace_auth(profile or require_env("DBX_PROFILE"))
    return GeminiGateway(host, auth, httpx.Client(timeout=60))
