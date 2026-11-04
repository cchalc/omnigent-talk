"""`omnigent-talk <command>`: the entrypoint behind the justfile demo recipes."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from omnigent_talk import gateway, routing


def cmd_probe(a: argparse.Namespace) -> int:
    service = gateway.service_name(a.service)
    reply = gateway.connect().generate(service, a.prompt)
    print(f"{service}: HTTP {reply.status} model={reply.model_version} text={reply.text!r}")
    if reply.error:
        print(f"error: {reply.error}")
    return 0 if reply.status == 200 else 1


def cmd_burst(a: argparse.Namespace) -> int:
    service = gateway.service_name(a.service)
    tags = {"demo": a.tag} if a.tag else None
    replies = routing.send_many(gateway.connect(), service, a.n, parallel=a.parallel, tags=tags)
    print(f"{a.n} requests to {service}:")
    print(routing.format_tally(routing.tally(replies)))
    errors = sorted({r.error for r in replies if r.error})
    for error in errors[:3]:
        print(f"  error: {error}")
    return 0


def cmd_ask(a: argparse.Namespace) -> int:
    from omnigent_talk import router

    r = router.ask(gateway.connect(), a.prompt, gateway.service_name)
    print(f"route={r.route} (by {r.classifier}) -> {r.service} [{r.model}] {r.latency_ms} ms")
    print(r.reply.text if r.reply.status == 200 else f"HTTP {r.reply.status}: {r.reply.error}")
    return 0 if r.reply.status == 200 else 1


def cmd_router_demo(a: argparse.Namespace) -> int:
    from collections import Counter

    from omnigent_talk import router

    prompts = [line.strip() for line in Path(a.file).read_text().splitlines()]
    prompts = [line for line in prompts if line and not line.startswith("#")]
    gw = gateway.connect()
    counts: Counter[str] = Counter()
    failed = 0
    for prompt in prompts:
        r = router.ask(gw, prompt, gateway.service_name)
        ok = r.reply.status == 200
        failed += not ok
        counts[f"{r.route:<7} -> {r.model}"] += 1
        status = "" if ok else f"  HTTP {r.reply.status}"
        flag = "  (keywords)" if r.classifier == "keywords" else ""
        print(f"{prompt[:58]:<58}  {r.route:<7} {r.model:<18} {r.latency_ms:>6} ms{flag}{status}")
    print(f"\n{len(prompts)} prompts:")
    print(routing.format_tally(counts))
    return 1 if failed else 0


def cmd_shim(a: argparse.Namespace) -> int:
    from omnigent_talk import gemini_shim

    host, auth = gateway.workspace_auth(gateway.require_env("DBX_PROFILE"))
    service = gateway.service_name(a.service)
    lite = gateway.service_name(a.lite) if a.lite else None
    argv = list(a.command)
    if a.agy:
        gemini_dir = gemini_shim.agy_gemini_dir(Path(gateway.require_env("AGY_DEMO_HOME")))
        argv = ["agy", f"--gemini_dir={gemini_dir}", *argv]
    if argv:
        return asyncio.run(gemini_shim.wrap(host, service, auth, argv, lite))
    port = int(gateway.require_env("SHIM_PORT"))
    key = gateway.require_env("SHIM_KEY")
    asyncio.run(gemini_shim.serve(host, service, auth, port, key, lite))
    return 0


def cmd_memory(a: argparse.Namespace) -> int:
    from omnigent_talk import memory

    profile = gateway.require_env("DBX_PROFILE")
    store_id = gateway.require_env("MEMORY_STORE")
    store = memory.open_store(profile, store_id, create=a.action == "create")
    if a.action == "create":
        print(f"memory store {store_id} ready")
    elif a.action == "remember":
        print(f"stored {memory.remember(store, a.user, a.text)}")
    else:
        hits = memory.recall(store, a.user, a.text)
        print("\n".join(hits) if hits else f"(nothing recalled for {a.user})")
    return 0


def cmd_sandbox(a: argparse.Namespace) -> int:
    from databricks.sdk import WorkspaceClient

    from omnigent_talk import sandbox

    w = WorkspaceClient(profile=gateway.require_env("DBX_PROFILE"))
    result = sandbox.run(w.sandbox, a.command, timeout_s=a.timeout)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    print(f"[exit {result.exit_code}]")
    return result.exit_code


def cmd_budget(a: argparse.Namespace) -> int:
    import json

    from databricks.sdk import WorkspaceClient

    from omnigent_talk.budget import unity_gateway_budget

    w = WorkspaceClient(profile=gateway.require_env("DBX_PROFILE"))
    config = w.config
    if not (config.account_id and config.workspace_id):
        raise SystemExit("The profile needs account_id and workspace_id set.")
    # A per-user block on a shared workspace would stop everyone, so by default it targets
    # only the caller. --everyone is the deliberate opt-out.
    user = w.current_user.me()
    if not (user.id and user.user_name):
        raise SystemExit("Could not resolve your user from the profile.")
    body = unity_gateway_budget(
        config.account_id,
        int(config.workspace_id),
        per_user_usd=a.per_user_usd,
        only_principal=None if a.everyone else int(user.id),
        block=not a.alert_only,
        # An alert-only budget with no action would do nothing, so it emails you.
        notify=user.user_name if a.alert_only else None,
    )
    print(json.dumps(body, indent=2))
    return 0


def cmd_skills_sync(a: argparse.Namespace) -> int:
    from omnigent_talk import uc_skills

    try:
        api = uc_skills.connect()
        try:
            results = api.sync(Path("skills"), dry_run=a.dry_run)
        finally:
            api.client.close()
    except uc_skills.SkillsApiError as error:
        print(f"skills sync failed: {error}", file=sys.stderr)
        return 1
    for result in results:
        if a.dry_run and result.status != "unchanged":
            action = f"would {result.status.removesuffix('d')}"
        else:
            action = result.status
        print(f"{result.skill_id}: {action} ({result.bundle_name})")
    return 0


def cmd_skills_list(a: argparse.Namespace) -> int:
    from omnigent_talk import uc_skills

    try:
        api = uc_skills.connect()
        try:
            skills = api.list_skills()
        finally:
            api.client.close()
    except uc_skills.SkillsApiError as error:
        print(f"skills list failed: {error}", file=sys.stderr)
        return 1
    for skill in skills:
        name = skill.get("name", "")
        if isinstance(name, str) and name:
            full_name = name.removeprefix("skills/")
            display_name = full_name if a.full else full_name.rsplit(".", 1)[-1]
            status = "finalized" if skill.get("finalize_time") else "draft"
            print(f"{display_name}: {status}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="omnigent-talk")
    sub = p.add_subparsers(dest="cmd", required=True)

    probe = sub.add_parser("probe", help="one native Gemini call to a model service")
    probe.add_argument("service", help="bare id (uses CATALOG.SCHEMA) or full name")
    probe.add_argument("--prompt", default=routing.PROMPT)
    probe.set_defaults(func=cmd_probe)

    burst = sub.add_parser("burst", help="N calls; tally served model and status codes")
    burst.add_argument("service")
    burst.add_argument("-n", type=int, default=20)
    burst.add_argument("--parallel", type=int, default=4)
    burst.add_argument("--tag", help="value for the request tag `demo`")
    burst.set_defaults(func=cmd_burst)

    shim = sub.add_parser(
        "shim",
        help="point agy at a model service: `shim <svc> -- agy` wraps one command; "
        "`shim <svc>` serves on SHIM_PORT with SHIM_KEY",
    )
    shim.add_argument("service")
    shim.add_argument("--lite", help="service for agy's background `*-lite` calls")
    shim.add_argument(
        "--agy", action="store_true", help="run agy (args after --) in an isolated gemini dir"
    )
    shim.add_argument("command", nargs="*", help="after --: the command (or agy args)")
    shim.set_defaults(func=cmd_shim)

    mem = sub.add_parser("memory", help="managed agent memory")
    mem.add_argument("action", choices=["create", "remember", "recall"])
    mem.add_argument("text", nargs="?", default="")
    mem.add_argument("--user", default="presenter")
    mem.set_defaults(func=cmd_memory)

    sbx = sub.add_parser("sandbox", help="run a shell command in a Databricks Sandbox")
    sbx.add_argument("command")
    sbx.add_argument("--timeout", type=int, default=60)
    sbx.set_defaults(func=cmd_sandbox)

    ask = sub.add_parser("ask", help="route one prompt by task: code/sql -> Qwen, else Gemini")
    ask.add_argument("prompt")
    ask.set_defaults(func=cmd_ask)

    demo = sub.add_parser("router-demo", help="route every prompt in a file and tally the routes")
    demo.add_argument("--file", default="demos/routing/prompts.txt")
    demo.set_defaults(func=cmd_router_demo)

    bud = sub.add_parser("budget", help="print an account budget body (apply it yourself)")
    bud.add_argument("--per-user-usd", type=float, default=1.0)
    bud.add_argument("--alert-only", action="store_true", help="email instead of blocking")
    bud.add_argument(
        "--everyone",
        action="store_true",
        help="apply the cap to every user in the workspace, not just you (shared workspaces!)",
    )
    bud.set_defaults(func=cmd_budget)

    skills = sub.add_parser("skills", help="manage portable skills in Unity Catalog (Beta)")
    skill_commands = skills.add_subparsers(dest="skills_cmd", required=True)
    skills_sync = skill_commands.add_parser("sync", help="create or update repo skill bundles")
    skills_sync.add_argument("--dry-run", action="store_true", help="show changes without writes")
    skills_sync.set_defaults(func=cmd_skills_sync)
    skills_list = skill_commands.add_parser("list", help="list skills in CATALOG.omnigent_talk")
    skills_list.add_argument("--full", action="store_true", help="show catalog-qualified names")
    skills_list.set_defaults(func=cmd_skills_list)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
