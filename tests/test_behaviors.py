from pathlib import Path

import yaml

from omnigent_talk.behavior_eval import BEHAVIORS, build_cases, cases_for, smoke_cases

ROOT = Path(__file__).parents[1]
REQUIRED_DIMENSIONS = (
    "**Intent:**",
    "**Evidence:**",
    "**Decision:**",
    "**Execution:**",
    "**Recovery:**",
    "**Desired conduct:**",
    "**Failure modes:**",
)


def _frontmatter(text: str) -> dict[str, object]:
    _, raw, _ = text.split("---", 2)
    result = yaml.safe_load(raw)
    assert isinstance(result, dict)
    return result


def test_behavior_specs_follow_agentbehavior_structure() -> None:
    for name in BEHAVIORS:
        path = ROOT / ".agents" / "behaviors" / name / "BEHAVIOR.md"
        text = path.read_text()
        metadata = _frontmatter(text)

        assert metadata["name"] == name
        assert isinstance(metadata["description"], str)
        assert 0 < len(metadata["description"]) <= 1024
        for heading in REQUIRED_DIMENSIONS:
            assert heading in text


def test_full_corpus_is_balanced_and_public_safe() -> None:
    cases = build_cases()

    assert len(cases) == 60
    for behavior in BEHAVIORS:
        selected = [case for case in cases if case.behavior == behavior]
        assert len(selected) == 15
        assert {case.expected_conformance for case in selected} == {"yes", "no"}
    assert all("Review sample" in case.trajectory for case in cases)


def test_smoke_corpus_covers_every_behavior_and_both_labels() -> None:
    cases = smoke_cases()

    assert len(cases) == 5
    assert {case.behavior for case in cases} == set(BEHAVIORS)
    assert {case.expected_conformance for case in cases} == {"yes", "no"}


def test_records_use_mlflow_genai_schema() -> None:
    record = cases_for("databricks-data-processing", smoke=False)[0]

    assert set(record) == {"inputs", "outputs", "expectations"}
    assert record["expectations"]["expected_conformance"] in {"yes", "no"}
