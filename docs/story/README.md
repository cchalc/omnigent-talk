# Replay story: from harnesses to a software factory

Replay everything the talk showed, in order: several harnesses on Omnigent, Databricks AI Gateway
model services and routing, and custom agents. Each chapter has a goal, the commands, a check, and
a fallback. `Tag: offline` chapters need no credentials. `Tag: workspace` chapters need a
Databricks workspace and `DBX_PROFILE` in `.env.local` (names in `.env.example`).

Background: [the Omnigent ecosystem map](../research/omnigent-ecosystem.md). Claims that matter on stage trace to
[facts.md](../research/facts.md); where one has no row, the chapter says so.

| Chapter | What you reproduce | Tag |
| :---- | :---- | :---- |
| [00-prereqs.md](00-prereqs.md) | Tools, `.env.local`, the offline gate | offline |
| [01-harnesses.md](01-harnesses.md) | One prompt through four harnesses | workspace |
| [02-gateway-model-services.md](02-gateway-model-services.md) | Model services as a bundle, then a native Gemini probe | workspace |
| [03-routing.md](03-routing.md) | Traffic splits, task routing, reading `destination_model` | workspace |
| [04-custom-agents.md](04-custom-agents.md) | The `rory` router agent and its guardrails | workspace |
| [05-smart-routing.md](05-smart-routing.md) | Smart Routing (Beta): preflight, preview, usage | workspace |
| [06-policies-memory-sandbox.md](06-policies-memory-sandbox.md) | Policies, agent memory, Sandbox | workspace |
| [07-software-factory.md](07-software-factory.md) | How the config layers compose into a repeatable factory | offline |

The test `tests/test_story.py` keeps the chapters honest: required headings, one tag each, only
real `just` recipes, and links that resolve.
