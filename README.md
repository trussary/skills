# trussary-skills

[Tiếng Việt](./README.vi.md)

The agent workflow behind Brio, Trussary's IELTS teaching tool, packaged as a Claude Code plugin: skills, subagents and hooks that take a piece of work from a roadmap issue to a merged PR with green CI, with a human deciding at each gate and agents doing the rest.

It is a fork of [mattpocock/skills](https://github.com/mattpocock/skills). Matt's skills (grilling, domain modeling, TDD, code review, wayfinder, specs and tickets) are the core; this fork adds the parts that let several agents build a spec in parallel and hand back something reviewable: implementer, merger, QA and reviewer subagents, an executor/advisor model split with a `## Run` record in every PR, read budgets per ticket, shell-write and large-read guards, and `/retro` to tune it all from what the records show.

## The loop

```
roadmap issue
  └─ /wayfinder        one map per slice: decision tickets resolved by grilling, research, prototypes
       └─ /to-spec     the map's destination, written up as a spec issue
            └─ /to-tickets   tracer-bullet tickets with blocking edges, executor and read budget each
                 └─ /implement-spec   implementers on the ready frontier, merged on one integration branch,
                                      /code-review per wave, /qa per UI ticket, PR open until CI is green
                      └─ human merges → branch and worktree cleaned up → /retro
```

`/implement` is the single-ticket version of `/implement-spec`. `/grill-with-docs`, `/tdd`, `/diagnosing-bugs`, `/research` and `/prototype` are used inside the loop or on their own.

## Install

Claude Code only: the subagents, hooks and `${CLAUDE_PLUGIN_ROOT}` paths are Claude Code features.

```bash
claude plugin marketplace add trussary/skills
claude plugin install trussary-skills@trussary
```

Then, in each repo, once:

```
/setup-trussary-skills
```

It writes `docs/agents/` (issue tracker, triage labels, domain docs, project facts, models) and a `## Workflow` and `## Agent skills` block in `CLAUDE.md`, then offers the guardrails: deny rules for pushes to `main` and force pushes, an opt-in cleanup of merged branches at session start, and the advisor model. [examples/brio](./examples/brio/docs/agents/) is a filled-in set from a real project.

Don't install this alongside `mattpocock-skills`: the skill names overlap. Pick one.

### Requirements

- `gh` for GitHub issues and PRs (GitLab and local markdown trackers work for the planning skills).
- `python3` for the hooks and tools.
- `/qa` and `/prototype` use the Claude desktop app's built-in browser and Artifacts.
- A codegraph MCP server is used when configured; without it agents use Grep and Read.

## What's in it

### User-invoked

- **[setup-trussary-skills](./skills/engineering/setup-trussary-skills/SKILL.md)**: Configure a repo for the workflow. Run once per repo.
- **[wayfinder](./skills/engineering/wayfinder/SKILL.md)**: Plan a chunk of work too big for one session as a map of decision tickets on the issue tracker.
- **[grill-with-docs](./skills/engineering/grill-with-docs/SKILL.md)**: Grilling that also updates `GLOSSARY.md` and ADRs inline.
- **[to-spec](./skills/engineering/to-spec/SKILL.md)**: Turn the conversation into a spec on the issue tracker.
- **[to-tickets](./skills/engineering/to-tickets/SKILL.md)**: Break a spec into tracer-bullet tickets with blocking edges, an executor and a read budget each.
- **[implement-spec](./skills/engineering/implement-spec/SKILL.md)**: Build a whole spec on one integration branch with parallel implementer subagents, review waves and QA, until CI is green.
- **[implement](./skills/engineering/implement/SKILL.md)**: Build one ticket or a small piece of work, test-first, closed out with `/code-review`.
- **[triage](./skills/engineering/triage/SKILL.md)**: Move issues through a state machine of triage roles.
- **[improve-codebase-architecture](./skills/engineering/improve-codebase-architecture/SKILL.md)**: Find deepening opportunities and grill through one.
- **[retro](./skills/engineering/retro/SKILL.md)**: Suggest improvements to the agent's environment after a session; generic ones go back to this repo as PRs.
- **[security-audit](./skills/engineering/security-audit/SKILL.md)**: Source-first security review or full audit. From [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) (MIT).
- **[wizard](./skills/engineering/wizard/SKILL.md)**: Generate an interactive bash wizard for steps only a human can do.

### Model-invoked

- **[grilling](./skills/productivity/grilling/SKILL.md)**: Interview the user about a plan in rounds until there is a shared understanding.
- **[domain-modeling](./skills/engineering/domain-modeling/SKILL.md)**: Challenge terms and record `GLOSSARY.md` entries and ADRs as they settle.
- **[codebase-design](./skills/engineering/codebase-design/SKILL.md)**: Vocabulary for deep modules, interfaces and seams.
- **[tdd](./skills/engineering/tdd/SKILL.md)**: Red-green-refactor, one vertical slice at a time.
- **[diagnosing-bugs](./skills/engineering/diagnosing-bugs/SKILL.md)**: A feedback loop that goes red on the bug, then minimise, hypothesise, fix, regression-test.
- **[code-review](./skills/engineering/code-review/SKILL.md)**: Standards and Spec review of a diff, as parallel subagents.
- **[qa](./skills/engineering/qa/SKILL.md)**: Use the running app like a manual tester at three widths, compare with the prototype and design system, publish QA evidence. Needs the Claude desktop app.
- **[prototype](./skills/engineering/prototype/SKILL.md)**: Throwaway prototypes to answer a design question, or a faithful port of settled ones. Needs the Claude desktop app for artifacts.
- **[research](./skills/engineering/research/SKILL.md)**: Investigate against primary sources and write the findings to the repo.
- **[pr](./skills/engineering/pr/SKILL.md)**: The shape of a PR body.
- **[writing-for-agents](./skills/productivity/writing-for-agents/SKILL.md)**: How to write skills, `CLAUDE.md` and `AGENTS.md`.

### Subagents

[`agents/`](./agents/): `trussary-skills:implementer`, `trussary-skills:merger`, `trussary-skills:qa`, `trussary-skills:reviewer`. Dispatched by `/implement`, `/implement-spec` and `/code-review`.

### Hooks and tools

- [`hooks/`](./hooks/): blocks shell commands that write files outside Edit/Write (`sed -i`, `>` redirects, inline Python writes), and caps reads of very large files. On whenever the plugin is enabled. `TRUSSARY_GUARDED_ROOTS` (default `apps,packages,src,lib`) and `TRUSSARY_NEVER_READ` in the `env` of `.claude/settings.json` tune them.
- [`tools/`](./tools/): `read-budget.py` (estimate a ticket's read budget), `subagent-peaks.py` (peak context and tokens per subagent role, for the `## Run` record), `cleanup-merged.sh` (remove merged branches and worktrees).

## Contributing and upstream

See [CONTRIBUTING.md](./CONTRIBUTING.md). Changes from mattpocock/skills are merged in by hand when upstream releases.

## License

MIT, see [LICENSE](./LICENSE). Based on [mattpocock/skills](https://github.com/mattpocock/skills) by Matt Pocock. `security-audit` is from [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill), MIT, see [its LICENSE](./skills/engineering/security-audit/LICENSE).
