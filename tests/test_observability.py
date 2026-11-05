"""Offline portability checks for the Unity Gateway observability assets."""

import json
import re
from pathlib import Path

SQL_DIR = Path("demos/observability")
DASHBOARD_PATH = Path("dashboards/agents.lvdash.json")
THREE_PART_NAME = re.compile(
    r"(?<!:)(?<![\w])([A-Za-z_][\w-]*)\.([A-Za-z_][\w-]*)\.([A-Za-z_][\w-]*)"
)
OBJECT_REFERENCE = re.compile(r"\b(?:FROM|JOIN)\s+([^\s,(;]+)", re.IGNORECASE)


def normalized_sql(sql: str) -> str:
    uncommented = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    return " ".join(uncommented.rstrip(" ;\n").split()).lower()


def test_sql_files_contain_no_catalog_literal():
    paths = sorted(SQL_DIR.glob("*.sql"))
    assert paths
    for path in [*paths, DASHBOARD_PATH]:
        names = THREE_PART_NAME.findall(path.read_text())
        assert all(catalog.lower() == "system" for catalog, _, _ in names), (path, names)


def test_dashboard_json_parses():
    dashboard = json.loads(DASHBOARD_PATH.read_text())
    assert dashboard["datasets"]
    assert dashboard["pages"]
    for dataset in dashboard["datasets"]:
        assert all(parameter.get("displayName") for parameter in dataset.get("parameters", []))


def test_dashboard_queries_reference_only_system_or_parameters():
    dashboard = json.loads(DASHBOARD_PATH.read_text())
    for dataset in dashboard["datasets"]:
        query = "".join(dataset["queryLines"])
        references = OBJECT_REFERENCE.findall(query)
        ctes = set(re.findall(r"(?:WITH|,)\s*([A-Za-z_]\w*)\s+AS\s*\(", query, re.IGNORECASE))
        assert references, dataset["name"]
        assert all(
            reference.lower().startswith("system.")
            or reference.upper().startswith("IDENTIFIER(:")
            or reference in ctes
            for reference in references
        ), (dataset["name"], references)


def test_every_dashboard_dataset_matches_its_sql_file():
    dashboard = json.loads(DASHBOARD_PATH.read_text())
    sources = {f"ds_{path.stem}": path for path in SQL_DIR.glob("*.sql")}
    assert {dataset["name"] for dataset in dashboard["datasets"]} == set(sources)
    for dataset in dashboard["datasets"]:
        query = "".join(dataset["queryLines"])
        assert normalized_sql(query) == normalized_sql(sources[dataset["name"]].read_text())
