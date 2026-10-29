---
name: tdd
description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests.
---

# Test-Driven Development

TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle: consult them before and during the loop, not after.

When exploring the codebase, read `GLOSSARY.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam. You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Ask: "What's the public interface, and which seams should we test?" Give each proposed seam a one-line note on what it catches and what it misses.

When the shape of that interface is itself in question (how deep the module is, where the seam belongs, what the interface should expose), call the Skill tool with "codebase-design" for the vocabulary. It is the shared source of the module, interface, depth, seam, adapter, leverage and locality terms, and it is a reference to consult, not a session to run.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

## Rules of the loop

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage (see the `code-review` skill), not the red → green implementation cycle.

## Keeping the suite fast and healthy

These rules apply on every cycle. The stack-specific half (runner commands, fixture scopes, tier markers, parallelism, the test database) lives in the `## Test suite` section of `docs/agents/project.md`: read it before the first cycle. If it is missing, work the runner and its options out from the repo's config files, and say so in the hand-back.

### Keep the red-green loop small

Run only the tests near the change while looping: one area, stop at the first failure, rerun the last failures, or only the tests affected by the changed files. Run the full suite before pushing, and CI runs it again.

### Make each test fast

Speed matters more than count: 2,000 tests at 2 ms are fine, 200 at 500 ms are not.

- Keep domain logic pure, with I/O pushed to the edges, so most tests need no DB, network or filesystem.
- Use in-memory fakes (a repository backed by a dict) instead of mocks or real infrastructure in unit tests. Mock only at architectural boundaries: LLM, external APIs, storage, email, clock. See [mocking.md](mocking.md).
- Create expensive setup once per session or module, not per test.
- DB tests run against a real database of the production engine; wrap each test in a transaction and roll it back instead of truncating or re-migrating.
- Find slow tests with the runner's duration report.

### Less test code, same coverage

- Parametrize near-identical cases instead of copy-pasting tests.
- For large input spaces (input variants, limits, rounding), use property-based tests. One property replaces dozens of examples.
- Build test data with factories or hand-rolled builders (`anOrder().withItems(2).build()`), so each test states only the fields it cares about and a schema change touches one builder.

### Test behavior, not implementation

- Test through a module's public interface, at the unit of behavior, not one test per method.
- If a refactor breaks many tests while behavior is unchanged, those tests are coupled to internals: rewrite them at the seam.
- Delete scaffolding tests once a higher-level test covers the same behavior.

### Tiers

- **Unit**: pure, milliseconds each, run constantly.
- **Integration**: real database and services; run before push and in CI.
- **E2e**: written by /qa only for flows worth re-running; never a regression gate.
- Mirror the source tree under each tier so it is obvious where a test lives, and select tiers by marker or file pattern.
- **Regression protection comes from unit and integration tests only.** E2e specs exist for /qa acceptance of a few fragile flows; a broken old e2e spec is fixed or deleted, never a reason to block a merge.

### Parallel and isolated

- Run tests in parallel. Tests must be independent: no shared mutable state, no fixed ports.
- CI runs lint, typecheck and tests as parallel jobs, caches dependencies, and shards when the suite grows.

### Keep it healthy

- Quarantine a flaky test immediately (skip it with a link to a new issue). A flaky suite trains people to ignore red.
- A change never leaves a **weakened** test: an assertion loosened or removed, an expected value edited to match new output without the spec asking for it, a test deleted with no higher-level test covering it, or a skip, `xfail` or `.only` without a linked issue. The quarantine above is the one allowed skip.
- Randomize test order to catch hidden coupling between tests.
- Coverage is a map of untested areas, not a target; there is no coverage threshold. Run mutation testing by hand on the core domain logic to check the tests actually catch bugs.

If the suite feels unmanageable, the cause is almost always too many slow tests touching I/O (make the logic pure) or too many brittle tests touching internals (test at the seam, delete the redundant ones). Fix those before reaching for tooling.
