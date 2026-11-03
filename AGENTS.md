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
| `demos/` | Per-demo READMEs and SQL |
| `docs/` | Plan, fact sheet, setup log |
| `talk/` | Talk content and fallbacks |

Run `just` for the recipes. Use those rather than the underlying tools, because CI calls the
same recipes.

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
  `UV_PROJECT_ENVIRONMENT`). Never Homebrew. `uv.lock` stays local because it records the
  internal PyPI mirror
- Underscores for identifiers, hyphens for infrastructure, as in the template
- Line length 100, enforced by Ruff. Run `just format` rather than reformatting by hand
- Every on-stage claim needs a source in `docs/research/facts.md`
- Run `just check` before reporting work finished
