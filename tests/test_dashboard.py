"""The AI/BI dashboard skill's checklist, so a broken layout fails before deploy."""

import json
from collections import defaultdict
from pathlib import Path

import pytest

DASHBOARD = json.loads(Path("dashboards/routing.lvdash.json").read_text())
WIDGETS = [item for page in DASHBOARD["pages"] for item in page["layout"]]
VERSIONS = {"counter": 2, "table": 2, "bar": 3, "line": 3, "filter-date-range-picker": 2}


def test_every_page_uses_grid_v1():
    assert all(page["layoutVersion"] == "GRID_V1" for page in DASHBOARD["pages"])


def test_canvas_rows_fill_twelve_columns():
    rows: dict[int, int] = defaultdict(int)
    for page in DASHBOARD["pages"]:
        if page["pageType"] == "PAGE_TYPE_CANVAS":
            for item in page["layout"]:
                rows[item["position"]["y"]] += item["position"]["width"]
    assert set(rows.values()) == {12}, rows


def test_query_lines_end_with_whitespace():
    for dataset in DASHBOARD["datasets"]:
        assert all(line[-1].isspace() for line in dataset["queryLines"]), dataset["name"]


@pytest.mark.parametrize("item", WIDGETS, ids=lambda item: item["widget"]["name"])
def test_widget_versions_and_field_bindings(item):
    widget = item["widget"]
    if "multilineTextboxSpec" in widget:
        return
    spec = widget["spec"]
    assert spec["version"] == VERSIONS[spec["widgetType"]]
    datasets = {d["name"] for d in DASHBOARD["datasets"]}
    queries = {q["name"]: q["query"] for q in widget["queries"]}
    assert all(q["datasetName"] in datasets for q in queries.values())
    fields = {f["name"] for q in queries.values() for f in q["fields"]}
    encodings = spec["encodings"]
    bound = [e for key in ("x", "y", "color", "value", "period") if (e := encodings.get(key))]
    bound += encodings.get("columns", []) + encodings.get("fields", [])
    for encoding in bound:
        assert encoding["fieldName"] in fields, encoding["fieldName"]
        if "queryName" in encoding:
            assert encoding["queryName"] in queries
