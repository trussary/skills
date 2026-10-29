---
name: prototype
description: Build a throwaway prototype to answer a design question, or port settled prototypes into the unified prototype. Checking and publishing need the Claude desktop app (its built-in browser pane and the Artifact tool). Use when the user wants to sanity-check whether a state model or logic feels right, explore what a UI should look like, or merge, port or republish prototypes.
---

# Prototype

Checking a prototype in the browser and publishing it need the Claude desktop app: the built-in browser pane (`mcp__Claude_Browser__*` tools) and the Artifact tool. Without them, build the files and hand the user the path to open.

Project facts come from the `## UI and QA` section of `docs/agents/project.md`: the design system, the unified prototype's directory and live URL, the prototype branch prefix, how a worktree serves prototypes, and the port sources (inventory, decision tables). A missing fact falls back to the default given here.

A prototype is **throwaway code that answers a question**. The question decides the shape.

## 0. Name the inputs

Before any code, write down in the prototype's plan line or top-of-file comment:

- **Sources of truth**: the source prototype files and branches, the inventory and decision tables (for settled prototypes, the ones `## UI and QA` lists under its port sources, or the ticket names), the design system, and the ADR or spec lines that fix scope (accepted file types, roles, states). Read the ADRs the ticket touches; for example, an ADR may fix which file types an upload accepts.
- **One sentence** saying what is ported from a source and what is invented here.

Done when every element the prototype shows traces to a named source or to the invented list. If the ticket names no source of truth, ask the user which sources apply before building.

## 0b. Scout brief

Every token read during orientation is carried by every later call of the session, so the reading goes to a subagent. Dispatch one `Explore` subagent (`model: "sonnet"`), started with a fresh context window, with the step 0 sources and the question. It returns a **scout brief**, not prose:

- for each file to touch: the `file:line` range and the exact existing string at every hook point a patch will anchor on;
- names checked to exist: design-system components and icons (per the unified prototype's README, when the project keeps one), globals, case or fixture keys, seed ids, localStorage prefixes;
- the load order the new file joins and the page that hosts it.

Build from the brief. Open a file yourself only on the lines the brief names, or when a patch anchor fails.

## Pick a branch

Identify which question is being answered, using the user's prompt, the surrounding code, or by asking if the user is around:

- **"Port, merge or republish settled prototypes"** → [PORT.md](PORT.md). A faithful port of approved screens into the unified prototype, never a rebuild.
- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file (free-play buttons plus tabbed guided walkthroughs) that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

The branches produce very different artifacts, so getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption at the top of the prototype.

## Rules that apply to every branch

1. **Throwaway from day one, and clearly marked as such.** Locate the prototype code close to where it will actually be used (next to the module or page it's prototyping for) so context is obvious, but name it so a casual reader can see it's a prototype, not production. For throwaway UI routes, obey whatever routing convention the project already uses; don't invent a new top-level structure.
2. **Trivial to run.** A UI prototype starts from one command in the project's task runner: `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file the user double-clicks. Either way, no thinking required to start it. A prototype in a worktree is served the way `## UI and QA` describes, without editing the shared launch config.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE, wipe me" name.
4. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
6. **Follow the project's design system.** Read its README before styling: the design system the map's Notes or the ticket names, else the one in `## UI and QA`, else the tokens and components already in the codebase. Apply the styling rules listed there (borders, shadows, how state is marked). Take the design system's component bundle fresh from its source, never from an older prototype; the unified prototype's README, when there is one, shows how to check a copy against the published one.
7. **Capture it when done.** Fold any validated decision into the real code, then capture the prototype itself as a **primary source**: commit it to a throwaway branch (the prefix `## UI and QA` names, default `prototype/`), out of main, and leave a context pointer to that branch on the implementation issue. Capture the answer too (the verdict and the question it settled) in the issue or a commit. The main branch keeps only the validated decision. The one exception is the unified prototype (when the project keeps one; default `prototypes/unified/`), which lives on main as the approved reference for every UI ticket.
