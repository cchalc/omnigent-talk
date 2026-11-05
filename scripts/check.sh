#!/usr/bin/env bash
# Pre-commit gate for a public repo: no secrets, no workspace hosts, nothing from .env.local.
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
root="$(pwd -P)"
scan="$(mktemp)"; linktext="$(mktemp -d)"
trap 'rm -rf "$scan" "$linktext"' EXIT

# What gets scanned: every tracked or unignored regular file, plus, for each link, its link text
# and everything it resolves to. Omnigent bundles a link's target, gitignored files included, so
# the target is what would be published. A link must resolve inside the repo (not to the repo
# root or .git); a dangling one is skipped, because there is nothing to publish yet.
while IFS= read -r -d '' f; do
  if [ ! -L "$f" ]; then printf '%s\0' "$f" >> "$scan"; continue; fi
  mkdir -p "$linktext/$(dirname "$f")"
  readlink "$f" > "$linktext/$f@link"
  printf '%s\0' "$linktext/$f@link" >> "$scan"
  if [ ! -e "$f" ]; then echo "check: skipping dangling link $f"; continue; fi
  target="$(realpath "$f")"
  case "$target" in
    "$root"|"$root/.git"|"$root/.git/"*) echo "check: $f links to the repo root or .git"; fail=1; continue ;;
    "$root/"*) ;;
    *) echo "check: $f links outside the repo"; fail=1; continue ;;
  esac
  if [ -n "$(find "$target" -type l -print -quit)" ]; then
    echo "check: $f resolves to a directory holding further links; not scanned"; fail=1; continue
  fi
  find "$target" -type f -print0 >> "$scan"
done < <(git ls-files -z --cached --others --exclude-standard -- . ':!scripts/check.sh' ':!docs/superpowers/plans/')
files() { cat "$scan"; }

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
