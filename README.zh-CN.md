# repo-medic

> 自包含的 **Claude Code skill 工具包**，用于日常代码维护。
> 重构 · 去重 · 数据库调优 · 文档整理 · 前端审查 · 工具 bootstrap · 自进化。

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-blueviolet)](https://docs.claude.com/en/docs/claude-code/skills)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![Sub-skills](https://img.shields.io/badge/sub--skills-7-orange.svg)](#子-skill-列表)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

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

## 为什么拆成多个 sub-skill 而非单体？

- **可分享** — 把 `py-improve` 给朋友不用带上无关的 `db-tweak`
- **聚焦** — 每个 skill 一个明确的职责
- **独立** — 无跨 skill 共享引用，分享时不会断裂
- **触发精准** — 每个 description 都列出显式 `Triggers:` 关键词供 Claude Code 自动匹配

## 安装

### 方式 1：Claude Code Plugin Marketplace（推荐）

在 Claude Code 内：

```
/plugin marketplace add ebziw/repo-medic
```

然后选 `Browse and install plugins` → `ebziw-repo-medic` → install。

### 方式 2：vercel-labs Skills CLI（多 agent）

```bash
npx skills add ebziw/repo-medic
```

支持 73+ agents（Claude Code / Codex / Cursor / OpenCode 等）。见 <https://github.com/vercel-labs/skills>。

### 方式 3：手动安装（任何 *nix）

```bash
# 安装所有 sub-skill
git clone https://github.com/ebziw/repo-medic.git
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

## 快速开始

### 直接调用

```
/py-improve                   # 问 Python 代码改进
/doc-reorg                    # 整理文档和目录
/db-tweak                     # 调优 PostgreSQL
/vue-improve                  # 审查 Vue 组件
/config-base                  # 检查工具依赖
/evolve                       # 蒸馏项目经验
```

### 通过 meta 路由（模糊请求）

```
/repo-medic 我的 Python god-function 太长
→ 路由到 py-improve

/repo-medic PG 迁移后查询变慢
→ 路由到 db-tweak

/repo-medic 看看缺什么工具
→ 路由到 config-base
```

### 示例：Intel iGPU 跑 BGE-M3 embedding

```
# 1. 检查已装什么
/config-base

# 2. 装缺的 Intel OpenCL ICD
python ~/.claude/skills/config-base/scripts/tools.py install intel-opencl-icd --yes

# 3. 让 py-improve 扫 OpenVINO loader 的静默吞错
/py-improve 检查 silent_swallow in my OpenVINO loader
```

## 设计原则

| # | 原则 | 来源 |
|---|---|---|
| 1 | **自包含** — `cp -r <sub-skill>` 独立可用 | 简单性 |
| 2 | **MANDATORY WORKFLOW + 🛑 GATE** — 显式 gate 防 LLM 跳过 | [wix/skills](https://github.com/wix/skills) |
| 3 | **Triggers 关键词在 frontmatter** — 显式列表供 Claude Code 匹配 | wix/skills |
| 4 | **14 硬约束**内嵌每个 skill — YAGNI / 禁 git reset / 批次先测最小 / daemon 4 步 | 跨 skill |
| 5 | **脚本只用标准库** — 不加新依赖 | YAGNI |
| 6 | **1 commit = 1 逻辑单元** — 原子，可独立回滚 | 提交卫生 |
| 7 | **自进化循环** — `evolve` sub-skill 扫项目历史回灌经验 | Meta |

## 路线图

- [x] v0.1.0 — 首发（4 sub-skills + meta）
- [x] v0.1.1 — Triggers 关键词 + marketplace.json + MANDATORY WORKFLOW
- [x] v0.2.0 — `config-base` sub-skill（工具链 bootstrap）
- [x] v0.2.1 — Windows 兼容（.cmd/.bat/.com + GBK fallback）
- [x] v0.3.0 — `evolve` sub-skill（自蒸馏）
- [ ] v0.4.0 — 社区文件（CONTRIBUTING + CoC + issue/PR 模板）+ README 完善 ← **当前**
- [ ] v0.5.0 — CI workflow（PR 跑 ruff + mypy + smoke test）
- [ ] v1.0.0 — 稳定 API + 第一轮外部用户反馈

## 贡献

欢迎新 sub-skill、bug 修复、文档改进！见 [CONTRIBUTING.md](CONTRIBUTING.md)。

请遵守 [Code of Conduct](CODE_OF_CONDUCT.md)。

## 安全

通过 [GitHub Security Advisories](https://github.com/ebziw/repo-medic/security/advisories/new) 报告漏洞。见 [SECURITY.md](SECURITY.md)。

## 协议

Apache-2.0 — 见 [LICENSE](LICENSE)。

## 维护者

- github.com/ebziw
- Issues: <https://github.com/ebziw/repo-medic/issues>
- Discussions: <https://github.com/ebziw/repo-medic/discussions>

## 致谢

灵感来源：

- [anthropics/skills](https://github.com/anthropics/skills) — 官方 Agent Skills
- [wix/skills](https://github.com/wix/skills) — 生产级 SKILL.md 模式
- [vercel-labs/skills](https://github.com/vercel-labs/skills) — 多 agent CLI
- [agentskills.io](https://agentskills.io/specification) — Agent Skills 规范

Star 历史：

[![Star History Chart](https://api.star-history.com/svg?repos=ebziw/repo-medic&type=Date)](https://star-history.com/#ebziw/repo-medic&Date)
