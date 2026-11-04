"""The bakehouse agents in `agents/`: one Omnigent bundle per harness, run and validated here.

Omnigent rejects `omni run AGENT --harness <x>-native`, so each bundle binds its harness and
`just agent <harness>` picks the bundle. The bundles share one system prompt and three skills:

- `agents/prompt.md` is the prompt. Omnigent only reads an `instructions:` file that resolves
  inside the bundle, so a link would be read as the literal text "prompt.md". Each bundle keeps
  a copy instead, and `validate` fails if a copy drifts (`sync-prompts` rewrites them).
- `agents/<bundle>/skills/<skill>` are relative links to the repo's `skills/<skill>`. Omnigent
  follows links on parse, and its uploader bundles them as regular files as long as they stay
  inside the Git checkout (`omnigent/cli.py`, `_bundle_files`).

Attribution: every run sets the same request tags (`request_tags`) three ways, because each
harness reaches the gateway differently:
- agy: `run` starts the Gemini shim with `AI_GATEWAY_REQUEST_TAGS`, and it stamps every call
  (`gemini_shim`). A shim already on `SHIM_PORT` is refused, since its tags are unknown.
- Claude Code: Omnigent keeps the `ANTHROPIC_CUSTOM_HEADERS` block it is given and appends its
  own attribution, so the tag header rides along.
- Claude Code, Codex, pi: Omnigent merges `OMNIGENT_CI_CONTEXT` into the request tags it sends
  on gateway routes. It only passes known CI keys, so the demo maps onto two of them:
  `pipeline` = the demo, `job` = the agent. Omnigent also sends `Databricks-Custom-Coding-Agent`
  (claude-code, codex, pi) by itself, which is the harness in usage.

Stdlib only, so `just agents-validate` can run it with the interpreter of the installed
`omni` tool, the one place the real Omnigent spec parser is importable.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT / "agents"
PROMPT = AGENTS_DIR / "prompt.md"
SKILLS = ("bakehouse-analyst", "bakehouse-genie", "gateway-observability")
DEMO = "bakehouse"
# Children get an explicit environment, never the caller's: a parent agent session exports
# routing variables (`ANTHROPIC_BASE_URL`, `OMNIGENT_*`, `DATABRICKS_HOST`, ...) that send a
# child to another workspace's gateway (docs/omni-fevm.md, round 2). Passed through: enough to
# run a CLI and reach the network, and nothing that picks a workspace or a model endpoint.
BASE_ENV_KEYS = (
    "PATH", "HOME", "USER", "LOGNAME", "SHELL", "TERM", "TERM_PROGRAM", "COLORTERM", "LANG",
    "LC_ALL", "LC_CTYPE", "TMPDIR", "SSH_AUTH_SOCK", "EDITOR", "VISUAL", "CODEX_HOME",
    "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR",
    "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE",
)  # fmt: skip
# From `.env.local` (the caller's value only when `.env.local` lacks one): what the skills read.
DEMO_ENV_KEYS = ("CATALOG", "SCHEMA", "WAREHOUSE_ID")
# What the shim reads besides the profile and the demo keys.
SHIM_ENV_KEYS = ("SHIM_PORT", "SHIM_KEY")
# Omnigent settings `.env.local` may carry.
OMNIGENT_HOME_KEYS = ("OMNIGENT_CONFIG_HOME", "OMNIGENT_DATA_DIR")
PROFILE_ENV_KEYS = ("DBX_PROFILE", "DATABRICKS_CONFIG_PROFILE")


@dataclass(frozen=True)
class Agent:
    harness: str  # the `just agent` argument
    bundle: str  # directory under agents/, and the spec's `name`
    executor_harness: str  # what the spec binds, as Omnigent canonicalizes it


AGENTS = {
    a.harness: a
    for a in (
        Agent("agy", "bakehouse-agy", "antigravity-native"),
        Agent("claude", "bakehouse-claude", "claude-native"),
        Agent("codex", "bakehouse-codex", "codex-native"),
        Agent("pi", "bakehouse-pi", "pi"),
    )
}


def request_tags(agent: Agent) -> dict[str, str]:
    """The tags every call from this agent should carry in `system.ai_gateway.usage`.

    `harness` is the short name (`agy`, `claude`, `codex`, `pi`), the shim's default for agy.
    """
    return {"demo": DEMO, "agent_spec": agent.bundle, "harness": agent.harness}


def ci_tags(agent: Agent) -> dict[str, str]:
    """The same tags in Omnigent's CI vocabulary, the only keys it forwards (see module doc)."""
    return {"pipeline": DEMO, "job": agent.bundle}


def sent_tags(agent: Agent) -> str:
    """Which tags reach the gateway for this harness, as far as the code paths show."""
    full, ci = json.dumps(request_tags(agent)), json.dumps(ci_tags(agent))
    if agent.harness == "agy":
        return f"{full} (shim)"
    if agent.harness == "claude":
        return f"{full} merged with {ci}"
    return f"{ci} (Omnigent CI keys; harness = coding_agent)"


def read_env_file(path: Path) -> dict[str, str]:
    """`KEY=value` lines from a dotenv file, comments and quotes stripped."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not key or key.startswith("#"):
            continue
        values[key] = value.split("#", 1)[0].strip().strip('"').strip("'")
    return values


def resolve_profile(environ: Mapping[str, str], local: Mapping[str, str]) -> str:
    """`DBX_PROFILE` from `.env.local`. An inherited profile that disagrees is an error."""
    profile = local.get("DBX_PROFILE", "").strip()
    if not profile:
        raise SystemExit("DBX_PROFILE is not set in .env.local (see .env.example).")
    for name in PROFILE_ENV_KEYS:
        inherited = environ.get(name, "").strip()
        if inherited and inherited != profile:
            raise SystemExit(
                f"{name}={inherited} in this shell, but .env.local has DBX_PROFILE={profile}. "
                f"Not guessing which workspace you meant: unset {name} or fix .env.local."
            )
    return profile


def base_env(environ: Mapping[str, str], local: Mapping[str, str], keys: tuple[str, ...]) -> dict:
    """The pass-through keys, the profile in both spellings, and `keys` from `.env.local`."""
    profile = resolve_profile(environ, local)
    env = {k: environ[k] for k in BASE_ENV_KEYS if environ.get(k)}
    env.update({k: v for k in keys if (v := local.get(k) or environ.get(k, ""))})
    env.update(DBX_PROFILE=profile, DATABRICKS_CONFIG_PROFILE=profile)
    return env


def agent_env(agent: Agent, environ: Mapping[str, str], local: Mapping[str, str]) -> dict[str, str]:
    """The environment for `omni run`: explicit, pinned to `.env.local`, tagged.

    `local` is `.env.local`. It is read directly, because a value inherited from a parent
    session would otherwise shadow it.
    """
    env = base_env(environ, local, DEMO_ENV_KEYS)
    for key in OMNIGENT_HOME_KEYS:
        if local.get(key):
            env[key] = os.path.expanduser(local[key].replace("$HOME", "~"))
    if local.get("OMNI_SERVER"):
        env["OMNIGENT_SERVER"] = local["OMNI_SERVER"]
    encoded = json.dumps(request_tags(agent), separators=(",", ":"))
    env["OMNIGENT_CI_CONTEXT"] = json.dumps(ci_tags(agent), separators=(",", ":"))
    if agent.harness == "claude":
        env["ANTHROPIC_CUSTOM_HEADERS"] = f"Databricks-Ai-Gateway-Request-Tags: {encoded}"
    return env


def shim_env(agent: Agent, environ: Mapping[str, str], local: Mapping[str, str]) -> dict[str, str]:
    """The environment for the Gemini shim: the profile, the services, this agent's tags."""
    env = base_env(environ, local, DEMO_ENV_KEYS + SHIM_ENV_KEYS)
    env["AI_GATEWAY_AGENT_SPEC"] = agent.bundle
    env["AI_GATEWAY_REQUEST_TAGS"] = json.dumps(request_tags(agent), separators=(",", ":"))
    env["AI_GATEWAY_CODING_AGENT"] = "antigravity"
    env["AI_GATEWAY_CLIENT_SURFACES"] = "omnigent"
    return env


# === prompt copies ===


def prompt_drift() -> list[str]:
    """Bundles whose prompt.md differs from agents/prompt.md."""
    source = PROMPT.read_text()
    return [
        a.bundle
        for a in AGENTS.values()
        if not (p := AGENTS_DIR / a.bundle / "prompt.md").exists() or p.read_text() != source
    ]


def cmd_sync_prompts(_: argparse.Namespace) -> int:
    source = PROMPT.read_text()
    for name in prompt_drift():
        (AGENTS_DIR / name / "prompt.md").write_text(source)
        print(f"rewrote agents/{name}/prompt.md")
    return 0


# === validate ===


def cmd_validate(_: argparse.Namespace) -> int:
    """Parse and validate every bundle with the installed Omnigent, offline."""
    try:
        spec_mod = importlib.import_module("omnigent.spec")
        aliases = importlib.import_module("omnigent.harness_aliases")
    except ImportError:
        print("omnigent is not importable here; run this with the `omni` tool's python")
        return 1
    failed = 0
    if drift := prompt_drift():
        fix = "uv run python -m omnigent_talk.agents sync-prompts"
        print(f"FAIL prompt drift in {', '.join(drift)}: run `{fix}`")
        failed += 1
    for agent in AGENTS.values():
        bundle = AGENTS_DIR / agent.bundle
        try:
            spec = spec_mod.load(bundle, expand_env=False)
        except Exception as exc:  # Omnigent raises its own error types
            print(f"FAIL {agent.bundle}: {exc}")
            failed += 1
            continue
        problems = []
        harness = aliases.canonicalize_harness(spec.executor.harness_kind)
        if spec.name != agent.bundle:
            problems.append(f"name is {spec.name!r}")
        if harness != agent.executor_harness:
            problems.append(f"harness is {harness!r}, want {agent.executor_harness!r}")
        if spec.instructions != PROMPT.read_text():
            problems.append("instructions are not agents/prompt.md")
        found = sorted(s.name for s in spec.skills)
        pending = [s for s in SKILLS if not (ROOT / "skills" / s / "SKILL.md").exists()]
        if missing := [s for s in SKILLS if s not in found and s not in pending]:
            problems.append(f"skills not loaded: {', '.join(missing)}")
        if problems:
            print(f"FAIL {agent.bundle}: {'; '.join(problems)}")
            failed += 1
            continue
        model = spec.executor.model or "provider default"
        note = f" (pending, not in skills/ yet: {', '.join(pending)})" if pending else ""
        print(f"ok   {agent.bundle}: {harness}, model={model}, skills={found}{note}")
    return 1 if failed else 0


# === print-config ===


def cmd_print_config(_: argparse.Namespace) -> int:
    port = os.environ.get("SHIM_PORT", "<SHIM_PORT>")
    print(f"""\
# Add to the Omnigent config the demo uses (OMNIGENT_CONFIG_HOME in .env.local). Nothing here
# is written for you.
#
# bakehouse-agy: the agy harness takes its endpoint from the DEFAULT Gemini provider only, so
# make the shim that default (unset `default` on the Databricks Gemini provider first; one
# default per family). `just agent agy` starts the shim on SHIM_PORT with this agent's tags.
providers:
  gemini-shim:
    kind: key
    default: [gemini]
    gemini:
      base_url: http://127.0.0.1:{port}
      api_key: <SHIM_KEY from .env.local>
#
# bakehouse-agy, durable model fix: if agy still opens on Gemini 3.1 Pro (the session model
# can be dropped on the remote-server path), set its default in agy's settings.json, i.e.
# ~/.gemini/antigravity-cli/settings.json (or the isolated --gemini_dir's copy):
#   "model": "Gemini 3.8 Flash (Medium)"
#
# bakehouse-pi: give pi the workspace provider, or it borrows ~/.codex/config.toml:
#   <name>: {{kind: databricks, profile: <DBX_PROFILE>, default: [pi]}}
#
# bakehouse-claude / bakehouse-codex use the default Anthropic / OpenAI providers. On a laptop
# with org-managed Claude Code or Codex settings those win (docs/omni-fevm.md).
#
# What each agent sets for request_tags in system.ai_gateway.usage:""")
    for agent in AGENTS.values():
        print(f"#   {agent.harness:<6} {sent_tags(agent)}")
    return 0


# === run ===


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_shim(env: dict[str, str]) -> subprocess.Popen[bytes]:
    """Serve the Gemini shim with this agent's tags. A port already in use is an error."""
    port = int(env.get("SHIM_PORT") or 0)
    if not (port and env.get("SHIM_KEY")):
        raise SystemExit("SHIM_PORT and SHIM_KEY must be set in .env.local for the agy agent.")
    if port_open(port):
        # Most likely a `just agy-serve` left running, with other tags or none: refuse to run
        # with attribution nobody can vouch for.
        raise SystemExit(f"SHIM_PORT {port} is already in use. Stop that process and retry.")
    # This interpreter already has the project installed, so no `uv` (or its env) is needed.
    argv = [sys.executable, "-m", "omnigent_talk.cli", "shim", "gemini_router"]
    shim = subprocess.Popen([*argv, "--lite", "gemini_fast"], env=env, cwd=ROOT)
    deadline = time.monotonic() + 30
    while not port_open(port):
        if shim.poll() is not None or time.monotonic() > deadline:
            shim.terminate()
            raise SystemExit("the Gemini shim did not start; see its log above")
        time.sleep(0.2)
    return shim


def cmd_run(a: argparse.Namespace) -> int:
    agent = AGENTS[a.harness]
    local = read_env_file(ROOT / ".env.local")
    env = agent_env(agent, os.environ, local)
    shim = start_shim(shim_env(agent, os.environ, local)) if agent.harness == "agy" else None
    try:
        print(f"[agent] {agent.bundle}: tags {json.dumps(request_tags(agent))}", file=sys.stderr)
        return subprocess.call(
            ["omni", "run", str(AGENTS_DIR / agent.bundle), *a.args], env=env, cwd=ROOT
        )
    finally:
        if shim is not None:
            shim.terminate()
            shim.wait(10)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m omnigent_talk.agents")
    sub = p.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="run a bakehouse agent with tagged gateway calls")
    run.add_argument("harness", choices=sorted(AGENTS))
    run.add_argument("args", nargs=argparse.REMAINDER, help="passed to `omni run`")
    run.set_defaults(func=cmd_run)
    sub.add_parser("validate", help="parse every bundle with the installed omnigent").set_defaults(
        func=cmd_validate
    )
    sub.add_parser("print-config", help="print the provider config to add").set_defaults(
        func=cmd_print_config
    )
    sub.add_parser("sync-prompts", help="copy agents/prompt.md into each bundle").set_defaults(
        func=cmd_sync_prompts
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
