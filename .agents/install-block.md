# The canonical install block

`README.md`, `README.vi.md` and changesets say this and nothing else. Change it here first, then propagate.

The plugin needs Claude Code: its subagents, hooks and `${CLAUDE_PLUGIN_ROOT}` paths have no equivalent elsewhere. It installs from this repo's own marketplace (`.claude-plugin/marketplace.json`, named `trussary`). Installed copies update when the `version` in `plugin.json` changes; the Release workflow sets it from `package.json` when the "chore: version skills" PR merges.

<canonical-block name="claude-code">

```bash
claude plugin marketplace add trussary/skills
claude plugin install trussary-skills@trussary
```

Then run `/setup-trussary-skills` once in each repo.

</canonical-block>

Don't install it alongside `mattpocock-skills`: the skill names overlap. Pick one.
