---
name: databricks-data-processing
description: Process Databricks data with an explicit workspace, bounded evidence, quality checks, and public-repo-safe outputs.
---

# Databricks data processing

**Intent:** Make data work reproducible, scoped, and safe for a public talk repository.

**When it applies:** Any query, schema inspection, data transformation, or result used by a demo,
test, chart, or slide.

**Evidence:** Identify the `DBX_PROFILE` supplied by `.env.local`, the input table or API, selected
columns, filters, row limits, and the checks that establish schema and result quality. Do not print
credentials or workspace identifiers.

**Decision:** Decide whether the operation is read-only or mutating, whether its sample is bounded,
and whether sensitive or identifying values could enter tracked output.

**Execution:** Use the configured profile explicitly, inspect schema before assumptions, bound
exploration, validate nulls/counts/types relevant to the claim, and keep workspace access behind a
replaceable seam. Commit only generic or redacted results.

**Recovery:** If the profile, data ownership, schema, or safe output boundary is unclear, stop and
inspect or ask. If a result contains identifying values, do not write it to the repository.

**Desired conduct:** The trace shows an explicit profile, a narrow query, a quality check, and a
redacted conclusion.

**Failure modes:** Relying on the CLI default profile, scanning unbounded data, copying raw rows
into docs, claiming quality without checks, or making offline tests require a workspace.
