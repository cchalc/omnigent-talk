import json
import re
from pathlib import Path

import httpx
import pytest
import yaml

from omnigent_talk import cli, uc_skills

SKILLS_ROOT = Path("skills")
AGENT_SKILL_NAME = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


def _frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text()
    assert text.startswith("---\n")
    _, raw, _ = text.split("---", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_every_skill_has_valid_frontmatter():
    directories = sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir())
    assert [path.name for path in directories] == [
        "bakehouse-analyst",
        "bakehouse-genie",
        "gateway-observability",
    ]
    for directory in directories:
        metadata = _frontmatter(directory / "SKILL.md")
        assert metadata["name"] == directory.name
        assert AGENT_SKILL_NAME.fullmatch(str(metadata["name"]))
        assert str(metadata["description"]).strip()


def test_skills_contain_no_literal_catalog_name():
    qualified_literal = re.compile(r"(?<![$<`])\b[a-z][a-z0-9_-]*\.omnigent_talk\.", re.I)
    for path in SKILLS_ROOT.rglob("*"):
        if path.is_file():
            assert not qualified_literal.search(path.read_text()), path


def _one_bundle(tmp_path: Path) -> tuple[Path, uc_skills.SkillBundle]:
    root = tmp_path / "skills"
    directory = root / "sample-skill"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        "---\nname: sample-skill\ndescription: A test skill.\n---\n\n# Test\n"
    )
    return root, uc_skills.discover_bundles(root)[0]


def _api(handler: httpx.MockTransport) -> uc_skills.SkillsApi:
    return uc_skills.SkillsApi(
        "https://workspace.example",
        "test_catalog",
        lambda: {"Authorization": "Bearer test"},
        httpx.Client(transport=handler),
    )


def test_discovery_skips_dotfiles_dot_directories_and_symlinks(tmp_path):
    root, _ = _one_bundle(tmp_path)
    directory = root / "sample-skill"
    (directory / ".DS_Store").write_bytes(b"metadata")
    hidden = directory / ".cache"
    hidden.mkdir()
    (hidden / "state").write_text("ignored")
    target_file = tmp_path / "outside.md"
    target_file.write_text("outside")
    (directory / "linked.md").symlink_to(target_file)
    target_directory = tmp_path / "outside-directory"
    target_directory.mkdir()
    (target_directory / "reference.md").write_text("outside")
    (directory / "linked-directory").symlink_to(target_directory, target_is_directory=True)

    (bundle,) = uc_skills.discover_bundles(root)

    assert [file.path for file in bundle.files] == ["SKILL.md"]


@pytest.mark.parametrize("path", ["", "/absolute", "C:\\absolute", "../escape", "a/../b", "a//b"])
def test_upload_rejects_unsafe_bundle_paths(path):
    def handle(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected request: {request.url}")

    api = _api(httpx.MockTransport(handle))
    bundle = uc_skills.SkillBundle("sample-skill", "sample_skill", (), "digest")

    with pytest.raises(ValueError, match="Unsafe skill bundle path"):
        api._upload(bundle, uc_skills.BundleFile(path, b"content"))


def test_sync_create_upload_finalize_sequence(tmp_path):
    root, bundle = _one_bundle(tmp_path)
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"skills": []})
        if request.url.path == uc_skills.SKILLS_API:
            return httpx.Response(
                200, json={"name": "skills/test_catalog.omnigent_talk.sample_skill"}
            )
        if request.method == "PUT":
            return httpx.Response(204)
        return httpx.Response(200, json={"etag": "final-etag"})

    api = _api(httpx.MockTransport(handle))
    results = api.sync(root)

    assert [result.status for result in results] == ["created"]
    assert [(request.method, request.url.path) for request in seen] == [
        ("GET", "/api/2.1/unity-catalog/skills"),
        ("POST", "/api/2.1/unity-catalog/skills"),
        ("PUT", "/api/2.0/fs/files/Skills/test_catalog/omnigent_talk/sample_skill/SKILL.md"),
        ("POST", "/api/2.1/unity-catalog/skills/test_catalog.omnigent_talk.sample_skill/finalize"),
    ]
    assert seen[1].url.params["parent"] == "schemas/test_catalog.omnigent_talk"
    assert seen[1].url.params["skill_id"] == "sample_skill"
    assert json.loads(seen[1].content) == {"comment": bundle.comment}
    assert seen[2].url.params["overwrite"] == "true"
    assert seen[2].content == bundle.files[0].content
    assert all(request.headers["Authorization"] == "Bearer test" for request in seen)


def test_existing_finalized_bundle_is_unchanged_and_not_created(tmp_path):
    root, bundle = _one_bundle(tmp_path)
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "skills": [
                    {
                        "name": "skills/test_catalog.omnigent_talk.sample_skill",
                        "bundle_name": "sample-skill",
                        "comment": bundle.comment,
                        "finalize_time": "2026-11-03T00:00:00Z",
                    }
                ]
            },
        )

    results = _api(httpx.MockTransport(handle)).sync(root)

    assert [result.status for result in results] == ["unchanged"]
    assert [(request.method, request.url.path) for request in seen] == [
        ("GET", "/api/2.1/unity-catalog/skills")
    ]


def test_existing_changed_bundle_updates_digest_with_finalize_etag(tmp_path):
    root, bundle = _one_bundle(tmp_path)
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "skills": [
                        {
                            "name": "skills/test_catalog.omnigent_talk.sample_skill",
                            "bundle_name": "sample-skill",
                            "comment": "old digest",
                            "finalize_time": "2026-11-02T00:00:00Z",
                        }
                    ]
                },
            )
        if request.method == "PUT":
            return httpx.Response(204)
        if request.method == "POST":
            return httpx.Response(200, json={"etag": "new+etag=="})
        return httpx.Response(200, json={})

    results = _api(httpx.MockTransport(handle)).sync(root)

    assert [result.status for result in results] == ["updated"]
    assert [request.method for request in seen] == ["GET", "PUT", "POST", "PATCH"]
    assert seen[-1].url.params["update_mask"] == "comment"
    assert seen[-1].url.params["etag"] == "new+etag=="
    assert json.loads(seen[-1].content) == {"comment": bundle.comment}


def test_dry_run_makes_no_writes(tmp_path):
    root, _ = _one_bundle(tmp_path)
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.method == "GET"
        return httpx.Response(200, json={"skills": []})

    results = _api(httpx.MockTransport(handle)).sync(root, dry_run=True)

    assert [result.status for result in results] == ["created"]
    assert [request.method for request in seen] == ["GET"]


class _FakeClient:
    def close(self) -> None:
        pass


class _ListApi:
    client = _FakeClient()

    def list_skills(self) -> list[dict[str, str]]:
        return [
            {
                "name": "skills/test_catalog.omnigent_talk.bakehouse_analyst",
                "finalize_time": "2026-11-03T00:00:00Z",
            }
        ]


def test_skills_list_is_stage_safe_unless_full_is_requested(monkeypatch, capsys):
    monkeypatch.setattr(uc_skills, "connect", _ListApi)

    assert cli.main(["skills", "list"]) == 0
    assert capsys.readouterr().out == "bakehouse_analyst: finalized\n"

    assert cli.main(["skills", "list", "--full"]) == 0
    assert capsys.readouterr().out == "test_catalog.omnigent_talk.bakehouse_analyst: finalized\n"


class _BrokenSyncApi:
    client = _FakeClient()

    def sync(self, skills_root: Path, *, dry_run: bool = False) -> list[uc_skills.SyncResult]:
        raise uc_skills.SkillsApiError("preview unavailable")


def test_skills_sync_api_error_is_one_line_without_traceback(monkeypatch, capsys):
    monkeypatch.setattr(uc_skills, "connect", _BrokenSyncApi)

    assert cli.main(["skills", "sync"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "skills sync failed: preview unavailable\n"
