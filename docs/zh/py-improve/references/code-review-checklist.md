# Code Review Subflow (project-doctor 子工作流)

> 触发: 用户说 "code review" / "合入前检查" / "CR checklist" / "静默吞错检测"
> 范围: 合入前机械可检查的规则集, 不靠靠感觉靠 checklist
> **核心原则**: 规则必须机械可判定 (pass/fail), 不靠 "资深工程师感觉".

## 目录

1. [no-silent-swallow (P0)](#no-silent-swallow-p0)
2. [Edit-Read 配对 (P1)](#edit-read-配对-p1)
3. [路由/配置 grep (P0)](#路由配置-grep-p0)
4. [部署验证 (P1)](#部署验证-p1)
5. [LLM 铁律 (P1)](#llm-铁律-p1)
6. [引用/数据 (P2)](#引用数据-p2)
7. [验证脚本](#验证脚本)

---

## no-silent-swallow (P0)

**严重级**: error (阻塞合入)

每个 `except Exception:` / `except <具体异常>:` 块必须满足以下任一条件, 否则 FAIL:

| # | 通过条件 | 识别方式 |
|---|---|---|
| 1 | 异常体含 WARN/ERROR 日志 | `_task_log(..., level='WARN')` / `logger.error(...)` / `logger.exception(...)` |
| 2 | 显式重新抛出 | `raise` / `raise SomeException(...)` |
| 3 | 嵌套 try 内层有日志, 外层 pass 是保护内层不炸 | 外层 `except: pass` 包着内层 `try: _task_log(...) except: pass` |
| 4 | 异常体含 `_silent_fail(...)` 或 `bump_counter("fail.xxx")` | 调用即视为已观测 |

**失败模式 (满足任一即 FAIL)**:

```python
# ❌ 完全静默
except Exception:
    pass

# ❌ 静默 fallback, 无日志
except Exception as e:
    return ""

# ❌ 静默赋值, 无日志
except Exception:
    _refs_rows = []

# ❌ 注释代替观测
except Exception:
    # 失败不阻塞
    return None
```

**正例 (PASS)**:

```python
# ✅ 有日志 + fallback
except Exception as e:
    _task_log(task_id, f'refs_rows 加载失败: {e}', level='WARN', stage='pipeline')
    _refs_rows = []

# ✅ 嵌套日志 (外层 pass 保护)
except Exception:
    try:
        _task_log(...)
    except Exception:
        pass

# ✅ 显式重新抛出
except Exception:
    raise

# ✅ 已记录 (_silent_fail)
except Exception:
    try:
        _silent_fail(task_id, 'event', 'reason')
    except Exception:
        pass
```

**机械检查命令**:

```bash
# 找出所有 bare except Exception: pass (最危险的)
grep -rnE "except\s+Exception\s*:\s*$" ${REPO_ROOT}/ --include="*.py" -A1 | grep -B1 "^\s*pass\s*$"

# 找出所有 except Exception: (不管后面跟什么)
grep -rnE "except\s+Exception\s*:\s*$" ${REPO_ROOT}/ --include="*.py" -A3

# 找出所有 except: pass (更宽泛)
grep -rnE "except\s*:\s*$" ${REPO_ROOT}/ --include="*.py" -A1 | grep -B1 "^\s*pass\s*$"
```

**判定**: 命中的每一行必须人工确认是否满足通过条件 1-4. 不满足 → FAIL.

---

## Edit-Read 配对 (P1)

**规则**: Edit 工具对未 Read 文件 silent fail (返回成功但没真改).

**检查**:
- 每次 Edit 调用前, 同一文件必须已 Read (同一 session context)
- Edit 后立即 grep 验证改动真生效
- cp 同步多环境后 md5sum 验证一致

**历史事故**: `main.py` router / `_call_llm.py` / `stage_search.py` / `vite.config.js` 均因 silent fail 导致用户看不到效果.

---

## 通用模式 (任意项目适用)

**规则**: 改路由/配置前 grep 全部副本 (多实例硬编码是 CONFLICT 源); 文档与数据矛盾时信数据并当场修文档.

**部署验证 (P1)**:
- [ ] 先 commit 再 git pull (dirty tree deploy 被静默冲掉)
- [ ] 部署后验证 PID 变 + deployed_at 新 (`curl /api/build-check` 或等价)
- [ ] cp 后必须 restart user service (worker/FastAPI 常驻进程)
- [ ] `systemctl --user is-active <svc>` 确认 active

---

## 前端 (JS/TS) 机械规则 (P1)

> 触发: diff 含 `.vue/.js/.jsx/.ts/.tsx`. 前 8 条 grep 可判 (v0.7.9 扩), 后 10 条人工点检.
> 全部泛化自一次真实的 pdf.js v3 selector 作用域事故（完整案例另存）。
> 路径 `${REPO_ROOT}/frontend/src/` 按项目前端源目录替换 (无则整节跳过).

**grep 可判**:

```bash
# 1. ArrayBuffer 直接传库无副本 (postMessage / getDocument({data: x}) 会 transfer → cache 空)
grep -rnE "getDocument\(\{ ?data: [a-zA-Z_]+|postMessage\([a-zA-Z_]+\)" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# 通过条件: 传的是 .slice(0) 副本, 或原 buffer 一次性使用不再复用

# 2. watchEffect/computed 体内对自身依赖 ref 赋值 (无限循环 → UI 冻结)
#    人工确认: watchEffect 体内直接 srcDoc.value = ... (srcDoc 被 watchEffect 读)
grep -rnE "watchEffect" "${REPO_ROOT}/frontend/src/" 2>/dev/null

# 3. 立即回调 (immediate:true / computed getter) 引用的 let/const 是否先声明
grep -rnE "immediate: ?true" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# 人工确认: watch 注册行之后才声明的变量, 被回调引用 → TDZ

# 4. 一次性消费 flag 复位依赖 watch/event (泄漏 → 吞后续行为)
grep -rnE "_skip[A-Za-z]+ ?= ?true|_pending[A-Za-z]* ?= ?true" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# 人工确认: flag 是否被无条件复位, 还是等 watch fire (等 = 泄漏)
```

**v0.7.9 增补 (grep 可判)**:

```bash
# 5. 固定 setTimeout 延迟做"先 A 后 B"顺序保证 (慢网络下反序 — 用完成 promise 门替代)
grep -rnE "setTimeout\([a-zA-Z]+, *[0-9]{2,4}\)" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# 人工确认: 该延迟是否在跨异步顺序场景 (等某加载完再启动)? 是 → 换真实完成信号

# 6. await 后写共享状态 (.value = / setX) 无 seq/token 校验 → out-of-order 晚到覆盖
grep -rnE "await .*\n.*\.value = " "${REPO_ROOT}/frontend/src/" 2>/dev/null  # 多行需 -U
# 人工确认: 慢异步结果写共享引用前, 是否有"我还是最新"校验 (token/seq/旧值比对)

# 7. 全局串行锁 (promise 链) 无 watchdog → 锁内 fn 永不 settle = 永久冻结
grep -rnE "Promise\.resolve\(\)\s*$|_withRenderLock|_renderQ|_lock = Promise" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# 人工确认: 链式锁内 fn 是否可能永不 settle (依赖 worker/连接等可被杀资源)?
#   是 → destroy 前 cancel + destroyed 标 + Promise.race watchdog 三件套

# 8. 重型资源 (worker/连接) 每操作新建实例 → 每操作重复下载/握手
grep -rnE "new (PDFWorker|Worker)\(|createConnection|new Pool" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# 人工确认: 循环/每请求内 new? 可共享单实例 + 用完即毁纪律?
```

**v0.7.9 增补 (人工点检)**:

| # | 检查 | 反例 |
|---|---|---|
| 9 | 状态标志 (errorMsg/loading) 每个出口都清 | 只在失败分支清, 成功/提前返回路径残留 → v-show 永久隐藏 = 白屏 |
| 10 | 批量预热/并发请求有限并发 (3-5 路) | forEach 直接 18 路 fetch, 后端每请求有计算 → 打满拖慢全 API |

**人工点检 (每 diff 抽 5 处)**:

| # | 检查 | 反例 |
|---|---|---|
| 5 | 解构/循环变量名与外层业务变量不重复 | `const [srcDoc] = await ...` 遮蔽外层 `srcDoc` ref |
| 6 | 传给库的 buffer 有副本或一次性 | `getDocument({data: bytes})` 后 bytes 还被 cache 复用 |
| 7 | 长生命周期缓存不存库实例 (doc/连接/worker) | `Map<pageNum, PDFDocumentProxy>` 当缓存 — 应存 bytes |
| 8 | 像素验证检测逻辑先自测 | 判空 `rgb<250` 不查 alpha → opaque 白底误报空 |

**机械判定**: #1 FAIL = 非副本直接传且 buffer 复用; #2 FAIL = watchEffect 体内写被追踪 ref; #3 FAIL = 后置声明被立即回调引用; #4 FAIL = flag 无无条件复位点.

---

## 验证脚本

```bash
#!/bin/bash
# 合入前机械检查 (模板: 需用时整块落盘 scripts/, 命名按项目定)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== CR: no-silent-swallow ==="
BARE_EXCEPT=$(grep -rnE "except\s+Exception\s*:\s*$" "${REPO_ROOT}/backend/" --include="*.py" -A1 | grep -B1 "^\s*pass\s*$" | grep -c "except" || true)
if [ "$BARE_EXCEPT" -gt 0 ]; then
    echo "❌ FAIL: ${BARE_EXCEPT} 处 bare except Exception: pass"
    grep -rnE "except\s+Exception\s*:\s*$" "${REPO_ROOT}/backend/" --include="*.py" -A1 | grep -B1 "^\s*pass\s*$"
    exit 1
fi
echo "✅ PASS: 0 处 bare except Exception: pass"

echo "=== CR: print in prod ==="
PRINT_PROD=$(grep -rnE "^\s*print\(" "${REPO_ROOT}/backend/" --include="*.py" | grep -v "/tests/" | grep -v "# " | wc -l || true)
if [ "$PRINT_PROD" -gt 0 ]; then
    echo "⚠️ WARNING: ${PRINT_PROD} 处 print 在 prod 路径"
    grep -rnE "^\s*print\(" "${REPO_ROOT}/backend/" --include="*.py" | grep -v "/tests/"
fi

echo "=== CR: undefined name (pyflakes) ==="
if command -v pyflakes &>/dev/null; then
    pyflakes "${REPO_ROOT}/backend/" 2>&1 | grep -E "undefined name" | head -10 || echo "✅ PASS: pyflakes 0 undefined"
fi

echo "=== CR: 需人工判定的 except 候选 (4 pass 条件之外) ==="
# 找 3 行内的 except 块: 无 WARN/ERROR 日志 + 无 raise + 无 _silent_fail 的记录候选
grep -rnE "except\s+(Exception|[A-Za-z]+Error)\s*(as\s+\w+)?\s*:" "${REPO_ROOT}/backend/" --include="*.py" -A3 \
  | awk '/^[^:]+:[0-9]+[:-]except/{file=$0; body=""; n=0}
         /^[^:]+:[0-9]+[:-][[:space:]]*(pass|continue|return|#|\s*$)/{body=body" "$0; n++}
         n>=3 && body !~ /logger\.(error|warning|exception)|raise|_silent_fail|bump_counter/{print "🔴 CANDIDATE: " file " → 检查是否 4 条件之一 (日志/raise/_silent_fail/嵌套保护)"}' || echo "✅ 无候选"

echo "=== CR: 全部通过 ==="
```

---

## 与 logging-observability 的关系

> logging-observability 子工作流 (Phase 1-5) 是 "修" — 检测 + 修复吞错.
> code review checklist 是 "防" — 合入前拦截新吞错.
>
> 两者互补: logging-observability 修历史欠债, code review 防新债产生.

---

## 已知坑

| 坑 | 现象 | 解决 |
|---|---|---|
| 规则太宽松 | "视情况而定" 变成 "总可以通过" | 规则必须 binary pass/fail, 不留 "视情况" |
| 规则太多 | checklist 变成负担, 没人用 | 保持 ≤ 10 条 P0 规则, 其余 P1/P2 抽样 |
| 机械误报 | 嵌套 try 内层有日志但被判定 FAIL | 通过条件 3 显式覆盖嵌套模式 |
| 规则过时 | 代码演进但规则没更新 | 每次踩坑后立即更新规则 (触发更新事件) |
| 删函数没清 `__all__` | `from ._module import *` 报 AttributeError | 删函数后 grep `__all__` 同步清理引用 |
| 删函数没清 import 链 | A 删了但 B `from A import X` → ImportError | 删前 grep 全仓库确认 0 caller |
| **变量/方法名遮蔽** | 同名家族 BUG: 同一变量名被两次不同来源 API 赋值, 第 2 次静默覆盖第 1 次结果 → 基于旧值的业务判断静默失效 (e.g. 账户冻结判断 3h; `import datetime` 被 `from datetime import datetime` 覆盖同族; 案例原文: arbit, projects/arbit.md) | 同一函数内**禁止同名变量被不同来源 API 二次赋值**; 第二次调用结果必须存新变量 (`balance_kc = ...`); 类型注解也救不了 (类型太宽) |
| **shell=True 命令行拼接** | 外部数据 (用户输入/URL/标题) 拼进 `subprocess.run(f"...{data}...")` 触发 bandit B602, 等价远程代码执行 | 一律 `shell=False` + 数组传参; 真要走 shell 必走 stdin 管道 (`subprocess.run(cmd, shell=True, input="...sql...\n")`), SQL/数据走 stdin 不进命令行 |
| **stdin 管道 + 嵌套 quote 转义** | `ssh "... mysql ... '{sql}'"` 多层引号; `-e "...{sql}..."` 中 ssh + mysql 双重吃引号; git-bash 还会再吃一层 | 三种稳定模式: ① scp SQL 文件 → remote 读 `<` 喂 mysql ② `printf sql | ssh ... mysql` (验证 ssh stdin pipe 工作) ③ heredoc 进 ssh 内 (`cat <<SQL \| mysql`); **不要在 windows 端 `-e` 拼内层双引号** |
| **MCP 工具输出超 token 限制** | ruff_check 588KB 文本 + 1.2K 行 JSON/MD 报头直接 200K 上限炸; 报告"result exceeds maximum allowed tokens", 输出落盘 tool-results | MCP server 设计必须分流: 短结果直返, 长结果 (≥10K 行/200K 字符) 必落盘; 主 agent 不读全文, **用 python 统计规则分布 + 路径频次** 决策再定点读 |
| **MCP server 自身接口漂移** | `mcp__python-refactor-local__bandit_scan` 走 `-f text` 失败 (bandit 1.9 已收 `-f txt`); 别的 MCP server 工具名/参数会变 | 每次 sweep 前**用 help/text 试 1 条最简调用**确认接口; 失败立即切本地 CLI (`python -m bandit -r ...`) 兜底, 别反复调 MCP 浪费时间 |
| **进程内缓存 + 改配置不重启** | 三个 yaml loader 都 `invalidate_cache()` 但 0 处调用, 加新成员/改映射后老值在用 | (沿用"config drift"规则) 进程内 module-level dict cache 也算 config: 改完必 deploy.sh 重启; 或监听 mtime 自动 cache miss; 加 CR checklist 必查 cache 文件是否有 invalidator |
| **Pyright pre-existing 错 vs 本次引入** | 存量项目常有大量 pre-existing Pyright 错 (副作用 import 不可解 / 未装包类型), 静默混在新错里, 难分"我引入的" (arbit 实测 39 条 pre-existing, 案例: projects/arbit.md) | 改文件前后各跑一次 `pyright_check <file>`; 改前 N 条 vs 改后 N 条, diff = 本次引入; 增量为 0 才算"零影响", 增量 > 0 必须逐条 review |
| **Helper 类型契约 + 静默兜底** | helper 返回类型与 docstring/caller 假设不符 (返回字符串, caller 当 dict 取 key) → 静默业务错或强转崩 | helper 禁 duck-type + 静默兜底: 强制 `isinstance` + `raise TypeError` 失败路径; 或 caller 端 `isinstance(x, dict)` 防御退化; CR checklist 加 "helper 返回值类型是否在 docstring 标注" |
| **README/docstring 写反事实** | 注释写"0=外界"实际"0=对方账号" (账号语义写反), 后续 3h 排查被误导 | 任何写"语义/枚举/常量解释"型注释前, **必 grep 真源配置文件** 一次 (`*.yaml` / DB schema / 官方 doc); CR checklist 加 "代码语义注释 vs 配置文件 抽 3 条抽校对" |
| **`.get(k, default)` 静默兜底** | 取数源错时 `.get` 返默认值调用方不报错但行为错 (e.g. 净值取数源错返 0 → 页面显示 0 净值) | `.get(k, default)` 仅在"键确实可选"用; **必传键**应 `result[k]` 显式 KeyError 让上游立刻知道; CR 看 dict 访问区分这两类 |

> systemd restart PID 不变等全局部署坑 → 单一源 SKILL.md 已知坑表, 此处不复制.
