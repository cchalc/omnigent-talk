#!/usr/bin/env bash
# Pre-commit gate for a public repo: no secrets, no workspace hosts, nothing from .env.local.
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
files() { git ls-files -z --cached --others --exclude-standard -- . ':!scripts/check.sh' ':!docs/superpowers/plans/'; }

# 1. Secret patterns: Databricks PATs, Google API keys, OpenAI keys, OAuth tokens.
if files | xargs -0 grep -nIE '(dapi[0-9a-f]{32}|AIza[0-9A-Za-z_-]{35}|sk-[A-Za-z0-9]{20,}|ya29\.[0-9A-Za-z_-]+|"refresh_token")'; then
  echo "check: possible secret (above)"; fail=1
fi

# 2. Workspace hostnames. Docs links are fine.
if files | xargs -0 grep -nIE '[a-z0-9-]+\.(cloud|gcp)\.databricks\.com|adb-[0-9]+\.[0-9]+\.azuredatabricks\.net|databricksapps\.com' \
   | grep -v 'docs\.databricks\.com'; then
  echo "check: workspace hostname (above); move it to .env.local"; fail=1
fi

# 3. Any value from .env.local (catalog names, URLs, IDs) leaking into a tracked file.
if [ -f .env.local ]; then
  while IFS='=' read -r key value; do
    value="${value%%#*}"; value="${value//[[:space:]]/}"; value="${value//\"/}"
    # Profile, schema and model names are not identifying; hosts, catalogs and IDs are.
    case "$key" in ''|\#*|DBX_PROFILE|SCHEMA|MEMORY_STORE|GEMINI_*|SHIM_PORT) continue ;; esac
    [ ${#value} -ge 8 ] || continue
    [[ "$value" == \$HOME* || "$value" == system.ai.* || "$value" == omnigent* ]] && continue
    if files | xargs -0 grep -nIF -- "$value"; then
      echo "check: value of $key from .env.local found (above)"; fail=1
    fi
  done < .env.local
fi
exit $fail
