"""The `rory` bundle's wiring and the renderer that fills its placeholders before upload."""

import re
from pathlib import Path

import pytest
import yaml

from omnigent_talk import agent_bundle

RORY = Path("agents/rory")
CONFIG = yaml.safe_load((RORY / "config.yaml").read_text())
WORKERS = {
    name: yaml.safe_load((RORY / "agents" / name / "config.yaml").read_text())
    for name in CONFIG["tools"]["agents"]
}
JUST_RECIPES = set(
    re.findall(r"^([a-z][\w-]*)(?:\s[^:\n]*)?:(?!=)", Path("justfile").read_text(), re.M)
)


def harness(spec):
    return spec["executor"]["config"]["harness"]


def test_every_declared_worker_has_a_config_with_its_name():
    assert set(WORKERS) == {"codex", "qwen"}
    for name, spec in WORKERS.items():
        assert spec["name"] == name


def test_harnesses():
    assert harness(CONFIG) == "claude-sdk"
    assert harness(WORKERS["codex"]) == "codex"
    assert harness(WORKERS["qwen"]) == "openai-agents"


def test_qwen_worker_targets_the_code_router_service():
    qwen = WORKERS["qwen"]["executor"]
    assert qwen["model"] == "${CATALOG}.${SCHEMA}.code_router"
    assert qwen["auth"] == {"type": "databricks", "profile": "${DBX_PROFILE}"}
    # The gateway service speaks chat completions, not the Responses API.
    assert qwen["config"]["use_responses"] is False


def test_router_asks_before_relaying_an_approval_and_bounds_dispatches():
    policies = CONFIG["guardrails"]["policies"]
    relay = policies["approval_relay"]["function"]
    assert relay["path"] == "omnigent.policies.builtins.cel.cel_policy"
    expression = relay["arguments"]["expression"]
    assert '"sys_session_send"' in expression
    assert '.contains("APPROVED")' in expression
    assert '"ASK"' in expression
    assert policies["spawn_bounds"]["function"]["arguments"]["max_dispatches_per_turn"] <= 3


def test_deploys_are_two_phase_and_only_through_just_recipes():
    assert "DEPLOY APPROVED" in CONFIG["prompt"]
    codex = WORKERS["codex"]["prompt"]
    assert "Do NOT deploy" in codex
    for recipe in re.findall(r"`just ([\w-]+)", codex):
        assert recipe in JUST_RECIPES, recipe
    # Headless, so it must never auto-approve or destroy; both stay with the presenter.
    assert "never add `--auto-approve`" in codex
    assert "Never run `just gateway-destroy`" in codex
    assert "DESTROY APPROVED" not in codex + CONFIG["prompt"]


def test_skills_are_named_after_their_directories():
    for skill in (RORY / "skills").glob("*/SKILL.md"):
        front = yaml.safe_load(skill.read_text().split("---")[1])
        assert front["name"] == skill.parent.name


def test_bundle_has_no_workspace_values():
    for path in RORY.rglob("*"):
        if path.is_file():
            text = path.read_text()
            assert ".databricks.com" not in text, path
            refs = set(re.findall(r"\$\{(\w+)\}", text))
            assert refs <= set(agent_bundle.PLACEHOLDERS), (path, refs)


ENV = {"CATALOG": "cat", "SCHEMA": "sch", "DBX_PROFILE": "prof"}


def test_render_text_fills_known_placeholders_and_keeps_others():
    text = "model: ${CATALOG}.${SCHEMA}.code_router\nprofile: ${DBX_PROFILE}\nkey: ${API_KEY}\n"
    assert agent_bundle.render_text(text, ENV) == (
        "model: cat.sch.code_router\nprofile: prof\nkey: ${API_KEY}\n"
    )


def test_render_text_refuses_a_missing_value():
    with pytest.raises(KeyError, match="CATALOG"):
        agent_bundle.render_text("${CATALOG}", {"SCHEMA": "sch"})


def test_render_copies_the_bundle_and_replaces_stale_output(tmp_path):
    dest = tmp_path / "rory"
    (dest / "agents" / "gone").mkdir(parents=True)
    rendered = agent_bundle.render(RORY, dest, ENV)
    assert not (dest / "agents" / "gone").exists()
    assert Path("agents/qwen/config.yaml") in rendered
    qwen = yaml.safe_load((dest / "agents/qwen/config.yaml").read_text())
    assert qwen["executor"]["model"] == "cat.sch.code_router"
    assert (dest / "skills/deploy/SKILL.md").is_file()


def test_render_refuses_a_dest_that_overlaps_the_source(tmp_path):
    (tmp_path / "config.yaml").write_text("name: x\n")
    for dest in (tmp_path, tmp_path / "out", tmp_path.parent):
        with pytest.raises(ValueError, match="overlaps"):
            agent_bundle.render(tmp_path, dest, ENV)
    assert (tmp_path / "config.yaml").is_file()


@pytest.mark.parametrize("name", ["../agents/rory", "rory/agents", "", "Rory", ".omnigent"])
def test_bundle_paths_take_only_a_slug(name):
    with pytest.raises(ValueError):
        agent_bundle.bundle_paths(name)


def test_bundle_paths_for_rory():
    assert agent_bundle.bundle_paths("rory") == (Path("agents/rory"), Path(".omnigent/rory"))


def test_render_rejects_a_directory_without_config(tmp_path):
    with pytest.raises(FileNotFoundError):
        agent_bundle.render(tmp_path, tmp_path / "out", ENV)
