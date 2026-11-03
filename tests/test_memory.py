from types import SimpleNamespace

from omnigent_talk import memory


class FakeStore:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], str] = {}

    def put(self, *, actor_id: str, path: str, content: str, description: str) -> None:
        self.rows[(actor_id, path)] = content

    def search(self, *, actor_id: str, query: str, limit: int) -> list[SimpleNamespace]:
        # Shaped like the SDK's MemorySearchResult(memory=Memory(content=...), score=...).
        hits = [c for (a, _), c in self.rows.items() if a == actor_id and query in c]
        return [SimpleNamespace(memory=SimpleNamespace(content=c), score=1.0) for c in hits[:limit]]


def test_same_fact_overwrites_instead_of_duplicating():
    store = FakeStore()
    memory.remember(store, "chris", "prefers Gemini")
    memory.remember(store, "chris", "prefers Gemini")
    assert len(store.rows) == 1


def test_recall_is_scoped_to_the_actor():
    store = FakeStore()
    memory.remember(store, "chris", "prefers Gemini")
    assert memory.recall(store, "chris", "Gemini") == ["prefers Gemini"]
    assert memory.recall(store, "someone-else", "Gemini") == []
