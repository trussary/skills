---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blocking links on a real tracker).
disable-model-invocation: true
---

# To Tickets

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-trussary-skills`.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Ticket titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests): vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice fits **under the implementer context budget** in the `## Planning` section of `docs/agents/project.md` (default 150k tokens). Most of it is fixed (default ~105k): the agent's start-up context plus its own thinking, edits and command output. What is left is the **read budget** (default 45k): the code it must read, any prototype, the ADRs and docs it names, and the tests. Measure it with `${CLAUDE_PLUGIN_ROOT}/tools/read-budget.py <files and dirs> --budget <read budget>` over the files the slice changes, their tests and the docs it names (~10 tokens a line), with one `--skip <path>` for each generated file `## Planning` or `## Generated files` says agents grep rather than read. A slice it reports over budget, or above ~20 files touched (deletions count: the agent reads what it removes), is split. Estimate from the files, not from module names: a name-based estimate runs low. The context budget is a target, not a measured fit: many small `sed`/`rg` reads can push a slice well past it with no one big file
- Any prefactoring should be done first

</vertical-slice-rules>

A slice with UI links the approved prototype(s) for its screens in a `## Prototype` section; the implementer reads them before coding. A slice that changes a shared contract (the list in `## Planning`; without one, a schema, API or type other tickets build on, or a DB migration) is its own ticket, labelled `contract`, and blocks the tickets that use it.

Title tickets `<Context>: <verb + outcome>`, using the glossary's context names and terms. When `## Planning` names track labels, label each ticket with its track.

Give each ticket its **blocking edges**: the other tickets that must complete before it can start. A ticket with no blockers can start immediately. Each ticket body states its blockers and, for every pair of siblings, whether they can run in either order; done when no ticket's dependencies live only in your head or the graph.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

### 4. Measure the depth

A graph's **depth** is the number of tickets on its **critical path**: the longest chain of blocking edges, where a lone ticket is depth 1. Every level costs wall time (`## Planning` may record a measured cost per level), because a blocked ticket cannot start until its blocker merges. Done when the depth is **5 or fewer**, or the user has accepted a deeper graph.

Name the critical path and its depth. Wide-refactor sequences count too: expand, migrate batches (siblings, one level together) and contract are three levels, four with an integrate-and-verify ticket. When the depth is above 5, cut it in this order, recomputing after each step:

1. **Contract first, and small.** Pull each `contract` ticket (schema, API, type) to the front, carrying only the shape the others need and no behaviour behind it. The backend and UI slices that use it then become siblings blocked only by the contract, not by each other.
2. **Merge small tail-chains.** Fold a chain of small tickets (A blocks B blocks C) into one ticket, whenever the merged ticket stays within the **read budget**. Estimate the merged size with step 3's slice rule, counting files the merged tickets share once. A merge that would cross it trades depth for size: leave those tickets apart and carry a warning into the quiz (which tickets, estimated merged read budget).

Still above 5: put the graph, the critical path and the options (accept the depth, merge past the read budget, cut scope) in front of the user and let them choose.

### 5. Quiz the user

Present the proposed breakdown as a numbered list. Open it with the graph's **depth** and critical path (for example "Depth 4: 1 → 3 → 6 → 9") and any read-budget warning from step 4. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work
- **Read budget**: the `read-budget.py` total in k tokens and the paths it was run on
- **Executor**: `opus` or `sonnet`, by the `## Executor tier` rule in `docs/agents/models.md`, with the condition that set it

Before estimating, read the `Peak context` lines of the last few implementation PRs' `## Run` records (`gh api 'repos/<owner>/<repo>/pulls?state=closed&sort=updated&direction=desc&per_page=50' --jq '[.[] | select(.merged_at and (.body // "" | contains("Peak context")))][:5][] | {number, body}'`, the slug from `docs/agents/issue-tracker.md`): when the measured peaks run above the context budget, estimate more tightly.

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?
- Is the depth acceptable? (Required whenever it is above 5 or a merge was refused for size.)

Iterate until the user approves the breakdown.

### 6. Publish the tickets to the configured tracker

Publish the approved tickets. **How** depends on the tracker `/setup-trussary-skills` configured; the tickets are the same either way, only the shape of the blocking edges changes:

- **Local files** → write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first). Each file's "Blocked by" lists the numbers/titles it depends on. Use the per-ticket file template below: one ticket per file, never a single combined file.
- **A real issue tracker (GitHub, Linear, …)** → publish one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Use the platform's native blocking relationship where it has one; otherwise set each ticket's "Blocked by" to the blocking issues. If the source was an existing issue, make each ticket its sub-issue (tracker doc's operation). Apply the `ready-for-agent` triage label unless instructed otherwise; the tickets are agent-grabbable by construction.

Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom.

Do NOT close or modify any parent issue.

<local-ticket-template>

# <NN>: <Ticket title>

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective, not a layer-by-layer implementation list.

**Blocked by:** the numbers/titles of the tickets that gate this one, or "None (can start immediately)".

**Status:** ready-for-agent

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

<issue-template>

## Parent

A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Prototype

Links to the approved prototype(s) for this ticket's screens (UI tickets only; omit otherwise). A ticket that ports a prototype lists, under each link, every section and visual element it carries (illustration, mascot, animation, image, copy block), each marked port or left out with the reason; the implementer and QA work through that list.

## Read budget

The `read-budget.py` total in k tokens and the paths it was run on (for example "38k: `src/orders/domain/checkout.py`, its tests, `CheckoutScreen.tsx`").

## Executor

`opus` or `sonnet`, and the tier condition that set it (for example "opus: changes the Order transition table").

## Blocked by

- A reference to each blocking ticket, or "None (can start immediately)". Add "Order with #<n>: either" for each sibling that can run in parallel or in either order.

</issue-template>

In either form, avoid specific file paths or code snippets: they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.
