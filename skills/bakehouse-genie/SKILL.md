---
name: bakehouse-genie
description: Ask the curated Bakehouse Genie agent and return its answer with any generated SQL.
---

# Bakehouse Genie

Require `DBX_PROFILE`; every command must pass `--profile "$DBX_PROFILE"`.

1. Run `databricks genie list-spaces --profile "$DBX_PROFILE" -o json` and select the single
   space whose title is exactly `omnigent-talk: Bakehouse analyst`. Stop if none or more than one
   matches. Never guess a space ID.
2. Start with
   `databricks genie start-conversation "$space_id" "$question" --profile "$DBX_PROFILE" -o json`.
   The CLI polls by default. Preserve the returned conversation and message IDs.
3. For a follow-up, run
   `databricks genie create-message "$space_id" "$conversation_id" "$question" --profile "$DBX_PROFILE" -o json`.
4. If a call used `--no-wait`, poll
   `databricks genie get-message "$space_id" "$conversation_id" "$message_id" --profile "$DBX_PROFILE" -o json`
   until `COMPLETED` or a terminal failure; time out after 20 minutes.

Return the completed natural-language answer and SQL from query attachments. Say explicitly when
Genie returned no SQL. Do not print workspace, space, conversation, message, or attachment IDs.
