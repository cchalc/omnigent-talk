"""Exercise a model service's routing: traffic split, rate limit, and fallback.

Each run tallies replies locally, from `modelVersion` and the status code, so the demo shows a
result straight away instead of waiting up to an hour for `system.ai_gateway.usage`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor

from omnigent_talk.gateway import GeminiGateway, Reply

PROMPT = "Reply with one word: pong"


def tally(replies: Iterable[Reply]) -> Counter[str]:
    """Count successes by served model and failures by status code."""
    counts: Counter[str] = Counter()
    for reply in replies:
        if reply.status == 200:
            counts[reply.model_version or "unknown model"] += 1
        else:
            counts[f"HTTP {reply.status}"] += 1
    return counts


def format_tally(counts: Counter[str]) -> str:
    total = sum(counts.values()) or 1
    width = max((len(k) for k in counts), default=0)
    rows = [
        f"  {key:<{width}}  {n:>4}  {100 * n / total:5.1f}%  {'#' * round(40 * n / total)}"
        for key, n in counts.most_common()
    ]
    return "\n".join(rows)


def send_many(
    gateway: GeminiGateway,
    service: str,
    n: int,
    *,
    parallel: int = 4,
    tags: dict[str, str] | None = None,
) -> list[Reply]:
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        return list(pool.map(lambda _: gateway.generate(service, PROMPT, tags=tags), range(n)))
