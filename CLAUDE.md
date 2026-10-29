This repo is the `trussary-skills` Claude Code plugin: skills in `skills/`, subagents in `agents/`, hooks in `hooks/` (`hooks/hooks.json`), helper scripts in `tools/`. It is a fork of mattpocock/skills; [CONTRIBUTING.md](./CONTRIBUTING.md) says how upstream is merged in.

Skills are organized into bucket folders under `skills/`:

- `engineering/`: daily code work
- `productivity/`: daily non-code workflow tools
- `misc/`, `in-progress/`, `deprecated/`: kept from upstream, not shipped

Every skill in `engineering/` or `productivity/` that the plugin ships has an entry in `.claude-plugin/plugin.json`'s `skills` array, a reference in `README.md` (skill name linked to its `SKILL.md`) and in its bucket `README.md`, grouped into **User-invoked** and **Model-invoked**. Run `claude plugin validate .` after touching either manifest.

Skills are generic; facts about one project live in that project's `docs/agents/*.md`. The templates are in `skills/engineering/setup-trussary-skills/` (`project.md`, `models.md`, the issue tracker, domain and triage label files), and a skill that reads a section of `docs/agents/project.md` states its fallback for when the section is missing. When you add or rename a section a skill reads, update the template and [examples/brio](./examples/brio/docs/agents/) in the same change.

Paths to files the plugin ships are written `${CLAUDE_PLUGIN_ROOT}/...` or `${CLAUDE_SKILL_DIR}/...` in skill and agent markdown; Claude Code substitutes them when it loads the file, and the Bash tool does not see them as variables. Subagents are dispatched by their plugin name, `trussary-skills:<agent>`.

Every `SKILL.md` is either user-invoked (`disable-model-invocation: true` plus `policy.allow_implicit_invocation: false` in `agents/openai.yaml`) or model-invoked. See [.agents/invocation.md](./.agents/invocation.md).

To (re)link every shipped skill into `~/.claude/skills` for local editing, run `scripts/link-skills.sh`.

No em-dashes anywhere in this repo's prose. Where a sentence reaches for one, rewrite it with a comma, colon, period, parentheses, or a conjunction.

Every skill that dispatches a subagent says to start it with a fresh context window.

## Agent skills

### Triage labels

Canonical names, unchanged. See `docs/agents/triage-labels.md`. Issues are judged against [`SCOPE.md`](./SCOPE.md).
