# Unity Catalog Skills demo

The repo's three portable Agent Skills bundles live in `skills/`. `just skills-sync` creates a
missing UC skill, uploads every bundle file through the Files API, and finalizes it; later content
changes are re-uploaded and finalized in place because UC Skills have no version numbers. Use
`just skills-sync --dry-run` before a rehearsal, `just skills-list` to verify registration, and
`just skills-grant '<principal>'` to grant consumers `READ VOLUME` on all three skills. Consumers
also need the usual `USE CATALOG` and `USE SCHEMA` traversal privileges.

UC object names use underscore IDs under `<CATALOG>.omnigent_talk`; bundle names remain
hyphenated. Unity Gateway Skills are Beta and require the workspace preview **Unity Gateway skills
in Genie**.

## Harness pickup

- Claude Code: copy/link bundles into `.claude/skills` or `.agents/skills`, or use `ug skills add`
  for a registered UC skill.
- Codex: copy/link bundles into `$CODEX_HOME/skills` or the shared `~/.agents/skills` directory.
- agy: place bundles in the workspace's `.agents/skills` directory.
- pi: pass a bundle with `--skill`.
- Unity Gateway/`ug`: its source exposes the undocumented MCP endpoint
  `https://<ws>/ai-gateway/skills/?schema=<c>.<s>`. Treat this as a demo probe, not a supported
  integration contract.

For a portable local demo, copy the same directory unchanged. Do not edit any harness's global
configuration during the talk.

## What to show

In Catalog Explorer, open `<CATALOG>` → `omnigent_talk` and show the three skills, their comments,
bundle names/descriptions, and finalized timestamps. Open one bundle to show `SKILL.md` and any
references. Do not show the browser address bar, workspace identifiers, owners, or principals.
