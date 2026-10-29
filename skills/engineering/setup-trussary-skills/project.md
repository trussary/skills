# Project

The facts about this repo that the workflow skills (`/implement`, `/implement-spec`, `/qa`, `/pr`, `/to-tickets`, `/wayfinder`, `/tdd`, `/research`, `/retro`) read instead of guessing. Each section is optional: a skill that finds a section missing falls back to the default it states, and says so in its hand-back.

Keep each section to the facts an agent cannot work out from the code in a minute. Delete a section rather than leave a placeholder in it.

## Layout

<!-- Where the code lives, and which paths count as "product code" for the Run record and CI selection. -->
- Product code: `<dirs, e.g. apps/ and packages/>`
- Design docs the code follows: `<dir, e.g. docs/design/>`; ADRs: `docs/adr/`

## Dev stack

<!-- How /qa and a human start the app from a checkout, and how to find its port. -->
- Start: `<command, e.g. make -C <abs checkout> dev>`
- Port: `<where the dev server prints it>`
- Parallel checkouts: `<env vars that move ports when another checkout holds them>`

## Checks

<!-- What an implementer runs while building, and once before hand-back. -->
- While building: `<focused test command, with a worker cap if checkouts share a machine or database>`
- Before hand-back: `<one command that runs what CI selects for the diff, or the full lint + typecheck + test>`
- Shared services: `<e.g. one Postgres shared by every checkout; each test run creates its own databases>`

## Generated files

<!-- How to resolve a merge conflict in a file that is generated or merged by key. One bullet per file. -->
- `<path>`: take either side, then `<regenerate command>`.

## Test suite

<!-- Stack-specific rules /tdd applies on every cycle: runner commands, fixtures, tiers, parallelism. -->

## UI and QA

<!-- What /qa and /prototype compare against. -->
- Design system: `<link or path>`
- Widths: `<e.g. 390, 860, 1280; which is primary>`
- Users to act as: `<roles>`
- Copy checks: `<locales, glossary, message-file check command>`

## Run record

<!-- Which PRs must end with the `## Run` record from docs/agents/models.md, and what checks it. -->
- Required when the PR changes: `<paths>`
- Checked by: `<CI job or script, or "nobody">`

## Paid APIs

<!-- How a /research probe calls a paid or keyed API without leaking keys or spend. -->

## Planning

<!-- Labels and budgets /wayfinder, /to-spec and /to-tickets use. -->
- Roadmap label: `<e.g. roadmap>`; slice label: `<e.g. slice>`
- Implementer context budget: `<e.g. 150k tokens, of which ~105k is fixed>`; read budget: `<e.g. 45k>`
- Read-budget skips: `<generated files read-budget.py leaves out, passed as --skip>`
- Shared contracts: `<shapes other tickets build on, which make a ticket a contract ticket>`
- Owners and tracks: `<who owns which slices, their handles, and track labels; omit for a solo repo>`

## Pull requests

<!-- /pr and /implement conventions. -->
- Branches: `<e.g. <issue#>-<slug>>`; merge: `<e.g. squash>`; `<one ticket per PR?>`
- PR prose language: `<e.g. English>`
- Review: `<e.g. no cross-review; PRs on a shared contract get the contract label and cc the other owner>`
