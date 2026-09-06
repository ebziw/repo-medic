# Changelog

All notable changes to repo-medic are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
