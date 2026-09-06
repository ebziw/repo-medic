# Code Refactor Subflow (project-doctor 子工作流)

> 触发: 用户说 "代码重构" / "god-fn 拆分" / "死代码清理" / "重复方法合并" / "架构优化"
> 范围: 仅代码层 (`.py` / `.go` / `.ts` / `.rs`), 不动目录结构 / 文档
> 顺序: 用户设计 (2026-08-04) — 先锁行为 → 审计 → 设计 → 计划 → 多 agent 执行 → 清理 → 文档同步

## 总纲：不打断用户 (2026-08-05)

默认行为 / 显式授权 / 冲突解决规则 (性能 vs 可读性 → 可读性胜; YAGNI vs 扩展 → YAGNI 胜; 抽象 vs 直白 → 直白胜; stdlib vs 已装库 → stdlib 胜) **全部见 SKILL.md §默认行为+显式授权, 不在此重复**.

每个 phase 内部不 confirm, phase 边界不 confirm, **只有 Phase 12 前的最终计划**会在执行前一次性输出 (基于 9-11 产出的 plan), 之后自动执行.

> 工具链降级顺序 (`codegraph MCP → CLI → grep fallback`) 见 Phase 1.

## 目录

1. [Phase 0: pre-flight](#phase-0-pre-flight)
2. [Phase 1: codegraph 建索引](#phase-1-codegraph-建索引)
3. [Phase 2: 读代码](#phase-2-读代码)
4. [Phase 3: TDD 保护网](#phase-3-tdd-保护网)
5. [Phase 4: /code-review 审计](#phase-4-code-review-审计)
6. [Phase 5: 拆解上帝函数](#phase-5-拆解上帝函数)
7. [Phase 6: 合并共用方法](#phase-6-合并共用方法)
8. [Phase 7: 合并字典 + 解决冲突](#phase-7-合并字典--解决冲突)
9. [Phase 8: improve-codebase-architecture 优化架构](#phase-8-improve-codebase-architecture-优化架构)
10. [Phase 9: writing-plans 写实施计划](#phase-9-writing-plans-写实施计划)
11. [Phase 10: /ponytail-audit 计划减法](#phase-10-ponytail-audit-计划减法)
12. [Phase 11: plan-eng-review 审计划](#phase-11-plan-eng-review-审计划)
13. [Phase 12: 多 subagents 执行](#phase-12-多-subagents-执行)
14. [Phase 13: 清理无用代码](#phase-13-清理无用代码)
15. [横切: 静默吞错扫描 (P0)](#横切-静默吞错扫描-p0-独立于-phase-体系)
16. [Phase 14: 删无用文件](#phase-14-删无用文件)
17. [Phase 15: 更新设计文档 + 代码注释](#phase-15-更新设计文档--代码注释)
18. [Phase 16: 成功指标评估](#phase-16-成功指标评估)

---

## Phase 0: pre-flight

> **调用前** 替换占位符: `${REPO_ROOT}` `${BACKUP_BIN}` `${BACKUP_ROOT}` `${PROJECT_NAME}` (见 SKILL.md §占位符约定)。不替换直接跑会报错。替换后执行一次确认无残留 `${`.

```bash
# 备份 + tag (带时间戳, 防同日重复跑 tag 冲突)
git tag project-doctor-code-baseline-$(date -u +%Y-%m-%d-%H%M%S)
${BACKUP_BIN} ${REPO_ROOT} ${BACKUP_ROOT}/${PROJECT_NAME}/code-$(date -u +%Y-%m-%d)/
```

**可选**: 大范围重构建议 git worktree 隔离 (`superpowers:using-git-worktrees`), 完成后再 merge, 不污染主分支。

---

## Phase 1: codegraph 建索引

**工具链降级** (唯一 authority, 顶部摘要不重复):

```
[1] MCP codegraph_explore (首选, 在对话中调; 本机 v1.5.0 已装)
    ↓ 不可用 (未注册到 mcp)
[2] codegraph CLI (shell)
    ↓ 不可用 (未装 / 麒麟 native build fail)
[3] grep + rg 人工索引 (fallback, 损失 call graph)
```

`.codegraph/` 目录存在 = 已建索引, 优先用 MCP 工具直接调用 (Claude 对话中). 不存在 → 跑 `codegraph init` 或 `codegraph build`.

**.codegraph/ 存在性检查** (自动, 不打断):

```bash
# 项目根有 .codegraph/ → 用 MCP 工具直接查
# 没 → 跑 codegraph init (一次性)
[ -d .codegraph ] && echo "INDEXED" || codegraph init -i
```

**[1] MCP 工具** (Claude Code 对话中调, 推荐):

```
codegraph_explore(query="how does X work", session_id="...")
codegraph_explore(query="<fn_name>")
codegraph_explore(query="<file_name>")
```

返回: 符号源码 + 调用路径 + blast radius (子毫秒级, 已 Read)。**该工具是 Read 等价** — Claude 拿到结果直接 Edit, 不需要再 Read 源文件.

**[2] CLI 工具** (shell):

```bash
# 建/更新图谱 (一次性; 增量默认开)
codegraph build
# 项目结构总览 (最热文件 = 候选热点)
codegraph map --limit 30
# 定位符号
codegraph where <name>
codegraph context <name> -T       # 源码 + 依赖 + 调用方
codegraph fn-impact <name> -T     # 影响范围
codegraph diff-impact --staged -T # 暂存变更影响
```

**[3] Fallback** (codegraph 装不上 / 麒麟 native build 失败 / 跨机):

```bash
# 函数索引
rg -n '^(func|def|class) ' src/ | wc -l          # 规模
rg -n '(elif|case|switch|&&|\|\|)' src/ | wc -l  # 复杂度粗略信号
# 引用计数
rg -n "<name>" src/ tests/ | wc -l              # 候选引用
```

**降级损失**:
- 无自动 call graph 遍历 → 死代码检查改为全仓库引用计数
- 无 blast radius → Phase 12 multi-agent 执行需要更多手动 dependency check
- 函数/调用路径全靠人工推理

**deliverable**: 函数/模块索引 (供 Phase 2 读代码 + Phase 5 定位 + Phase 13 死代码 7 步)。

---

## Phase 2: 读代码

读项目结构 + 核心文件, 理解:
- 分层 / 模块边界 / 数据流
- 各模块职责 (1 句话)
- 可疑点随手记 (上帝函数 / 重复 / 死代码 / 硬编码), 供 Phase 4 汇总

```bash
# 函数索引 (Phase 1 产物) + 复杂度粗排
rg -n '^(func|def|class) ' src/ | wc -l          # 规模
rg -n '(elif|case|switch|&&|\|\|)' src/ | wc -l  # 复杂度粗略信号
```

**deliverable**: `docs/audit/<date>-code-reorg.md` 代码地图 + 可疑点笔记。

---

## Phase 3: TDD 保护网

**目的**: 重构前锁当前行为, 让后续改动可验证回归。**先建网再动手。**

```bash
Skill: test-driven-development
```

**TDD 模式** (本流水线以重构为主 → 主要 Characterization):

| 场景 | 模式 | 验证 |
|---|---|---|
| 既有行为重构 (extract/rename) | Characterization: 写当前行为 passing test | 新旧行为字节级一致 |
| 新功能 / 修 bug (审计发现) | Red-Green: failing → 实现 → passing → refactor | 红 → 绿 → 仍绿 |
| 纯删除 (清理阶段) | Structural: grep 0 caller + 框架注册点检查 | 7 步 checklist 全 0 |
| 重命名 / 移动 (跨模块) | Regression: 全量 test + lint + type-check | 全绿 + 0 引用泄漏 |

**deliverable**: 关键路径行为测试全绿 (改动前后基线)。

---

## Phase 4: /code-review 审计

**目的**: 找出所有要改的点, 形成问题清单 (驱动 5-8 各设计步)。

```bash
Skill: code-review
# 输出: 按严重度排序的问题清单 (bug / 坏味道 / 过度设计 / 死代码)
```

**deliverable**: `docs/audit/<date>-code-reorg.md` 问题清单, 每条含 file:line + 建议动作, 标注归属:
- → Phase 5 (上帝函数)
- → Phase 6 (重复方法)
- → Phase 7 (字典冲突)
- → Phase 8 (架构)
- → Phase 13/14 (死代码/文件)

> **skill 缺失降级**: 无 code-review → Claude 自查: 边界条件 / 失败路径 / 重复 / 死代码 / 过度设计 逐项过。

---

## Phase 5: 拆解上帝函数

从 Phase 4 清单挑 god-fn 候选 (cyclomatic 高 / 行数多), 逐一定位拆解点。

```bash
codegraph context "<fn_name>" -T   # 源码 + 依赖 + 调用方
codegraph fn-impact "<fn_name>" -T  # 影响范围
```

**顺序** (低风险 → 高风险):
| 步骤 | 操作 | 风险 |
|---|---|---|
| 5a | 纯函数拆分 (无状态) | 低 |
| 5b | 有 mutable state 拆分 (State dataclass + 集成 test) | 高 |

**每步 1 commit**:
```
refactor(<module>): split <fn>
- cyclomatic: <N> → <M>
- tests: <file>:<line> guards behavior
```

> ⚠️ **此步是"识别 + 设计"**: 实际改代码放 Phase 12 多 agent 执行。若走单 agent 小重构, 可在网内直接改。**拆分后调用链 > 3 层且无收益 → 不要拆 (过度设计信号)。**

---

## Phase 6: 合并共用方法

从 Phase 4 清单挑重复方法 (同逻辑多份实现)。

**识别**: `rg -n '<pattern>' src/` 多命中 + 函数体相似 → 候选。

**原则**:
- 同逻辑 → 1 份实现, caller 全迁移
- 仅在签名/边界有差异 → 抽象公共部分 + 参数化差异
- 不确定是否真重复 (相似但语义不同) → 走「不打断」决策表: 风险最小 = 不合并 (默认); 真歧义 = 兜底问

**deliverable**: 重复方法清单 + 合并方案 (进 Phase 9 计划)。

---

## Phase 7: 合并字典 + 解决冲突

从 Phase 4 清单挑字典重复/矛盾定义。完整方法见 `@references/dict-dedup.md:1`。

**4 类问题**:
| 类型 | 定义 | 处理 |
|---|---|---|
| DUPLICATE | 值/结构完全一致 | 自动合并: 留 1 处权威源, 别处 re-export |
| CONFLICT | 同名字段值不一致 | **CONFLICT 必须用户决策** (?)— 风险大 (业务数值), 兜底停下来问 |
| STALE | 无 caller 的过时副本 | 删 + git rm |
| REVERSE-MISSING | 有 a→b 缺 b→a | 补反向 dict |

**detect**:
```bash
# 候选 + fingerprint 聚类 (见 dict-dedup.md step 1-2)
grep -rnE '^\s*[A-Z][A-Z_0-9]+\s*[:=]\s*[\{\[]' src/ --include="*.py"
```

> **CONFLICT 处理** (唯一兜底停下来问的场景): 真值识别 > 自动合并。commit msg 含 `decided: A 是真值, B 是 typo`。

---

## Phase 8: improve-codebase-architecture 优化架构

从 Phase 4 清单挑架构级问题 (耦合 / 分层不清 / 依赖混乱)。

```bash
Skill: improve-codebase-architecture
```

**deliverable**: 架构优化建议清单 (解耦 / 分层 / 边界) 进 Phase 9 计划。

---

## Phase 9: writing-plans 写实施计划

把 Phase 4-8 所有发现整合成**可执行计划** — 大规模重构必须有计划再执行。

```bash
Skill: superpowers:writing-plans
```

**计划要求**:
- 每步: 改什么 (file:line) / 验证 (测试名 / lint) / 回滚点
- 顺序: 低风险 → 高风险, 每步独立可回滚
- 明确哪些步骤可并行 (多 agent 执行用)

**deliverable**: `<project>/plans/<date>-code-reorg.md`

---

## Phase 10: /ponytail-audit 计划减法

对**计划**做减法审计 — 砍掉过度设计 / 不必要的抽象 / 假需求步骤。

```bash
Skill: ponytail-audit
# 对计划每步输出: <tag> <what to cut>. <replacement>. [plan-step]
# 标签: delete / stdlib / native / yagni / shrink
```

**应用**: 审计结果直接改计划 (删步 / 简化 / 降级), 不执行原计划。

> **skill 缺失降级**: Claude 自查 — 每步问"这步是为哪个已发生问题加的?" 答不上就删。

---

## Phase 11: plan-eng-review 审计划

工程审查计划, 按建议修改调整。

```bash
Skill: plan-eng-review
```

**审查重点**: 边界条件 / 失败路径 / 性能影响 / 测试覆盖 / 回滚方案。

**冲突解决** (多 review 不一致时):
1. 性能 vs 可读性: 可读性胜 (perf 后续实测)
2. YAGNI vs 未来扩展: YAGNI 胜 (需要时再加)
3. 抽象 vs 直白: 直白胜 (1 impl = 假接缝)
4. stdlib vs 已装库: stdlib 胜 (除非已装库明显更优)

**deliverable**: 定稿计划 (Phase 12 执行依据)。

---

## Phase 12: 多 subagents 执行

**执行前**: 输出最终计划 (1 段文字, 来自 Phase 9-11 产出) — 已不再 confirm, 直接跑。

按定稿计划分发执行, 独立步骤并行。

```bash
Skill: superpowers:subagent-driven-development
```

**规则**:
- 独立步骤 → 并行 subagent (worktree 隔离避免文件冲突)
- 依赖步骤 → 顺序执行
- 每步完成后跑对应测试 (Phase 3 网 + 新增)
- 每步 1 commit, 可独立回滚
- 冲突 (同文件并发) → 串行化或合并后统一 rebase

---

## Phase 13: 清理无用代码

重构后清死代码 (拆解/合并可能产生新 dead code)。**死代码 7 步 checklist** (0 caller grep = 候选信号, 不是证明):

| # | 检查 | 命令 |
|---|---|---|
| 1 | codegraph 静态引用 | `codegraph fn-impact "<name>"` (或 rg 全仓库) |
| 2 | 文本/配置/manifest 搜索 | `rg -n "<name>" --glob '*.{toml,yaml,yml,json,ini,cfg}'` |
| 3 | 框架注册点 (CLI 入口 / decorator / router / signal) | `rg "@app.route|@pytest.fixture|@click.command"` |
| 4 | 公开 API / export 检查 | `rg "^__all__"` / `__init__.py` re-export |
| 5 | 动态调用 (getattr / importlib / eval) | `rg "getattr|importlib|eval\("` |
| 6 | 测试 + 生成代码 | 搜 `tests/` `build/` `dist/` `*_pb2.py` |
| 7 | 对外 API 公开性确认 | 列出 import/export 来源 → 是内部 = 删; 对外 = 兜底问 |

**清理**: 7 步全 0 → 跑下方横切静默吞错扫描 → 删 + commit。

---

## 横切: 静默吞错扫描 (P0, 独立于 phase 体系)

> **不属于任何 phase** — Code Subflow 全流程 (Phase 5-6 拆分 / Phase 12 执行 / Phase 13 清理 / 任何 Edit) **每次改文件后立即跑**, 即扫即改. 放 phase 尾部才扫 = 错过拆分的吞错点.
> 扫描**改动涉及的函数及其调用链**中的静默吞错隐患. 不只是被删函数, 还包括被修改函数、被拆分函数的上下游.

**扫描范围**: Phase 5-6 拆分的上帝函数及 helper / Phase 13 清理的死代码周边调用链 / 一切被 Edit 文件.

**扫描命令**: 同 `logging-observability.md` Phase 1.1 (3 条 grep, 单一源 `@references/logging-observability.md:1`), 不改写重复. 自动化: `scripts/audit/silent_swallow.py` (Phase 13.1 + 13.2 context-aware 过滤).

**判定标准**: 4 模式判定表 + 4 条 pass 条件唯一在 `@references/code-review-checklist.md:1` (no-silent-swallow), 此处不复制.

**修复模板**:

```python
# 修复前 (静默吞错)
except Exception:
    pass

# 修复后 (有观测)
except Exception as _e:
    _task_log(task_id, f'xxx 失败: {_e}', level='WARN', stage='pipeline')
```

**为什么**: 代码整理是发现隐患的最佳时机. 平时不动这些代码就没人看, 整理时顺手修 = 技术债清零.

**deliverable**: `docs/audit/<date>-code-reorg.md` 含静默吞错修复清单 (file:line + 修复前 + 修复后).

---

## Phase 14: 删无用文件

整文件 0 caller 的死文件删除 (dead files), 区别于 Phase 13 的 dead functions。

```bash
# 候选: 文件内 0 定义被引用 + 0 import
rg -l "import.*from" src/ | xargs rg -l "def |class |func " | while read f; do
  base=$(basename "$f")
  refs=$(rg -l "import.*${base%.*}|from.*${base%.*}" src/ tests/ 2>/dev/null | wc -l)
  [ "$refs" -le 1 ] && echo "CANDIDATE: $f"
done
```

**规则**:
- 跨文件引用为 0 + 非对外 API → 删 + `git rm`
- 对外 API / 被外部依赖 → 走 Phase 13 第 7 步用户确认
- 删前确认文件不在 `build/` `dist/` 引用链上

---

## Phase 15: 更新设计文档 + 代码注释

重构后的文档/注释同步 — 反映**最新代码**。

**注释** (关键方法必备):
```python
def process_payment(order_id: str, amount: Decimal) -> PaymentResult:
    """处理支付请求, 返回支付结果.

    Args:
        order_id: 订单 ID (UUID 格式字符串)
        amount: 支付金额, 两位小数精度

    Returns:
        PaymentResult: {success: bool, transaction_id: str?, error: str?}

    Side effects:
        - 写 payment_log 表
        - 调用三方支付 API (可重试 3 次)

    Caller:
        _checkout, _retry_payment
    """
```

**文档一致性核对** (env var / systemd / 端口):
```bash
# 5.1 代码 env var → env.md (按项目语言选一种)
# Python
grep -roPh 'os\.environ\.get\(["\x27]\K[A-Z_][A-Z_0-9]+' src/ | sort -u > /tmp/code_vars.txt
# Go
grep -roPh 'os\.Getenv\(["\x27]\K[A-Z_][A-Z_0-9]+' src/ | sort -u > /tmp/code_vars.txt
# TypeScript / Node
grep -roP 'process\.env\.[A-Z_][A-Z_0-9]+' src/ | grep -oP 'env\.\K[A-Z_]+' | sort -u > /tmp/code_vars.txt
# 其他 → 手动: rg -noE '[A-Z][A-Z_0-9]{2,}' src/ 人工筛选
grep -oP '\| \`[A-Z_]+\`' env.md | tr -d '|`' | sort -u > /tmp/doc_vars.txt
diff /tmp/code_vars.txt /tmp/doc_vars.txt

# 5.2 systemd unit vs env.md (Linux only)
ls ~/.config/systemd/user/*.service 2>/dev/null | awk -F/ '{print $NF}' | sort -u > /tmp/units.txt
grep -oP '[a-z]+-[a-z-]+\.service' env.md deploy.md 2>/dev/null | sort -u > /tmp/doc_units.txt
diff /tmp/units.txt /tmp/doc_units.txt

# 5.3 端口 vs 文档
grep -rnP '127\.0\.0\.1:\d+' src/ deploy/ 2>/dev/null | grep -oP ':\d+' | sort -u > /tmp/ports.txt
grep -oP '\|\s*\d+\s*\|' env.md | grep -oP '\d+' | sort -u > /tmp/doc_ports.txt
diff /tmp/ports.txt /tmp/doc_ports.txt

# 5.4 doc 引用文件存在性
grep -rn "docs/[a-zA-Z_-]*\.md" docs/ 2>/dev/null | grep -oP 'docs/[a-zA-Z_-]+\.md' | while read f; do
  [ ! -f "$f" ] && echo "BROKEN: $f"
done
```

**修复**: code 缺 env var → config.py 加 + env.md 同步; doc 缺 unit/port → env.md 补; BROKEN → 改/删。

---

## Phase 16: 成功指标评估

**做完如何判定值不值得** (结果写进 audit 报告):

| 指标 | 目标 |
|---|---|
| cyclomatic 降幅 | god-fn 拆分后核心方法 < 原 60% |
| 死代码删除 | 7 步 checklist 全 0 caller |
| 重复合并 | 同逻辑 1 份实现 |
| 测试 | 重构前后全绿, 无删除测试 |
| 注释 | 关键方法 ratio ≥ 0.3 (heuristic) |

**不值得的迹象** (停止或回滚):
- 拆分后调用链 > 3 层且无收益
- 性能回退但可读性未改善
- 删除的"死代码"实际被动态引用 (第 7 步漏了)

---

## Phase 16.5: 合入前 CR (Code Subflow 末尾自动跑, P0)

**完整规则**: `@references/code-review-checklist.md:1` (no-silent-swallow 4 pass 条件 / Edit-Read 配对 / 路由 grep / 部署验证).

**必跑项** (代码重构场景特有):
- [ ] 合入前 CR 脚本跑通 (bare except 0 命中) — 脚本模板见 `code-review-checklist.md` 验证脚本节, 需用时落盘 `scripts/`
- [ ] `scripts/audit/reorg_drift.py` (改过 import / 删过 module 必跑) — 0 残留引用
- [ ] 本次改动文件无新增 `except: pass` / `except Exception: return default`
- [ ] helper 无 duck-typing 静默兜底 (`except AttributeError` 默认 fallback 模式)

**设计**: Code Review 从独立 subflow 集成到这里 = 用户不需要主动知道跑它. Full Reorg (runbook) 也依赖本 phase (见 runbook Phase 6).
