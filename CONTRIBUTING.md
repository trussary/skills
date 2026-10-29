# Contributing

## Changes to the skills

Open a PR against `main` with a changeset (`npx changeset`): `patch` for a wording or behaviour fix, `minor` for a new skill, subagent, hook or `docs/agents` section. The Release workflow opens a "chore: version skills" PR; merging it bumps `plugin.json`, which is what makes installed plugins update.

A change that only one project needs belongs in that project's `docs/agents/*.md` or `CLAUDE.md`, not here. `/retro` sorts its findings this way: project-specific ones edit the project, generic ones become a PR here.

Before a PR:

```bash
claude plugin validate .
python3 -m unittest discover -s hooks -p 'test_*.py'
```

## Pulling from upstream

This repo is a fork of [mattpocock/skills](https://github.com/mattpocock/skills). When upstream releases:

```bash
git fetch upstream
git switch -c sync-upstream origin/main
git merge upstream/main
```

- Conflicts in a skill we changed: keep ours, then take upstream's improvement by hand when it does not fight ours.
- Files we removed (`docs/engineering`, `docs/productivity`, `.out-of-scope`, `ask-matt`): keep them removed.
- A new upstream skill: leave it out of `plugin.json` until someone has used it in a real project.
- Check the merged prose for duplicated or contradicting sentences, then add a `patch` changeset naming the upstream version.
