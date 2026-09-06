# Changelog

All notable changes to repo-medic are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.5.0] — 2026-09-06

### Added
- **Fully bilingual documentation**: all 7 sub-skills' docs (SKILL.md + references + templates)
  rewritten in English (runtime), with the complete 简体中文 versions mirrored under `docs/zh/<skill>/`
  for human readers. README gains a language switcher and per-language doc links.

### Fixed
- `doc-reorg` SKILL.md: Phase 0 backup command was malformed (`rsync` missing destination) —
  the mandatory workflow GATE could never pass as written
- `db-tweak` SKILL.md: commit-granularity GATE mislabeled "iron law 2" → now cites hard constraint 2;
  baseline filename made consistent (`baseline-<date>.json`)
- `evolve` SKILL.md: injection path template corrected to `<target-skill>/references/<topic>.md`
- `config-base` `tools.py`: `uv` bootstrap no longer self-referential (installs via pip)
- Frontmatter `description` values quoted — unquoted `Triggers:` inline colon was invalid strict YAML
- Stale `scripts/audit/` paths in `py-improve` references and script docstrings → `scripts/`
- Removed internal infrastructure hostnames from public docs; KB sync steps now say
  "the KB endpoint's public-knowledge collection (skip if no KB system is configured)"

### Changed
- **`evolve` injection redesigned to be upgrade-safe**: lessons are no longer written into skill
  packages (which get replaced wholesale on upgrade). All lessons now go to an additive companion
  skill `~/.claude/skills/repo-medic-lessons/` (per-skill buckets + index), which no release ever touches
- Shipped scripts (`silent_swallow.py`, `config_drift.py`, `plan-delete.sh`, `audit-plan-delete.sh`)
  fully translated to English (docstrings, help text, user-facing output); logic unchanged
- Meta router description trimmed (dropped over-generic triggers `install` / `route` / `bootstrap`)

## [0.4.0] — 2026-09-06

### Added
- **Community files** for public release:
  - `CONTRIBUTING.md` — how to add a sub-skill (naming, MANDATORY WORKFLOW, hard constraints)
  - `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
  - `SECURITY.md` — vulnerability disclosure policy
  - `.github/ISSUE_TEMPLATE/bug_report.md` + `feature_request.md`
  - `.github/PULL_REQUEST_TEMPLATE.md` with MANDATORY WORKFLOW checklist
- `CHANGELOG.md` (this file)

### Changed
- `README.md` — rewritten with badges, TOC, quick-start table, design principles, roadmap, inspirations, star history
- `README.zh-CN.md` — synced with new English README

## [0.3.0] — 2026-09-06

### Added
- `evolve` sub-skill: scans git log + `docs/work-note/*.md` Symptom/Cause/Fix
  pattern → extracts lesson candidates → user reviews → injects into
  target sub-skill. Goal: avoid repeating past mistakes.

## [0.2.1] — 2026-09-06

### Fixed
- `config-base`: Windows compat — `.cmd`/`.bat`/`.com` wrappers need
  `shell=True` + string form; GBK output uses `errors='replace'`

## [0.2.0] — 2026-09-06

### Added
- `config-base` sub-skill: detect + install + upgrade dependencies
  (ruff/mypy/codegraph/node/psql/mcp) via `tools.py check` / `install`
- MANDATORY WORKFLOW CHECKLIST + 🛑 GATE markers on
  doc-reorg / db-tweak / vue-improve (matching py-improve)

## [0.1.1] — 2026-09-06

### Added
- `Triggers:` keyword list in each sub-skill description (Wix pattern)
- `.claude-plugin/marketplace.json` for `/plugin marketplace add`
- MANDATORY WORKFLOW CHECKLIST + 🛑 GATE in py-improve/SKILL.md

## [0.1.0] — 2026-09-06

### Added
- Initial release of repo-medic meta-skill + 4 sub-skills:
  - `py-improve` — Python code improvements
  - `doc-reorg` — directory + document + file reorganization
  - `db-tweak` — PostgreSQL tuning
  - `vue-improve` — Vue 3 frontend improvements
- Apache-2.0 license
- README.md + README.zh-CN.md
