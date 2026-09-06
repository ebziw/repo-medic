# PostgreSQL Tuning Reference

Generic PostgreSQL tuning reference for the `db-tweak` skill. 9 铁律 + 7 phase + 8 模式 framework + tooling stack.

---

## 9 铁律 (Hard Constraints)

| # | 铁律 | 说明 |
|---|---|---|
| 1 | **证据先行** | 任何 schema 变更前必须 `EXPLAIN ANALYZE` 当前查询 + `pg_stat_statements` 历史。改之前先看到基线。 |
| 2 | **DDL CONCURRENTLY** | 索引创建必须 `CREATE INDEX CONCURRENTLY`。否则锁表，线上 502。 |
| 3 | **删除三核对** | DROP 前核对：①是否仍被引用（`pg_depend` / `pg_constraint`）②备份存在 ③有 RENAME 退场窗口 |
| 4 | **名字正则陷阱** | 标识符全小写 + 下划线；避免双引号大小写敏感；避免 PG 保留字（`user`, `order`, `group`） |
| 5 | **statement_timeout 30s** | 所有 session 设 `SET statement_timeout = '30s'` 防单查询拖垮连接池 |
| 6 | **VACUUM FULL 勇哥批** | 默认 autovacuum；`VACUUM FULL` 锁表 8x 表大小时间，**必须 owner 审批** |
| 7 | **锁查双时钟** | 锁等待超 5s 必查；DB 时间 != 业务时间，跨时区报表必显式带 tz |
| 8 | **DDL 不裸跑** | 所有 DDL 走 migration tool（`yoyo-migrations` / `sqlx-migrate` / 自研），不直接 `psql -c` |
| 9 | **删除前先 rename** | DROP COLUMN/TABLE 之前必先 `ALTER ... RENAME TO PLAN_DELETE_<原名>` + 1+ 周测试 + owner 审 → 才真 DROP |

---

## 7 Phase (大版本或全量重构)

| Phase | 目标 | 产物 |
|---|---|---|
| 1. **大版本升级审计** | PG 12→16 前的扩展兼容性 + 弃用 API 清单 | upgrade-audit.md |
| 2. **证据采集** | `pg_stat_statements` top 20 慢查询 + 表大小 + 索引 bloat | baseline.json |
| 3. **模式 sweep** | 8 模式检查（见下）清单 | sweep-report.md |
| 4. **修复** | 建索引 / 改 schema / 调参数 | migration 脚本 |
| 5. **验证** | 回归测试 + EXPLAIN 对比 + p95 latency 对比 | verify-report.md |
| 6. **沉淀** | work-note 写入 docs/work-note/ + KB 同步 | work-note.md |
| 7. **退场流水线** | `plan-delete.sh` RENAME → 7 天 review → DROP | audit-plan-delete.sh 标记 Ready to DROP |

---

## 8 模式 (Anti-patterns to Detect)

| # | 模式 | 检测 | 修法 |
|---|---|---|---|
| 1 | **TOAST 进 WHERE** | EXPLAIN 显示外联 TOAST 表 | 改条件用主表字段，或建表达式索引 |
| 2 | **TOAST 全表窗口** | `pg_stat_user_tables.seq_scan >> idx_scan` 大表 | 强制索引扫描 / 加 hint |
| 3 | **ORDER BY 无索引** | EXPLAIN 中 Sort 节点无 Index | 加 btree 索引匹配 ORDER BY 顺序 |
| 4 | **OFFSET 深分页** | `LIMIT 20 OFFSET 100000` | 改 keyset pagination (`WHERE id > last_id`) |
| 5 | **统计过期** | `pg_stat_user_tables.n_mod_since_analyze > 1000` | `ANALYZE table_name` 或调 autovacuum_analyze_scale_factor |
| 6 | **隐式 cast** | EXPLAIN 显示 `Cast` 节点跨类型 | 显式 cast 或改 schema 类型一致 |
| 7 | **SELECT *** | text 字段被扫但不用 | 明确列名；大 text 字段单独 SELECT |
| 8 | **btree bloat** | `pgstatginindex` / `pgstatindex` bloat > 30% | `REINDEX CONCURRENTLY`（PG 12+） |

---

## 工具栈

| 工具 | 用途 |
|---|---|
| **HypoPG** | 假设索引 — `CREATE INDEX ON tbl (col) WHERE ...` 不真建，看 planner 是否会用 |
| **pg_stat_monitor** | 时间分桶查询统计（比 pg_stat_statements 更细粒度） |
| **pgstattuple** | 表/索引 bloat 量化 |
| **Postgres MCP** (`crystaldba/postgres-mcp`) | LLM 直连 PG，跑 EXPLAIN + 调索引 |
| **pgcli** | 命令行交互（语法高亮 + 自动补全） |
| **pgFormatter** | SQL 格式化（CI lint） |

---

## 退场流水线（铁律 9 实操）

```bash
# 1. RENAME（业务代码暂不删，先改名字）
./scripts/plan-delete.sh --column public.users.legacy_field
# 输出：
# ALTER TABLE public.users RENAME COLUMN legacy_field TO PLAN_DELETE_legacy_field;
# (记录到 ~/.cache/db-tweak/pending-drops/users.legacy_field.json)

# 2. 监控 7+ 天，看是否有未迁移引用
./scripts/audit-plan-delete.sh
# 列所有 pending + DAYS_LEFT + STATUS

# 3. DAYS_LEFT ≤ 0 后再真 DROP（仍需 owner 审批）
# owner 显式说 "drop" 才动；否则无限期保留
```

---

## 监控关键指标

| 指标 | 阈值 | 工具 |
|---|---|---|
| 连接数使用率 | < 80% | `pg_stat_activity` count / max_connections |
| 缓存命中率 | > 99% | `pg_stat_database` blks_hit / (blks_hit + blks_read) |
| 复制延迟 | < 1s | `pg_stat_replication` replay_lag |
| 长事务 | > 5min 告警 | `pg_stat_activity.state = 'active' AND xact_start < now() - interval '5 min'` |
| 死锁 | 任何发生 | `pg_stat_database.deadlocks` delta > 0 |
| 表膨胀 | bloat > 30% | `pgstattuple` |

---

## 关联

- `py-improve` — 慢查询的 Python 调用方代码审查
- `doc-reorg` — schema 文档同步（schema 变更 → env.md / deploy.md）
- `repo-medic`（meta） — 路由入口
