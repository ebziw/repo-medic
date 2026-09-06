---
name: py-improve
description: Python 代码改进 — god-fn 拆分 / 死代码删除 / 重复方法合并 / 字典常量去重 / 静默吞错修复 / 日志可观测性 / 合入前 CR。包含 ruff/vulture/bandit/radon/pyright MCP 工具链。Triggers: god-fn, 死代码, 静默吞错, 字典去重, 日志, code review, 重构, Python, pytest, mypy, ruff, vulture, 拆分, 重复, refactor, dedup, silent error, god function
metadata:
  type: domain
  scope: public
---

# py-improve — Python 代码改进

self-contained skill。复制整个目录即可分享给其他项目。

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Reconnaissance

- [ ] **Read** `references/code-refactor.md` in full (17 phases methodology)
- [ ] **Read** `references/code-review-checklist.md` (合入前机械规则)
- [ ] **Read** `references/logging-observability.md` (静默吞错扫描命令)
- [ ] **Read** `references/dict-dedup.md` if dict/constant changes involved
- [ ] **Run** 静默吞错扫描: `python scripts/silent_swallow.py src/`
- [ ] **Run** 引用残留扫描: `python scripts/reorg_drift.py` (if renaming/moving)
- [ ] **Build** codegraph (大项目 ≥ 5min 时): `codegraph build --no-incremental`
- [ ] 🛑 **GATE**: 拿到 baseline metrics 后才能进 Phase 1（无基线 = 无改进证据）

### Phase 1: Diagnose

- [ ] **List god-fn candidates**: cyclomatic > 15 OR 行数 > 100（`radon cc -s src/`）
- [ ] **List 死代码 candidates**: ruff `F401` / `F841` / pyright `reportUnused*`
- [ ] **List 重复**: 相同函数签名 ≥ 2 处（grep function def）
- [ ] **List 字典/常量重复**: `references/dict-dedup.md` 4 类问题分类对照
- [ ] 🛑 **GATE**: 列完候选 + 用户确认范围后才能动（避免无目标大改）

### Phase 2: Execute

- [ ] **1 commit = 1 logical unit**（铁律 2）— 一次只改一类问题
- [ ] **写测试 first**（TDD 4 模式之一: Characterization / Red-Green / Regression / Structural）
- [ ] **改完立即跑** `pytest` + `ruff check` + `mypy`（铁律 6）
- [ ] **每个 commit 跑** `silent_swallow.py src/`（铁律横切 13.1）
- [ ] 🛑 **GATE**: 测试必须全绿才能下个 commit（红 = 退回 Phase 2）

### Phase 3: Verify

- [ ] **所有测试绿**: `pytest tests/` 0 fail
- [ ] **无新增 silent-swallow**: `silent_swallow.py src/` output 不增
- [ ] **codegraph 无 broken import**: `codegraph where <moved_module>` 仍可解析
- [ ] **新增功能有 test**: `pytest --cov` 新代码有覆盖
- [ ] **commit 历史清晰**: `git log --oneline` 一目了然每个 commit 一个改进点
- [ ] 🛑 **GATE**: 全部勾选 = 可以汇报完成。任何一项未勾 = 不能说"done"

---

## 包含

| 路径 | 内容 |
|---|---|
| `references/code-refactor.md` | god-fn 拆分 + 死代码 7 步 + TDD 4 模式 + YAGNI |
| `references/code-review-checklist.md` | 合入前机械规则 + no-silent-swallow P0 |
| `references/logging-observability.md` | 静默吞错扫描命令 + 修法模板 |
| `references/dict-dedup.md` | 字典/常量去重 4 类问题分类 + Phase 0-5 |
| `references/dict-dedup-case-levelcfg.md` | _LEVEL_CFG CONFLICT 案例教学 |
| `scripts/silent_swallow.py` | 静默吞错扫描器 |
| `scripts/reorg_drift.py` | 引用残留扫描（删 module 后检查 caller） |
| `mcp_servers/python_refactor_server.py` | MCP server: ruff/vulture/bandit/radon/pyright |

## 使用

```bash
# 静默吞错扫描
python ~/.claude/skills/py-improve/scripts/silent_swallow.py src/

# 引用残留
python ~/.claude/skills/py-improve/scripts/reorg_drift.py

# MCP 工具（注册到 ~/.claude/settings.json）
# 见 mcp_servers/python_refactor_server.py
```

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 + 零提前防御 (YAGNI)**: 只用 stdlib + 已装库。不为假设风险提前加 try/except / retry / fallback / 抽象层。
2. **commit 颗粒度**: 1 逻辑单元 = 1 commit，独立可回滚。
3. **默认回滚 = rsync 备份还原** (无损)。**绝对禁止 `git reset --hard`**。
4. **死代码证明需 7 步 checklist**: 静态引用 + 文本搜索 + 框架注册 + export + 动态调用 + 测试/生成 + 用户签字。0 caller grep ≠ 证明。
5. **TDD 按场景分 4 模式**: Characterization / Red-Green / Structural (7 步 + 全 build/test) / Regression。
6. **commit 前全量测试全绿**，不破 CI。**项目级例外**：当本项目跑测试本身不安全时（如测试会改动生产数据），以项目自己的规则为准——在运行报告里记录该例外，并跑能覆盖本次改动的最安全子集。
7. **prod 锁定**: 不动线上代码，owner 显式授权才动。
8. **宁缺勿伪**: 不确定的事实留 TODO，不编。校验靠 grep / codegraph / pyright 实测。
9. **DB 删除必走退场流水线**: DROP 前 RENAME → PLAN_DELETE_<原名> → 7 天测试 → user 审。
10. **批量任务先测最小**: 任何批量操作先选最小样本 (1-10) 跑通 + 计时，按比例推全量耗时。**禁止直接开最大集合**。
11. **daemon / 服务代码改动 4 步独立**: ①本地 Edit ②本地 py_compile 验证 ③scp 上传 + 清 __pycache__ ④systemctl restart + pgrep 验证 PID 变了。**不链式 restart && smoke**。
12. **buffer 所有权被转移**: 缓存方必须保留副本，每次传递前 bytes.slice(0) / np.array(..., copy=True)。
13. **hash 化构建产物必须整目录同步**: 前端 chunk 名带 hash — 只推改的文件 → index.html 引用新 hash → 缺 chunk → MIME text/html 404。
14. **部署/发布后必须验证实际生效产物标识**: 脚本输出 "✓ done" ≠ 部署成功。

## 关联

- `/repo-medic` — meta 入口
- `/doc-reorg` — 重构后目录归档
- `/db-tweak` — DB 相关调用方审查

## 仓库

github.com/ebziw/repo-medic — Apache-2.0。
