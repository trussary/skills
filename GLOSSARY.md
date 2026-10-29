# trussary-skills

A Claude Code plugin of agent skills, subagents and hooks for one workflow, from roadmap to merged PR. Skills are organized into buckets and consumed by per-repo configuration emitted by `/setup-trussary-skills`.

## Language

**Issue tracker**:
The tool that hosts a repo's issues: GitHub Issues, Linear, a local `.scratch/` markdown convention, or similar. Skills like `to-tickets`, `to-spec`, and `triage` read from and write to it.
_Avoid_: backlog manager, backlog backend, issue host

**Issue**:
A single tracked unit of work inside an **Issue tracker**: a bug, task, spec, or slice produced by `to-tickets`.
_Avoid_: ticket, except for a **Ticket** or **Decision ticket** (below)

**Decision ticket**:
A `wayfinder` unit: a child **Issue** of a `wayfinder:map` holding a *question* whose resolution is a decision, not a slice of a build to execute. The **decision** qualifier is what keeps it distinct from an implementation ticket; `wayfinder` introduces the term, then uses "ticket".

**Triage role**:
A canonical state-machine label applied to an **Issue** during triage (e.g. `needs-triage`, `ready-for-afk`). Each role maps to a real label string in the **Issue tracker** via `docs/agents/triage-labels.md`.

**Roadmap**:
The one **Issue** that lists a phase's **Slices** in order.

**Slice**:
A vertical piece of the **Roadmap**, planned as a `wayfinder` map whose destination is one **Spec** (a large slice has sub-maps, each with its own **Spec**).

**Spec**:
An **Issue** describing one buildable destination, written by `to-spec` and split into **Tickets** by `to-tickets`.

**Ticket**:
An implementation **Issue** produced by `to-tickets`: a tracer-bullet slice of a **Spec** with blocking edges, an **Executor** and a read budget. Distinct from a **Decision ticket**.

**Executor**:
The model that builds a **Ticket**, chosen by the tier rule in `docs/agents/models.md`.
_Avoid_: worker model

**Advisor**:
A stronger model the **Executor** consults at fixed points; it reads the executor's transcript, so it is a consult, not a review.

**Run record**:
The `## Run` section that ends every implementation PR: executor, findings, tokens, wall-clock, red CI rounds, peak context. `retro` tunes the workflow from it.

**Project facts**:
What a consuming repo records in `docs/agents/project.md` so skills read commands, paths and budgets instead of guessing.

## Relationships

- An **Issue tracker** holds many **Issues**
- An **Issue** carries one **Triage role** at a time
- A **Decision ticket** is an **Issue** (a child of a `wayfinder:map`)
- A **Roadmap** holds many **Slices**; a **Slice** ends in one **Spec** per leaf map
- A **Spec** splits into many **Tickets**; each **Ticket** has one **Executor**
- An implementation PR closes one or more **Tickets** and ends with one **Run record**

## Flagged ambiguities

- "backlog" was previously used to mean both the *tool* hosting issues and the *body of work* inside it. Resolved: the tool is the **Issue tracker**; "backlog" is no longer used as a domain term.
- "backlog backend" / "backlog manager". Resolved: collapsed into **Issue tracker**.
