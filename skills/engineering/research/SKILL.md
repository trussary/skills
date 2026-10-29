---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

Spin up a **background agent**, started with a fresh context window, to do the research, so you keep working while it reads. If you are already that agent (a subagent running this skill), do the steps below yourself and return the findings as text plus the path of the file you wrote.

The job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

## Secrets

When a probe calls a paid or keyed API (a model provider, a provider SDK), read the key from the environment by variable name inside the script, and print only the status code and the response fields the finding needs. Request objects, headers and environment values stay out of tool output. Redact any key or `Authorization` value as `<redacted>` in output, notes and the committed file.

## Cost

A probe that spends money goes through the metered client and research key the `## Paid APIs` section of `docs/agents/project.md` names, never a raw call to the provider. Without that section: put a hard spend limit in the script, spend on a key kept for research and stop if it is not set, and never pass the app's own key. Either way, put the total USD spent in the findings file.
