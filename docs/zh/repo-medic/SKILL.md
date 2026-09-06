---
name: repo-medic
description: 仓库代码维护 skill 包入口。路由到子 skill：Python 代码改进 (py-improve) / 文档目录整理 (doc-reorg) / 数据库调优 (db-tweak) / Vue 前端改进 (vue-improve) / 工具链 bootstrap (config-base) / 自进化 (evolve)。用于日常代码重构、字典去重、静默吞错、目录归档、PG 调优、Vue 组件审查、依赖安装、蒸馏项目经验避免未来踩坑等场景。Triggers: repo-medic, code maintenance, 路由, route, meta skill, 代码维护, 项目日常, bootstrap, install, 踩坑, 进化, evolve
metadata:
  type: meta
  scope: public
---

# repo-medic — meta router

## 裸调用 — 显示 help

不带参数调用（`/repo-medic`）时，打印 help 块后停止，不要猜测子 skill。**用当前对话语言打印**（用户在说中文用下面的中文块，说英文用英文块）：

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

## 路由

**直接调对应 sub-skill**（推荐，零开销）：

| Sub-skill | 范围 |
|---|---|
| `/py-improve` | Python 代码（重构、字典去重、静默吞错、日志、CR） |
| `/doc-reorg` | 目录 + 文档 + 文件一次性整理 |
| `/db-tweak` | 数据库（PG 慢查询、索引、DDL、9 铁律） |
| `/vue-improve` | Vue 3 + TS + Vite + Pinia 前端改进 |
| `/config-base` | 工具链 bootstrap（检测 + 安装依赖） |
| `/evolve` | 自进化（扫项目踩的坑 → 蒸馏 → 注入 sub-skill） |

**模糊时调本 skill**，按 prompt 关键词路由：

| 关键词 | 路由到 |
|---|---|
| god-fn / 死代码 / 静默吞错 / 日志 / 字典 / Python / 重构 / pytest / mypy / ruff | `py-improve` |
| 重命名 / 归档 / tmp / 目录结构 / 文档 / 模板 / env / README / doc-reorg | `doc-reorg` |
| 索引 / EXPLAIN / VACUUM / 慢查询 / DROP / PG / DB / 调优 | `db-tweak` |
| Vue / 组件 / Pinia / Vite / setup / watch / ref / 路由 | `vue-improve` |
| 工具 / 依赖 / 安装 / bootstrap / 配置 / 升级 / missing / setup | `config-base` |
| 踩坑 / 教训 / 经验 / 蒸馏 / postmortem / retrospective / evolve / 进化 / KB 反哺 | `evolve` |

如果都不匹配，列出可用的 sub-skill 让用户选。

## 子 skill 路径

每个 sub-skill 自包含（cp -r 即分享）：所有 references/、scripts/、mcp_servers/ 在自己目录里。

- `~/.claude/skills/py-improve/`
- `~/.claude/skills/doc-reorg/`
- `~/.claude/skills/db-tweak/`
- `~/.claude/skills/vue-improve/`
- `~/.claude/skills/config-base/`

## 仓库

github.com/liyong-labs/repo-medic — 开源（Apache-2.0）。欢迎贡献新 sub-skill 或改进现有。
