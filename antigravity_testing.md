# Antigravity Testing & Verification Log

This document records the architecture, configuration discovery, and prompt/response test logs for Google Antigravity (`agy`) running through Databricks Unity Catalog AI Gateway via Omnigent.

---

## 1. Architecture: How agy Calls are Proxied

When running `omni agy` with a Databricks profile configured (`native_gemini: true`), calls do **not** go directly to Google's public endpoints. Instead, they flow through a two-stage local and workspace proxy:

```
+------------------+
|    agy CLI       |  (Native Antigravity binary)
|  (Local Client)  |
+--------+---------+
         |
         | HTTP (Gemini REST / SSE: generateContent / streamGenerateContent)
         | Headers: x-goog-api-key: <ephemeral-gateway-key>
         v
+------------------+
| Omnigent Gateway |  (omnigent.harnesses.antigravity_native.gateway)
|  (Local Proxy)   |  - Listens on 127.0.0.1:<random-port>
+--------+---------+  - Maps model names (e.g. gemini-3.8-flash -> system.ai.gemini-3-8-flash)
         |            - Dynamically resolves Databricks OAuth token from profile
         |
         | HTTPS (Unity Catalog AI Gateway)
         | URL: https://<workspace-host>/ai-gateway/gemini/v1beta/models/<model>:streamGenerateContent
         | Headers: Authorization: Bearer <databricks-token>
         v
+------------------+
| Databricks Unity |  (Unity Catalog AI Gateway & Model Serving)
|    AI Gateway    |  - Enforces governance, rate limits, audit logging
+--------+---------+  - Dispatches to external model endpoint (e.g. Google Cloud / Vertex AI)
```

---

## 2. Determining the Workspace and Endpoint

To inspect which Databricks workspace and endpoint your calls are proxied through:

### A. Check the Active Omnigent Configuration
Look at your active Omnigent config (for instance `~/.omnigent-fevm/config.yaml` or `~/.omnigent/config.yaml`):

```bash
# View active provider and profile
cat ~/.omnigent-fevm/config.yaml
```
Look for:
```yaml
providers:
  databricks-gemini-fevm-cjc:
    default: true
    kind: databricks
    native_gemini: true
    profile: <profile-name>     # e.g., fevm-cjc (set in DBX_PROFILE)
server: https://<workspace-host>/api/2.0/omnigent
```

### B. Resolve the Databricks Workspace URL for that Profile
Use the Databricks CLI to inspect the workspace host backing that profile:

```bash
databricks auth describe --profile <profile-name>
```
The `host` field shows the Databricks workspace host (e.g. `https://<workspace-host>`).

### C. Upstream Endpoint URL
Omnigent translates agy's requested model into the corresponding Unity Catalog AI Gateway route:
* **Model translation:** `gemini-3.8-flash` -> `system.ai.gemini-3-8-flash`
* **Full upstream endpoint:**
  `POST https://<workspace-host>/ai-gateway/gemini/v1beta/models/system.ai.gemini-3-8-flash:streamGenerateContent`

### D. Verify via Running Process & Session Link
* Inspect the running process:
  ```bash
  ps -ef | grep -E "(agy|gateway)"
  ```
  You will see:
  `python3 -m omnigent.harnesses.antigravity_native.gateway --profile <profile-name> -- agy --gemini_dir=...`
* If running inside tmux/Omnigent, the tmux status bar or web UI session link points to:
  `https://<workspace-host>/omnigent/c/<conversation-id>`

---

## 3. Where the Antigravity Configuration Lives

The setup consists of three configuration layers:

1. **Omnigent Provider Layer (`~/.omnigent-fevm/config.yaml`)**:
   Defines the Databricks connection and specifies `native_gemini: true`, instructing Omnigent to wrap `agy` with the local Gemini-to-Databricks gateway rather than passing raw Google credentials.

2. **Isolated agy Settings (`<agy-session-home>/.gemini/antigravity-cli/settings.json`)**:
   Omnigent launches `agy` with an isolated `--gemini_dir`:
   ```json
   {
     "model": "Gemini 3.8 Flash (Medium)",
     "modelProvider": "gemini"
   }
   ```
   Setting `"modelProvider": "gemini"` is critical: without this, `agy` defaults to its Google Keychain OAuth login. With `modelProvider: "gemini"`, `agy` respects `GOOGLE_GEMINI_BASE_URL` (the local Omnigent proxy) and `GEMINI_API_KEY` (the ephemeral proxy token).

3. **Gateway Translation Engine (`omnigent/harnesses/antigravity_native/gateway.py`)**:
   Runs as the parent wrapper. It queries available models via Databricks Model Discovery, starts a local Starlette/uvicorn proxy on `127.0.0.1`, injects `GOOGLE_GEMINI_BASE_URL`, and proxies all calls upstream.

---

## 4. Why Setting It Up Through Omnigent Helps

Setting up `agy` through Omnigent provides several major advantages:

1. **Protocol & Authentication Bridging:**
   * `agy` speaks the Google Gemini REST/SSE API and natively expects either Google OAuth or a Google Gemini API key.
   * Databricks AI Gateway requires short-lived Databricks OAuth Bearer tokens (`Authorization: Bearer ...`).
   * Omnigent transparently resolves, caches, and refreshes Databricks OAuth tokens per request without modifying the `agy` binary.

2. **Enterprise Governance & Centralized Observability:**
   * Instead of developer queries leaving laptops directly to Google under personal logins, all traffic routes through the enterprise Unity Catalog AI Gateway.
   * All prompts, token usage, system tables, rate limits, and budget tracking are managed centrally in Databricks.

3. **Model Name Disambiguation & Tiered Routing:**
   * `agy` asks for names like `gemini-3.8-flash` or background preview models like `gemini-3.1-flash-lite-preview`.
   * Omnigent normalizes and maps these to Databricks Model Serving catalog services (`system.ai.gemini-3-8-flash` / `system.ai.gemini-3-1-flash-lite`).

4. **Environment Isolation:**
   * Keeps personal Google credentials in `~/.gemini` separate from enterprise Databricks work.
   * Injects Omnigent MCP tools (session history, terminal management, policy controls) into the agent's context.

---

## 5. Test Log

Use the table below to record test prompts, responses, and verification details.

### Entry 1
* **Date / Time:** 2026-11-03 21:49:14
* **Profile / Workspace:** Configured via `$DBX_PROFILE` (`fevm-cjc`) -> `https://<workspace-host>`
* **Model Requested:** `gemini-3.8-flash` -> translated to `system.ai.gemini-3-8-flash`
* **Prompt:**
  > "where is the model I am accessing?"
* **Response Summary:**
  > Clarified dual nature: assistant running via Antigravity bridged through Omnigent Databricks Gateway, with backend inference on Gemini hosted via Databricks Unity AI Gateway.
* **Routing Path Verified:**
  `agy` -> `127.0.0.1 (gateway.py)` -> `https://<workspace-host>/ai-gateway/gemini/v1beta/models/system.ai.gemini-3-8-flash:streamGenerateContent`

---

<!-- Add new entries below -->
