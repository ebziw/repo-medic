# repo-medic

> A self-contained **Claude Code skill toolkit** for daily code maintenance.
> Refactor · Dedup · DB tune · Doc organize · Frontend improve · Bootstrap tools · Self-evolve.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-blueviolet)](https://docs.claude.com/en/docs/claude-code/skills)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![Sub-skills](https://img.shields.io/badge/sub--skills-7-orange.svg)](#sub-skills)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[English](README.md) | [简体中文](README.zh-CN.md)

---

## What is repo-medic?

A **meta-skill package** for [Claude Code](https://docs.claude.com/en/docs/claude-code/skills) that bundles 6 focused sub-skills for code maintenance. Each sub-skill is **self-contained** — copy one folder and it works standalone.

Inspired by [anthropics/skills](https://github.com/anthropics/skills), [wix/skills](https://github.com/wix/skills), and the [Agent Skills spec](https://agentskills.io/specification).

## Sub-skills

| Sub-skill | Scope |
|---|---|
| [`py-improve`](./py-improve/) | Python code: god-fn splitting, dead code, dict/constant dedup, silent-error scanning, logging, code review |
| [`doc-reorg`](./doc-reorg/) | Directory + document + file reorganization (git mv, tmp archive, doc classification) |
| [`db-tweak`](./db-tweak/) | PostgreSQL: slow query, indexes, 9 iron rules, 7-phase methodology, drop retirement pipeline |
| [`vue-improve`](./vue-improve/) | Vue 3 + TypeScript + Vite + Pinia code improvements |
| [`config-base`](./config-base/) | Toolchain bootstrap: detect + install + upgrade dependencies (ruff/mypy/codegraph/node/psql) |
| [`evolve`](./evolve/) | Self-evolve: scan project pitfalls → distill lessons → inject into sub-skills |
| [`repo-medic`](./repo-medic/SKILL.md) | Meta router — routes prompt to the right sub-skill |

Each sub-skill ships with:

- A `SKILL.md` containing a **MANDATORY WORKFLOW CHECKLIST** with 🛑 GATE markers (prevents LLM skipping critical steps)
- The 14 universal hard constraints embedded inline
- A `references/` folder with deep methodology
- Optional `scripts/` (stdlib only) and `mcp_servers/` (for MCP integration)
- Apache-2.0 license

> 🌏 **Documentation languages** — every sub-skill's full docs (SKILL.md + references) are available in
> [English](./) (runtime, under each skill folder) and
> [简体中文](./docs/zh/) (mirrored under `docs/zh/<skill>/`).

## Why sub-skills, not a monolith?

- **Shareable** — send a friend `py-improve` without dragging in `db-tweak`
- **Focused** — each skill has one clear responsibility
- **Independent** — no cross-skill shared references to break on share
- **Trigger-accurate** — each description lists explicit `Triggers:` keywords for Claude Code's skill auto-matching

## Installation

### Option 1: Claude Code Plugin Marketplace (recommended)

In Claude Code:

```
/plugin marketplace add liyong-labs/repo-medic
```

Then select `Browse and install plugins` → `liyong-labs-repo-medic` → install.

### Option 2: vercel-labs Skills CLI (multi-agent)

```bash
npx skills add liyong-labs/repo-medic
```

Supports 73+ agents (Claude Code, Codex, Cursor, OpenCode, etc.). See <https://github.com/vercel-labs/skills>.

### Option 3: Manual install (any *nix)

```bash
# Install all sub-skills
git clone https://github.com/liyong-labs/repo-medic.git
cd repo-medic
for d in repo-medic py-improve doc-reorg db-tweak vue-improve config-base evolve; do
  ln -s "$(pwd)/$d" ~/.claude/skills/$d
done
```

Or pick the ones you need:

```bash
# Just Python code review
cp -r py-improve ~/.claude/skills/

# Just DB tuning
cp -r db-tweak ~/.claude/skills/
```

After install, verify with `/config-base`:

```bash
python ~/.claude/skills/config-base/scripts/tools.py check
```

## Usage

### Invoking

Bare `/repo-medic` (no argument) prints a language-aware help block. Otherwise:

```
/py-improve                   # direct: Python code improvement
/doc-reorg                    # direct: docs + directory reorganization
/db-tweak                     # direct: PostgreSQL tuning
/vue-improve                  # direct: Vue 3 frontend improvement
/config-base                  # direct: toolchain check/install
/evolve                       # direct: distill project lessons
```

Fuzzy routing via the meta router:

```
/repo-medic my Python god-function is huge
→ routed to py-improve

/repo-medic PG query slow after migration
→ routed to db-tweak

/repo-medic find which tools I'm missing
→ routed to config-base
```

End-to-end example (config-base + py-improve):

```
# 1. Check what's installed
/config-base

# 2. Install a missing tool (dry-run by default; --yes to proceed)
python ~/.claude/skills/config-base/scripts/tools.py install ruff --yes

# 3. Scan silent errors in your script
/py-improve check silent_swallow in my OpenVINO loader
```

### What each sub-skill does — and why

**`py-improve` — Python code health**
What: god-function splitting, dead-code removal, dict/constant dedup, silent-swallow scanning (`except: pass` → log or raise), logging observability, pre-merge code review.
Why: a silent `except: pass` hides failures until data is already corrupted — the scanner ships context-aware filters (e.g. `StopIteration` handlers, cleanup paths) so you see real swallows, not idioms. Dead code is deleted only after a 7-step reference-proof, because "looks unused" is how working code gets deleted. Refactors run behind a TDD safety net so behavior stays byte-for-byte.

**`doc-reorg` — one-pass directory + document reorganization**
What: `git mv` renames, tmp/debug artifact archiving, doc classification (MRD/PRD/ARCH/DESIGN/TEST/RESEARCH), env.md/deploy.md sync.
Why: backup-first (`rsync` snapshot + a GATE that blocks Phase 1 until it exists) because mass renames are the easiest way to break imports and links. Every old path keeps a redirect/symlink so external references never 404. Each run writes a work-note recording what moved and why — the next person shouldn't have to archaeologize.

**`db-tweak` — PostgreSQL tuning with a retirement pipeline**
What: slow-query diagnosis (`EXPLAIN (ANALYZE, BUFFERS)`), index design, 9 iron laws, 7-phase flow, and a DROP retirement pipeline (`RENAME TO PLAN_DELETE_*` → 7-day observation → user-approved DROP).
Why: baseline-first — you cannot prove an index helped without a before/after comparison. `CONCURRENTLY` + explicit lock timeouts, because DDL is what takes production down. Destructive changes go through rename-and-wait: a DROP is instant and irreversible, a RENAME is instant and reversible.

**`vue-improve` — Vue 3 + TS + Vite + Pinia**
What: component/store/Vite-build patterns plus a known-pitfall sweep (setup TDZ, `watchEffect` misuse, Pinia destructuring losing reactivity, third-party worker scope, chunk-hash deploy verification).
Why: these specific bugs recur across codebases — libraries like pdf.js/ECharts share workers silently and break selector scoping. Deploys are verified by curl-checking every hashed chunk URL, because "build succeeded" ≠ "users can load it".

**`config-base` — toolchain bootstrap**
What: `tools.py check` reports installed/missing/outdated tools across Python/Node/DB toolchains; `install <name>` dry-runs by default and asks before touching the machine.
Why: agents fail mysteriously when a linter or DB client is missing — explicit detection turns "weird error" into "install this". Dry-run default because package installation mutates the machine and must stay a user decision.

### evolve — lessons that survive upgrades

`/evolve` turns your project's pain into reusable lessons:

1. **Extract** — scan `git log` + `docs/work-note/` for Symptom/Cause/Fix patterns, cluster, rank by frequency
2. **Review** — present candidates; you accept / reject / modify each (nothing is written without your OK)
3. **Bucket** — write each lesson to `~/.claude/skills/repo-medic-lessons/lessons/<sub-skill>/<topic>.md` and update that companion skill's index
4. **Verify** — smoke test + work-note

**Why a companion skill outside the packages?** Skill directories are replaced wholesale when you upgrade — plugin update, `cp -r`, or a fresh clone all overwrite `py-improve/` and friends. Lessons written inside a skill folder would be destroyed by the very act of staying up to date. `repo-medic-lessons/` is never touched by any release, so your accumulated project history compounds instead of resetting.

**Why additive-only?** Lessons never modify the shipped `SKILL.md` files or the 14 hard constraints. A lesson can never silently weaken a safety gate — and upgrading repo-medic can never silently revert your lessons.

**How lessons are consumed:** the companion skill's description accumulates trigger keywords per domain, so Claude Code auto-loads it when a related task appears; you can also read a bucket directly before running a sub-skill.

Per-project specifics still belong in that project's own work-notes — evolve is for lessons worth carrying across projects.

## Design Principles

| # | Principle | Source |
|---|---|---|
| 1 | **Self-contained** — `cp -r <sub-skill>` works standalone | Simplicity |
| 2 | **MANDATORY WORKFLOW CHECKLIST + 🛑 GATE** — explicit gates prevent LLM skipping | From [wix/skills](https://github.com/wix/skills) |
| 3 | **Triggers keywords in frontmatter** — explicit list for Claude Code skill matching | From wix/skills |
| 4 | **14 hard constraints** embedded per skill — YAGNI, no git reset, batch-sample-first, etc. | Cross-cutting |
| 5 | **Stdlib only for scripts** — no new dependencies | YAGNI rule |
| 6 | **1 commit = 1 logical unit** — atomic, independently revertible | Commit hygiene |
| 7 | **Self-evolve loop** — `evolve` distills project history into lessons stored in an upgrade-safe companion skill | Meta |

## Roadmap

- [x] v0.1.0 — Initial release (4 sub-skills + meta)
- [x] v0.1.1 — Triggers keywords + marketplace.json + MANDATORY WORKFLOW
- [x] v0.2.0 — `config-base` sub-skill (toolchain bootstrap)
- [x] v0.2.1 — Windows compatibility (.cmd/.bat/.com + GBK fallback)
- [x] v0.3.0 — `evolve` sub-skill (self-distill pitfalls)
- [x] v0.4.0 — Community files (CONTRIBUTING, CoC, issue/PR templates) + README polish
- [x] v0.5.6 — `repo-medic-lessons` extended with 9 more lessons from `kb-104@local` (silent-fallback / cold-query perf / god-fn characterization / stale-test judgment / ooxml-strict / long-lived unit / pkill -f / third-party-config prod-input / shared-backend each-consumer) ← **current**
- [x] v0.5.5 — Companion skill `repo-medic-lessons` ships 8 distilled lessons (6 root-cause classes) from fleet `/evolve` output
- [x] v0.5.0 — Fully bilingual docs: English runtime skills + 简体中文 mirror (`docs/zh/`)
- [x] v0.5.1 — Language-aware `/repo-medic` help + evolve polish
- [ ] v0.6.0 — CI workflow (ruff + mypy + smoke tests on PR)
- [ ] v1.0.0 — Stable API + first external user feedback round

## Contributing

We welcome new sub-skills, bug fixes, and docs improvements! See [CONTRIBUTING.md](CONTRIBUTING.md).

Please also follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities via [GitHub Security Advisories](https://github.com/liyong-labs/repo-medic/security/advisories/new). See [SECURITY.md](SECURITY.md).

## License

Apache-2.0 — see [LICENSE](LICENSE).

## Maintainer

- github.com/liyong-labs
- Issues: <https://github.com/liyong-labs/repo-medic/issues>
- Discussions: <https://github.com/liyong-labs/repo-medic/discussions>

## Acknowledgments

Inspired by:

- [anthropics/skills](https://github.com/anthropics/skills) — official Agent Skills spec
- [wix/skills](https://github.com/wix/skills) — production SKILL.md patterns
- [vercel-labs/skills](https://github.com/vercel-labs/skills) — multi-agent skills CLI
- [agentskills.io](https://agentskills.io/specification) — Agent Skills specification

Star history:

[![Star History Chart](https://api.star-history.com/svg?repos=liyong-labs/repo-medic&type=Date)](https://star-history.com/#liyong-labs/repo-medic&Date)
