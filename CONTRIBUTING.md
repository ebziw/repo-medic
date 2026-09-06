# Contributing to repo-medic

Thanks for your interest! repo-medic is a community-maintained skill toolkit for Claude Code. We welcome:

- 🐛 Bug reports
- 💡 Feature requests (new sub-skills, new audit scripts, new MANDATORY WORKFLOW phases)
- 📝 Documentation improvements
- 🧪 Tests
- 🔌 New sub-skills

## How to add a new sub-skill

1. **Pick a focused scope** — one sub-skill = one domain (e.g. `py-improve` = Python code, NOT Python + JS)
2. **Self-contained** — `cp -r <sub-skill> ~/.claude/skills/` should work standalone
3. **Naming** — kebab-case, `<verb>-<noun>` pattern (e.g. `py-improve`, `doc-reorg`). Check `name` collisions on PyPI/npm/GitHub first
4. **SKILL.md structure**:
   ```yaml
   ---
   name: your-skill
   description: <one-line, ends with Triggers: keyword1, keyword2>
   metadata:
     type: domain  # or ops | meta
     scope: public
   ---
   # Your skill name
   
   ## 🛑 MANDATORY WORKFLOW — check all before declaring done
   
   ### Phase 0: Reconnaissance
   - [ ] ...
   ### Phase 1: ...
   ...
   ```
5. **MANDATORY WORKFLOW** — each sub-skill must have explicit Phase 0-3+ with checklist + 🛑 GATE markers (this prevents LLM from skipping critical steps)
6. **14 hard constraints** — embed in every SKILL.md (see `repo-medic/SKILL.md` for the canonical list)
7. **References** — put methodology in `references/<topic>.md`, link from SKILL.md
8. **Scripts** — stdlib only when possible (YAGNI = no new deps per CLAUDE.md rule 1)
9. **Tests** — if you add scripts, add at least one smoke test

## Code style

- Python: ruff + mypy strict (see `py-improve/scripts/` for examples)
- Markdown: keep lines ≤ 100 chars
- Commits: follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)

## Commit messages

```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(py-improve): add silent-swallow MANDATORY GATE marker

Add explicit 🛑 GATE after silent_swallow scan to prevent LLM
from proceeding without verifying scan output.

Refs: anthropics/skills#12 (template inspiration)
```

## Pull request process

1. Fork the repo
2. Create a branch: `git checkout -b feat/my-skill`
3. Make changes
4. Run self-check:
   ```bash
   # from your sub-skill dir
   ruff check .
   mypy .
   ```
5. Update README.md + README.zh-CN.md sub-skill table
6. Update `.claude-plugin/marketplace.json` if adding a new sub-skill
7. Push + open PR
8. Wait for review

## Testing

- Each sub-skill that includes scripts must have at least one test
- Use stdlib `unittest` (no pytest required for portability)
- Smoke tests over unit tests — verify the entry point works

## Release process

1. Maintainer bumps version in `pyproject.toml` (not applicable — pure skills repo, no Python package) + README badge
2. Maintainer writes CHANGELOG entry
3. Maintainer tags `vX.Y.Z`
4. Push tag → triggers release workflow (TBD)

## Code of conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Questions?

- 💬 Discussions: <https://github.com/liyong-labs/repo-medic/discussions>
- 🐛 Issues: <https://github.com/liyong-labs/repo-medic/issues>
- 📧 Maintainer: open an issue first (do not email directly)
