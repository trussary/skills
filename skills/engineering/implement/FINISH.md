# Finish: Definition of Done, PR, CI, cleanup

Shared by `/implement` and `/implement-spec`. `<owner>/<repo>` is the repo slug in `docs/agents/issue-tracker.md`; the CI workflow name and its jobs are in `## Checks` of `docs/agents/project.md` (below, `ci` stands for the workflow that runs on pull requests).

## Definition of Done

A ticket is done when all of these hold:

1. Domain logic is covered by tests written with /tdd.
2. /code-review raises nothing serious.
3. Tickets with UI: /qa reports the screens match the prototype.
4. Every acceptance bullet is met. Deferred work (unmet bullets you chose to defer, refactors, untested paths) goes into one follow-up issue that the PR body links. Only a real decision goes to the user before the PR is ready: whether to fix a bullet now or change the ticket. The PR body reports met criteria and the follow-up issue.
5. A PR is open (body written with /pr, `Closes #<n>` for every ticket it resolves), every commit is pushed (`git status -sb` level with the remote), and CI is green. For `/implement-spec`, "green" means the `ci` run that followed the ready transition.
6. After a human merges it: the change is deployed to staging (once staging exists) and the flow checked there; the ticket is closed by `Closes #<n>`.

## PR and CI

### Single ticket (`/implement`)

Unchanged by the integration-branch flow below: the PR opens ready (created without `draft=true`), so CI runs on every push.

1. Push the branch and open the PR with `gh api repos/<owner>/<repo>/pulls -f title=<title> -f head=<branch> -f base=main -F body=@<file>`, body per /pr, ending with the `## Run` record in `docs/agents/models.md` (Run record); `## Run record` of `docs/agents/project.md` may limit it to PRs that change certain paths. Update its red CI rounds once CI is green.
2. Watch CI (`gh pr checks <pr> --watch`). On a red check, read the failing log (`gh run view <run-id> --log-failed`), fix, push, and watch again. Repeat until every check is green.
3. A flaky test is not a fix target to retry blindly: quarantine it with a skip that links a new issue, per /tdd.
4. Stop when CI is green. Report the PR link; the human merges.

### Integration branch (`/implement-spec`)

A draft PR runs no CI; its `ci` check is green or skipped on every push. A green `ci` on a draft is not a merge signal and not a "notify" signal.

1. **Draft until the end.** Push each merge to the draft PR; ignore its `ci` check.
2. **Parallel full CI.** When the last ticket is merged, dispatch one full run and keep its id:
   ```bash
   gh workflow run ci --ref <integration-branch>
   gh run list --workflow ci --event workflow_dispatch --branch <integration-branch> --limit 1 --json databaseId,createdAt
   ```
   (`gh workflow run` prints no run id; confirm `createdAt` is after the dispatch.) The run is not a PR check; it goes on while `/qa` runs. It skips any job that runs on `pull_request` only (`## Checks` names them), which the final run covers. Read it with `gh run watch <run-id>` (in the background), and on red `gh run view <run-id> --log-failed`.
3. **Mark ready.** Once the dispatched run has finished, `/qa` has passed and the fixes are pushed, write the PR body per /pr ending with the `## Run` record into a file and record the time. With a draft, apply the body with the PR-body `gh api` call in `docs/agents/issue-tracker.md` (`gh pr ready` does not set it), then mark it ready (`gh pr ready <pr>` locally; in a cloud session, which refuses GraphQL, `gh api -X POST repos/<owner>/<repo>/pulls/<pr>/ccr/ready_for_review`); with no draft, create it with the `gh api .../pulls` call in step 1 (opens ready) and skip the ready step. Either starts one full `ci` run.
4. **Watch the run after ready.** `gh pr checks` right after `gh pr ready` shows the stale draft result and returns at once; do not use it. Find the `pull_request` run for the head sha created after the time you recorded, then watch it:
   ```bash
   gh run list --workflow ci --event pull_request --branch <integration-branch> --json databaseId,headSha,createdAt
   gh run watch <run-id> --exit-status
   ```
   On red, read the log, fix, push, and watch the next run on the new head sha. Quarantine a flaky test per /tdd, as in the single-ticket flow.
5. **Notify.** When that run is green, update the `Red CI rounds` line of the PR body (count per `docs/agents/models.md`, Run record) and send the PushNotification tool (deferred; load it with ToolSearch `select:PushNotification`) with the PR link. If the tool is missing, put the link at the top of the final report. The human merges; agents never run `gh pr merge`.

## Cleanup after merge

When the PR shows `MERGED`, or the user says it is merged, run `<plugin root>/tools/cleanup-merged.sh <branch>` per /pr, then remove any test container an agent started by hand (`## Dev stack` names which containers are the agents' and which stay).

A follow-up PR targets `main` (`base=main` in the create call): an integration branch is deleted at merge, and GitHub closes every PR based on it.
