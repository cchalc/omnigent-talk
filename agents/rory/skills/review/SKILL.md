---
name: review
description: Brief the Codex worker for a code review of a branch, PR or file, and present its findings. Use whenever the user asks to review, check or audit code.
---

# review: a code review by the Codex worker

1. Pin the scope before dispatching. Work out the branch and its base (ask if the user did not
   say; this repo's feature branches usually target `cchalcraft/model-services-demo`), or the
   exact files or PR.
2. Send `codex` a message that starts with `REVIEW:` and gives the scope, e.g.
   `REVIEW: git diff cchalcraft/model-services-demo...HEAD on branch cchalcraft/custom-agents`.
   Add any focus the user named (tests, leaks, a file).
3. Present codex's findings as it wrote them, in order: `path:line`, the problem, the fix. Do not
   add findings of your own.
4. If the user wants fixes, that is a separate request: confirm first, then send codex an
   explicit instruction naming the findings to fix.
