---
name: repo-medic
description: "Repo code maintenance skill package entry. Routes to sub-skills: py-improve (Python) / doc-reorg (docs + directories) / db-tweak (PostgreSQL) / vue-improve (Vue 3) / config-base (toolchain) / evolve (pitfall distillation). Use when the maintenance request is ambiguous and no single sub-skill clearly matches. Triggers: repo-medic, code maintenance, meta skill, project upkeep, evolve, pitfall distillation"
metadata:
  type: meta
  scope: public
---

# repo-medic — meta router

## Bare invocation — show help

When invoked with no argument (`/repo-medic`), print the help block and stop. Do not guess a sub-skill. **Print it in the language of the ongoing conversation** (English block below; if the user is writing Chinese, use the Chinese block):

```
repo-medic — code maintenance skill toolkit

  /py-improve     Python code (refactor, dedup, silent errors, logging, CR)
  /doc-reorg      Directory + document + file reorganization
  /db-tweak       PostgreSQL (slow queries, indexes, DDL, 9 iron laws)
  /vue-improve    Vue 3 + TS + Vite + Pinia frontend
  /config-base    Toolchain bootstrap (detect + install dependencies)
  /evolve         Distill project pitfalls into reusable lessons

Usage: /repo-medic <request>   → routes to the matching sub-skill
       /<sub-skill> <request>  → invoke a sub-skill directly
```

```
repo-medic — 代码维护 skill 工具包

  /py-improve     Python 代码（重构、去重、静默吞错、日志、CR）
  /doc-reorg      目录 + 文档 + 文件一次性整理
  /db-tweak       PostgreSQL（慢查询、索引、DDL、9 铁律）
  /vue-improve    Vue 3 + TS + Vite + Pinia 前端
  /config-base    工具链 bootstrap（检测 + 安装依赖）
  /evolve         蒸馏项目踩坑为可复用经验

用法：/repo-medic <需求>   → 路由到匹配的 sub-skill
     /<sub-skill> <需求>  → 直接调用某个 sub-skill
```

## Routing

**Invoke the target sub-skill directly** (recommended — zero overhead):

| Sub-skill | Scope |
|---|---|
| `/py-improve` | Python code (refactor, dict dedup, silent errors, logging, code review) |
| `/doc-reorg` | Directory + document + file reorganization in one pass |
| `/db-tweak` | Database (PG slow queries, indexes, DDL, 9 iron rules) |
| `/vue-improve` | Vue 3 + TS + Vite + Pinia frontend improvement |
| `/config-base` | Toolchain bootstrap (detect + install dependencies) |
| `/evolve` | Self-evolution (scan project pitfalls → distill → inject into sub-skills) |

**Invoke this skill when the target is ambiguous**, route by prompt keywords:

| Keywords | Route to |
|---|---|
| god-fn / dead code / silent error / logging / dict / Python / refactor / pytest / mypy / ruff | `py-improve` |
| rename / archive / tmp / directory structure / docs / templates / env / README / doc-reorg | `doc-reorg` |
| index / EXPLAIN / VACUUM / slow query / DROP / PG / DB / tuning | `db-tweak` |
| Vue / component / Pinia / Vite / setup / watch / ref / router | `vue-improve` |
| tools / dependencies / install / bootstrap / config / upgrade / missing / setup | `config-base` |
| pitfall / lesson / retrospective / postmortem / distill / evolve / KB feedback | `evolve` |

If nothing matches, show the same help block and let the user choose.

## Sub-skill paths

Each sub-skill is self-contained (`cp -r` to share): all references/, scripts/, mcp_servers/ live inside its own directory.

- `~/.claude/skills/py-improve/`
- `~/.claude/skills/doc-reorg/`
- `~/.claude/skills/db-tweak/`
- `~/.claude/skills/vue-improve/`
- `~/.claude/skills/config-base/`
- `~/.claude/skills/evolve/`

## Repository

github.com/ebziw/repo-medic — open source (Apache-2.0). Contributions welcome: new sub-skills or improvements to existing ones.
