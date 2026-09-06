# Changelog

All notable changes to repo-medic are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.5.4] — 2026-09-06

### Fixed
- `config-base` `tools.py`: `mcp` was reported OUTDATED on Windows — the probe
  used `mcp.__version__` (attribute does not exist), captured a traceback as
  the "version" and compared it. Now probes via
  `importlib.metadata.version("mcp")`
- `config-base` `tools.py`: probe output containing no parseable version
  (traceback / banner / encoding garbage) is now reported as a probe ERROR,
  never silently compared into OUTDATED
- `config-base` `tools.py`: subprocess output decoded as UTF-8 explicitly
  (locale GBK mangled some tool banners on Windows)

### Added
- `config-base` `tools.py`: `optional` tool flag — `pnpm` and `psql` now show
  as `OPTIONAL` (skip if the project doesn't use them) instead of MISSING,
  with their own counter in the summary line

## [0.5.3] — 2026-09-06

### Fixed
- `evolve/scripts/extract.py` — git log failure was silent (rc != 0 returned an
  empty list with no message); now warns on stderr, and also warns when the
  scan window yields 0 commits
- `evolve/scripts/extract.py` — work-note field matching was too strict
  (exact `**Symptom**:` bold labels only); now also matches `## Symptom`
  headings and plain `Symptom:` labels; partially-documented notes become
  candidates with gaps marked "(not documented in source note)"
- `py-improve/scripts/silent_swallow.py` — passing a single existing `.py`
  file reported a misleading "directory does not exist"; files are now
  accepted alongside directories

### Changed
- `evolve` SKILL.md Phase 3: lessons dir is `git init`-ed on first run so the
  1-lesson-1-commit gate is enforceable and lessons get history
- `py-improve` hard constraint 6 gained a project-level exception clause
  (when running tests is unsafe in the project, the project's own rule wins;
  record the exception + run the safest covering subset)

## [0.5.2] — 2026-09-06

### Fixed
- `evolve/scripts/extract.py` produced 0 candidates from a repo full of fix
  commits. Three independent causes:
  1. the frequency gate dropped every single-occurrence commit candidate,
     killing the whole commit path (kept only if the same subject repeated)
  2. commit-pitfall keywords missed common Chinese subjects (修复/回滚/报错/…)
  3. `--since=30d` — git silently returns EMPTY output for the `Nd` shorthand
     (must be `N.days`); input is now normalized, default stays `7d`
  Commit candidates now kept on keyword-score >= 2 or repetition, capped at
  `--max-candidates 10`; verified on two real repos (50 commits → 11 candidates)

## [0.5.1] — 2026-09-06

### Added
- `repo-medic` bare invocation (`/repo-medic` with no argument) now prints a
  language-aware help block (English or 简体中文, matching the conversation)
  instead of guessing a sub-skill

### Fixed
- `py-improve/scripts/reorg_drift.py` — docstring/help/output translated to
  English (last untranslated shipped script); stale `scripts/audit/` path in
  docstring corrected
- `evolve` SKILL.md description + Usage wording aligned with the
  additive-only/upgrade-safe injection design; Contents table now lists
  `templates/lessons-skill.md`

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
