---
name: rehearsal-ready-talk-demos
description: Prepare deterministic, timed, screen-safe talk demos with verified outputs and rehearsed fallbacks.
---

# Rehearsal-ready talk demos

**Intent:** Make every live segment understandable and recoverable under conference conditions.

**When it applies:** Demo scripts, runbook steps, live workspace views, recordings, and dry runs.

**Evidence:** Identify the exact command or keystrokes, prerequisites, expected visible output,
time budget, fallback asset, and switch-to-fallback threshold.

**Decision:** A demo is stage-ready only when its happy path is repeatable, its failure path is
rehearsed, and the visible screen contains no secret or workspace-identifying information.

**Execution:** Use project recipes, run preflight, prepare terminals/tabs, redact recordings, set a
numeric fallback threshold, time the segment, and record failures and overruns in `lessons.md`.

**Recovery:** Switch to the named fallback when the threshold expires; narrate the expected result
without troubleshooting live. Update the runbook and repeat the dry run after a failure.

**Desired conduct:** The trace contains a verified happy path, expected result, timebox, fallback,
screen-hygiene check, and rehearsal outcome.

**Failure modes:** Improvising commands, waiting indefinitely on Wi-Fi or eventual consistency,
showing credentials/hosts, recording no fallback, or declaring readiness without a timed dry run.
