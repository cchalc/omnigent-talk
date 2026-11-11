# 00. Prerequisites and the offline gate

Tag: offline

## Goal

Get a clean clone to a green `just check`, with no credentials and no workspace. Then write your
own `.env.local` with names filled in, so chapter 01 can reach a workspace.

When you finish you have the tools below, a `.env.local` you filled in yourself, and `just check`
exiting 0. Nothing in this chapter contacts a Databricks workspace.

## Steps

### 1. Install the tools

Install with Nix, `uv`, or the tool's official installer. Homebrew is forbidden for this project,
including any `brew` line that a script or skill suggests (AGENTS.md, Constraints).

| Tool | Why you need it | How to install |
| :---- | :---- | :---- |
| git | Clone the repo. The leak scan reads `git ls-files` | Nix or the system |
| just | Every recipe. CI runs the same recipes (ci.yml) | `nix profile install nixpkgs#just` |
| uv | Python 3.12 (`.python-version`, `requires-python` in pyproject.toml) and the venv | `nix profile install nixpkgs#uv` |
| jq | `just gateway-show` pipes through it (justfile). Chapter 02 | `nix profile install nixpkgs#jq` |
| Databricks CLI | Bundle recipes, `databricks api`, and `databricks experimental aitools`, which the justfile calls | Nix, or the official installer. Check that `databricks experimental aitools --help` works |
| omni | The Omnigent CLI. Chapter 01 onward | See step 6 |
| agy | Antigravity CLI, for native `omni agy` in chapter 01. Needs agy 1.1.13 or newer (facts, Omnigent table, "agy install") | Official installer. It is a `curl ... | bash` script, so read it before you run it |

npm is not needed by any recipe or by `pyproject.toml`. If you want the `claude` CLI for the native
TUI in chapter 01, install it the way your organization documents.

### 2. Clone the repo

```bash
git clone <repo-url> omnigent-talk
cd omnigent-talk
```

Use the public repo URL. The steps use no absolute paths into your home directory.

### 3. Create `.env.local` and fill in names

```bash
cp .env.example .env.local
```

`.env.local` is gitignored, and `just` loads it for every recipe (`set dotenv-load` in the
justfile). Put your own values in it. Never put them in a tracked file. For this chapter you fill
in nothing, because `just check` runs without `.env.local`. `scripts/check.sh`
reads the file only if it exists, and the tests need no credentials.

These are the names, and the chapter that first needs each one:

| Name | Chapter | What to put in it |
| :---- | :---- | :---- |
| `DBX_PROFILE` | 01 onward | The Databricks CLI profile for your workspace. You choose it. Nothing infers it (AGENTS.md, Databricks workflow) |
| `OMNI_SERVER` | 01 onward | The managed Omnigent server URL, `https://<workspace>/api/2.0/omnigent` |
| `OMNIGENT_CONFIG_HOME` | 01 | An isolated Omnigent config directory for this workspace. Use an absolute path. Never `~/.omnigent` |
| `OMNIGENT_DATA_DIR` | 01 | The same isolated directory. It holds tokens, the host daemon and logs (omni-fevm, "Isolated state") |
| `CATALOG` | 02 onward | The catalog that holds the demo schema. `service_name()` needs it (gateway.py) |
| `SCHEMA` | 02 onward | The demo schema. Defaults to `omnigent_talk` |
| `SHIM_PORT`, `SHIM_KEY` | 02 | A local port and key for `just agy-serve` (cli.py). The key is a random string you make up, not a Databricks token |
| `MEMORY_STORE` | 06 | The managed agent memory store id |
| `WAREHOUSE_ID` | none yet | No recipe reads it today. Leave it empty |
| `BEHAVIOR_EVAL_EXPERIMENT`, `BEHAVIOR_JUDGE_MODEL` | opt-in | Only for `just behavior-eval-setup` and the other behavior-eval recipes. Not used in this story |
| `GEMINI_MODEL`, `GEMINI_FLASH_MODEL` | none yet | Named in talk/prep-reference.md. No recipe reads them yet |
| `DBX_GCP_PROFILE` | none yet | Optional GCP profile from the plan. No recipe reads it yet |

The `scripts/check.sh` leak scan fails if any value in `.env.local` shows up in a tracked file.
Keep values in `.env.local` only, and keep `.env.local` out of commits.

### 4. Install dependencies

```bash
just install
```

This runs `uv sync --all-groups` into `~/.virtualenvs/omnigent-talk`, which the justfile sets with
`UV_PROJECT_ENVIRONMENT`. Recipes keep the repo free of a `.venv`. If you run `uv run` outside `just`, export
`UV_PROJECT_ENVIRONMENT="$HOME/.virtualenvs/omnigent-talk"` first. `uv.lock` is gitignored, so `just install` may
create it locally. Don't commit it (.gitignore, AGENTS.md).

### 5. Run the offline gate

```bash
just check
```

`just check` runs three things in order: `lint` (ruff format check, ruff check, pyright), `test`
(pytest), and `scripts/check.sh` (the public-repo leak scan). Run it before you report any change as
finished (AGENTS.md, Constraints).

### 6. Install Omnigent and record the version

The repo does not record the install command for `omni`. Take it from the Omnigent releases page,
[github.com/omnigent-ai/omnigent/releases](https://github.com/omnigent-ai/omnigent/releases). The
latest published release in facts is v0.20.0 (2026-10-28).

The talk setup ran on `omnigent 0.22.0.dev0`, a development build. Behavior differs from the
release in places. For example, `omni agy --model` is dropped on 0.22.0.dev0 (see chapter 01).
omnigent-ecosystem warns that several installs can disagree,
such as a standalone `omni` and one bundled with a vendor wrapper. Run `omni --version` from the
binary you actually use, and write the result down. The agent recipes call `omnigent`, so check
`omnigent --version` too.

### 7. Know the isolated wrapper (presenter-side, not in this repo)

The presenter runs the workspace demos through a wrapper named `omni-fevm`. It lives in the
presenter's own shell config. Nothing in this repo defines it, and no `just` recipe calls it.
docs/omni-fevm.md explains it. In short, it does three things:

- It runs plain `omni`, not an internal wrapper around it. Internal wrappers pre-configure Claude
  Code and Codex against their own gateway, so changing only the server would leave model traffic
  in the wrong workspace.
- It isolates the whole Omnigent home with `OMNIGENT_CONFIG_HOME` and `OMNIGENT_DATA_DIR`. Your
  daily `~/.omnigent` is never read or written.
- It runs hermetically. It removes inherited `ANTHROPIC_`, `CLAUDE_CODE_`, `OMNIGENT_` and `UG_`
  variables for the child process, so a shell that started inside an agent session can't route
  calls to another workspace.

The wrapper pins its profile with `DATABRICKS_CONFIG_PROFILE`. Make that value the same as your
`DBX_PROFILE`, and point the server at your `OMNI_SERVER`. Chapter 01 writes `omni-fevm` for this wrapper. To replay without the presenter's file, a
function like this does the same three things. It is a sketch, not tested here:

```bash
omni_ws() {
  env $(env | grep -oE '^(ANTHROPIC_|CLAUDE_CODE_|OMNIGENT_|UG_)[A-Z0-9_]*' | sed 's/^/-u /') \
    OMNIGENT_CONFIG_HOME="$OMNIGENT_CONFIG_HOME" OMNIGENT_DATA_DIR="$OMNIGENT_DATA_DIR" \
    OMNIGENT_SERVER="$OMNI_SERVER" DATABRICKS_CONFIG_PROFILE="$DBX_PROFILE" omni "$@"
}
```

Use `omni_ws` wherever chapter 01 says `omni-fevm`. Don't copy the presenter's file.

The rule for this repo is that nothing edits `~/.omnigent` or `~/.gemini`.
Recipes print config for you to apply. agy runs with its own `--gemini_dir` under
`~/.cache/omnigent-talk/agy`, set by the justfile's `AGY_DEMO_HOME` (AGENTS.md,
Constraints). Config in the isolated home changes only through `omni` commands (`setup`, `login`,
`host`), not by hand.

## Verify

Run each check. All of them must pass before you start chapter 01.

```bash
just check
```

Green looks like this. `ruff format --check` and `ruff check` report no problems. pyright reports
0 errors. pytest ends with a `passed` count and no `failed` or `error`. `scripts/check.sh` prints
nothing and exits 0. Don't check the number of tests against a hardcoded count. The count was
80 when this chapter was drafted, but that figure was not re-counted here.

Then confirm the local files stay out of git:

```bash
git check-ignore -v .env.local
git status --short
```

`check-ignore` should name the `.gitignore` rule that matches `.env.local`. `git status --short`
should not list `.env.local` or `uv.lock`.

Last, confirm the Omnigent binary you'll use:

```bash
omni --version
```

It should print a version. Write it down, because chapter 01's expected results were recorded on
`0.22.0.dev0`.

## Fallback

- **No Nix.** Install `uv` and the Databricks CLI with their official installers. For `just`, use
  its official installer. Never use Homebrew.
- **`just` can't be installed.** Stop and report it as unavailable. The recipes are the gate that
  CI runs (AGENTS.md, "Use those rather than the underlying tools"). Don't run the
  underlying commands by hand and call it done.
- **`uv sync` fails on Python.** Run `uv python install 3.12`, then `just install` again.
  `.python-version` pins 3.12.
- **The leak scan finds a value.** Remove the value from the tracked file it was found in. Don't add
  it to an allowlist, and don't commit.
- **`tests/test_story.py` fails on a missing chapter.** That means the story is still being
  written, not that your machine is broken. Run
  `uv run pytest tests/test_story.py -k 00-prereqs` to check this chapter on its own.
