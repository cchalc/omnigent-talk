"""Offline checks on the bakehouse analytics bundle, so a public-repo leak, a schema the bundle
could destroy, or a Genie payload the API rejects fails before `just analytics-deploy`."""

import json
import re
from collections import defaultdict
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).parents[1]
ANALYTICS = ROOT / "analytics"
BUNDLE = yaml.safe_load((ANALYTICS / "databricks.yml").read_text())
RESOURCE_FILES = sorted((ANALYTICS / "resources").glob("*.yml"))
RESOURCES = {path.name: yaml.safe_load(path.read_text()) for path in RESOURCE_FILES}
SQL_FILES = sorted((ANALYTICS / "sql").glob("*.sql"))
DASHBOARD = json.loads((ANALYTICS / "dashboards" / "bakehouse.lvdash.json").read_text())

HEX_ID = re.compile(r"[0-9a-f]{32}")
HOST = re.compile(
    r"[a-z0-9-]+\.(cloud|gcp)\.databricks\.com|azuredatabricks\.net|databricksapps\.com"
)
# Objects a statement reads or names: FROM/JOIN targets, metric-view sources, Genie identifiers.
OBJECT_REF = re.compile(
    r"(?:\bFROM|\bJOIN|\bTABLE|\bVIEW|source:|identifier:)\s+([`\w${}.-]+)", re.I
)
CATALOG_VAR = "${var.catalog}.${var.schema}."
WIDGET_VERSIONS = {"counter": 2, "table": 2, "bar": 3, "line": 3, "pie": 3}


def _resources(kind: str) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for doc in [BUNDLE, *RESOURCES.values()]:
        found.update((doc.get("resources") or {}).get(kind) or {})
    return found


GENIE = _resources("genie_spaces")["bakehouse_analyst"]
SPACE = GENIE["serialized_space"]


def _analytics_files() -> list[Path]:
    return [p for p in ANALYTICS.rglob("*") if p.is_file() and ".databricks" not in p.parts]


def test_bundle_is_isolated_and_uses_variables():
    assert BUNDLE["bundle"]["name"] == "omnigent_talk_analytics"
    assert BUNDLE["bundle"]["engine"] == "direct"
    assert BUNDLE["include"] == ["resources/*.yml"]
    variables = BUNDLE["variables"]
    assert "default" not in variables["catalog"]
    assert variables["schema"]["default"] == "omnigent_talk"
    assert variables["warehouse_id"]["lookup"] == {"warehouse": "Serverless Starter Warehouse"}
    assert set(RESOURCES) == {
        "bakehouse.dashboard.yml",
        "bakehouse_analyst.genie_space.yml",
        "bakehouse_build.job.yml",
    }


def test_no_schema_resource_so_destroy_cannot_drop_the_shared_schema():
    for doc in [BUNDLE, *RESOURCES.values()]:
        assert "schemas" not in (doc.get("resources") or {})
        assert "catalogs" not in (doc.get("resources") or {})
    assert "resources" not in BUNDLE


@pytest.mark.parametrize("path", _analytics_files(), ids=lambda p: str(p.relative_to(ANALYTICS)))
def test_no_workspace_hosts_or_catalog_literals(path: Path):
    text = path.read_text()
    assert not HOST.search(text), "workspace hostname"
    assert "http://" not in text
    assert "https://" not in text
    for ref in OBJECT_REF.findall(text):
        ref = ref.strip("`").rstrip(".")
        parts = ref.split(".")
        if ref.startswith("${var.catalog}"):
            assert ref.startswith(CATALOG_VAR), ref
        elif "" in parts:
            continue  # prose such as ".env.local", not an object name
        elif len(parts) == 3:
            # The public sample catalog is the only literal catalog allowed.
            assert parts[:2] == ["samples", "bakehouse"], ref
        else:
            assert len(parts) == 1, f"{ref}: name bakehouse objects bare or via ${{var.catalog}}"


@pytest.mark.parametrize("path", SQL_FILES, ids=lambda p: p.name)
def test_sql_files_take_catalog_and_schema_from_job_parameters(path: Path):
    sql = path.read_text()
    assert "USE CATALOG IDENTIFIER({{catalog}});" in sql
    assert "USE SCHEMA IDENTIFIER({{schema}});" in sql
    job = _resources("jobs")["bakehouse_build"]
    params = {p["name"] for p in job["parameters"]}
    assert set(re.findall(r"\{\{(\w+)\}\}", sql)) <= params


def test_job_runs_every_sql_file_in_order_on_the_warehouse():
    job = _resources("jobs")["bakehouse_build"]
    tasks = job["tasks"]
    paths = [Path(t["sql_task"]["file"]["path"]).name for t in tasks]
    assert paths == [p.name for p in SQL_FILES]
    for previous, task in pairwise(tasks):
        assert task["depends_on"] == [{"task_key": previous["task_key"]}]
    assert all(t["sql_task"]["warehouse_id"] == "${var.warehouse_id}" for t in tasks)
    defaults = {p["name"]: p["default"] for p in job["parameters"]}
    assert defaults["catalog"] == "${var.catalog}"
    assert defaults["schema"] == "${var.schema}"


def test_copies_drop_pii_columns():
    sql = (ANALYTICS / "sql" / "01_copy_tables.sql").read_text()
    selects = re.findall(r"AS SELECT(.*?)FROM samples", sql, re.S)
    selected = " ".join(selects)
    for column in ("cardNumber", "first_name", "last_name", "email", "phone", "address", "postal"):
        assert column not in selected, column


def _metric_views() -> dict[str, dict[str, Any]]:
    sql = (ANALYTICS / "sql" / "03_metric_views.sql").read_text()
    bodies = re.findall(
        r"CREATE OR REPLACE VIEW (\w+)\s+WITH METRICS\s+LANGUAGE YAML\s+AS \$\$(.*?)\$\$;",
        sql,
        re.S,
    )
    return {name: {"raw": body, "yaml": yaml.safe_load(body)} for name, body in bodies}


def test_metric_views_define_the_contracted_measures_and_dimensions():
    views = _metric_views()
    assert set(views) == {"bakehouse_sales_metrics", "bakehouse_review_metrics"}
    sales = views["bakehouse_sales_metrics"]["yaml"]
    assert {m["name"] for m in sales["measures"]} >= {
        "Total Revenue",
        "Units Sold",
        "Transaction Count",
        "Unique Customers",
        "Average Transaction Value",
        "Avg Units per Transaction",
        "Revenue per Customer",
    }
    assert {d["name"] for d in sales["dimensions"]} >= {
        "Sales Day",
        "Sales Month",
        "Product",
        "Payment Method",
        "Franchise Name",
        "Franchise City",
        "Franchise Country",
        "Franchise Size",
        "Customer Country",
        "Customer Continent",
        "Supplier Name",
        "Supplier Ingredient",
    }
    supplier = {d["name"]: d["expr"] for d in sales["dimensions"]}
    assert "'Unknown'" in supplier["Supplier Name"]
    assert "'Unknown'" in supplier["Supplier Ingredient"]
    reviews = views["bakehouse_review_metrics"]["yaml"]
    assert {m["name"] for m in reviews["measures"]} >= {
        "Review Count",
        "Avg Review Length",
        "Positive Reviews",
        "Negative Reviews",
        "Mixed Reviews",
    }
    assert {d["name"] for d in reviews["dimensions"]} >= {
        "Franchise Name",
        "Franchise City",
        "Sentiment",
        "Review Day",
    }


@pytest.mark.parametrize("name", ["bakehouse_sales_metrics", "bakehouse_review_metrics"])
def test_metric_view_yaml_survives_the_sql_task_statement_splitter(name: str):
    # The SQL task splits on ; and tracks quotes before it sees $$, so one apostrophe or
    # semicolon in the YAML text breaks the statement.
    raw = _metric_views()[name]["raw"]
    assert ";" not in raw
    assert raw.count("'") % 2 == 0
    assert not re.search(r"\w'\w", raw)


def test_genie_space_invariants():
    assert GENIE["title"] == "omnigent-talk: Bakehouse analyst"
    assert GENIE["warehouse_id"] == "${var.warehouse_id}"
    assert SPACE["version"] == 2
    questions = SPACE["config"]["sample_questions"]
    instructions = SPACE["instructions"]
    texts = instructions["text_instructions"]
    examples = instructions.get("example_question_sqls", [])
    assert len(questions) == 10
    assert len(texts) == 1
    for array in (questions, texts, examples):
        ids = [item["id"] for item in array]
        assert all(HEX_ID.fullmatch(i) for i in ids), ids
        assert ids == sorted(ids)
    instruction_ids = [i["id"] for i in texts + examples]
    assert len(set(instruction_ids)) == len(instruction_ids)
    assert len({q["id"] for q in questions}) == len(questions)
    assert all(isinstance(q["question"], list) for q in questions + examples)
    assert all(isinstance(e["sql"], list) for e in examples)
    assert all(isinstance(t["content"], list) for t in texts)


def test_genie_data_sources_are_the_bakehouse_objects_sorted():
    tables = SPACE["data_sources"]["tables"]
    identifiers = [t["identifier"] for t in tables]
    assert identifiers == sorted(identifiers)
    assert all(i.startswith(CATALOG_VAR) for i in identifiers)
    assert {i.removeprefix(CATALOG_VAR) for i in identifiers} == {
        "bakehouse_sales_metrics",
        "bakehouse_review_metrics",
        "bakehouse_transactions",
        "bakehouse_customers",
        "bakehouse_franchises",
        "bakehouse_suppliers",
        "bakehouse_reviews",
        "bakehouse_review_sentiment",
    }
    for table in tables:
        names = [c["column_name"] for c in table.get("column_configs", [])]
        assert names == sorted(names)


def test_dashboard_resource_fills_in_catalog_and_schema():
    dashboard = _resources("dashboards")["bakehouse"]
    assert dashboard["file_path"] == "../dashboards/bakehouse.lvdash.json"
    assert dashboard["dataset_catalog"] == "${var.catalog}"
    assert dashboard["dataset_schema"] == "${var.schema}"
    assert dashboard["warehouse_id"] == "${var.warehouse_id}"


@pytest.mark.parametrize("dataset", DASHBOARD["datasets"], ids=lambda d: d["name"])
def test_dashboard_datasets_read_only_bare_bakehouse_objects(dataset: dict[str, Any]):
    assert all(line[-1].isspace() for line in dataset["queryLines"])
    sql = "".join(dataset["queryLines"])
    ctes = set(re.findall(r"(\w+) AS \(", sql))
    sources = set(re.findall(r"\b(?:FROM|JOIN)\s+([`\w.]+)", sql, re.I)) - ctes
    assert sources
    assert all(re.fullmatch(r"bakehouse_\w+_metrics", s) for s in sources), sources


def test_dashboard_layout_fills_the_grid():
    assert all(page["layoutVersion"] == "GRID_V1" for page in DASHBOARD["pages"])
    rows: dict[int, int] = defaultdict(int)
    for page in DASHBOARD["pages"]:
        for item in page["layout"]:
            rows[item["position"]["y"]] += item["position"]["width"]
    assert set(rows.values()) == {12}, rows


WIDGETS = [item["widget"] for page in DASHBOARD["pages"] for item in page["layout"]]


@pytest.mark.parametrize("widget", WIDGETS, ids=lambda w: w["name"])
def test_dashboard_widget_versions_and_field_bindings(widget: dict[str, Any]):
    if "multilineTextboxSpec" in widget:
        return
    spec = widget["spec"]
    assert spec["version"] == WIDGET_VERSIONS[spec["widgetType"]]
    datasets = {d["name"]: "".join(d["queryLines"]) for d in DASHBOARD["datasets"]}
    fields = set()
    for query in widget["queries"]:
        sql = datasets[query["query"]["datasetName"]]
        for field in query["query"]["fields"]:
            assert re.search(rf"\b{field['name']}\b", sql), field["name"]
            fields.add(field["name"])
    for key in ("x", "y", "color", "value", "angle"):
        if encoding := spec["encodings"].get(key):
            assert encoding["fieldName"] in fields, encoding["fieldName"]
