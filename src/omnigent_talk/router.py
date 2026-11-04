"""Route each prompt by task: coding and SQL to Qwen, everything else to Gemini 3.8 Flash.

A model service never reads the prompt (it splits at random by weight), so the decision is
made here, before the gateway. One cheap call to `gemini_fast` labels the prompt; the request
then goes to that route's service, tagged with the route, so `system.ai_gateway.usage` (and the
routing dashboard) shows every decision next to the model that actually served it.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Protocol

from omnigent_talk.gateway import Reply

CLASSIFIER = "gemini_fast"
ROUTES = {"code": "qwen_code", "sql": "qwen_code", "general": "gemini_general"}
# Single-destination services, so the configured model is the served one. The chat API echoes
# the service name instead of the model; the usage table has the real `destination_model`.
SERVICE_MODELS = {"qwen_code": "qwen35-122b-a10b", "gemini_general": "gemini-3-8-flash"}

CLASSIFY_PROMPT = (
    "Classify the user's request. Answer with exactly one word:\n"
    "sql - writing, fixing or explaining a SQL query\n"
    "code - writing, fixing or explaining program code in any other language\n"
    "general - anything else"
)
_LABEL = re.compile(r"\b(sql|code|general)\b", re.IGNORECASE)
_SQL_WORDS = re.compile(r"\b(sql|select|join|group by|query|queries|table|schema)\b", re.I)
_CODE_WORDS = re.compile(
    r"\b(code|function|python|typescript|javascript|rust|bug|script|regex|regular expression|"
    r"class|implement|refactor|unit test)\b",
    re.I,
)


class ChatGateway(Protocol):
    def chat(
        self,
        service: str,
        messages: list[dict[str, str]],
        *,
        tags: dict[str, str] | None = None,
        max_tokens: int = ...,
    ) -> Reply: ...


@dataclass(frozen=True)
class Routed:
    route: str
    classifier: str  # "gemini_fast", or "keywords" when the model's answer was unusable
    service: str
    model: str
    reply: Reply
    latency_ms: int


def parse_label(answer: str) -> str | None:
    match = _LABEL.search(answer)
    return match[1].lower() if match else None


def keyword_route(prompt: str) -> str:
    if _SQL_WORDS.search(prompt):
        return "sql"
    if _CODE_WORDS.search(prompt):
        return "code"
    return "general"


def classify(gateway: ChatGateway, prompt: str, qualify=lambda s: s) -> tuple[str, str]:
    """Return (route, classifier). Falls back to keywords rather than failing the request."""
    try:
        reply = gateway.chat(
            qualify(CLASSIFIER),
            [{"role": "system", "content": CLASSIFY_PROMPT}, {"role": "user", "content": prompt}],
            tags={"demo": "router", "stage": "classify"},
            # Flash Lite thinks before answering; a tiny budget leaves an empty reply.
            max_tokens=256,
        )
    except Exception:
        return keyword_route(prompt), "keywords"
    label = parse_label(reply.text) if reply.status == 200 else None
    if label is None:
        return keyword_route(prompt), "keywords"
    return label, CLASSIFIER


def ask(gateway: ChatGateway, prompt: str, qualify=lambda s: s) -> Routed:
    """Classify, then send the prompt to its route's service tagged with the decision."""
    route, classifier = classify(gateway, prompt, qualify)
    service = ROUTES[route]
    started = time.monotonic()
    reply = gateway.chat(
        qualify(service),
        [{"role": "user", "content": prompt}],
        tags={"demo": "router", "stage": "answer", "route": route, "classifier": classifier},
    )
    latency_ms = round(1000 * (time.monotonic() - started))
    return Routed(route, classifier, service, SERVICE_MODELS[service], reply, latency_ms)
