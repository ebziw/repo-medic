# Pull Request

## Description

<!-- Brief summary of the changes -->

## Type of change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New sub-skill (new sub-skill directory added)
- [ ] ✨ New feature (new audit script, MCP tool, etc.)
- [ ] 📝 Documentation only
- [ ] ♻️ Refactor (no functional change)
- [ ] 🔧 Chore (CI, tooling, meta)

## Sub-skill(s) affected

- [ ] `repo-medic` (meta)
- [ ] `py-improve`
- [ ] `doc-reorg`
- [ ] `db-tweak`
- [ ] `vue-improve`
- [ ] `config-base`
- [ ] `evolve`
- [ ] New sub-skill: `<name>`

## Checklist

<!-- Verify before requesting review -->

- [ ] **Self-contained** — `cp -r <modified-skill> ~/.claude/skills/` works standalone
- [ ] **SKILL.md** has frontmatter (name, description with Triggers, metadata)
- [ ] **MANDATORY WORKFLOW CHECKLIST** with 🛑 GATE markers (if added/modified)
- [ ] **14 hard constraints** embedded in SKILL.md (if added/modified)
- [ ] **README.md + README.zh-CN.md** updated (sub-skill table row if new sub-skill)
- [ ] **marketplace.json** updated (if new sub-skill)
- [ ] **No new dependencies** (YAGNI rule 1; stdlib only)
- [ ] **1 commit = 1 logical unit** (commit hygiene)
- [ ] **Tested locally** before pushing
- [ ] **Lint clean**: `ruff check .` and `mypy .` (for Python files)

## Test plan

<!-- How did you verify this works? -->

## Screenshots / logs

<!-- Optional: visual proof or output snippets -->

## Breaking changes

<!-- None? Or list what user needs to do. -->

## Related issues

<!-- Fixes #123, relates to #456 -->
