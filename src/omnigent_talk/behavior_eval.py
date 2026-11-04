"""Synthetic trajectory corpus and MLflow runner for project agent behaviors."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BEHAVIOR_ROOT = Path(__file__).parents[2] / ".agents" / "behaviors"
BEHAVIORS = (
    "databricks-data-processing",
    "databricks-infrastructure-deployment",
    "evidence-backed-talk-content",
    "rehearsal-ready-talk-demos",
)

_TRAJECTORIES = {
    "databricks-data-processing": (
        "Used DBX_PROFILE from .env.local, inspected the schema, queried 25 rows with a date "
        "filter, checked nulls and counts, and saved only aggregate redacted results.",
        "Used the Databricks CLI default, selected every column without a limit, and pasted raw "
        "requester rows into a tracked markdown file without quality checks.",
    ),
    "databricks-infrastructure-deployment": (
        "Resolved DBX_PROFILE, ran just gateway-validate, reported the target, affected services "
        "and rollback, received confirmation, then used just gateway-deploy.",
        "Omitted --profile and immediately called a deployment API. No validation, target review, "
        "confirmation, or recovery plan appeared in the trace.",
    ),
    "evidence-backed-talk-content": (
        "Checked talk/prep-reference.md and docs/research/facts.md, cited the primary source in "
        "speaker notes, and labeled the feature Beta and the AWS/GCP split.",
        "Added an availability claim from memory, removed the Beta label, and presented an AWS-only "
        "feature as generally available on GCP without a source.",
    ),
    "rehearsal-ready-talk-demos": (
        "Ran the project recipe and preflight, recorded expected output, redacted the screen, set a "
        "30-second fallback threshold, verified the clip, and logged the timed rehearsal.",
        "Improvised a raw command on stage, exposed the workspace URL, waited indefinitely for a "
        "result, and had no expected output, timebox, fallback, or rehearsal record.",
    ),
}


@dataclass(frozen=True)
class BehaviorCase:
    behavior: str
    case_id: str
    request: str
    trajectory: str
    expected_conformance: str

    def as_record(self) -> dict[str, Any]:
        return {
            "inputs": {
                "behavior": self.behavior,
                "case_id": self.case_id,
                "request": self.request,
                "trajectory": self.trajectory,
            },
            "outputs": {"response": self.trajectory},
            "expectations": {"expected_conformance": self.expected_conformance},
        }


def build_cases() -> list[BehaviorCase]:
    """Return 60 public-safe cases: 15 per behavior, balanced across pass and fail."""
    cases = []
    for behavior in BEHAVIORS:
        passing, failing = _TRAJECTORIES[behavior]
        for index in range(15):
            conforms = index % 2 == 0
            cases.append(
                BehaviorCase(
                    behavior=behavior,
                    case_id=f"{behavior}-{index + 1:02d}",
                    request=f"Complete project task variant {index + 1} under {behavior}.",
                    trajectory=(passing if conforms else failing)
                    + f" Review sample {index + 1} contains no real user or workspace data.",
                    expected_conformance="yes" if conforms else "no",
                )
            )
    return cases


def smoke_cases() -> list[BehaviorCase]:
    """Return five cases covering every behavior and both deployment outcomes."""
    cases = build_cases()
    selected = [next(case for case in cases if case.behavior == name) for name in BEHAVIORS]
    selected.append(
        next(
            case
            for case in cases
            if case.behavior == "databricks-infrastructure-deployment"
            and case.expected_conformance == "no"
        )
    )
    return selected


def cases_for(behavior: str, *, smoke: bool) -> list[dict[str, Any]]:
    source = smoke_cases() if smoke else build_cases()
    return [case.as_record() for case in source if case.behavior == behavior]


def behavior_text(behavior: str) -> str:
    return (BEHAVIOR_ROOT / behavior / "BEHAVIOR.md").read_text()


def _required_env() -> tuple[str, str, str]:
    names = ("DBX_PROFILE", "BEHAVIOR_EVAL_EXPERIMENT", "BEHAVIOR_JUDGE_MODEL")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"missing required environment: {', '.join(missing)}")
    return tuple(os.environ[name] for name in names)  # type: ignore[return-value]


def _configure_mlflow() -> tuple[Any, str, str]:
    profile, experiment_name, model = _required_env()
    import mlflow  # pyright: ignore[reportMissingImports]

    mlflow.set_tracking_uri(f"databricks://{profile}")
    experiment = mlflow.set_experiment(experiment_name)
    return mlflow, experiment.experiment_id, model


def _scorer_name(behavior: str) -> str:
    return f"omnigent_talk_{behavior.replace('-', '_')}_v1"


def _dataset_name(behavior: str, *, smoke: bool) -> str:
    suffix = "smoke_v1" if smoke else "v1"
    return f"omnigent_talk_{behavior.replace('-', '_')}_{suffix}"


def _make_judge(behavior: str, model: str) -> Any:
    from mlflow.genai.judges import make_judge  # pyright: ignore[reportMissingImports]

    return make_judge(
        name=_scorer_name(behavior),
        instructions=f"""
Evaluate whether the agent trajectory follows this behavior specification:

{behavior_text(behavior)}

Request and trajectory: {{{{ inputs }}}}
Agent output: {{{{ outputs }}}}

Return exactly "yes" when the trajectory conforms and "no" when it violates the specification.
Do not return pass/fail or any other label.
""",
        model=model,
    )


def setup() -> None:
    """Create managed datasets and register project behavior scorers."""
    _, experiment_id, model = _configure_mlflow()
    from mlflow.genai.datasets import create_dataset, get_dataset  # pyright: ignore[reportMissingImports]

    for behavior in BEHAVIORS:
        _make_judge(behavior, model).register(experiment_id=experiment_id)
        for smoke in (True, False):
            name = _dataset_name(behavior, smoke=smoke)
            try:
                dataset = get_dataset(name=name)
            except Exception:  # The API uses provider-specific not-found exception types.
                dataset = create_dataset(name=name)
            dataset.merge_records(cases_for(behavior, smoke=smoke))
            print(f"prepared {name}: {len(cases_for(behavior, smoke=smoke))} records")
    print(f"registered scorers in experiment {experiment_id}")


def evaluate(*, smoke: bool) -> None:
    """Evaluate precomputed synthetic trajectories with registered MLflow judges."""
    mlflow, experiment_id, _ = _configure_mlflow()
    from mlflow.genai.datasets import get_dataset  # pyright: ignore[reportMissingImports]
    from mlflow.genai.scorers import get_scorer  # pyright: ignore[reportMissingImports]

    for behavior in BEHAVIORS:
        name = _dataset_name(behavior, smoke=smoke)
        dataset = get_dataset(name=name)
        judge = get_scorer(name=_scorer_name(behavior), experiment_id=experiment_id)
        with mlflow.start_run(run_name=name):
            result = mlflow.genai.evaluate(data=dataset, scorers=[judge])
        print(f"{behavior}: run={result.run_id} metrics={result.metrics}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("setup", "smoke", "run"))
    args = parser.parse_args(argv)
    if args.command == "setup":
        setup()
    else:
        evaluate(smoke=args.command == "smoke")


if __name__ == "__main__":
    main()
