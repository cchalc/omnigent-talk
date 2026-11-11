# 07 - A software factory is configuration

Tag: offline

## Goal

Read chapters 01-06 again as one machine. Each thing you set up lives at a different configuration
layer, and that separation is why the whole setup can be copied, reviewed and rerun. By the end you
can point at the file that decides each choice.

## Steps

Walk the layers in the ecosystem map and
match each to something you already did:

| Question | Layer | Where it lives here | Chapter |
| :---- | :---- | :---- | :---- |
| Which harness runs? | Project config, or `--harness` | `omni run --harness ...` | 01 |
| Which model answers? | Gateway model service | `resources/model_services.yml` | 02 |
| Where does the work go? | Routing in front of the service | `src/omnigent_talk/router.py` | 03 |
| What may the agent do? | Agent spec guardrails | `agents/rory/config.yaml` | 04 |
| Who picks the model per task? | Smart Routing (Beta) | the gateway, not the repo | 05 |
| What is allowed at all? | Server and gateway policy | managed workspace settings | 06 |

Then look at how the repo keeps secrets out of a public tree:

```bash
git ls-files agents/rory
just agent-render
```

`agent-render` needs `CATALOG`, `SCHEMA` and `DBX_PROFILE` set, so run it only if you have them. The tracked bundle holds
`${CATALOG}`, `${SCHEMA}` and `${DBX_PROFILE}`. The renderer fills them into a gitignored copy, and
only that copy is uploaded (`agent_bundle.py`).

Finally, run the gate that protects the pattern:

```bash
just check
```

## Verify

- `just check` passes: formatting, lint, types, tests, and the public-repo leak scan.
- You can name, for each row above, the single file you would edit to change that behavior.
- `just check` finishes without a leak-scan hit: no secret pattern, no workspace hostname, and none of your `.env.local` values in tracked files. It does not catch emails or IDs, so read the diff yourself.

## Fallback

If `just agent-render` fails with a variable that is not set, that is the point: the value belongs
in `.env.local`, which is gitignored (names in `.env.example`). Fill it in, or skip the render and
read the bundle instead.

## The pattern in one paragraph

Keep the generic core small and public: the harness choice and the agent bundle with placeholders.
Keep the private overlay on the machine: server, profile, providers, rendered values. Put
guardrails in the spec so they travel with the agent, and put organization policy at the server so
they cannot be edited away. Route work at the gateway so changing a model is a bundle change, not a
code change. When all five hold, a new teammate can reproduce your factory from the repo plus their
own `.env.local`.

Caveat: this story covers what is merged on `main`. Several unmerged branches change the routing
splits and rename a model service. They are not part of the replay.
