# Port settled prototypes

Porting brings approved screens into the unified prototype (the directory `## UI and QA` of `docs/agents/project.md` names, default `prototypes/unified/`) as a **faithful port**: the source file's markup, CSS and behaviour copied as-is. The only changes are the ones a named source settles (a decision table, an ADR, `GLOSSARY.md`) and the swap to shared parts (design-system components, the unified prototype's shared shell and string files). Read the unified prototype's README first for the file map.

## 1. Brief

Step 0 of the [SKILL](SKILL.md), filled per area: source branch and file, the inventory rows and decisions that touch it (from the port sources in `## UI and QA`, or the ticket), the ADR lines that fix its scope. Confirm the brief with the user before building. A ticket that names no source branch and no decision table goes back to the user.

## 2. Copy verbatim

`git show <source-branch>:<path> > <unified-dir>/<file>` and commit that copy alone (`port: copy <source> verbatim`), so the next diff shows only the adaptation. Read the source file from git, whole, never retyped from memory or a summary.

## 3. Adapt

Change only what step 1 listed: decisions, shared shell and DS parts, EN source strings. Use design-system components exactly as their `preview.html` shows them.

## 4. Pilot, then fan out

Port one area end to end and show the user side-by-side screenshots: source prototype and port, same state, same width. Wait for their visual sign-off. Only then hand the remaining areas to parallel agents, each started with a fresh context window and its own step 1 brief and the signed-off pilot as the reference.

Done when every ported screen matches its source in a side-by-side screenshot, except the listed decisions.

## 5. Republish

1. Read the live artifact (URL in `## UI and QA` or the unified prototype's README) with the Artifact tool (`action: read`) and merge anything published there that main lacks.
2. List `git branch -a --no-merged main | grep <prototype-prefix>` (default `prototype/`); for each branch, `git log main..<branch> -- <unified-dir>` shows unified-prototype work not yet on main. Merge that work first.
3. Publish `<unified-dir>` to the same URL.
