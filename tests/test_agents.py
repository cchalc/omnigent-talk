import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from omnigent_talk import agents
from omnigent_talk.agents import (
    AGENTS,
    SKILLS,
    agent_env,
    read_env_file,
    request_tags,
    shim_env,
    start_shim,
)

ROOT = Path(__file__).parents[1]
BUNDLES = [ROOT / "agents" / a.bundle for a in AGENTS.values()]


def config(bundle: Path) -> dict:
    raw = yaml.safe_load((bundle / "config.yaml").read_text())
    assert isinstance(raw, dict)
    return raw


def omnigent_python() -> str | None:
    """An interpreter that can import omnigent: this one, or the installed `omni` tool's."""
    if importlib.util.find_spec("omnigent") is not None:
        return sys.executable
    omni = shutil.which("omni")
    if omni is None:
        return None
    shebang = Path(omni).read_text(errors="replace").splitlines()[0]
    return shebang.removeprefix("#!").strip() if shebang.startswith("#!") else None


def test_one_bundle_per_harness_binding_the_intended_harness():
    assert sorted(AGENTS) == ["agy", "claude", "codex", "pi"]
    for agent in AGENTS.values():
        raw = config(ROOT / "agents" / agent.bundle)
        assert raw["spec_version"] == 1
        assert raw["name"] == agent.bundle
        assert raw["executor"]["type"] == "omnigent"
        assert raw["executor"]["config"]["harness"] == agent.executor_harness


def test_agy_pins_a_served_model():
    # Unpinned, agy starts on Gemini 3.1 Pro, which the workspace rejects.
    assert config(ROOT / "agents" / "bakehouse-agy")["executor"]["model"] == "gemini-3.8-flash"


def test_pi_avoids_gemini_on_the_gateway():
    model = config(ROOT / "agents" / "bakehouse-pi")["executor"]["model"]
    assert "gemini" not in model


def test_prompts_are_identical_copies_of_the_shared_prompt():
    source = (ROOT / "agents" / "prompt.md").read_text()
    for bundle in BUNDLES:
        assert config(bundle)["instructions"] == "prompt.md"
        prompt = bundle / "prompt.md"
        # A link would escape the bundle, and Omnigent would read "prompt.md" as the prompt.
        assert not prompt.is_symlink()
        assert prompt.read_text() == source
    assert agents.prompt_drift() == []


def test_every_bundle_links_the_same_three_skills_and_nothing_else():
    for bundle in BUNDLES:
        assert config(bundle)["skills"] == "none"
        links = sorted(p.name for p in (bundle / "skills").iterdir())
        assert links == sorted(SKILLS)
        for skill in SKILLS:
            assert os.readlink(bundle / "skills" / skill) == f"../../../skills/{skill}"


def test_skills_are_exposed_for_agy_workspace_discovery():
    for skill in SKILLS:
        assert os.readlink(ROOT / ".agents" / "skills" / skill) == f"../../skills/{skill}"


def test_bundles_hold_nothing_identifying():
    pattern = re.compile(
        r"dapi[0-9a-f]{32}|\.cloud\.databricks\.com|\.azuredatabricks\.net|"
        r"\.gcp\.databricks\.com|@databricks\.com|[0-9a-f]{16}\b"
    )
    local = read_env_file(ROOT / ".env.local")
    values = [v for k, v in local.items() if k in {"CATALOG", "WAREHOUSE_ID"} and len(v) >= 4]
    files = [p for p in (ROOT / "agents").rglob("*") if p.is_file() and not p.is_symlink()]
    readme = ROOT / "demos" / "bakehouse-agents" / "README.md"
    for path in [*files, readme]:
        text = path.read_text()
        assert not pattern.search(text), path
        assert not any(v in text for v in values), path


@pytest.mark.skipif(omnigent_python() is None, reason="omnigent is not installed")
def test_every_bundle_parses_with_the_installed_omnigent():
    python = omnigent_python()
    assert python is not None
    result = subprocess.run(
        [python, "-I", str(ROOT / "src" / "omnigent_talk" / "agents.py"), "validate"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [line.split()[1].rstrip(":") for line in result.stdout.splitlines()] == [
        a.bundle for a in AGENTS.values()
    ]


INHERITED = {
    "PATH": "/bin",
    "HOME": "/home/presenter",
    "ANTHROPIC_BASE_URL": "https://other.example/ai-gateway/anthropic",
    "OMNIGENT_SERVER": "https://other.example/api/2.0/omnigent",
    "OMNIGENT_CONFIG_HOME": "/elsewhere",
    "CLAUDE_CODE_USE_GATEWAY": "1",
    "CLAUDECODE": "1",
    "UG_PROFILE": "x",
    "DATABRICKS_HOST": "https://other.example",
    "DATABRICKS_TOKEN": "t",
    "DATABRICKS_WORKSPACE_ID": "1",
    "SOME_SECRET": "s",
}
LOCAL = {
    "DBX_PROFILE": "demo",
    "CATALOG": "cat",
    "SCHEMA": "omnigent_talk",
    "SHIM_PORT": "8765",
    "SHIM_KEY": "k",
    "OMNI_SERVER": "https://ws.example/api/2.0/omnigent",
    "OMNIGENT_CONFIG_HOME": "/demo-home",
}


def test_agent_env_is_explicit_pinned_and_tagged():
    env = agent_env(AGENTS["claude"], INHERITED, LOCAL)
    tags = {"demo": "bakehouse", "agent_spec": "bakehouse-claude", "harness": "claude"}
    name, _, value = env.pop("ANTHROPIC_CUSTOM_HEADERS").partition(": ")
    assert name == "Databricks-Ai-Gateway-Request-Tags"
    assert json.loads(value) == tags
    assert json.loads(env.pop("OMNIGENT_CI_CONTEXT")) == {
        "pipeline": "bakehouse",
        "job": "bakehouse-claude",
    }
    # Nothing else from the caller: no gateway URLs, Omnigent routing, host or token.
    assert env == {
        "PATH": "/bin",
        "HOME": "/home/presenter",
        "DBX_PROFILE": "demo",
        "DATABRICKS_CONFIG_PROFILE": "demo",
        "CATALOG": "cat",
        "SCHEMA": "omnigent_talk",
        "OMNIGENT_SERVER": LOCAL["OMNI_SERVER"],
        "OMNIGENT_CONFIG_HOME": "/demo-home",
    }


def test_shim_env_is_minimal_and_carries_this_agents_tags():
    env = shim_env(AGENTS["agy"], INHERITED, LOCAL)
    assert json.loads(env.pop("AI_GATEWAY_REQUEST_TAGS")) == request_tags(AGENTS["agy"])
    assert env == {
        "PATH": "/bin",
        "HOME": "/home/presenter",
        "DBX_PROFILE": "demo",
        "DATABRICKS_CONFIG_PROFILE": "demo",
        "CATALOG": "cat",
        "SCHEMA": "omnigent_talk",
        "SHIM_PORT": "8765",
        "SHIM_KEY": "k",
        "AI_GATEWAY_AGENT_SPEC": "bakehouse-agy",
        "AI_GATEWAY_CODING_AGENT": "antigravity",
        "AI_GATEWAY_CLIENT_SURFACES": "omnigent",
    }


def test_shim_defaults_and_agent_tags_agree_for_agy():
    from omnigent_talk.gemini_shim import attribution_headers

    headers = attribution_headers(shim_env(AGENTS["agy"], {}, LOCAL))
    assert json.loads(headers["Databricks-Ai-Gateway-Request-Tags"]) == {
        "demo": "bakehouse",
        "agent_spec": "bakehouse-agy",
        "harness": "agy",
    }


def test_only_claude_gets_custom_headers():
    for harness, agent in AGENTS.items():
        env = agent_env(agent, {}, LOCAL)
        assert ("ANTHROPIC_CUSTOM_HEADERS" in env) == (harness == "claude")
        assert not any(k.startswith("AI_GATEWAY_") for k in env)


@pytest.mark.parametrize("name", ["DBX_PROFILE", "DATABRICKS_CONFIG_PROFILE"])
def test_a_conflicting_inherited_profile_is_refused(name):
    for build in (agent_env, shim_env):
        with pytest.raises(SystemExit, match=f"{name}=other"):
            build(AGENTS["agy"], {name: "other"}, LOCAL)


def test_an_agreeing_inherited_profile_is_fine():
    inherited = {"DBX_PROFILE": "demo", "DATABRICKS_CONFIG_PROFILE": "demo"}
    assert agent_env(AGENTS["pi"], inherited, LOCAL)["DATABRICKS_CONFIG_PROFILE"] == "demo"


def test_the_profile_must_come_from_env_local():
    with pytest.raises(SystemExit, match=r"DBX_PROFILE is not set in \.env\.local"):
        agent_env(AGENTS["agy"], {"DBX_PROFILE": "demo"}, {})


def test_an_occupied_shim_port_fails_closed():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with pytest.raises(SystemExit, match=f"SHIM_PORT {port} is already in use"):
            start_shim({"SHIM_PORT": str(port), "SHIM_KEY": "k"})


def test_read_env_file_strips_comments_and_quotes(tmp_path):
    path = tmp_path / ".env.local"
    path.write_text('# c\nA=1   # note\nB="two"\n\nC\nD=$HOME/x\n')
    assert read_env_file(path) == {"A": "1", "B": "two", "D": "$HOME/x"}
    assert read_env_file(tmp_path / "missing") == {}
