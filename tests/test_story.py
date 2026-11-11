"""The replay story under docs/story/: every chapter is complete and names only real recipes."""

import re
from pathlib import Path

import pytest

STORY = Path("docs/story")
CHAPTERS = sorted(STORY.glob("[0-9][0-9]-*.md"))
JUST_RECIPES = set(
    re.findall(r"^([a-z][\w-]*)(?:\s[^:\n]*)?:(?!=)", Path("justfile").read_text(), re.M)
)
HEADINGS = ("## Goal", "## Steps", "## Verify", "## Fallback")
TAG = re.compile(r"^Tag: (offline|workspace)$", re.M)
EXPECTED = {
    "00-prereqs",
    "01-harnesses",
    "02-gateway-model-services",
    "03-routing",
    "04-custom-agents",
    "05-smart-routing",
    "06-policies-memory-sandbox",
    "07-software-factory",
}


def test_the_story_has_every_planned_chapter():
    assert {chapter.stem for chapter in CHAPTERS} == EXPECTED


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda path: path.stem)
def test_chapter_has_required_headings_and_one_tag(chapter):
    text = chapter.read_text()
    for heading in HEADINGS:
        assert heading in text, f"{chapter.name} is missing {heading}"
    assert len(TAG.findall(text)) == 1, f"{chapter.name} needs exactly one 'Tag:' line"


@pytest.mark.parametrize("chapter", [*CHAPTERS, STORY / "README.md"], ids=lambda path: path.stem)
def test_every_just_recipe_named_exists(chapter):
    named = set(re.findall(r"`just ([a-z][\w-]*)", chapter.read_text()))
    assert named <= JUST_RECIPES, f"{chapter.name} names unknown recipes: {named - JUST_RECIPES}"


@pytest.mark.parametrize("chapter", [*CHAPTERS, STORY / "README.md"], ids=lambda path: path.stem)
def test_relative_links_resolve(chapter):
    for target in re.findall(r"\]\((?!https?:|#)([^)#]+)", chapter.read_text()):
        assert (chapter.parent / target).exists(), f"{chapter.name} links to missing {target}"


def test_readme_indexes_every_chapter():
    readme = (STORY / "README.md").read_text()
    for chapter in CHAPTERS:
        assert chapter.name in readme, f"README does not index {chapter.name}"
