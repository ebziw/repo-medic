# repo-medic v0.4.0 — community-ready release

> **Self-contained Claude Code skill toolkit for daily code maintenance.**
> Refactor · Dedup · DB tune · Doc organize · Vue review · Tool bootstrap · Self-evolve.

## What's new in v0.4.0

First release with **community-facing files**. Ready for public contribution.

### Added
- **`CONTRIBUTING.md`** — how to add a new sub-skill (naming, MANDATORY WORKFLOW, hard constraints)
- **`CODE_OF_CONDUCT.md`** — Contributor Covenant 2.1
- **`SECURITY.md`** — vulnerability disclosure policy (GitHub Security Advisories)
- **`.github/ISSUE_TEMPLATE/`** — `bug_report.md` + `feature_request.md`
- **`.github/PULL_REQUEST_TEMPLATE.md`** — with MANDATORY WORKFLOW checklist
- **`CHANGELOG.md`** — full version history (v0.1.0 → v0.4.0)
- **`logo.svg`** + **`social-preview.svg`** — branding assets for GitHub sidebar + social cards
- **README.md** fully rewritten with badges, TOC, sub-skill table, install methods, design principles, roadmap

### Changed
- README structure aligned with hot open-source project standards (anthropics/skills, wix/skills, openai/openai-python)
- Added Star History chart at the bottom of README
- Roadmap updated to v0.5.0 / v1.0.0 milestones

## Why use repo-medic?

- **Self-contained** — `cp -r <sub-skill> ~/.claude/skills/` works standalone
- **MANDATORY WORKFLOW CHECKLIST + 🛑 GATE markers** — prevents LLM from skipping critical steps
- **Triggers keywords in frontmatter** — explicit list for Claude Code skill auto-matching
- **14 hard constraints** embedded per skill (YAGNI, no `git reset --hard`, batch-sample-first, daemon 4-step, etc.)
- **Cross-platform** — Windows + Linux + macOS (`.cmd`/`.bat`/`.com` wrappers handled)
- **Self-evolve loop** — `evolve` sub-skill scans project history and feeds lessons back

## Install

### Option 1: Claude Code Plugin Marketplace (recommended)

```
/plugin marketplace add ebziw/repo-medic
```

### Option 2: vercel-labs Skills CLI (multi-agent)

```bash
npx skills add ebziw/repo-medic
```

### Option 3: Manual

```bash
git clone https://github.com/ebziw/repo-medic.git
cd repo-medic
for d in repo-medic py-improve doc-reorg db-tweak vue-improve config-base evolve; do
  ln -s "$(pwd)/$d" ~/.claude/skills/$d
done
```

## Quick Start

```
/py-improve                   # Python code review
/doc-reorg                    # reorganize docs and directories
/db-tweak                     # tune PostgreSQL
/vue-improve                  # review Vue 3 components
/config-base                  # bootstrap missing tools
/evolve                       # distill project lessons

# Or fuzzy routing via meta:
/repo-medic my Python god-function is huge
→ routed to py-improve
```

## Full Changelog

See [CHANGELOG.md](https://github.com/ebziw/repo-medic/blob/main/CHANGELOG.md).

## Acknowledgments

Inspired by:

- [anthropics/skills](https://github.com/anthropics/skills) — official Agent Skills
- [wix/skills](https://github.com/wix/skills) — production SKILL.md patterns
- [vercel-labs/skills](https://github.com/vercel-labs/skills) — multi-agent CLI
- [agentskills.io](https://agentskills.io/specification) — Agent Skills spec

## License

Apache-2.0 — see [LICENSE](https://github.com/ebziw/repo-medic/blob/main/LICENSE).

---

**Full Changelog**: <https://github.com/ebziw/repo-medic/commits/v0.4.0>
