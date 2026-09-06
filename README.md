# repo-medic

A self-contained Claude Code skill toolkit for daily code maintenance: refactoring, deduplication, silent-error scanning, directory/document reorganization, PostgreSQL tuning, and Vue 3 frontend improvements.

## Sub-skills

| Sub-skill | Scope |
|---|---|
| [`py-improve`](./py-improve/) | Python code: god-fn splitting, dead code, dict/constant dedup, silent-error scanning, logging, code review |
| [`doc-reorg`](./doc-reorg/) | Directory + document + file reorganization (git mv, tmp archive, doc classification) |
| [`db-tweak`](./db-tweak/) | PostgreSQL: slow query, indexes, 9 iron rules, 7-phase methodology, drop retirement pipeline |
| [`vue-improve`](./vue-improve/) | Vue 3 + TypeScript + Vite + Pinia code improvements |
| [`config-base`](./config-base/) | Toolchain bootstrap: detect + install + upgrade dependencies (ruff/mypy/codegraph/node/psql) |
| [`repo-medic`](./repo-medic/SKILL.md) | Meta router — routes prompt to sub-skill |

Each sub-skill is **self-contained**: `cp -r <sub-skill> ~/.claude/skills/` works as-is.

## Why sub-skills, not a monolith?

- **Shareable** — send a friend `/py-improve` without dragging in `/db-tweak`
- **Focused** — each skill has one clear responsibility
- **Independent** — no cross-skill shared resources to break on share

## Install

```bash
# Clone the repo
git clone https://github.com/ebziw/repo-medic.git
cd repo-medic

# Symlink (or copy) all sub-skills to your Claude Code skills dir
for d in repo-medic py-improve doc-reorg db-tweak vue-improve; do
  ln -s "$(pwd)/$d" ~/.claude/skills/$d
done
```

Or copy individually:

```bash
cp -r vue-improve ~/.claude/skills/
```

## Usage

Invoke any sub-skill directly:

```
/py-improve
/doc-reorg
/db-tweak
/vue-improve
```

Or use the meta router with a fuzzy prompt:

```
/repo-medic my Python god-function needs splitting
→ routed to py-improve
```

## Hard constraints (apply to all sub-skills)

Each sub-skill's `SKILL.md` embeds the same 14 hard constraints (YAGNI, commit granularity, no `git reset --hard`, dead-code 7-step proof, TDD 4 modes, prod lock, no-fabrication, DB drop retirement, batch-sample-first, daemon 4-step, buffer ownership, hash-build full sync, deployment verification, etc.).

## License

Apache-2.0 — see [LICENSE](./LICENSE).

## Repository

https://github.com/ebziw/repo-medic
