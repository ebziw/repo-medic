# repo-medic

> A self-contained **Claude Code skill toolkit** for daily code maintenance.
> Refactor · Dedup · DB tune · Doc organize · Frontend improve · Bootstrap tools · Self-evolve.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-blueviolet)](https://docs.claude.com/en/docs/claude-code/skills)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![Sub-skills](https://img.shields.io/badge/sub--skills-7-orange.svg)](#sub-skills)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[English](README.md) | [中文](README.zh-CN.md)

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

## Why sub-skills, not a monolith?

- **Shareable** — send a friend `py-improve` without dragging in `db-tweak`
- **Focused** — each skill has one clear responsibility
- **Independent** — no cross-skill shared references to break on share
- **Trigger-accurate** — each description lists explicit `Triggers:` keywords for Claude Code's skill auto-matching

## Installation

### Option 1: Claude Code Plugin Marketplace (recommended)

In Claude Code:

```
/plugin marketplace add ebziw/repo-medic
```

Then select `Browse and install plugins` → `ebziw-repo-medic` → install.

### Option 2: vercel-labs Skills CLI (multi-agent)

```bash
npx skills add ebziw/repo-medic
```

Supports 73+ agents (Claude Code, Codex, Cursor, OpenCode, etc.). See <https://github.com/vercel-labs/skills>.

### Option 3: Manual install (any *nix)

```bash
# Install all sub-skills
git clone https://github.com/ebziw/repo-medic.git
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

## Quick Start

### Direct invocation

```
/py-improve                   # ask Python code improvement questions
/doc-reorg                    # reorganize docs and directories
/db-tweak                     # tune PostgreSQL
/vue-improve                  # review Vue components
/config-base                  # check tool dependencies
/evolve                       # distill project lessons
```

### Fuzzy routing via meta

```
/repo-medic my Python god-function is huge
→ routed to py-improve

/repo-medic PG query slow after migration
→ routed to db-tweak

/repo-medic find which tools I'm missing
→ routed to config-base
```

### Example: BGE-M3 embedding on Intel iGPU (config-base + py-improve)

```
# 1. Check what's installed
/config-base

# 2. Install missing Intel OpenCL ICD
python ~/.claude/skills/config-base/scripts/tools.py install intel-opencl-icd --yes

# 3. Ask py-improve to scan silent errors in your embedding script
/py-improve check silent_swallow in my OpenVINO loader
```

## Design Principles

| # | Principle | Source |
|---|---|---|
| 1 | **Self-contained** — `cp -r <sub-skill>` works standalone | Simplicity |
| 2 | **MANDATORY WORKFLOW CHECKLIST + 🛑 GATE** — explicit gates prevent LLM skipping | From [wix/skills](https://github.com/wix/skills) |
| 3 | **Triggers keywords in frontmatter** — explicit list for Claude Code skill matching | From wix/skills |
| 4 | **14 hard constraints** embedded per skill — YAGNI, no git reset, batch-sample-first, etc. | Cross-cutting |
| 5 | **Stdlib only for scripts** — no new dependencies | YAGNI rule |
| 6 | **1 commit = 1 logical unit** — atomic, independently revertible | Commit hygiene |
| 7 | **Self-evolve loop** — `evolve` sub-skill scans project history and injects lessons back | Meta |

## Roadmap

- [x] v0.1.0 — Initial release (4 sub-skills + meta)
- [x] v0.1.1 — Triggers keywords + marketplace.json + MANDATORY WORKFLOW
- [x] v0.2.0 — `config-base` sub-skill (toolchain bootstrap)
- [x] v0.2.1 — Windows compatibility (.cmd/.bat/.com + GBK fallback)
- [x] v0.3.0 — `evolve` sub-skill (self-distill pitfalls)
- [ ] v0.4.0 — Community files (CONTRIBUTING, CoC, issue/PR templates) + README polish ← **current**
- [ ] v0.5.0 — CI workflow (ruff + mypy + smoke tests on PR)
- [ ] v1.0.0 — Stable API + first external user feedback round

## Contributing

We welcome new sub-skills, bug fixes, and docs improvements! See [CONTRIBUTING.md](CONTRIBUTING.md).

Please also follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities via [GitHub Security Advisories](https://github.com/ebziw/repo-medic/security/advisories/new). See [SECURITY.md](SECURITY.md).

## License

Apache-2.0 — see [LICENSE](LICENSE).

## Maintainer

- github.com/ebziw
- Issues: <https://github.com/ebziw/repo-medic/issues>
- Discussions: <https://github.com/ebziw/repo-medic/discussions>

## Acknowledgments

Inspired by:

- [anthropics/skills](https://github.com/anthropics/skills) — official Agent Skills spec
- [wix/skills](https://github.com/wix/skills) — production SKILL.md patterns
- [vercel-labs/skills](https://github.com/vercel-labs/skills) — multi-agent skills CLI
- [agentskills.io](https://agentskills.io/specification) — Agent Skills specification

Star history:

[![Star History Chart](https://api.star-history.com/svg?repos=ebziw/repo-medic&type=Date)](https://star-history.com/#ebziw/repo-medic&Date)
