# Changelog

All notable changes to repo-medic are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.5.8] — 2026-09-07

### Added — Competitor research absorbed

**doc-reorg** (2 new references):
- `references/ai-cruft-detector.md` — borrowed from `asamarts/alint` `agent-hygiene@v1` ruleset: catch AI-authored cruft before commit (versioned-dup filenames / scratch docs at root / AI-affirmation prose / debug residue / model-attributed TODOs)
- `references/safe-apply-protocol.md` — borrowed from `j-256/reorg` `apply --yes` + `--undo` semantics: undo-script generation + drift-abort-the-whole-batch invariant

**db-tweak** (3 new references):
- `references/pgx-anti-pattern-codes.md` — borrowed from `losefor/pg-explain`: 19 stable `PGX_*` codes (cartesian product / seq scan large / row misestimate / stale statistics / low cache hit / sort spill / memoize evict / ...) for greppable EXPLAIN findings
- `references/governed-undo-protocol.md` — borrowed from `aiops-tools/postgres-aiops`: every write op captures real before-state (create_index ↔ drop_index, update_setting ↔ prior value); `terminate_backend` / `run_vacuum` declare no-undo; audit jsonl
- `references/risk-tier-and-simulation.md` — borrowed from `valkdb.com` (testcontainer isolation, metadata-only) + `Azimutt Inspector` (severity × confidence scoring): T1-T4 risk tiers, simulate-fix-before-merge workflow

### Sources surveyed (not absorbed — reference only)

- doc-reorg: Orgit, project-pruner, Foldweave (Change File), spindle (BLAKE3 ledger), dosido (TS-import rewrite), pka (multi-agent context)
- db-tweak: PGTuner (visual EXPLAIN diff), pganalyze (auto_explain + Index Advisor), Postgres-AIops (35 MCP tools), PgDoctor (AI suggestions + confidence)

### Rationale

Absorb only what fits the **borrow-the-stable-codes-or-design-pattern** rule:
1. Stable greppable vocabularies (PGX_*) — agents + humans + scripts share one language
2. Reusable protocols (undo / safe-apply / risk-tier) — apply to many DB / file changes
3. Pattern catalogues (ai-cruft detector) — pre-commit gate, runs against any repo

Skipped: visual dashboards (out of scope for a CLI skill), pricing SaaS (non-OSS), and language-specific tooling that doesn't transfer (dosido is TS-only).

## [0.5.7] — 2026-09-07

### Changed
- **`repo-medic-lessons` py-improve bucket**: distilled from 9 → 5 lessons per
  user directive "扔掉那些极其罕见的case，合并重复的case，提炼还不够抽象
  和泛化的case，最终形成一套对大多数项目质量提升都有价值的方法论".
- **Removed** (rare or tool-specific, low cross-project value):
  - `cross-stage-enum-sync` — merged into `handoff-receiver-pair-check` (same root cause: implicit contract)
  - `third-party-api-params-audit` — only applies when integrating vendor paid APIs
  - `sql-string-concat-no-inline-comments` — only applies to Python projects with hand-built SQL
  - `ooxml-strict-mode-references` — PowerPoint-specific
- **Rewritten** (5 lessons): each now opens with a one-sentence **Principle**,
  then Symptom-as-pattern (multiple cases), then Fix-as-rule. Trigger-keyword
  list trimmed to drop tool-specific terms (wait_for / pptx / notesMaster etc).
- Net effect: bucket went from "kb-specific incident records" to "universal
  Python quality methodology". Triggers still grep-friendly.

### Rationale

A lesson is worth keeping if (a) the principle applies to >50% of mature
Python codebases, AND (b) the failure mode is non-obvious to a senior dev.
Rare / tool-specific lessons are noise — the v0.5.5 + v0.5.6 mix had 4 that
failed criterion (a).

## [0.5.6] — 2026-09-07

### Added
- **`repo-medic-lessons`**: 9 more lessons (v0.5.5 had 8, now 17 total), distilled
  from `kb-104@local` (`Administrator` on this machine) `/evolve` output
  (2026-09-06 search-cold-query-iter3 / qa-rerank-silent-timeout /
  embed-contract / maybe-rerank-split / ppt-notes-chain / stale-test batch).
- 5 py-improve: `silent-fallback-grade-not-uniform` (freq 3 — highest in batch) /
  `perf-measure-cold-and-breakdown` / `god-fn-split-requires-characterization` /
  `stale-test-vs-impl-judgment` / `ooxml-strict-mode-references`
- 4 config-base: `long-lived-service-must-be-unit` / `pkill-f-can-self-match` /
  `third-party-config-must-replicate-prod-input` /
  `shared-backend-change-verify-each-consumer`
- Trigger keyword index in SKILL.md expanded for new lessons

### Source
- Local `~/.claude/skills/repo-medic-lessons/` had 10 lessons (different from
  kb@kb ECS); missed in v0.5.5 because local fleet scan used `ls` filter that
  hid directory. Second-pass `find` revealed.
- Two new clusters merged into single principles: silent-fallback + bare-nohup
  → "service longevity + observability"; third-party-config + ooxml-strict →
  "real consumer validation, not SDK pass".

## [0.5.5] — 2026-09-07

### Added
- **New companion skill: `repo-medic-lessons`** — distilled hard-won lessons
  accumulated by `/evolve` from real projects. Bucketed per sub-skill
  (`py-improve` / `config-base` / `db-tweak`). Lives outside any single skill
  package so upgrades never erase them. 8 lessons covering 6 root-cause classes:
  - py-improve: `handoff-receiver-pair-check` / `cross-stage-enum-sync` /
    `third-party-api-params-audit` / `sql-string-concat-no-inline-comments`
  - config-base: `runtime-evidence-chain` / `import-path-observability` /
    `paid-api-cost-from-official-docs`
  - db-tweak: `failure-loop-conn-budget`
- Each lesson follows Symptom / Cause / Fix / Sources / Frequency / Triggers /
  Related hard constraints. Trigger-keyword index in SKILL.md for fast lookup.

### Source
- Lessons distilled from fleet `kb@kb` `~/.claude/skills/repo-medic-lessons/`
  output (8 lessons written by `/evolve` on 2026-09-06, after user's command
  to "把它们写下来的坑和避坑 prompt 取回来，蒸馏提炼抽象升华，合并到 repo-medic").
- Two clusters merged into single principles: handoff-receiver + cross-stage-enum
  → "implicit contract must be explicit"; sys.path + systemd cat → "runtime
  evidence chain"; paid-api-params + paid-cost → "third-party doc audit".

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
