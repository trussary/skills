---
name: implement-spec
description: "Implement the result of /to-spec and /to-tickets in code."
disable-model-invocation: true
---

**Run autonomously until the PR is ready, CI is green and the human is notified.** Don't stop to ask unless genuinely blocked (a domain decision nobody has made, missing access, an acceptance bullet nobody can meet).

`<plugin root>` in the files this skill reads (FINISH.md, IMPLEMENTER.md, `docs/agents/models.md`) is `${CLAUDE_PLUGIN_ROOT}`.

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker should have been provided to you. If not, tell the user to run `/setup-trussary-skills`. Repo facts (layout, dev stack, checks, generated files, budgets) come from `docs/agents/project.md`; executor and advisor rules from `docs/agents/models.md`.

The goal is the entire spec implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers. Every subagent waits for its own children before reporting; resume one that reports partial work with SendMessage. Start every new subagent with a fresh context window.

**Implementer subagents** run in the background, **at most 3 at once** (implementers and fixers together; the concurrency line of `## Planning` overrides it): every one shares this machine's CPU and any shared test services, and past that cap each ticket takes several times longer. When a slot frees, dispatch the next frontier ticket on the critical path (the one blocking the most others) first.

Run every **implementer subagent** and **fixer subagent** with `subagent_type: "trussary-skills:implementer"` and every **QA subagent** with `subagent_type: "trussary-skills:qa"`. An implementer runs on the `model` its ticket's `## Executor` names (`"sonnet"` when it has none), a fixer by the fixer line of the Executor tier in `docs/agents/models.md`, a QA subagent on `"sonnet"`; run every **merger subagent** with `subagent_type: "trussary-skills:merger"` and every review sub-agent with `subagent_type: "trussary-skills:reviewer"` on the session model (the plugin's `agents/`: a narrow toolset, so each starts with less context than a general-purpose agent). The Sonnet ones inherit the Opus advisor (`docs/agents/models.md`).

## Steps

1. Read the spec and tickets to understand the task graph.

2. When two or more tickets touch the same modules, run an **exploration subagent** first (`subagent_type: "Explore"`, `model: "sonnet"`; if a codegraph MCP server is configured, it explores with `codegraph_explore` instead of grep + read loops, running `codegraph init -i` first if `.codegraph/` is missing; otherwise with Grep/Read); otherwise it is optional. It saves markdown notes in a directory outside the repo, readable by every later subagent: one section per ticket, naming each symbol to read or change as `path:start-end` with a line on what it does, plus the external docs the ticket needs. Done when every ticket has its section and no section quotes a whole file. This keeps each **implementer subagent** on implementation rather than re-exploring the same files.

3. Create the integration branch, named `<spec-issue#>-<slug>`, from the latest `origin/main`; resuming an existing one, merge `origin/main` into it first. Make sure any shared test services are up, per [IMPLEMENTER.md](../implement/IMPLEMENTER.md#test-database). If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets. A draft PR runs no CI: its `ci` check shows green or skipped on every push, which is not a signal.

4. Use **implementer subagents** to implement each ticket, each in its own worktree on its own branch. The prompt holds only the ticket number, the absolute worktree path, the branch, the integration branch, the path of the ticket's section in the exploration notes and of the findings file (step 7), plus: "Build this ticket per `${CLAUDE_PLUGIN_ROOT}/skills/engineering/implement/IMPLEMENTER.md` and hand back in its format."

5. A Sonnet hand-back with `advisor 0` goes back to its subagent (SendMessage) to make the first advisor call of `docs/agents/models.md` (When the executor consults the advisor) and act on it before it merges. Merge finished work to the integration branch with one **merger subagent** per batch: every implementer and fixer branch that has handed back since the last merger started. The merger resolves conflicts per [IMPLEMENTER.md](../implement/IMPLEMENTER.md#generated-files), follows its Shell section, and merges the batch in order. Merges run one batch at a time, so this step sits on the critical path: keep it short.
   - A branch that already holds the current integration tip (`git -C <wt> merge-base --is-ancestor HEAD <branch>`) merges as a fast-forward onto the tree its implementer just checked: it needs no checks.
   - After the batch, the merger checks once, and fixes on the integration branch before handing back, that no conflict markers remain (`git -C <wt> grep -nE '^(<<<<<<<|=======$|>>>>>>>)'`), every post-merge check `## Checks` names passes (a single migration head, say), and, when any branch of the batch needed a real merge, the "Before hand-back" command of `## Checks` passes with the integration tip before the batch as its base.

6. If this changes the **frontier** of available tickets, fill the free implementer slots from it.

7. When a wave (the tickets dispatched together) is merged, call the Skill tool with `code-review` on the integration branch since the previous review sha, record the reviewed sha, and act once both reviewers have reported. Append each serious finding to the findings file next to the exploration notes, as one line: the ticket whose code it is, that ticket's executor, its class (status literal, glossary term, missing test for a bullet, ...) and `path:line`; the Run record counts findings by executor from it, and later implementers read it before their first edit. Fix the findings with **fixer subagents** (implementer subagents given only their findings, each finding with its `path:line`), while the next wave runs; a fixer takes the next free slot ahead of new frontier tickets, since its fix blocks merge and QA; their branches merge through step 5. One fixer per area (each product-code directory `## Layout` names) and ticket, at most 5 findings each; a finding on a shared contract, or an unmet acceptance bullet, gets a fixer of its own.

8. QA runs wave by wave, alongside the next wave's build. Start one dev stack (the Start command of `## Dev stack`) from a QA worktree after the first wave with UI is merged. When a wave's review fixes are merged, fast-forward the QA worktree to the integration tip (restart the stack when `## Dev stack` says a change needs it) and run one **QA subagent** per ticket with UI in that wave, one after another on that stack. Each prompt holds the ticket number, the QA worktree path and branch, the web port and the PR, plus: "The stack is already up on that port; leave it running. Call the Skill tool with `qa` for this ticket and hand back its verdict line and artifact link. If you have no browser tools, say so and stop." QA fixes merge through step 5. The orchestrator stops the stack after the last QA.

   Once all tickets are merged and reviewed, dispatch one full CI run on the integration branch and keep its run id, per [FINISH.md](../implement/FINISH.md#integration-branch-implement-spec); its red jobs go to an area fixer as in step 7.

   Raise to the user every acceptance bullet the hand-backs, the review or the QA left unmet, per FINISH.md Definition of Done.

9. Remove every **implementer subagent** worktree and branch.

10. Finish per [FINISH.md](../implement/FINISH.md#integration-branch-implement-spec): mark the PR ready (open it first if no draft exists) with `Closes #<n>` for the spec and every ticket, fix CI until the run after the ready transition is green, then send the push notification with the PR link. After the human merges, run the cleanup in that file (`${CLAUDE_PLUGIN_ROOT}/tools/cleanup-merged.sh <branch>`).
