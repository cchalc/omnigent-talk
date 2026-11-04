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


def test_sql_files_contain_no_catalog_literal():
    for path in SQL_DIR.glob("*.sql"):
        names = THREE_PART_NAME.findall(path.read_text())
        assert all(catalog.lower() == "system" for catalog, _, _ in names), (path, names)


def test_dashboard_json_parses():
    dashboard = json.loads(DASHBOARD_PATH.read_text())
    assert dashboard["datasets"]
    assert dashboard["pages"]


def test_dashboard_queries_reference_only_system_or_parameters():
    dashboard = json.loads(DASHBOARD_PATH.read_text())
    for dataset in dashboard["datasets"]:
        query = "".join(dataset["queryLines"])
        references = OBJECT_REFERENCE.findall(query)
        assert references, dataset["name"]
        assert all(
            reference.lower().startswith("system.") or reference.upper().startswith("IDENTIFIER(:")
            for reference in references
        ), (dataset["name"], references)
