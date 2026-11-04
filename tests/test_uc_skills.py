import json
import re
from pathlib import Path

import httpx
import yaml

from omnigent_talk import uc_skills

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
