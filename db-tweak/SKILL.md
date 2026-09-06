---
name: db-tweak
description: PostgreSQL 数据库调优 — 慢查询优化 / 索引设计 / 9 铁律 / 7 phase / 8 模式 / 退场流水线（PLAN_DELETE_ rename）。包含 plan-delete.sh、audit-plan-delete.sh、config_drift.py。用于触发：PG 慢查询、索引、EXPLAIN、VACUUM、DROP COLUMN/TABLE、SQL 调优、PG schema 变更。
metadata:
  type: domain
  scope: public
---

# db-tweak — PostgreSQL 调优

self-contained skill。覆盖 PG 慢查询优化、索引、DDL 安全、字段/表删除的退场流水线。

## 包含

| 路径 | 内容 |
|---|---|
| `references/db-tuning.md` | 9 铁律 + 7 phase + 8 模式 + 工具栈 + 监控指标 |
| `scripts/plan-delete.sh` | DROP 前 RENAME → PLAN_DELETE_ 流水线（auto-emit ALTER + 记录 pending JSON） |
| `scripts/audit-plan-delete.sh` | 列所有 pending + DAYS_LEFT + STATUS（Ready to DROP 标记） |
| `scripts/config_drift.py` | live config (systemd / crontab / .env) vs git 检测 |

## 使用

```bash
# 慢查询 → 看 references/db-tuning.md 8 模式 sweep

# DROP 前退场
./scripts/plan-delete.sh --column public.users.legacy_field
./scripts/plan-delete.sh --table public.old_logs
./scripts/plan-delete.sh --index public.idx_unused

# 7 天后 review
./scripts/audit-plan-delete.sh

# config drift（live vs git-tracked）
python scripts/config_drift.py --all --repo /path/to/project
```

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 + 零提前防御 (YAGNI)**: 只用 stdlib + 已装库。db-tweak 自带的脚本优先用，不用额外装 pgcli/psql 之外的工具。
2. **commit 颗粒度**: 1 逻辑单元 = 1 commit。DDL migration 一个 commit。
3. **默认回滚 = rsync 备份还原**。**绝对禁止 `git reset --hard`**。DB schema 退场走 PLAN_DELETE_ rename（非 DROP，保留回滚窗口）。
4. **死代码证明需 7 步 checklist**: 字段/索引删除前必确认无引用（pg_depend + 应用代码 grep + ORM migration）。
5. **TDD 按场景分 4 模式**: schema 变更用 Structural (全 build/test)。
6. **commit 前全量测试全绿**: 必跑 migration 干跑（pg_restore dry-run）+ 应用回归。
7. **prod 锁定**: DDL on prod 走 migration tool，owner 审。**不裸跑 `psql -c "ALTER ..."`**。
8. **宁缺勿伪**: 不确定的事实验证靠 EXPLAIN ANALYZE + pg_stat_statements。
9. **DB 删除必走退场流水线**: DROP COLUMN/TABLE 之前必先 RENAME → PLAN_DELETE_<原名> → 1+ 周测试 + owner 审。配套 `scripts/plan-delete.sh`。
10. **批量任务先测最小**: 大批量 migration 先选最小 schema 子集（1-10 表）跑通 + 计时。
11. **daemon / 服务代码改动 4 步独立**: DB 触发器/PL 改完后独立验证：①本地 dry-run ②staging apply ③prod maintenance window apply ④监控锁等待。
12. **buffer 所有权被转移**: COPY FROM 客户端传 buffer — 缓存方保留副本。
13. **hash 化构建产物必须整目录同步**: 索引 rebuild（REINDEX CONCURRENTLY）必须等所有 backend 节点完成才能切流量。
14. **部署/发布后必须验证实际生效产物标识**: migration apply 后查 `pg_indexes` / `pg_attribute` / `pg_class` 确认新 schema 生效，不看脚本退出码。

## DB 专属铁律

| # | 铁律 | 说明 |
|---|---|---|
| 1 | 证据先行 | EXPLAIN ANALYZE + pg_stat_statements 基线 |
| 2 | DDL CONCURRENTLY | 索引创建必须 CONCURRENTLY |
| 3 | 删除三核对 | 引用 + 备份 + RENAME 窗口 |
| 4 | 名字正则陷阱 | 全小写下划线，避免双引号大小写 |
| 5 | statement_timeout 30s | session-level |
| 6 | VACUUM FULL 勇哥批 | 默认 autovacuum，FULL 锁表必 owner 批 |
| 7 | 锁查双时钟 | 锁 > 5s 必查；DB 时间 != 业务时间 |
| 8 | DDL 不裸跑 | 走 migration tool |
| 9 | 删除前先 rename | PLAN_DELETE_ + 1 周测试 + owner 审 |

## 关联

- `/repo-medic` — meta 入口
- `/py-improve` — 慢查询的 Python 调用方代码审查
- `/doc-reorg` — schema 变更后 env.md / deploy.md 同步

## 仓库

github.com/ebziw/repo-medic — Apache-2.0。
