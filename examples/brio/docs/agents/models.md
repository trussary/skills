# Models

Which model does the work, and when it asks for advice.

## Setup

- **Executor:** each ticket names its own in a `## Executor` section, by the [tier rule](#executor-tier); a ticket without one goes to Sonnet. The implementer and fixer subagents of `/implement-spec` and `/implement` run on it (Agent `model`).
- **Advisor:** Opus, set repo-wide by `"advisorModel": "opus"` in `.claude/settings.json`. Subagents inherit it. An Opus session with a human in the loop consults it at its own judgement; an Opus executor by the [points below](#when-the-executor-consults-the-advisor).
- **Opus** runs everything with a human in the loop (grilling, `/to-spec`, `/to-tickets`, `/wayfinder`), the `/implement-spec` orchestrator and its merger subagents, which resolve conflicts.

Why: Sonnet with an Opus advisor scored higher than Sonnet alone at lower cost per task on SWE-bench Multilingual ([the advisor strategy](https://claude.com/resources/articles/the-advisor-strategy), [Claude Code advisor docs](https://code.claude.com/docs/en/advisor)). Brio tickets fit that shape: each is under 150k tokens with its seams named. The advisor reads the executor's own transcript, so it is a consult, not an independent review; `/code-review` and `/qa` stay as they are.

Needs Claude Code 2.1.260+, the Anthropic API directly, and telemetry left on (`DISABLE_TELEMETRY` keeps the advisor off).

## Executor tier

A ticket goes to **Opus** when any of these holds, and to **Sonnet** otherwise:

- it is labelled `contract` (a shared shape other tickets build on);
- it adds or changes a transition table (`*_states.py`, ADR 0020);
- it changes the domain code of two or more modules;
- its read budget is over 30k.

A fixer runs on Opus for a finding on a shared contract or an unmet acceptance bullet, and on its ticket's executor otherwise.

Why: the 2026-10-29 retro measured Sonnet at 0.6 serious findings a ticket on UI and copy work (#1025) and 1.3 on a restyle (#1070), against 4.8 on chat domain logic with transition tables and contracts (#1144).

## When the executor consults the advisor

The advisor call forwards the whole transcript to Opus, so its price grows with the context; Claude Code has no cap or trigger. A Sonnet executor consults it at these points, and nowhere else:

1. Once, after reading the ticket, its notes and the code, before the first Edit: the plan for each seam and how each acceptance bullet will be shown done. Context is smallest here, and a wrong approach costs the most.
2. When the same failure goes red twice in a row (a test, typecheck or CI check).

The hand-back's `advisor <n>` is at least 1; the orchestrator sends a Sonnet hand-back with `advisor 0` back to make the first call before it merges. An Opus executor consults it only at point 2.

The 2026-10-29 retro found 22 of 37 Sonnet implementers never called it, and 4 calls in three specs came before the first edit.

## Run record

Every implementation PR ends its body with:

```markdown
## Run

- Executor: <model that built the tickets, e.g. Sonnet 5.5; "mixed: Opus 5.5 #12 #14, Sonnet 5.5 the rest" when it differs per ticket>
- Tickets: <number of tickets the PR closes>
- Serious /code-review findings by executor: <findings/tickets per model, from the findings file of /implement-spec, e.g. "Opus 9/4, Sonnet 5/8"; for /implement, the one executor, e.g. "Sonnet 2/1">
- Advisor calls: <total of the hand-backs' `advisor <n>` for Sonnet tickets, e.g. "9 over 8 Sonnet tickets"; "n/a" with no Sonnet ticket>
- Tokens: <total, cache reads included, then per role, e.g. "312M (implementer 95M, fixer 73M, qa 60M, orchestrator 47M)"; for /implement, the dev pastes the /usage total or writes "n/a">
- Wall-clock: <orchestrator session, first to last line, e.g. "5.1h"; for /implement, "n/a">
- Serious /code-review findings: <count>
- Red CI rounds: <count of failed `ci` runs on the branch, from `gh run list`>
- Peak context: <highest true peak per role, e.g. "implementer 316k (#721, compacted), fixer 190k, qa 140k"; "n/a" for /implement>
```

Before writing the body, the orchestrator runs `scripts/subagent-peaks.py --spec <spec issue#>`: it copies the top row of each role into Peak context, and the summary under the table into Tokens and Wall-clock. `/retro` and `/to-tickets` compare Peak context with the 150k budget; `/retro` reads Tokens and Wall-clock for cost and time.

CI checks it: the `changes` job fails a PR that changes `apps/` or `packages/` when a field is missing, a count is not a number, or the findings line says `/code-review` did not run (`.github/scripts/run-record.py`). Fix the body, then re-run the job.

Count Red CI rounds with `gh`. It is the number of failed `ci` runs on the PR branch (the integration branch for `/implement-spec`; the dispatched full run counts, a cancelled run does not; the `/implement-spec` order is in [FINISH.md](../../.claude/skills/implement/FINISH.md#integration-branch-implement-spec)):

```bash
gh run list --branch <branch> --workflow ci --limit 200 --json conclusion \
  --jq '[.[] | select(.conclusion == "failure")] | length'
```

`/retro` reads these. The revert rule looks at the Sonnet-built tickets of the last five merged PRs that have any, counted from `Serious /code-review findings by executor`: if they average more than one serious finding a ticket, or a merged regression traces back to one of them, move the tier line up (the read-budget bound down to 20k, or one more condition to Opus). A window of five keeps a recent slide from being averaged away by older PRs. The window counts only PRs merged after the last change to the tier line: the PRs that moved it were already acted on, so counting them again would move it twice for one slide (#1144 alone, 58 findings over 12 tickets, would have kept the 2026-10-29 window above 1 for five more PRs). With fewer than five such PRs since the change, judge on those there are.
