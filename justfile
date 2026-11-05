# omnigent-talk recipes. Settings come from .env.local (gitignored; see .env.example).
# Model services: demos/model-services/README.md.

set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load
set dotenv-filename := ".env.local"
set positional-arguments

# Out-of-source venv, so `uv run` never creates .venv in the repo.
export UV_PROJECT_ENVIRONMENT := env("HOME") / ".virtualenvs/omnigent-talk"
# Isolated agy gemini dir for the shim; ~/.gemini is never touched.
export AGY_DEMO_HOME := env("HOME") / ".cache/omnigent-talk/agy"

bundle := 'databricks bundle --profile "$DBX_PROFILE" --var catalog="$CATALOG" --var schema="$SCHEMA"'
talk := "uv run omnigent-talk"
talk_memory := "uv run --extra memory omnigent-talk"

# Show the recipes
default:
    @just --list

# === DEV ===

# Install dependencies, including dev
install:
    uv sync --all-groups

# Add the agent-memory SDK (Beta) on top of install
install-memory:
    uv sync --all-groups --extra memory

# Check formatting, lint, and types
lint:
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright

# Fix formatting and any auto-fixable lint
format:
    uv run ruff format .
    uv run ruff check --fix .

# Run the tests. Needs no credentials and no workspace
test:
    uv run pytest

# Everything CI runs, plus the public-repo leak scan. Run before every commit
check: lint test
    bash scripts/check.sh

# === UNITY GATEWAY MODEL SERVICES (bundle: databricks.yml, resources/) ===

# Validate the bundle against the workspace
gateway-validate:
    {{bundle}} validate --strict --target dev

# Create or update the schema and the model services
gateway-deploy:
    {{bundle}} deploy --target dev

# Delete everything the bundle created
gateway-destroy:
    {{bundle}} destroy --target dev

# === AGENT BEHAVIOR EVALUATION (opt-in; creates MLflow state and uses judge tokens) ===

# Create/update managed datasets and register the four behavior judges
behavior-eval-setup:
    uv run --extra eval python scripts/behavior_eval.py setup

# Five redacted synthetic trajectories: a cheap pipeline/scorer sanity check
behavior-eval-smoke:
    uv run --extra eval python scripts/behavior_eval.py smoke

# Sixty redacted synthetic trajectories: 15 per project behavior
behavior-eval:
    uv run --extra eval python scripts/behavior_eval.py run

# Show a model service's routing, fallback and rate limits
gateway-show service="gemini_router":
    databricks ai-gateway get-model-service "model-services/$CATALOG.$SCHEMA.$1" --profile "$DBX_PROFILE" -o json \
      | jq '{name: (.name | sub(".*\\."; "")), config, supported_api_types}'

# One native Gemini call (the go/no-go for agy on a custom service)
probe service="gemini_router":
    {{talk}} probe "$1"

# Traffic split: N calls, tallied by the model that served each one
split-demo n="20" service="gemini_router":
    {{talk}} burst "$2" -n "$1" --tag split

# Rate limit: burst calls and count the 429s. No service has a rate_limits block yet,
# so add one to resources/model_services.yml and redeploy before using this
ratelimit-demo n="60" service="gemini_router":
    {{talk}} burst "$2" -n "$1" --parallel 8 --tag ratelimit

# Routing per service from system.ai_gateway.usage (rows land within about an hour)
usage-sql pattern="%":
    databricks experimental aitools tools query demos/routing/usage.sql --param service_pattern="$1" --profile "$DBX_PROFILE"

# Print an account budget body: blocks YOUR Unity Gateway use past the monthly cap.
# Flags: --alert-only (email instead of block), --everyone (all users; not on shared workspaces)
budget per_user_usd="1.00" *flags:
    {{talk}} budget --per-user-usd "$@"

# === ANTIGRAVITY (agy) ON A CUSTOM MODEL SERVICE ===

# Bare agy through the shim: turns -> gemini_router, background lite calls -> gemini_fast.
# Runs in the directory you call it from, which becomes agy's workspace
[no-cd]
agy *args:
    uv run --project "{{justfile_directory()}}" omnigent-talk shim gemini_router --lite gemini_fast --agy -- "$@"

# Long-running shim on SHIM_PORT for `omni agy` (pair with `just agy-provider`)
agy-serve service="gemini_router" lite="gemini_fast":
    {{talk}} shim "$1" --lite "$2"

# Print the Omnigent provider entry that points agy at `just agy-serve`. Add it yourself
agy-provider:
    @printf 'providers:\n  gemini-shim:\n    kind: key\n    default: [gemini]\n    gemini:\n      base_url: http://127.0.0.1:%s\n      api_key: <SHIM_KEY from .env.local>\n' "$SHIM_PORT"
    @echo "# Only one provider may be the gemini default: unset it on the other one first."

# === BAKEHOUSE AGENTS (agents/) ===

# One bakehouse agent: agy (shim -> gemini_router), claude, codex or pi. Tags its gateway calls
agent harness="agy" *args:
    uv run python -m omnigent_talk.agents run "$@"

# Parse and validate every agents/ bundle with the installed omnigent (offline)
agents-validate:
    "$(sed -n '1s/^#!//p' "$(command -v omni)")" -I src/omnigent_talk/agents.py validate

# Print the provider config the agents need, and their tags. Add it yourself
agents-print-config:
    @uv run python -m omnigent_talk.agents print-config

# === AGENT MEMORY (managed, Lakebase-backed, Beta) ===

# Create the memory store named by MEMORY_STORE (idempotent)
memory-create:
    {{talk_memory}} memory create

# Store a fact for a user
remember text user="presenter":
    {{talk_memory}} memory remember "$1" --user "$2"

# Recall facts for a user. A different user recalls nothing
recall query user="presenter":
    {{talk_memory}} memory recall "$1" --user "$2"

# === DATABRICKS SANDBOX (Beta) ===

# Run a shell command in a throwaway sandbox, then delete it
sandbox-run cmd:
    {{talk}} sandbox "$1"

# Show the sandbox has its own identity and filesystem
sandbox-isolation:
    {{talk}} sandbox 'whoami; echo "home=$HOME"; ls -a ~ | head'

# === TASK ROUTING (code/SQL -> Qwen, everything else -> Gemini 3.8 Flash) ===

# Route one prompt: a gemini_fast call classifies it, then it goes to qwen_code or gemini_general
ask prompt:
    {{talk}} ask "$1"

# Route every prompt in demos/routing/prompts.txt and tally the decisions
router-demo:
    {{talk}} router-demo

# === ROUTING METRICS ===

# Print the routing dashboard's URL (deployed with `just gateway-deploy`)
dashboard-url:
    {{bundle}} summary -o json | jq -r '.resources.dashboards.routing.url'

# The dashboard's routing breakdown, in the terminal
routing-metrics:
    databricks experimental aitools tools query demos/routing/metrics.sql --profile "$DBX_PROFILE"
