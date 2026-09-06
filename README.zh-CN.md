# repo-medic

自包含的 Claude Code skill 工具包，覆盖日常代码维护：重构、字典去重、静默吞错、目录/文档归档、PostgreSQL 调优、Vue 3 前端改进。

## 子 skill

| Sub-skill | 范围 |
|---|---|
| [`py-improve`](./py-improve/) | Python 代码：god-fn 拆分、死代码、字典/常量去重、静默吞错扫描、日志、CR |
| [`doc-reorg`](./doc-reorg/) | 目录 + 文档 + 文件整理（git mv、tmp 归档、文档分类） |
| [`db-tweak`](./db-tweak/) | PostgreSQL：慢查询、索引、9 铁律、7 phase、退场流水线 |
| [`vue-improve`](./vue-improve/) | Vue 3 + TS + Vite + Pinia 前端改进 |
| [`config-base`](./config-base/) | 工具链 bootstrap：检测 + 安装 + 升级依赖（ruff/mypy/codegraph/node/psql） |
| [`evolve`](./evolve/) | 自进化：扫描项目踩的坑 → 蒸馏经验 → 注入 sub-skill（避免重蹈覆辙） |
| [`repo-medic`](./repo-medic/SKILL.md) | Meta 路由 — 根据 prompt 关键词路由到子 skill |

每个子 skill **自包含**：`cp -r <sub-skill> ~/.claude/skills/` 直接可用。

## 为什么拆成多个 sub-skill 而非单体？

- **可分享** — 把 `py-improve` 给朋友不用带上无关的 `db-tweak`
- **聚焦** — 每个 skill 一个明确的职责
- **独立** — 无跨 skill 共享资源，分享时引用不会断裂

## 安装

```bash
git clone https://github.com/ebziw/repo-medic.git
cd repo-medic

# 软链（或复制）所有 sub-skill 到 Claude Code skills 目录
for d in repo-medic py-improve doc-reorg db-tweak vue-improve; do
  ln -s "$(pwd)/$d" ~/.claude/skills/$d
done
```

或单独复制：

```bash
cp -r vue-improve ~/.claude/skills/
```

## 使用

直接调 sub-skill：

```
/py-improve
/doc-reorg
/db-tweak
/vue-improve
```

或用 meta 路由（模糊 prompt）：

```
/repo-medic 我的 Python god-function 要拆
→ 路由到 py-improve
```

## 硬约束（所有 sub-skill 通用）

每个 sub-skill 的 `SKILL.md` 都内嵌相同的 14 条硬约束（YAGNI、commit 颗粒度、禁止 `git reset --hard`、死代码 7 步证明、TDD 4 模式、prod 锁定、宁缺勿伪、DB 删除退场、批次先测最小、daemon 4 步独立、buffer 所有权、hash 产物整目录同步、部署验证实际标识等）。

## 协议

Apache-2.0 — 见 [LICENSE](./LICENSE)。

## 仓库

https://github.com/ebziw/repo-medic
