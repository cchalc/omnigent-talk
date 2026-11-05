"""Render an Omnigent agent bundle from the repo into a local, uploadable copy.

The repo is public, so tracked bundles under `agents/` keep `${CATALOG}`, `${SCHEMA}` and
`${DBX_PROFILE}` as placeholders. `omnigent agent add` only expands `${VAR}` in a few fields
(connection, api_key auth, MCP URLs), not `executor.model` or `auth.profile`, so the copy it
uploads is rendered here first, into a gitignored directory.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Mapping
from pathlib import Path

PLACEHOLDERS = ("CATALOG", "SCHEMA", "DBX_PROFILE")
_REF = re.compile(r"\$\{(" + "|".join(PLACEHOLDERS) + r")\}")
_NAME = re.compile(r"[a-z][a-z0-9_-]*")


def bundle_paths(name: str) -> tuple[Path, Path]:
    """The tracked bundle `agents/<name>` and its rendered copy `.omnigent/<name>`."""
    if not _NAME.fullmatch(name):
        raise ValueError(f"agent name {name!r} must be a single lowercase slug, like 'rory'")
    return Path("agents") / name, Path(".omnigent") / name


def render_text(text: str, env: Mapping[str, str]) -> str:
    """Replace the known placeholders. Any other `${VAR}` is left for omnigent to expand."""

    def value(match: re.Match[str]) -> str:
        name = match[1]
        if not env.get(name):
            raise KeyError(f"{name} is not set (put it in .env.local)")
        return env[name]

    return _REF.sub(value, text)


def render(src: Path, dest: Path, env: Mapping[str, str]) -> list[Path]:
    """Copy bundle `src` to `dest`, rendering placeholders in YAML and Markdown files.

    `dest` is replaced, so a renamed or deleted file in the repo never lingers in the upload.
    Returns the rendered files, relative to `dest`.
    """
    if not (src / "config.yaml").is_file():
        raise FileNotFoundError(f"{src} has no config.yaml")
    s, d = src.resolve(), dest.resolve()
    if d.is_relative_to(s) or s.is_relative_to(d):
        # `dest` is wiped first, so an overlap would delete the bundle being rendered.
        raise ValueError(f"{dest} overlaps {src}")
    if dest.exists():
        shutil.rmtree(dest)
    rendered: list[Path] = []
    for path in sorted(src.rglob("*")):
        target = dest / path.relative_to(src)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in {".yaml", ".yml", ".md"}:
            text = path.read_text()
            out = render_text(text, env)
            target.write_text(out)
            if out != text:
                rendered.append(target.relative_to(dest))
        else:
            shutil.copy2(path, target)
    return rendered
