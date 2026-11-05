"""Managed agent memory (Beta): one store, recall scoped by actor.

`memory_stores.create` provisions the backing Lakebase storage itself, so there is no Lakebase
project to set up. `actor_id` scopes recall but is not access control; isolate with one store
per trust boundary.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Any, Protocol


class Store(Protocol):
    def put(self, *, actor_id: str, path: str, content: str, description: str) -> Any: ...
    def search(self, *, actor_id: str, query: str, limit: int) -> Iterable[Any]: ...


def fact_path(text: str) -> str:
    """Stable path per fact, so remembering the same thing twice overwrites rather than duplicates."""
    return f"/facts/{hashlib.sha256(text.encode()).hexdigest()[:16]}.md"


def remember(store: Store, actor: str, text: str) -> str:
    path = fact_path(text)
    store.put(actor_id=actor, path=path, content=text, description=text[:80])
    return path


def recall(store: Store, actor: str, query: str, limit: int = 3) -> list[str]:
    return [_content(item) for item in store.search(actor_id=actor, query=query, limit=limit)]


def _content(item: Any) -> str:
    # search() returns MemorySearchResult(memory=Memory(content=...), score=...).
    memory = getattr(item, "memory", item)
    if isinstance(memory, dict):
        return str(memory.get("content", memory))
    return str(getattr(memory, "content", memory))


def open_store(profile: str, name: str, *, create: bool = False) -> Store:
    """Find the store by display name (ids are server-assigned), creating it when asked.

    Needs the `memory` extra.
    """
    from databricks.sdk import WorkspaceClient

    try:
        from databricks_agentkit import AgentKitClient  # pyright: ignore[reportMissingImports]
    except ImportError as exc:
        raise SystemExit("Agent memory needs the extra: uv sync --extra memory") from exc
    stores = AgentKitClient(WorkspaceClient(profile=profile)).memory_stores
    for store in stores.list():
        if store.display_name == name:
            return store
    if not create:
        raise SystemExit(f"Memory store {name!r} not found. Run `just memory-create`.")
    return stores.create(name, description="omnigent-talk demo memory")
