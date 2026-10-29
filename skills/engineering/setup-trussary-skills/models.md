# Models

Which model does the work, and when it asks for advice.

## Setup

- **Executor:** each ticket names its own in a `## Executor` section, by the [tier rule](#executor-tier); a ticket without one goes to Sonnet. The implementer and fixer subagents of `/implement-spec` and `/implement` run on it (Agent `model`).
- **Advisor:** Opus, set repo-wide by `"advisorModel": "opus"` in `.claude/settings.json`. Subagents inherit it. An Opus session with a human in the loop consults it at its own judgement; an executor by the [points below](#when-the-executor-consults-the-advisor).
- **Opus** runs everything with a human in the loop (grilling, `/to-spec`, `/to-tickets`, `/wayfinder`), the `/implement-spec` orchestrator and its merger subagents, which resolve conflicts.

Why: a cheaper executor with a stronger advisor scores close to the stronger model alone at lower cost per task ([the advisor strategy](https://claude.com/resources/articles/the-advisor-strategy), [Claude Code advisor docs](https://code.claude.com/docs/en/advisor)), and tickets cut by `/to-tickets` fit that shape: each fits the implementer context budget with its seams named. The advisor reads the executor's own transcript, so it is a consult, not an independent review; `/code-review` and `/qa` stay as they are.

Needs the advisor feature of Claude Code, the Anthropic API directly, and telemetry left on (`DISABLE_TELEMETRY` keeps the advisor off).

## Executor tier

A ticket goes to **Opus** when any of these holds, and to **Sonnet** otherwise:

- it is labelled `contract` (a shared shape other tickets build on);
- it adds or changes a state transition table;
- it changes the domain code of two or more modules;
- its read budget is over 30k.

A fixer runs on Opus for a finding on a shared contract or an unmet acceptance bullet, and on its ticket's executor otherwise.

These are starting values. `/retro` moves the line from the `## Run` records ([revert rule](#run-record)).

## When the executor consults the advisor

The advisor call forwards the whole transcript, so its price grows with the context. A Sonnet executor consults it at these points, and nowhere else:

1. Once, after reading the ticket, its notes and the code, before the first Edit: the plan for each seam and how each acceptance bullet will be shown done. Context is smallest here, and a wrong approach costs the most.
2. When the same failure goes red twice in a row (a test, typecheck or CI check).

The hand-back's `advisor <n>` is at least 1; the orchestrator sends a Sonnet hand-back with `advisor 0` back to make the first call before it merges. An Opus executor consults it only at point 2.

## Run record

Every implementation PR ends its body with:

```markdown
## Run

- Executor: <model that built the tickets; "mixed: Opus #12 #14, Sonnet the rest" when it differs per ticket>
- Tickets: <number of tickets the PR closes>
- Serious /code-review findings by executor: <findings/tickets per model, e.g. "Opus 9/4, Sonnet 5/8">
- Advisor calls: <total of the hand-backs' `advisor <n>` for Sonnet tickets; "n/a" with no Sonnet ticket>
- Tokens: <total, cache reads included, then per role, e.g. "312M (implementer 95M, fixer 73M, qa 60M, orchestrator 47M)"; for /implement, the /usage total or "n/a">
- Wall-clock: <orchestrator session, first to last line; for /implement, "n/a">
- Serious /code-review findings: <count>
- Red CI rounds: <count of failed CI runs on the branch>
- Peak context: <highest true peak per role, e.g. "implementer 196k (#721, compacted), fixer 120k"; "n/a" for /implement>
```

Before writing the body, the orchestrator runs `<plugin root>/tools/subagent-peaks.py --spec <spec issue#>` (`<plugin root>`: the trussary-skills plugin directory, which `/implement-spec` names): it copies the top row of each role into Peak context, and the summary under the table into Tokens and Wall-clock. `/retro` and `/to-tickets` compare Peak context with the implementer context budget in `docs/agents/project.md`; `/retro` reads Tokens and Wall-clock for cost and time. Which PRs need the record, and what checks it, is in the `## Run record` section of `docs/agents/project.md`.

Count Red CI rounds with `gh`: the failed runs of the CI workflow on the PR branch (a cancelled run does not count):

```bash
gh run list --branch <branch> --workflow <ci workflow> --limit 200 --json conclusion \
  --jq '[.[] | select(.conclusion == "failure")] | length'
```

`/retro` reads these. The revert rule looks at the Sonnet-built tickets of the last five merged PRs that have any, counted from `Serious /code-review findings by executor`: if they average more than one serious finding a ticket, or a merged regression traces back to one of them, move the tier line up (the read-budget bound down, or one more condition to Opus). The window counts only PRs merged after the last change to the tier line, so one slide never moves it twice. With fewer than five such PRs since the change, judge on those there are.
