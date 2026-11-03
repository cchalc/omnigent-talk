# Presentation prep reference

What to say, what to show, and what not to claim. Read this before writing slides or speaker notes (plan Task 14). Every claim links back to a row in `docs/research/facts.md`.

## Gemini models: 3.8 Flash live, Argon mentioned

**Decision (2026-11-02):** every live demo runs on **Gemini 3.8 Flash**. **Gemini 4 Argon** gets one release-note slide and is never demoed. See plan decision 11.

**Why:** the demo workspace (FEVM, profile `fevm-cjc`) serves Gemini 3.1 Flash-Lite, 3.5, 3.7 and 3.8 Flash, but not Argon (probed 2026-11-02). We demo what we can run live, and only mention the rest.

| Use | Model name | Where it appears |
|---|---|---|
| Live main model | `system.ai.gemini-3-8-flash` | `omni agy --model gemini-3.8-flash`, `GEMINI_MODEL`, smoke test, policy demo |
| Cheap contrast model | `system.ai.gemini-3-1-flash-lite` | `GEMINI_FLASH_MODEL`, routing / cost contrast |
| Mentioned only | Gemini 4 Argon | one slide in segment 5 |

**Argon slide content:**
- Headline: *Gemini 4 Argon is on Unity Gateway.*
- Quote: "Google Gemini 4 Argon is now available on Unity Gateway. You can access this model using Foundation Model APIs." (release notes, **Oct 13 2026**)
- Source / QR: https://docs.databricks.com/gcp/en/release-notes/unity-gateway/#google-gemini-4-argon-is-now-available-on-unity-gateway
- Point to make: the newest Gemini models land on Unity Gateway as they ship, behind the same governance (UC permissions, rate limits, budgets, usage tracking) used for the 3.8 Flash demo. Switching to Argon is a model-name change, not a new integration.

**Say:**
- "Live today you're seeing Gemini 3.8 Flash, served by Databricks through the native Gemini API."
- "Gemini 4 Argon is also on Unity Gateway, as of the October 13 release notes. Same gateway, same controls."

**Don't say:**
- That the demo runs on Argon, or show Argon in a terminal or the usage table.
- That Argon is available on every cloud or region. The release note names none.
- That the demo workspace is on GCP. It's AWS (see the cross-cloud note below).

**Model names on slides:** use `system.ai.gemini-*` Unity Catalog model service names. The legacy `databricks-gemini-*` endpoints return 403 (*"no longer available. Use Unity Catalog model services."*), so don't show them.

**Day-of check:** re-run Omnigent's Gemini discovery or `demos/05-tracing/smoke.sh "system.ai.gemini-4-argon"` against `fevm-cjc`. If Argon starts being served, it's *optional* to switch the live model. Only switch after a clean dry run, and update this file, `.env.local` and the runbook together.

**Fallback:** if 3.8 Flash is slow or down on the day, switch to `system.ai.gemini-3-7-flash` (also served). Use the recorded `talk/fallbacks/antigravity-setup.mov` if the gateway itself fails.

## Other on-stage framing rules

- **Label Beta features** on the slide where they appear: Smart Routing, Skills API, agent memory, Databricks Sandbox, the unified trace table, and Omnigent on Databricks.
- **Antigravity is a community-supported Omnigent harness.** Say so when introducing `omni agy`.
- **Cross-cloud honesty.** The demo workspace and Sandbox are on AWS (Sandbox is AWS-only today). The Gemini and Unity Gateway story is cited from the GCP docs. One slide, in the recap.
- **Product name** is **Unity Gateway** (CLI `ug`), not "Unity AI Gateway". The system table is still `system.ai_gateway.usage`.
- **Public repo, public screen:** no workspace hostnames, IDs, emails or tokens on screen. The workspace URL lives in `.env.local` and the `omni-fevm` wrapper only.
