# Project

Brio's project facts for the trussary-skills workflow. Brio is an IELTS teaching tool: FastAPI backend in `apps/api`, Next.js web in `apps/web`, shared packages in `packages/`. This file is the merged example; skills read the section headings.

## Layout

- Product code: `apps/` and `packages/` (`apps/api` the Python API, `apps/web` the web app, `packages/` shared packages such as the design-system tokens `packages/ds`). Fixer areas under `/implement-spec`: `apps/api`, `apps/web`, `packages/`.
- Design docs the code follows: `docs/design/` (`jobs.md`, `api-conventions.md`, `module-contracts.md`, ...); ADRs: `docs/adr/`. A ticket or spec names the ones to read; a deliberate deviation edits that doc in the same commit.
- Prototypes: `prototypes/`. The Spec reviewer's leftover-reference grep covers code and `docs/`, excluding `prototypes/`.
- `.claude/settings.json` sets `env.TRUSSARY_GUARDED_ROOTS=apps,packages` and `env.TRUSSARY_NEVER_READ=apps/web/src/api/schema.d.ts`, so the `shell-write.py` hook guards `apps/` and `packages/`, and the `large-read.py` hook always denies reading `apps/web/src/api/schema.d.ts` (grep it: `rg -n 'TypeName' apps/web/src/api/schema.d.ts`, or use codegraph_explore).
- The `shell-write.py` hook exists because the 2026-10-29 retro counted 26 Edit calls against ~410 shell writes in one /implement-spec run.
- Prototype files are not in codegraph: take the lines from the scout brief of the prototype skill, find them with `grep -n`, or Read with offset/limit <= 200.

- Example paths the skills used to cite: `apps/api/src/brio/modules/authoring/domain/exam_edit.py`, `ChatScreen.tsx`.
- Helper scripts live in `scripts/` in Brio (`scripts/read-budget.py`, `scripts/cleanup-merged.sh`, `scripts/subagent-peaks.py`); the plugin ships the same tools in `tools/`. (source: pr, to-tickets, wayfinder)

## Dev stack

- Start: `make -C <abs checkout> dev` in the background (or `pnpm --dir <abs checkout> dev` where `make` is missing). `make dev` seeds the dev data. (`/implement-spec` starts one `make dev` stack from a QA worktree after the first wave with UI is merged). After fast-forwarding the QA worktree, HMR reloads; restart the stack after a migration.
- Test Postgres: if `docker ps` shows a compose Postgres on `127.0.0.1:5432`, use it; otherwise start one with `make -C <main checkout> up` (the main checkout is the first line of `git worktree list`).
- After merge, remove any test container an agent started by hand (`docker ps -a`: names like `pg-*` or `agent-*`; the compose `*-postgres-1` stays).
- Shell: zsh on macOS. Quote globs and words that start with `=` (`'--include=*.py'`, `'==='`); `grep` is ugrep, so prefer `rg` for long regexes.
- Plain-command examples for worktree permission checks: `git -C <abs worktree> ...`, `uv run --directory <abs worktree>/apps/api ...`, `pnpm -C <abs worktree> --filter web ...`.
- `cleanup-merged.sh` also runs from the SessionStart hook in `.claude/settings.json` (`--merged`), so a merge needs no prompt.

- Port: the web port is the one the dev server prints, `@brio/web:dev: - Local: http://localhost:<port>`; checkouts differ, so read it rather than assume 3000. `capture.mjs` used to default to `http://localhost:$BRIO_WEB_PORT`; pass `BASE_URL=http://localhost:$BRIO_WEB_PORT` (or the printed port) now.
- Parallel checkouts: when another checkout holds the ports, prefix `BRIO_PG_PORT=5433 BRIO_MINIO_PORT=9100 BRIO_MINIO_CONSOLE_PORT=9101`.
- Stop: a stack a /qa run started is stopped afterwards with `docker compose --project-directory <abs checkout> down -v`; a stack that was already up keeps running.

## Checks

- While building: only the test files you touch, `uv run --directory <abs worktree>/apps/api pytest <paths> -n 2` at most, and the one package's typecheck or lint you changed.
- Before hand-back: `scripts/ci-select-run.sh <base> <abs worktree>` (`<base>`: the integration branch under `/implement-spec`, `origin/main` under `/implement`; selection rules live in `.github/ci-modules.toml`). The merger runs `scripts/ci-select-run.sh <integration tip before the batch> <abs worktree> 4` when any branch of a batch needed a real merge.
- After a merge batch: no conflict markers remain (`git -C <wt> grep -nE '^(<<<<<<<|=======$|>>>>>>>)'`) and Alembic shows exactly one head (`uv run --directory <wt>/apps/api alembic heads`).
- Shared services: all checkouts share one Postgres; each pytest run creates and drops its own databases (`apps/api/tests/conftest.py`), so worktrees never need their own server.
- CI: the workflow is `ci`. A dispatched `gh workflow run ci` skips `images-check` (pull_request only), which the run after the ready transition covers.

## Generated files

- `apps/web/src/api/schema.d.ts`: take either side, then regenerate with `pnpm -C <abs worktree> --filter web gen:api`. It is only ever generated. Agents grep it, they do not read it; `read-budget.py` skips it (see `## Planning`).
- `en.json` / `vi.json`: keep the union of keys, then `pnpm -C <abs worktree> --filter web check:messages`.
- `uv.lock`: take either side, then `uv lock --directory <abs worktree>/apps/api`.

## Test suite

- Runner: `uv run --directory <abs worktree>/apps/api pytest <paths>`; worker cap `-n 2` while building, since checkouts share a machine and one Postgres.

Stack: FastAPI backend tested with pytest, Next.js web tested with Vitest.

Keep the red-green loop small:

```bash
pytest tests/unit/scoring -x --lf      # one area, stop at first failure, rerun last failures
pytest -k "band and not slow"          # filter by name
pytest --testmon                       # only tests affected by changed code (pytest-testmon)
vitest related src/scoring/band.ts     # Vitest: tests touching a file; plain `vitest` watch does this by module graph
vitest --changed HEAD~1
```

Make each test fast:

- Keep domain logic (scoring, band conversion, Citation checks, Profile) pure, with I/O pushed to the edges.
- In-memory fakes: e.g. a `FakeAttemptRepo` backed by a dict. Mock only at architectural boundaries: LLM, ASR, storage, email, clock.
- Expensive setup once per session or module: `@pytest.fixture(scope="session")`, Vitest `globalSetup`.
- DB tests run against Postgres in Testcontainers; wrap each test in a transaction and roll it back instead of truncating or re-migrating.
- Find slow tests with `pytest --durations=20` or Vitest's reporter timings.

Less test code, same coverage:

- Parametrize with `@pytest.mark.parametrize`, `it.each`.
- Property-based tests for large input spaces (spelling variants in an Answer key, word limits, band rounding): Hypothesis, fast-check.
- Factories: factory_boy, `@faker-js/faker`, or a hand-rolled `aQuestion().withSkill("TFNG").build()`.

Tiers:

```
tests/
  unit/          # pure, ms each, run constantly
  integration/   # real Postgres via Testcontainers; run before push and in CI
e2e/             # Playwright, written by /qa only for flows worth re-running; never a regression gate
```

- Mirror `src/` under each tier.
- Select tiers with `@pytest.mark.integration` (`pytest -m "not integration"`), and in Vitest with separate workspace projects or `*.int.test.ts`.

Parallel and healthy:

- `pytest -n auto` (pytest-xdist); Vitest runs in parallel by default.
- CI shards when the suite grows: `vitest --shard`, `pytest-split`.
- Randomize order: `pytest-randomly`, `vitest --sequence.shuffle`.
- Mutation testing by hand (mutmut, Stryker) on scoring and band conversion.

- In the PR body's `Removed tests:` line, name each removed test as Python `test_*`, or the vitest title, with why. (source: pr)

## UI and QA

- Copy skill for the hand-back's `Skills called` line: `vietnamese-education-copy <n | no VI strings>`.

- Design system: [Brio design system](<design system artifact link>) (README at `project/README.md`): tokens, components, and the Vietnamese UI terms in its README. A design system that the ticket or its map names overrides this link.
- Design system styling rules (for prototypes): borders are 0.5px `trans-10` hairlines; shadows sit only on the main card (`shadow-app-section`) and popovers (`overlay-elevated` + `shadow-popover-glow`). Mark state with dots, chips or a `trans-yellow` fill. Take `bundle.js` / `bundle.css` fresh from the artifact's `project/components/`, never from an older prototype; `prototypes/unified/README.md` shows how to check a copy against the published one.
- Widths: 390, 860 and 1280 px; Students use phones, so 390 is primary (overflow, wrapping and clipping checked at 390). These are capture.mjs's defaults, so no `QA_WIDTHS` is needed.
- Users to act as: the Teacher and a Student. Sign in at `/dev/sign-in?next=<path>`: `<admin dev email>` for the Teacher, `<student dev email>` for a Student of "Dev Class". To switch role in one flow, sign in again as the other account; set up a role whose screens are not under test through the API instead (`POST /api/auth/dev-sign-in`, then the requests). Use it the way a Teacher or Student would.
- Sign-in module for capture.mjs: `QA_SIGN_IN=<path to the module below>`, shot roles `teacher` and `student`. Save it in the Brio repo (e.g. `e2e/qa-sign-in.mjs`) or the scratchpad. It makes the session the way `e2e/auth.setup.ts` makes the Teacher's:

  ```js
  // QA_SIGN_IN module for capture.mjs: signs the request context in as "teacher" or "student".
  const ACCOUNTS = { teacher: "<admin dev email>", student: "<student dev email>" };

  export default async function signIn(request, as, base) {
    const headers = { "X-Brio-Client": "web", Origin: new URL(base).origin };
    const signedIn = await request.post("/api/auth/dev-sign-in", { data: { email: ACCOUNTS[as] }, headers });
    if (signedIn.status() !== 204) throw new Error(`dev sign-in as ${as}: ${signedIn.status()} (DEV_SIGN_IN on? brio seed-dev run?)`);
    const me = await (await request.get("/api/me")).json();
    const mine = me.memberships.filter((m) => m.app === as);
    const membership = mine.find((m) => m.workspace_kind === "organization") ?? mine[0];
    if (!membership) throw new Error(`${ACCOUNTS[as]} has no ${as} membership (run brio seed-dev)`);
    await request.patch("/api/me", { data: { current_membership_id: membership.id }, headers });
  }
  ```

  `teacher` signs in as dev-admin in its organization Workspace; `student` as dev-in-class-1.
- Copy checks: Vietnamese UI copy and glossary terms (`GLOSSARY.md`, design system README).
- E2e flows worth a Playwright spec: the offline answer queue, submitting, Exam score hiding, sign-in and invitations.
- QA Evidence language: headings stay English; prose is Vietnamese; Vietnamese UI copy under test is quoted verbatim.
- Sharing the QA Evidence artifact: tell the user that sharing it with the other devs is the user's call.

### Prototypes

- Unified prototype: `prototypes/unified/`, on main, the approved reference for every UI ticket. File map, Serve instructions and the live artifact URL are in `prototypes/unified/README.md`. Shared parts to swap in when porting: DS components, `shell.js`, `i18n.js`. Scout briefs check DS components and icons per that README, globals, `CASE` keys, seed ids and localStorage prefixes.
- Serving in a worktree: a prototype in a worktree is served through `.claude/preview` and the `prototypes-wt` entry, per `prototypes/unified/README.md` (Serve); `launch.json` stays as it is.
- The unified prototype's local server serves React's development build, so runtime errors arrive with names.
- Prototype branch prefix: `prototype/` (republish lists `git branch -a --no-merged main | grep prototype/`).

### Prototype port sources

- The #78 inventory: `docs/research/prototype-inventory.md` on branch `research/prototype-inventory`.
- The #79 decision tables, in that issue's "Kết quả" section. A port changes only what the #79 decision table, an ADR or `GLOSSARY.md` settles.
- The #80 design system (the link above).
- Scope-fixing ADR example: ADR 0008 fixes which Material types an upload accepts.

- Screenshots live in the QA Evidence artifact that `/qa` publishes, never in git: for a ticket with UI, the PR's Evidence is the artifact link plus a one-line verdict, with no images in the PR body. Template wording: `**Before:** <output/failing test run, or for a UI ticket the QA Evidence artifact link>`, `**After:** <output/passing test run, or for a UI ticket the QA Evidence link and its verdict>`. (source: pr)
- `.claude/preview/` is a directory of links into worktrees (`prototypes/unified/README.md`); `cleanup-merged.sh` drops the links that dangle after a worktree is removed. (source: tools/cleanup-merged.sh)

## Run record

- Required when the PR changes: `apps/` or `packages/`.
- Checked by: the `changes` CI job (`.github/scripts/run-record.py`); it fails on a missing field, a non-number count, or a findings line saying `/code-review` did not run. Fix the body, then re-run the job.

- Required when the PR changes `apps/` or `packages/`; a PR that touches neither leaves it out. (source: pr)
- Checked by: CI's `changes` job (`.github/scripts/run-record.py`); its findings line is the count from a /code-review that ran on the branch. (source: pr)
- The Peak-context limit `subagent-peaks.py` flags is 150k (`--limit 150`, the default). (source: tools/subagent-peaks.py)

## Paid APIs

A research probe that spends money goes through `AiClient` (`brio.shared.ai`, inside `measuring.measuring_client(max_usd=..., use="research")`), never a raw call to `openrouter.ai/api`: every paid call then leaves an `ai_call` row, the run stops at its limit and prints its total. That spends on `OPENROUTER_RESEARCH_API_KEY` (ADR 0017 "One OpenRouter key per use") and stops if it is not set; never pass the dev app's key. Keyed APIs probed include OpenRouter.

## Planning

- Implementer context budget: 150k tokens (implementer, fixer and QA subagents).
- Implementer concurrency: at most 3 implementers and fixers at once. Spec #1164 ran 13 at once and each ticket took 77 to 102 minutes, single typechecks 18 minutes; #1183 ran 3 and its tickets took 10 to 25.

- Structure: the roadmap (a GitHub issue labelled `roadmap`) splits a phase into vertical slices, and each slice is a wayfinder map labelled `slice`; a large slice has sub-maps. A spec covers one leaf map (a slice, or a sub-map of one), written once that map has reached its destination. `/to-tickets` then breaks the spec into tickets, and `/implement-spec` builds them. (source: to-spec)
- Roadmap label: `roadmap`; slice label: `slice`. Before creating a map, list the existing slice and map titles: `gh api --paginate 'repos/trussary/brio/issues?labels=slice&state=all&per_page=100' --jq '.[] | {number, title}'`, and pick a name none of them uses. (source: wayfinder)
- Implementer context budget: under 150k tokens. About 105k of that is fixed, measured on spec #1128's implementers: ~31k before the agent reads a file, ~75k on its own thinking, edits and command output. That leaves a read budget of ~45k: the code it must read, any prototype, the ADRs and docs it names, and the tests. (source: to-tickets)
- Evidence for the budget: #1140 was estimated at 45k from module names; the script reads 50k for its files, and the agent peaked at 230k. The 150k is a target, not a measured fit: #1167 and #1187 (spec #1164, #1183) peaked at 202k and 222k with ~60-65k of command output from ~100 small `sed`/`rg` reads (no one big file) and ~55-75k of their own thinking and edits. (source: to-tickets)
- Read-budget skips: `--skip apps/web/src/api/schema.d.ts` on every `read-budget.py` run (agents grep it, they do not read it). (source: tools/read-budget.py)
- Depth cost: every level of the ticket graph costs about 13 minutes of wall time (9 to 21, measured on 5 specs, issue #411). (source: to-tickets)
- Wayfinder ticket size: about 100K tokens of work in one agent session, on top of the ~95K every session starts with. (source: wayfinder)
- Shared contracts: Question, Skill, Answer key, Citation, Response, Attempt, the API between web and backend, a DB migration. A slice or PR that changes one is its own ticket/PR, labelled `contract`. (source: to-tickets, pr, wayfinder)
- Owners: two devs, `@<dev-a>` and `@<dev-b>`. A `contract` PR ends its body with `cc @<the other dev>`. (source: pr, wayfinder)
- Tracks: label each ticket `track:<dev-a|dev-b|shared>`. Each slice belongs to one dev, so a contract change inside the slice alone reaches no one: at wayfinder resolution, list the open tickets of the other dev, outside this map, that the change affects, and draft a `cc @<other dev>` brief comment for the user to post. (source: to-tickets, wayfinder)
- Ticket titles: `<Context>: <verb + outcome>`, with context names and glossary terms in English. (source: to-tickets)
- Example Executor line: "opus: changes the Exam transition table". Example Read budget line: "38k: `apps/api/src/brio/modules/authoring/domain/exam_edit.py`, its tests, `ChatScreen.tsx`". (source: to-tickets)

## Pull requests

<!-- No template heading yet: setup-trussary-skills/project.md needs a `## Pull requests` section for these. -->
- Branch: `<issue#>-<slug>`, cut from the latest `main`, one ticket per PR (an `/implement-spec` integration branch carries one spec). Squash merge. (source: pr)
- Language: write the prose of the PR body in Vietnamese. Keep in English: the PR title (squash merge makes it the commit subject), the template's section headings and labels (Summary, Evidence, Before, After, Merge Danger, Door, Blast Radius, one-way, two-way), technical terms and `GLOSSARY.md` terms (Material, Activity, Skill, Exam, Response, Citation...), code, identifiers, file paths, branch names, commands, test names and pseudocode. Write natural Vietnamese, not a word-for-word translation. (source: pr; appeared in the conventions list, the template intro and the Sections intro)
- Review: no cross-review. The human merges once CI is green, after /code-review (and /qa for UI). A `contract` PR gets /code-review too, docs-only included. (source: pr)
- Contract PRs: cc the other dev (see `## Planning` owners). An objection from the cc'd dev is raised as a new issue; it doesn't block the PR. (source: pr)
- After merge: the SessionStart hook in `.claude/settings.json` (`matcher: startup`) runs `nohup "$CLAUDE_PROJECT_DIR"/scripts/cleanup-merged.sh --merged > "$(git -C "$CLAUDE_PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir)/cleanup-merged.log" 2>&1 &`, so every new session sweeps merged branches (log: `.git/cleanup-merged.log`). (source: pr, tools/cleanup-merged.sh)
