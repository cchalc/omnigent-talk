"""Ask Unity Gateway Smart Routing (Beta) which model it would pick, without running the task.

With Smart Routing on, the Omnigent server sends each prompt (and each subagent task) to the
workspace router at `/ai-gateway/routing/v1/routes:select`, strategy `task_v1`, then launches the
harness on the picked model (omnigent/server/smart_routing.py, ExternalRoutingClient). This
module makes the same call, so the decision and its rationale can be shown on stage before a
session runs. `task_v1` infers its scenario from the model families offered and rejects a partial
menu, so each family sends its full arm menu (omnigent/models/model_fallbacks.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from omnigent_talk.gateway import GeminiGateway

ROUTE = "/ai-gateway/routing/v1/routes:select"
ROUTER = "task_v1"
MENUS: dict[str, tuple[str, ...]] = {
    "claude": ("claude-opus-4-8", "claude-sonnet-5"),
    "codex": ("glm-5-2", "gpt-5-6-sol", "gpt-5-6-luna"),
}


@dataclass(frozen=True)
class Pick:
    status: int
    model: str | None
    rationale: str
    error: str | None = None


def select_body(prompt: str, family: str) -> dict[str, Any]:
    """The `routes:select` request Omnigent sends: the menu, the prompt and the strategy."""
    options = [{"model": model, "harness": family} for model in MENUS[family]]
    return {
        "route_options": options,
        # Omnigent truncates the prompt to 4000 characters before routing.
        "task": {"prompt": prompt[:4000]},
        "route_selector": {"router_name": ROUTER},
    }


def parse_pick(response: httpx.Response) -> Pick:
    try:
        payload: Any = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    if not response.is_success:
        error = payload.get("message") or response.text[:200] or response.reason_phrase
        return Pick(response.status_code, None, "", str(error))
    selection = payload.get("route_selection") or [{}]
    model = (selection[0].get("route_option") or {}).get("model")
    error = None if model else "router returned no route selection"
    return Pick(response.status_code, model, str(payload.get("rationale", "")), error)


def select(gateway: GeminiGateway, prompt: str, family: str) -> Pick:
    """One routing decision from the workspace router. Runs no model on the task itself."""
    response = gateway.client.post(
        f"{gateway.host.rstrip('/')}{ROUTE}",
        headers=gateway.headers(),
        json=select_body(prompt, family),
    )
    return parse_pick(response)


def server_info(gateway: GeminiGateway, server: str) -> dict[str, Any]:
    """Smart Routing as the Omnigent server reports it on `/v1/info`."""
    response = gateway.client.get(f"{server.rstrip('/')}/v1/info", headers=gateway.headers())
    response.raise_for_status()
    info = response.json()
    return {
        "smart_routing_enabled": info.get("smart_routing_enabled"),
        "smart_routing_sources": info.get("smart_routing_sources"),
    }
