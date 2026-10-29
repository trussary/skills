# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Every operation is a REST call, `gh api repos/trussary/brio/...`: cloud sessions refuse GraphQL and `/search`, and the `gh issue` / `gh pr` subcommands use GraphQL.

## Conventions

- **Create an issue**: `gh api repos/trussary/brio/issues -f title="..." -F body=@<file> -f 'labels[]=<label>'`. Write multi-line bodies to a file first.
- **Read an issue**: `gh api repos/trussary/brio/issues/<number> --jq '{title, state, body, labels: [.labels[].name]}'`, comments from `gh api repos/trussary/brio/issues/<number>/comments --jq '.[].body'`.
- **List issues**: `gh api --paginate 'repos/trussary/brio/issues?state=open&labels=<label>&per_page=100' --jq '.[] | select(.pull_request | not) | {number, title, labels: [.labels[].name]}'` (the endpoint returns PRs too; the `select` drops them).
- **Comment on an issue**: `gh api repos/trussary/brio/issues/<number>/comments -F body=@<file>`
- **Apply / remove labels**: `gh api -X POST repos/trussary/brio/issues/<number>/labels -f 'labels[]=<label>'` / `gh api -X DELETE repos/trussary/brio/issues/<number>/labels/<label>`
- **Edit an issue body**: `gh api -X PATCH repos/trussary/brio/issues/<number> -F body=@<file>`
- **Close**: **Comment on an issue**, then `gh api -X PATCH repos/trussary/brio/issues/<number> -f state=closed -f state_reason=completed`

Infer the repo from `git remote -v`; `gh` does this automatically when run inside a clone.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the `gh pr` equivalents:

- **Read a PR**: `gh api repos/trussary/brio/pulls/<number> --jq '{title, body, state, merged_at}'`, the diff from `gh api repos/trussary/brio/pulls/<number> -H 'Accept: application/vnd.github.diff'`.
- **List external PRs for triage**: `gh api 'repos/trussary/brio/pulls?state=open&per_page=100' --jq '.[] | {number, title, author_association}'` then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE` (drop `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Comment / label / close**: the issue calls above work on a PR (a PR is an issue for comments, labels and `state=closed`). Edit a PR body with `gh api -X PATCH repos/trussary/brio/pulls/<number> -F body=@<file>`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh api repos/trussary/brio/issues/42 --jq '{title, pr: (.pull_request != null)}'`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run the **Read an issue** command above.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Roadmap and slice maps (Brio)**: the roadmap is one issue labelled `roadmap`, listing slices in order with milestones. Each slice is a map labelled `wayfinder:map` + `slice`, a sub-issue of the roadmap; a large slice has sub-maps, each a sub-issue of its slice map. Every slice starts as an issue labelled `slice` (sub-issue of the roadmap) holding the wayfinder input: draft destination, scope, ADRs to read, prototypes and fog. Run `/wayfinder` on that issue about a week before the slice starts: charting turns the same issue into the map (rewrite its body with the map template, add `wayfinder:map`). A leaf map's destination is one spec ready for `/to-spec`; a map with sub-maps closes when every sub-map has closed.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. **Create an issue** with `labels[]=wayfinder:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (`gh api` on the sub-issues endpoint). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: GitHub's **native issue dependencies**, the canonical, UI-visible representation. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only, the live gate). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`gh api repos/trussary/brio/issues/<map>/sub_issues`, keep `state == "open"`), drop any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `gh api -X POST repos/trussary/brio/issues/<n>/assignees -f 'assignees[]=<login>'` (`<login>` from `gh api user --jq .login`), the session's first write.
- **Resolve**: **Comment on an issue** with the answer, then close with the **Close** command above, then append a context pointer (gist + link) to the map's Decisions-so-far.
