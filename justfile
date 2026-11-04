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

# REQUESTS_PER_MINUTE: gemini_router's per-user limit. Low (30) trips the 429 demo quickly
# but can stall agy, which makes several calls per turn; raise it for the agy segment.
bundle := 'databricks bundle --profile "$DBX_PROFILE" --var catalog="$CATALOG" --var schema="$SCHEMA" --var requests_per_minute="${REQUESTS_PER_MINUTE:-30}"'
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
    {{bundle}} validate

# Create or update the schema and the model services
gateway-deploy:
    {{bundle}} deploy

# Delete everything the bundle created
gateway-destroy:
    {{bundle}} destroy

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

# Rate limit: burst past the per-user requests-per-minute limit and count the 429s
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
