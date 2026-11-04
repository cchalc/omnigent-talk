# Portable talk skills

These Agent Skills bundles are the source registered by `just skills-sync` in the Beta Unity
Catalog Skills API. The command always uses `DBX_PROFILE` and `CATALOG` from `.env.local`; it
does not use the Databricks CLI default profile.

Agent Skills names use hyphens (`bakehouse-analyst`). Unity Catalog accepts hyphens, but this
project registers conservative unquoted identifiers with underscores (`bakehouse_analyst`). The
sync maps each directory name by replacing `-` with `_`; the `name` in `SKILL.md` stays
hyphenated. The three UC names are therefore:

- `<CATALOG>.omnigent_talk.bakehouse_analyst`
- `<CATALOG>.omnigent_talk.bakehouse_genie`
- `<CATALOG>.omnigent_talk.gateway_observability`

The sync stores a bundle digest in each skill's comment. Matching finalized bundles are reported
as unchanged; changed bundles upload every file, finalize again, and record the new digest with an
etag-guarded metadata update. UC Skills have no version number, and there is currently no DAB or
Terraform resource for them.
