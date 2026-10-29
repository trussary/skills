#!/usr/bin/env bash
# Clean up after a merged PR: remove its worktree(s), delete the local branch,
# fast-forward local main, and drop dangling links in .claude/preview/ (into removed worktrees).
# The remote branch is left alone: GitHub deletes it on merge.
#
# Usage: tools/cleanup-merged.sh <branch | PR number>
#        tools/cleanup-merged.sh --merged
# --merged sweeps every local branch whose PR is MERGED. It skips a worktree with local
# changes or one that a running process (a live session, a dev server) has as its cwd.
# setup-trussary-skills can wire --merged as an opt-in SessionStart hook, so a merge needs no prompt.
# Every GitHub call is REST (`gh api`): cloud sessions refuse GraphQL, which `gh pr` uses.
set -euo pipefail

arg="${1:-}"
if [ -z "$arg" ]; then
  echo "usage: $0 <branch | PR number> | --merged" >&2
  exit 2
fi

# Work from the main checkout (first entry of the worktree list), never from a worktree about to be removed.
main_dir=$(git worktree list --porcelain | sed -n '1s/^worktree //p')
cd "$main_dir"

git fetch --quiet --prune origin

# Worktree paths checked out on branch $1, main checkout excluded.
worktrees_of() {
  local wt=""
  while IFS= read -r line; do
    case "$line" in
      "worktree "*) wt=${line#worktree } ;;
      "branch refs/heads/$1") [ "$wt" != "$main_dir" ] && printf '%s\n' "$wt" ;;
    esac
  done < <(git worktree list --porcelain)
}

# Remove branch $1 and its worktrees. In sweep mode ($2 = sweep) a busy or dirty worktree
# is skipped with a note instead of failing.
clean_branch() {
  local branch=$1 mode=${2:-} wt
  while IFS= read -r wt; do
    [ -n "$wt" ] || continue
    if [ "$mode" = sweep ] && lsof -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' |
      awk -v p="$wt" '$0 == p || index($0, p "/") == 1 { f = 1 } END { exit !f }'; then
      echo "skipped $branch: a running process is in $wt"
      return 0
    fi
    if ! git worktree remove "$wt"; then
      echo "worktree $wt has local changes; inspect it, then remove it by hand." >&2
      [ "$mode" = sweep ] && return 0
      exit 1
    fi
    echo "removed worktree $wt"
  done < <(worktrees_of "$branch")
  git worktree prune
  if git show-ref --verify --quiet "refs/heads/$branch"; then
    git branch -D "$branch"
  fi
  echo "cleaned up $branch"
}

if [ "$arg" = "--merged" ]; then
  # The 200 most recently updated closed PRs, merged ones matched against local branches. A branch
  # counts only when its tip is in the merged PR head, so a reused branch name with new commits stays.
  merged=$(for page in 1 2; do
    gh api "repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100&page=$page" \
      --jq '.[] | select(.merged_at != null) | .head.ref + " " + .head.sha'
  done)
  current=$(git symbolic-ref --short HEAD 2>/dev/null || true)
  while IFS= read -r branch; do
    [ "$branch" = main ] || [ "$branch" = "$current" ] && continue
    oid=$(printf '%s\n' "$merged" | awk -v b="$branch" '$1 == b { print $2; exit }')
    [ -n "$oid" ] || continue
    if git merge-base --is-ancestor "refs/heads/$branch" "$oid" 2>/dev/null; then
      clean_branch "$branch" sweep
    else
      echo "skipped $branch: its tip is not in merged PR head ${oid:0:7}"
    fi
  done < <(git for-each-ref --format='%(refname:short)' refs/heads)
else
  # A number is the PR itself; a branch name is its latest PR.
  status='(if .merged_at then "MERGED" else (.state | ascii_upcase) end) + " " + .head.ref + " " + .head.sha'
  case "$arg" in
    *[!0-9]*) info=$(gh api "repos/{owner}/{repo}/pulls?state=all&head={owner}:$arg" --jq ".[0] // empty | $status") ;;
    *) info=$(gh api "repos/{owner}/{repo}/pulls/$arg" --jq "$status") ;;
  esac
  if [ -z "$info" ]; then
    echo "no PR found for $arg; nothing removed." >&2
    exit 1
  fi
  read -r state branch oid <<<"$info"
  if [ "$state" != "MERGED" ]; then
    echo "PR $arg is $state, not MERGED; nothing removed." >&2
    exit 1
  fi
  # Same guard as --merged: a reused branch name with commits past the merged head stays.
  if git show-ref --verify --quiet "refs/heads/$branch" &&
    ! git merge-base --is-ancestor "refs/heads/$branch" "$oid" 2>/dev/null; then
    echo "skipped $branch: its tip is not in merged PR head ${oid:0:7}; nothing removed." >&2
    exit 1
  fi
  clean_branch "$branch"
fi

# Preview links into a removed worktree dangle; drop them. .claude/preview, when a repo uses it,
# is a directory of links, never walked through when it is a link itself; absent, this is a no-op.
if [ -L .claude/preview ] && [ ! -e .claude/preview ]; then
  rm .claude/preview
  echo "removed dangling preview link .claude/preview"
fi
[ -L .claude/preview ] || for link in .claude/preview/* .claude/preview/.[!.]*; do
  if [ -L "$link" ] && [ ! -e "$link" ]; then
    rm "$link"
    echo "removed dangling preview link $link"
  fi
done

# Fast-forward local main when the main checkout is on main. Local edits stay: git refuses
# the merge only when an incoming change touches an edited file.
if [ "$(git symbolic-ref --short HEAD 2>/dev/null || true)" != "main" ]; then
  echo "main checkout is not on main; skipped fast-forward."
elif ! git merge --quiet --ff-only origin/main 2>/dev/null; then
  echo "git refused to fast-forward main (an incoming change touches a local edit, or main has diverged); skipped it."
fi
