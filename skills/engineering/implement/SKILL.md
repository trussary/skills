---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets. Use this skill for a single ticket (a bug, a chore, a ticket from `/triage`); use `/implement-spec` for a spec with its ticket graph.

`<plugin root>` in the files this skill reads (FINISH.md, IMPLEMENTER.md, `docs/agents/models.md`) is `${CLAUDE_PLUGIN_ROOT}`.

**Run autonomously until a PR is open and CI is green.** Don't stop to ask unless genuinely blocked (a domain decision nobody has made, missing access, an acceptance bullet you cannot meet). Merging is the human's call.

Repo facts (layout, checks, generated files, budgets) come from `docs/agents/project.md`; the repo slug and `gh` calls from `docs/agents/issue-tracker.md`; executor and advisor rules from `docs/agents/models.md`. If `docs/agents/issue-tracker.md` is missing, tell the user to run `/setup-trussary-skills`.

1. Claim the ticket (assign yourself, per `docs/agents/issue-tracker.md`).
2. Work in a worktree on a branch named `<issue#>-<slug>`, based on the latest `origin/main`.
3. Build it with one subagent, `subagent_type: "trussary-skills:implementer"`, started with a fresh context window, on the `model` the ticket's `## Executor` names (`"sonnet"` when it has none, per the Executor tier of `docs/agents/models.md`). The prompt holds the ticket number, the absolute worktree path and the branch, plus: "Build this ticket per `${CLAUDE_SKILL_DIR}/IMPLEMENTER.md`, base `origin/main`, and hand back in its format." A Sonnet hand-back with `advisor 0` goes back to it (SendMessage) for the first advisor call.
4. Use /code-review and fix what it raises.
5. For a ticket with UI, call the Skill tool with `qa`.
6. Finish per `${CLAUDE_SKILL_DIR}/FINISH.md`: Definition of Done, PR, CI until green, cleanup after merge (`${CLAUDE_PLUGIN_ROOT}/tools/cleanup-merged.sh`). The PR body carries the Hand-back facts from IMPLEMENTER.md.
