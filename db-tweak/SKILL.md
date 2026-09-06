---
name: db-tweak
description: PostgreSQL 数据库调优 — 慢查询优化 / 索引设计 / 9 铁律 / 7 phase / 8 模式 / 退场流水线（PLAN_DELETE_ rename）。包含 plan-delete.sh、audit-plan-delete.sh、config_drift.py。Triggers: PostgreSQL, PG, 索引, EXPLAIN, VACUUM, 慢查询, DROP, schema, 调优, plan-delete, migration, database tune, query optimization, bloat
metadata:
  type: domain
  scope: public
---

# db-tweak — PostgreSQL 调优

self-contained skill。覆盖 PG 慢查询优化、索引、DDL 安全、字段/表删除的退场流水线。

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Baseline (证据先行 — 铁律 1)

- [ ] **Read** `references/db-tuning.md` in full (9 铁律 + 7 phase + 8 模式)
- [ ] **抓 top 20 慢查询**: `SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 20;`
- [ ] **表大小 + 索引 bloat 快照**: 用 `pgstattuple` 量化，存 baseline.json
- [ ] **EXPLAIN ANALYZE** 当前慢查询（带 BUFFERS 选项）保存前后对比基线
- [ ] 🛑 **GATE**: baseline 文档落盘 (`baseline-<date>.json`) 才能进 Phase 1

### Phase 1: 9 铁律预检（铁律 1-9 全过一遍）

- [ ] **铁律 1**: EXPLAIN ANALYZE 有缓存？`(plan_time + exec_time) / total`
- [ ] **铁律 2**: 即将跑的 DDL 是否用 CONCURRENTLY？
- [ ] **铁律 3**: DROP 候选引用 / 备份 / RENAME 窗口 3 项都核了？
- [ ] **铁律 4**: 标识符全小写下划线？无 PG 保留字？
- [ ] **铁律 5**: 所有 session 设 `SET statement_timeout = '30s'`？
- [ ] **铁律 6**: 即将 VACUUM FULL？owner 批了？
- [ ] **铁律 7**: 当前锁等待 > 5s？查 `pg_stat_activity`？
- [ ] **铁律 8**: DDL 走 migration tool（不裸 `psql -c`）？
- [ ] **铁律 9**: DROP 走 `plan-delete.sh` 而不是直接 DROP？
- [ ] 🛑 **GATE**: 9 条任一未达 = 进 Phase 2 前修正

### Phase 2: 8 模式 sweep

- [ ] **TOAST 进 WHERE**: EXPLAIN 看外联节点
- [ ] **TOAST 全表窗口**: 大表 seq_scan >> idx_scan
- [ ] **ORDER BY 无索引**: EXPLAIN 中 Sort 节点
- [ ] **OFFSET 深分页**: 查 `LIMIT N OFFSET > 10000`
- [ ] **统计过期**: `pg_stat_user_tables.n_mod_since_analyze` 大值
- [ ] **隐式 cast**: EXPLAIN 中 Cast 节点
- [ ] **SELECT ***: 应用代码 grep `SELECT \*` 找候选
- [ ] **btree bloat**: `pgstattuple` 量化
- [ ] 输出 `sweep-report.md` 列命中项 + 修复建议

### Phase 3: Fix

- [ ] **新索引**: `CREATE INDEX CONCURRENTLY idx_xxx ON tbl (col) WHERE ...` (铁律 2)
- [ ] **改 schema 类型**: 走 migration tool，prod 走 maintenance window (铁律 7)
- [ ] **关掉 SELECT ***: 应用代码改列名
- [ ] **OFFSET → keyset**: WHERE id > last_id LIMIT N
- [ ] **REINDEX CONCURRENTLY** (PG 12+) for btree bloat > 30%
- [ ] **ANALYZE** for 统计过期
- [ ] 🛑 **GATE**: 每个 fix 单独 commit（铁律 2），commit 后 `EXPLAIN ANALYZE` 复跑确认改进

### Phase 4: Verify

- [ ] **回归测试**: 应用层 pytest/e2e 全绿
- [ ] **EXPLAIN 对比**: Phase 0 baseline vs 现在 — p95 latency 应下降
- [ ] **buffer hit rate**: Phase 0 vs 现在 — 应 ≥ 99%
- [ ] **replication lag**: `pg_stat_replication.replay_lag < 1s` (铁律 7)
- [ ] **无新增 lock**: 监控 5 分钟无 `wait_event_type = 'Lock'`
- [ ] 🛑 **GATE**: 全部绿 = 可以汇报改进幅度。任何一项退化 = 立即回滚 migration

### Phase 5: Drop retirement (铁律 9)

- [ ] 不适用场景跳过
- [ ] **RENAME**: `./scripts/plan-delete.sh --column public.users.legacy_field`
- [ ] **7 天观察期**: 监控应用无 `column not found` 错误
- [ ] **audit 检查**: `./scripts/audit-plan-delete.sh` 列 DAYS_LEFT
- [ ] **owner 显式授权** DROP
- [ ] **真 DROP**: 在 owner 授权窗口执行
- [ ] 🛑 **GATE**: 7 天观察 + owner 授权两个条件都满足才能 DROP

### Phase 6: Document + Share

- [ ] **写 work-note**: `docs/work-note/<date>-db-tune.md` (Phase 0 baseline + Phase 4 verify 对比)
- [ ] **KB 同步**: 推 ms.bitensor.com public-knowledge（如果用 KB 系统）
- [ ] **更新 schema 文档**: 字段/表变更 → env.md / deploy.md

---

## 包含

| 路径 | 内容 |
|---|---|
| `references/db-tuning.md` | 9 铁律 + 7 phase + 8 模式 + 工具栈 + 监控指标 |
| `scripts/plan-delete.sh` | DROP 前 RENAME → PLAN_DELETE_ 流水线 |
| `scripts/audit-plan-delete.sh` | 列所有 pending + DAYS_LEFT + STATUS |
| `scripts/config_drift.py` | live config (systemd / crontab / .env) vs git 检测 |

## 使用

```bash
./scripts/plan-delete.sh --column public.users.legacy_field
./scripts/plan-delete.sh --table public.old_logs
./scripts/plan-delete.sh --index public.idx_unused
./scripts/audit-plan-delete.sh
python scripts/config_drift.py --all --repo /path/to/project
```

## DB 专属铁律

| # | 铁律 |
|---|---|
| 1 | 证据先行 |
| 2 | DDL CONCURRENTLY |
| 3 | 删除三核对 |
| 4 | 名字正则陷阱 |
| 5 | statement_timeout 30s |
| 6 | VACUUM FULL owner 批 |
| 7 | 锁查双时钟 |
| 8 | DDL 不裸跑 |
| 9 | 删除前先 rename |

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 (YAGNI)**: 用自带工具优先，不为假设场景加 `pgcli` / HypoPG 之外的依赖。
2. **commit 颗粒度**: 1 个 migration = 1 commit。
3. **默认回滚 = RENAME 窗口**（PLAN_DELETE_）。**绝对禁止 `git reset --hard`**。
4. **死代码证明**: 字段/索引删除前必查 `pg_depend` + 应用代码 grep + ORM migration。
5. **TDD**: schema 变更用 Structural（build + test）。
6. **commit 前全量测试全绿**: migration dry-run + 应用回归。
7. **prod 锁定**: prod DDL 走 migration tool + owner 审。**不裸 `psql -c`**。
8. **宁缺勿伪**: 验证靠 EXPLAIN + pg_stat_statements。
9. **DB 删除必走退场流水线**: PLAN_DELETE_ + 7 天 + owner 审。
10. **批量任务先测最小**: 大批 migration 先 sample 1-10 表。
11. **daemon 改动 4 步独立**: 触发器/PL 改后 4 步独立验证。
12. **buffer 所有权**: COPY FROM 客户端 buffer 保留副本。
13. **hash 化产物整目录同步**: 索引 rebuild 多 backend 节点完成才切流量。
14. **部署验证实际生效**: migration apply 后查 `pg_indexes` / `pg_attribute` 确认新 schema。

## 关联

- `/repo-medic` — meta 入口
- `/py-improve` — 慢查询的 Python 调用方代码审查
- `/doc-reorg` — schema 变更后 env.md / deploy.md 同步
- `/config-base` — bootstrap PG 客户端工具（psql / pgcli / migration tool）

## 仓库

github.com/ebziw/repo-medic — Apache-2.0。
