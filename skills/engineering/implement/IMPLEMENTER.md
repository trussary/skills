# Implementer brief

How one ticket gets built: by `/implement`, and by every implementer subagent of `/implement-spec`. Repo facts come from `docs/agents/project.md`; where a section named below is missing, use the fallback given and say so in the hand-back.

## Before code

1. Read the ticket with `gh` per `docs/agents/issue-tracker.md`.
2. Under `/implement-spec`: confirm your worktree is based on the integration branch, and reset onto it if not.
3. If the ticket has a `## Prototype` section, read every linked prototype with the Artifact tool (`action: "read"`). The prototype is the target for layout, flow and UI copy.
4. Read every ADR and design doc the ticket or spec names (the design-docs directory is in `## Layout`; default `docs/design/`). The code follows them; a deliberate deviation edits that doc in the same commit.
5. Start from your section of the exploration notes, when the prompt names one. To see any code beyond it: if a codegraph MCP server is configured, query `codegraph_explore` with the symbol names (one call returns their current line-numbered source, safe to Edit from, plus callers and tests); otherwise find the symbol with `rg -n` and Read its lines. Read a file only for its exact lines (offset/limit ≤ 200); after an edit, check your change with `git -C <abs worktree> diff`. A hook enforces this on files over 400 lines. Your context budget is the implementer budget in `## Planning` (150k if unset), so every file you read once stays in it for the whole ticket.

## Shell

Worktree permission checks pass only plain commands, so:

- One plain command per `Bash` call, with literal absolute paths: `git -C <abs worktree> ...`, and the directory flag of the repo's own tools (`<tool> --directory <abs worktree>/<pkg> ...`, `<tool> -C <abs worktree> ...`).
- Change existing files with Edit, so only the changed lines leave your context; Write is for new files. The plugin's shell-write hook blocks `sed -i`, `>` redirects and inline Python that write into product code.
- Multi-step logic, pipes and loops go into a script file in the scratchpad, run by its path. Such a script reads and checks; the edits it would make go through Edit.
- Wait with `run_in_background` or the Monitor tool; Monitor is deferred, so load it once with `ToolSearch` (`select:Monitor`) before the first call.
- Shell quirks of the machine (quoting, which `grep`) are in `## Dev stack`.

## Test database

Shared services the tests need (a database every checkout shares, how each run isolates itself, how to start it) are in `## Checks` "Shared services" and `## Dev stack`. Don't start a private server per worktree when the section says one is shared. With no such section, follow the repo's test docs.

## Build

- Call the Skill tool with `tdd` at the seams the ticket or spec names; if none are named, pick the highest existing seam and state it in the hand-back. Watch each new test go red before making it pass.
- On Sonnet: before your first Edit, call the `advisor` tool once with your plan for each seam and how each acceptance bullet will be shown done, then again when the same failure goes red twice (`docs/agents/models.md`, When the executor consults the advisor). On Opus, only the second.
- While building, run only the test files you touch and the one package's typecheck or lint you changed, with the "While building" command and worker cap of `## Checks`.
- Under `/implement-spec`, read the earlier waves' findings file when the prompt names one before your first edit: the same mistake in your ticket is a finding of the next wave.
- Before hand-back, run the "Before hand-back" command of `## Checks` once (`<base>`: the integration branch under `/implement-spec`, `origin/main` under `/implement`); with no such section, run the repo's lint, typecheck and the tests of the packages you changed. Under `/implement-spec`, merge the integration branch tip into your branch first, so the merger can fast-forward your branch without checks. Rerun it only after fixing what it reported. The full suite runs once, in CI at the end.

## Generated files

Resolve a conflict in a generated or key-merged file per `## Generated files` of `docs/agents/project.md`. With no entry for a file: a generated file takes either side and is regenerated with its generator; a message or translation file keeps the union of keys; a lockfile takes either side and is relocked.

## Hand-back

Wait for any subagent you started before reporting. Report in this shape:

```
Ticket #<n>, branch <branch>, head <sha>
Acceptance: one line per bullet: done (`path::test_name` or the check that shows it) | deferred (reason)
QA: per UI bullet: checked in a browser (width) | left to the integration QA (reason) | no UI
Red first: the tests you watched fail before they passed
Outside the ticket's file list: <paths and why> | none
Doc edits: <ADR or design docs changed> | none
Skills called: tdd <n>, <each copy skill `## UI and QA` names> <n | no strings>, advisor <n>
```
