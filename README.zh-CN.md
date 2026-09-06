# repo-medic

> 自包含的 **Claude Code skill 工具包**，用于日常代码维护。
> 重构 · 去重 · 数据库调优 · 文档整理 · 前端审查 · 工具 bootstrap · 自进化。

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-blueviolet)](https://docs.claude.com/en/docs/claude-code/skills)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![Sub-skills](https://img.shields.io/badge/sub--skills-7-orange.svg)](#子-skill-列表)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[简体中文](README.zh-CN.md) | [English](README.md)

[English](README.md) | [中文](README.zh-CN.md)

---

## repo-medic 是什么？

为 [Claude Code](https://docs.claude.com/en/docs/claude-code/skills) 打包的 **meta-skill 包**，包含 6 个聚焦的子 skill，覆盖代码维护场景。每个子 skill **自包含** — 拷贝一个文件夹就能独立用。

设计灵感来自 [anthropics/skills](https://github.com/anthropics/skills)、[wix/skills](https://github.com/wix/skills)、[Agent Skills 规范](https://agentskills.io/specification)。

## 子 skill 列表

| Sub-skill | 范围 |
|---|---|
| [`py-improve`](./py-improve/) | Python 代码：god-fn 拆分、死代码、字典/常量去重、静默吞错扫描、日志、CR |
| [`doc-reorg`](./doc-reorg/) | 目录 + 文档 + 文件整理（git mv、tmp 归档、文档分类） |
| [`db-tweak`](./db-tweak/) | PostgreSQL：慢查询、索引、9 铁律、7 phase、退场流水线 |
| [`vue-improve`](./vue-improve/) | Vue 3 + TS + Vite + Pinia 前端改进 |
| [`config-base`](./config-base/) | 工具链 bootstrap：检测 + 安装 + 升级依赖（ruff/mypy/codegraph/node/psql） |
| [`evolve`](./evolve/) | 自进化：扫描项目踩的坑 → 蒸馏经验 → 注入 sub-skill |
| [`repo-medic`](./repo-medic/SKILL.md) | Meta 路由 — 根据 prompt 关键词路由到子 skill |

每个子 skill 都包含：

- 一份 `SKILL.md`，含 **MANDATORY WORKFLOW CHECKLIST**（必填工作流清单）+ 🛑 GATE 标记（防止 LLM 跳过关键步骤）
- 14 条通用硬约束内嵌
- `references/` 文件夹含深度方法论
- 可选 `scripts/`（纯标准库）和 `mcp_servers/`（MCP 集成）
- Apache-2.0 协议

> 🌏 **文档语言** — 每个 sub-skill 的完整文档（SKILL.md + references）提供两个版本：
> [简体中文](./docs/zh/)（镜像在 `docs/zh/<skill>/`）和
> [English](./)（运行时加载版，在各 skill 目录下）。

## 为什么拆成多个 sub-skill 而非单体？

- **可分享** — 把 `py-improve` 给朋友不用带上无关的 `db-tweak`
- **聚焦** — 每个 skill 一个明确的职责
- **独立** — 无跨 skill 共享引用，分享时不会断裂
- **触发精准** — 每个 description 都列出显式 `Triggers:` 关键词供 Claude Code 自动匹配

## 安装

### 方式 1：Claude Code Plugin Marketplace（推荐）

在 Claude Code 内：

```
/plugin marketplace add liyong-labs/repo-medic
```

然后选 `Browse and install plugins` → `liyong-labs-repo-medic` → install。

### 方式 2：vercel-labs Skills CLI（多 agent）

```bash
npx skills add liyong-labs/repo-medic
```

支持 73+ agents（Claude Code / Codex / Cursor / OpenCode 等）。见 <https://github.com/vercel-labs/skills>。

### 方式 3：手动安装（任何 *nix）

```bash
# 安装所有 sub-skill
git clone https://github.com/liyong-labs/repo-medic.git
cd repo-medic
for d in repo-medic py-improve doc-reorg db-tweak vue-improve config-base evolve; do
  ln -s "$(pwd)/$d" ~/.claude/skills/$d
done
```

或选装：

```bash
# 只装 Python 代码审查
cp -r py-improve ~/.claude/skills/

# 只装数据库调优
cp -r db-tweak ~/.claude/skills/
```

装完验证：

```bash
python ~/.claude/skills/config-base/scripts/tools.py check
```

## 用法

### 调用方式

裸调 `/repo-medic`（不带参数）会按当前对话语言打印 help 块。其余：

```
/py-improve                   # 直调：Python 代码改进
/doc-reorg                    # 直调：文档 + 目录整理
/db-tweak                     # 直调：PostgreSQL 调优
/vue-improve                  # 直调：Vue 3 前端改进
/config-base                  # 直调：工具链检查/安装
/evolve                       # 直调：蒸馏项目经验
```

meta 路由（模糊请求）：

```
/repo-medic 我的 Python god-function 太长
→ 路由到 py-improve

/repo-medic PG 迁移后查询变慢
→ 路由到 db-tweak

/repo-medic 看看缺什么工具
→ 路由到 config-base
```

端到端示例（config-base + py-improve）：

```
# 1. 检查已装什么
/config-base

# 2. 装缺的工具（默认 dry-run，--yes 才真正执行）
python ~/.claude/skills/config-base/scripts/tools.py install ruff --yes

# 3. 扫脚本里的静默吞错
/py-improve 检查 silent_swallow in my OpenVINO loader
```

### 每个 sub-skill 做什么 — 以及为什么这么设计

**`py-improve` — Python 代码健康**
做什么：god-function 拆分、死代码删除、字典/常量去重、静默吞错扫描（`except: pass` → 改 log 或 raise）、日志可观测性、合入前 CR。
为什么：静默 `except: pass` 会把失败藏到数据已损坏才暴露 — 扫描器内置 context-aware 过滤（如 `StopIteration` 惯用法、cleanup 路径），让你看到的是真吞错不是惯用法。死代码必须先过 7 步引用证明才准删，因为「看起来没用」正是误删在用代码的原因。重构全程跑在 TDD 安全网后面，保证行为不变。

**`doc-reorg` — 目录 + 文档一次性整理**
做什么：`git mv` 重命名、tmp/debug 产物归档、文档分类（MRD/PRD/ARCH/DESIGN/TEST/RESEARCH）、env.md/deploy.md 同步。
为什么：备份先行（`rsync` 快照 + GATE 挡住 Phase 1）——批量重命名最容易弄断 import 和链接。每个旧路径必须留 redirect/symlink，外部引用永不 404。每次运行写 work-note 记录什么动了、为什么动——下一个人不用考古。

**`db-tweak` — PostgreSQL 调优 + 删除退役流水线**
做什么：慢查询诊断（`EXPLAIN (ANALYZE, BUFFERS)`）、索引设计、9 铁律、7 阶段流程、DROP 退役流水线（`RENAME TO PLAN_DELETE_*` → 7 天观察 → user 批准才 DROP）。
为什么：baseline 先行——没有前后对比就无法证明索引有效。`CONCURRENTLY` + 显式 lock timeout，因为搞挂生产的多半是 DDL。破坏性操作走「先改名后等待」：DROP 是瞬间且不可逆的，RENAME 是瞬间且可逆的。

**`vue-improve` — Vue 3 + TS + Vite + Pinia**
做什么：组件/store/Vite 构建模式 + 已知坑清单扫查（setup TDZ、`watchEffect` 误用、Pinia 解构丢响应性、第三方库 worker 作用域、chunk-hash 部署验证）。
为什么：这些坑在每个代码库都反复出现——pdf.js/ECharts 这类库静默共享 worker、悄悄破坏 selector 作用域。部署后逐个 curl 校验带 hash 的 chunk URL，因为「build 成功」≠「用户加载得到」。

**`config-base` — 工具链 bootstrap**
做什么：`tools.py check` 报告 Python/Node/DB 工具链的已装/缺失/过期；`install <name>` 默认 dry-run，动手前先问。
为什么：agent 失败得很神秘时，多半是缺 linter 或 DB client——显式检测把「诡异报错」变成「装这个」。默认 dry-run 因为装包会改机器，必须由用户拍板。

### evolve — 升级不丢的经验库

`/evolve` 把项目的痛变成可复用的经验：

1. **提取** — 扫 `git log` + `docs/work-note/` 里的 Symptom/Cause/Fix 模式，聚类，按频率排序
2. **审核** — 逐条给用户看，接受/拒绝/修改（没你的 OK 什么都不写）
3. **分桶** — lesson 写入 `~/.claude/skills/repo-medic-lessons/lessons/<sub-skill>/<topic>.md`，并更新 companion skill 的索引
4. **验证** — smoke test + work-note

**为什么放包外的 companion skill？** skill 目录在升级时被整体替换——plugin 更新、`cp -r`、fresh clone 都会覆盖 `py-improve/` 等目录。写在 skill 文件夹里的经验，会在你保持更新的那一刻被销毁。`repo-medic-lessons/` 不属于任何版本发布，升级永远碰不到它——项目积累的历史只会复利，不会清零。

**为什么只做加法？** lesson 永不修改发布的 `SKILL.md` 和 14 硬约束。lesson 无法悄悄削弱安全 gate，升级 repo-medic 也无法悄悄回滚你的经验。

**经验怎么被消费？** companion skill 的 description 按域积累 trigger 关键词，相关任务出现时 Claude Code 自动加载；也可以在跑某个 sub-skill 前直接读对应桶。

项目特有的细节仍留在该项目自己的 work-note 里——evolve 孞的是值得跨项目带走的经验。

## 设计原则

| # | 原则 | 来源 |
|---|---|---|
| 1 | **自包含** — `cp -r <sub-skill>` 独立可用 | 简单性 |
| 2 | **MANDATORY WORKFLOW + 🛑 GATE** — 显式 gate 防 LLM 跳过 | [wix/skills](https://github.com/wix/skills) |
| 3 | **Triggers 关键词在 frontmatter** — 显式列表供 Claude Code 匹配 | wix/skills |
| 4 | **14 硬约束**内嵌每个 skill — YAGNI / 禁 git reset / 批次先测最小 / daemon 4 步 | 跨 skill |
| 5 | **脚本只用标准库** — 不加新依赖 | YAGNI |
| 6 | **1 commit = 1 逻辑单元** — 原子，可独立回滚 | 提交卫生 |
| 7 | **自进化循环** — `evolve` 把项目历史蒸馏成 lesson，存入升级安全的 companion skill | Meta |

## 路线图

- [x] v0.1.0 — 首发（4 sub-skills + meta）
- [x] v0.1.1 — Triggers 关键词 + marketplace.json + MANDATORY WORKFLOW
- [x] v0.2.0 — `config-base` sub-skill（工具链 bootstrap）
- [x] v0.2.1 — Windows 兼容（.cmd/.bat/.com + GBK fallback）
- [x] v0.3.0 — `evolve` sub-skill（自蒸馏）
- [x] v0.4.0 — 社区文件（CONTRIBUTING + CoC + issue/PR 模板）+ README 完善
- [x] v0.5.0 — 全量双语文档：英文运行时 + 简体中文镜像（`docs/zh/`）
- [ ] v0.5.1 — 语言自适应 `/repo-medic` help + evolve 完善 ← **当前**
- [ ] v0.6.0 — CI workflow（PR 跑 ruff + mypy + smoke test）
- [ ] v1.0.0 — 稳定 API + 第一轮外部用户反馈

## 贡献

欢迎新 sub-skill、bug 修复、文档改进！见 [CONTRIBUTING.md](CONTRIBUTING.md)。

请遵守 [Code of Conduct](CODE_OF_CONDUCT.md)。

## 安全

通过 [GitHub Security Advisories](https://github.com/liyong-labs/repo-medic/security/advisories/new) 报告漏洞。见 [SECURITY.md](SECURITY.md)。

## 协议

Apache-2.0 — 见 [LICENSE](LICENSE)。

## 维护者

- github.com/liyong-labs
- Issues: <https://github.com/liyong-labs/repo-medic/issues>
- Discussions: <https://github.com/liyong-labs/repo-medic/discussions>

## 致谢

灵感来源：

- [anthropics/skills](https://github.com/anthropics/skills) — 官方 Agent Skills
- [wix/skills](https://github.com/wix/skills) — 生产级 SKILL.md 模式
- [vercel-labs/skills](https://github.com/vercel-labs/skills) — 多 agent CLI
- [agentskills.io](https://agentskills.io/specification) — Agent Skills 规范

Star 历史：

[![Star History Chart](https://api.star-history.com/svg?repos=liyong-labs/repo-medic&type=Date)](https://star-history.com/#liyong-labs/repo-medic&Date)
