"""scripts/check.sh against throwaway Git repos: links are scanned through, not skipped."""

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "check.sh"
# Split so this file doesn't trip the scan it tests.
HOST = "ws1.cloud." + "databricks.com"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")


def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    shutil.copy(SCRIPT, root / "scripts" / "check.sh")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".gitignore").write_text("private/\n")
    (root / "README.md").write_text("clean\n")
    return root


def check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/check.sh"], cwd=root, capture_output=True, text=True, check=False
    )


def test_a_clean_tree_passes(tmp_path):
    assert check(repo(tmp_path)).returncode == 0


def test_a_planted_host_in_a_regular_file_fails(tmp_path):
    root = repo(tmp_path)
    (root / "notes.md").write_text(f"https://{HOST}\n")
    assert check(root).returncode == 1


def test_a_link_to_an_ignored_in_repo_file_with_a_host_fails(tmp_path):
    root = repo(tmp_path)
    (root / "private").mkdir()
    (root / "private" / "host.md").write_text(f"https://{HOST}\n")
    (root / "skills").mkdir()
    (root / "skills" / "leak").symlink_to("../private")
    result = check(root)
    assert result.returncode == 1
    assert "workspace hostname" in result.stdout


def test_a_link_to_a_clean_in_repo_dir_passes(tmp_path):
    root = repo(tmp_path)
    (root / "shared").mkdir()
    (root / "shared" / "SKILL.md").write_text("clean\n")
    (root / "link").symlink_to("shared")
    assert check(root).returncode == 0


def test_a_dangling_link_is_tolerated_and_reported(tmp_path):
    root = repo(tmp_path)
    (root / "pending").symlink_to("../not-there-yet")
    result = check(root)
    assert result.returncode == 0
    assert "skipping dangling link pending" in result.stdout


def test_a_dangling_link_whose_text_names_a_host_fails(tmp_path):
    root = repo(tmp_path)
    (root / "pending").symlink_to(f"/mnt/{HOST}/skill")
    assert check(root).returncode == 1


def test_a_link_outside_the_repo_fails(tmp_path):
    root = repo(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("clean\n")
    (root / "out").symlink_to(outside)
    result = check(root)
    assert result.returncode == 1
    assert "links outside the repo" in result.stdout


def test_a_link_to_the_repo_root_fails(tmp_path):
    root = repo(tmp_path)
    (root / "loop").symlink_to(".")
    assert check(root).returncode == 1
