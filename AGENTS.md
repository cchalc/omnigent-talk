# Agent guide

The build log and live demo environment for a talk on Omnigent as a meta-harness, with Gemini
on Databricks. Conventions follow the FDE project template (`reusable-ip-ai`
`projects/dabs/repo_template`), with a justfile in place of its Makefile. `just check` passes as
it stands. Keep it passing.

## Layout

| Path | Holds |
| :---- | :---- |
| `src/omnigent_talk/` | Demo logic: gateway client, agy shim, routing tallies, memory, sandbox, budget |
| `tests/` | Offline tests. No `__init__.py`, so pytest resolves them by path |
| `databricks.yml`, `resources/` | Bundle for the Unity Gateway schema and model services |
| `analytics/` | Separate bundle for the bakehouse analytics demo: build job, metric views, dashboard, Genie agent. It does not own the schema, so its destroy can't touch the model services |
| `skills/` | Portable agent skills, registered as Unity Catalog skills in the demo schema by `just skills-sync` |
| `agents/` | One Omnigent agent bundle per harness (agy, Claude Code, Codex, pi), sharing one prompt and `skills/` |
| `demos/` | Per-demo READMEs and SQL |
| `docs/` | Plan, fact sheet, setup log |
| `talk/` | Talk content and fallbacks |

Run `just` for the recipes. Use those rather than the underlying tools, because CI calls the
same recipes.

## Working workflow

- Worktrunk owns child worktrees and integration: use `wt switch --create <branch>`, `wt list`,
  and `wt merge`. The project pre-merge hook runs `just check`
- Jujutsu is colocated only in the primary worktree. The installed JJ 0.45.1 cannot initialize
  inside a Git worktree, so `jj status`, `jj diff`, and `jj log` are primary-worktree commands;
  child worktrees use Worktrunk and Git. Do not try to add a second `.jj` store there
- Preserve unrelated dirty files. Never reset, discard, or overwrite another worktree's changes
- Install tools with Nix, `uv`, `uv tool`, npm, or a reviewed official installer. **Homebrew is
  forbidden for this project, without exception**

## Databricks workflow

- The project workspace is the profile the presenter selected in gitignored `.env.local` as
  `DBX_PROFILE`. Never infer, substitute, or hardcode a profile, even when a CLI has a default
- Use `just gateway-validate` before infrastructure changes. State the target and blast radius,
  get confirmation for deploy/destroy, then use the bundle recipes rather than ad hoc API calls
- Workspace-backed behavior evaluation is opt-in: `just behavior-eval-setup`, then
  `just behavior-eval-smoke` or `just behavior-eval`. These commands can create MLflow state and
  spend model credits; they are not part of `just check`

## Agent behaviors

Review recurring conduct against `.agents/behaviors/*/BEHAVIOR.md`. These are evaluation specs,
not executable skills. They cover Databricks data work, infrastructure deployment, sourced talk
content, and rehearsal-ready demos. When preparing slides or demos, read `talk/prep-reference.md`
and treat `docs/research/facts.md` as the claims source of truth.

## Constraints

- **The repo is public.** No workspace hosts, catalog names, workspace or account IDs, emails,
  tokens, or keys in tracked files. They live in `.env.local` (gitignored; names in
  `.env.example`). `scripts/check.sh` scans for these, including every value in `.env.local`
- Tests run with no credentials and no workspace. Anything reaching Databricks goes behind a
  seam a test can replace (`httpx.MockTransport`, fake stores and sandbox APIs)
- Never pick a Databricks profile on the user's behalf; it comes from `DBX_PROFILE`
- Never edit `~/.omnigent`, `~/.omnigent-fevm`, or `~/.gemini`. Recipes print config for the
  presenter to apply. agy runs with an isolated `--gemini_dir`
- Python runs in the out-of-source venv `~/.virtualenvs/omnigent-talk` (the justfile exports
  `UV_PROJECT_ENVIRONMENT`). Never use Homebrew. `uv.lock` stays local because it records the
  internal PyPI mirror
- Underscores for identifiers, hyphens for infrastructure, as in the template
- Line length 100, enforced by Ruff. Run `just format` rather than reformatting by hand
- Every on-stage claim needs a source in `docs/research/facts.md`
- Run `just check` before reporting work finished
