# Logging Observability Subflow (project-doctor 子工作流)

> 触发: 用户说 "日志可观测性" / "结构化日志" / "日志吞错" / "silent error" / "logging audit" / "排查加日志"
> 范围: 仅日志相关 (吞错检测 + 结构化 + 关键路径状态点), 不改业务逻辑
> **核心原则**: 日志必须能严格反映程序是否按设计运行. **决不静默吞错**. 排查时不靠猜, 靠 grep.

## 目录

1. [核心铁律](#核心铁律)
2. [Phase 1: 吞错检测](#phase-1-吞错检测)
3. [Phase 2: 关键路径状态点](#phase-2-关键路径状态点)
4. [Phase 3: 结构化日志升级](#phase-3-结构化日志升级)
5. [Phase 4: 日志级别规范](#phase-4-日志级别规范)
6. [Phase 5: 验证](#phase-5-验证)

---

## 核心铁律

> **静默吞错 = 排查噩梦**. 当程序吞掉异常不记录, 出问题时无任何线索, debug 时只能 "猜哪里坏了".
>
> **正确做法**: 每个 except 必须记录 (含 traceback + 上下文), 让程序"说出"它看到了什么.

**反模式 (0容忍)**:
- ❌ `try: ... except: pass` — 完全吞掉
- ❌ `try: ... except Exception: continue` — 吞掉不记
- ❌ `try: ... except: return None` — 吞掉, 调用方不知
- ❌ `print(...)` 在 prod 路径代替 logger — 无 level / 无时间 / 无 location
- ❌ 关键路径无任何 logger — 出事只能复现

**正模式**:
- ✅ `except Exception as e: logger.error("xxx failed", exc_info=True, extra={"ctx": ctx})`
- ✅ 关键决策点必有 `logger.info("processing X", extra={"id": x})`
- ✅ 边界条件 (外部 IO / 用户输入 / 配置文件) 必有 `logger.warning("unexpected input: ...")`

---

## Phase 1: 吞错检测

**扫描**: 找出所有吞错 / 静默失败.

```bash
# 1.1 Python: bare except / except pass
grep -rnE "except\s*:\s*(pass|continue|return\s+None|return\s+\"\")" ${REPO_ROOT}/ --include="*.py"
grep -rnE "except\s+Exception\s*:\s*(pass|continue)" ${REPO_ROOT}/ --include="*.py"
grep -rnE "except\s+.*\s+as\s+\w+\s*:\s*$" ${REPO_ROOT}/ --include="*.py" -A1 | grep -B1 "pass\|continue\|return None"

# 1.2 Python: print 在 prod 路径 (排除 test / script / docs)
grep -rnE "^\s*print\(" ${REPO_ROOT}/ --include="*.py" \
  | grep -v "/tests/" | grep -v "/scripts/" | grep -v "/docs/"

# 1.3 Go: 忽略 error (Go 的特殊吞错)
grep -rnE "_\s*=\s*\w+\(" ${REPO_ROOT}/ --include="*.go" \
  | xargs -I{} echo "{} | grep -E '_\s*=\s*\w+Err\|_\s*=\s*\w+\.\w*'"

# 1.4 Go: log.Print vs log.Fatal vs slog
grep -rnE "log\.Print(ln)?\(" ${REPO_ROOT}/ --include="*.go"

# 1.5 Node/TS: console.log 在 prod 路径
grep -rnE "console\.(log|error|warn)" ${REPO_ROOT}/ --include="*.ts" --include="*.js" \
  | grep -v "/tests/" | grep -v "/scripts/"

# 1.6 catch 块空 / 仅 console
grep -rnE "catch\s*\([^)]*\)\s*\{\s*\}" ${REPO_ROOT}/ --include="*.ts" --include="*.js"
grep -rnE "catch\s*\([^)]*\)\s*\{[^}]*console\.(log|error)" ${REPO_ROOT}/ --include="*.ts" --include="*.js"
```

**deliverable**: `docs/audit/<date>-logging-gaps.md` 含:
- 吞错点列表 (file:line + 上下文)
- print 在 prod 路径列表
- Go `_` 忽略 error 列表
- 评级: Critical (吞错) / Warning (print) / Info (建议加日志)

---

## Phase 2: 关键路径状态点

**关键路径定义**: 程序的核心业务流, 出错时必须能定位到"走到了哪一步".

```bash
# 2.1 找主入口函数 / 关键业务流程
# 例: 后端: API handler / job runner / scheduler
#     前端: route handler / state mutator / API call wrapper
grep -rnE "def\s+(process|handle|run|execute|main|start|dispatch)" ${REPO_ROOT}/ --include="*.py" | head -20

# 2.2 这些函数体内缺日志吗?
# 检查: 函数入口 / 每个分支 / 外部 IO 前 / return 前
```

**关键状态点模板** (每个主流程函数必加):

```python
def process_order(order_id: str, items: list[Item]) -> OrderResult:
    # 入口: 记录参数 + 数量
    logger.info("processing order", extra={
        "order_id": order_id,
        "item_count": len(items),
        "user_id": current_user.id,
    })

    try:
        # 关键 IO: 记录开始
        logger.debug("validating items")
        validated = validate_items(items)

        # 关键决策: 记录分支
        if validated.has_hazardous:
            logger.warning("hazardous items detected", extra={
                "order_id": order_id,
                "hazardous_types": validated.hazardous_types,
            })

        # 关键 IO 完成: 记录结果
        logger.debug("payment started")
        payment = charge_payment(order_id, validated.total)
        logger.info("payment succeeded", extra={
            "order_id": order_id,
            "amount": payment.amount,
            "txn_id": payment.txn_id,
        })

        return OrderResult(success=True, order_id=order_id)

    except PaymentError as e:
        # 失败: 记录完整上下文 + traceback
        logger.error("payment failed", extra={
            "order_id": order_id,
            "amount": validated.total,
            "user_id": current_user.id,
        }, exc_info=True)
        return OrderResult(success=False, error="payment")

    except ValidationError as e:
        logger.warning("validation failed", extra={
            "order_id": order_id,
            "errors": e.errors,
        })
        return OrderResult(success=False, error="validation")
```

**最少日志要求**:
1. **入口**: `logger.info` with 主要参数
2. **每个 except**: `logger.error/warning` with 上下文 + `exc_info=True`
3. **外部 IO 前**: `logger.debug` 标记开始
4. **外部 IO 后**: `logger.info/debug` 标记结果
5. **关键决策点**: `logger.info/warning` 记录走的分支
6. **退出前**: 至少 1 条 `logger.info` 说明成功/失败

---

## Phase 3: 结构化日志升级

**目标**: 让日志可被 grep / 解析 / 聚合, 而不只是给人看.

### Python: structlog / loguru

```python
# 推荐: loguru (零配置, 自动结构化)
from loguru import logger

# 推荐: stdlib logging + JSON handler (无新依赖)
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": record.created,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            **getattr(record, "__dict__", {}).get("extra", {}),
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(handlers=[handler], level=logging.INFO)
```

### Go: slog (stdlib, Go 1.21+)

```go
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
slog.SetDefault(logger)

slog.Info("processing order", "order_id", orderID, "item_count", len(items))
slog.Error("payment failed", "order_id", orderID, "err", err)  // err 自动带 traceback
```

### Node/TS: pino (fastest JSON logger)

```typescript
import pino from 'pino';
const logger = pino({ level: 'info' });

logger.info({ order_id, item_count: items.length }, 'processing order');
logger.error({ err, order_id }, 'payment failed');  // err 自动序列化
```

**统一字段约定** (跨语言):
- `timestamp` (ISO 8601)
- `level` (debug/info/warning/error)
- `message` (人类可读短句)
- `module` / `logger` (来源标识)
- 业务字段: `order_id` / `user_id` / `txn_id` / `request_id` (snake_case, 跨语言一致)
- 错误: `err` / `error` + 原始异常对象 (含 traceback)

---

## Phase 4: 日志级别规范

| 级别 | 何时用 | 生产默认 |
|------|--------|----------|
| **DEBUG** | 详细诊断, 上线后可关闭 | ❌ off |
| **INFO** | 关键状态点 / 业务事件 | ✅ on |
| **WARNING** | 异常但程序继续 (重试, 降级, 边界输入) | ✅ on |
| **ERROR** | 当前请求失败, 但服务不死 | ✅ on |
| **CRITICAL/FATAL** | 服务不可用, 立即告警 | ✅ on + 告警 |

**判定标准**:
- 用户能看到影响 → ERROR
- 程序能恢复 → WARNING
- 程序不能恢复 → CRITICAL/FATAL + 进程退出
- 状态变更 → INFO
- 排查用 → DEBUG (开发开, 生产关)

**反模式**:
- ❌ INFO 用来排查 bug (噪声, 应该 DEBUG)
- ❌ WARNING 当 ERROR 用 (用户已经失败, 不是"可能")
- ❌ ERROR 不带 `exc_info` (丢 traceback)
- ❌ 所有日志都 ERROR (淹没真实告警)

---

## Phase 5: 验证

```bash
# 5.1 吞错点 0 命中
grep -rnE "except\s*:\s*(pass|continue)" ${REPO_ROOT}/ --include="*.py" | wc -l  # 应为 0

# 5.2 print 在 prod 路径 0 命中
grep -rnE "^\s*print\(" ${REPO_ROOT}/ --include="*.py" | grep -v test | wc -l  # 应为 0

# 5.3 关键函数都有入口日志
# 抽样检查 5-10 个主流程函数, 每个至少有 1 条 logger.info/info

# 5.4 except 都有 logger
grep -rnE "except\s+\w+(\s+as\s+\w+)?\s*:" ${REPO_ROOT}/ --include="*.py" -A2 \
  | grep -B1 "logger\.(error|warning)" | wc -l
# 应该 ≈ except 总数 (允许少数真的可以静默的: 如 KeyboardInterrupt 重抛)

# 5.5 结构化字段一致 (抽样 5 个 logger 调用, 看 extra dict 字段命名)
# 期望: order_id / user_id / txn_id / request_id snake_case 一致

# 5.6 跑测试, 触发一些错误, 看日志输出
${TEST_RUNNER} 2>&1 | grep -E "ERROR|CRITICAL" | head -20
# 期望: 每个 ERROR 都有 traceback + 上下文

# 5.7 性能: 日志不能阻塞主流程
# 在 prod 跑 1 小时, p99 延迟没增加 > 5%
```

**结束标准**:
- 吞错点 0 (除 KeyboardInterrupt / SystemExit 重抛)
- print 在 prod 路径 0
- 关键函数有入口 + 退出 + 异常日志
- 日志格式结构化 (JSON / 一致字段)
- ${TEST_RUNNER} 全绿
- 日志聚合 (Loki / ELK) 能 grep 到所有 ERROR

---

## YAGNI 注意 (零提前防御)

> 来自通用硬约束 #1: 不为没发生过的风险提前设计防御机制.

- ❌ 不要为每个函数加 "trace log" (太多没用的日志)
- ❌ 不要为"将来可能扩展"加 dynamic context injection
- ❌ 不要为"安全审计"加单独的 audit log channel (除非真有合规要求)
- ✅ **已发生的问题才补**: 用户报告 "我看不出为什么失败" → 加 ERROR 日志
- ✅ **关键路径就够**: 不是每个函数都要日志, 主流程 + 边界 + 异常才要

---

## 已知坑

| 坑 | 现象 | 解决 |
|---|---|---|
| 日志太多反而掩盖错误 | ERROR 被 INFO 淹没 | 生产默认 INFO, DEBUG 关, ERROR 用告警通道 |
| 日志含敏感信息 (password / token) | 合规问题 | logger 字段禁敏感, 或用 secret redaction filter |
| 异步日志丢消息 | 进程退出时丢日志 | sync 模式 + flush on shutdown, 或 accept 风险 (业务可恢复) |
| 跨进程 trace 断裂 | 微服务调用链断 | 用 trace_id (OpenTelemetry / 自定义 header 透传) |
| 日志时区错 | 多时区混淆 | 统一 UTC 存储 + 本地化展示 |
| `exc_info=True` 漏掉 | ERROR 没 traceback | linter 规则: 每个 except 必须有 exc_info 或 logger.exception |

---

## 实战案例: 抓取任务 24h=0 bug (silent error 教训)

> **真实案例教学**. 24h ingest 突然为 0, 排查多花 2h 才定位根因 — 全是静默 except 吞错.
> 案例原文 (kb 真实符号名 / 路径): 见 `projects/kb.md`.

### Bug 根因 (4 类 silent error)

| 位置 | 反模式 | 修复 |
|------|--------|------|
| `_batch_write` (批量写库) | 静默 `except: pass` 吞 DB 错误, rowcount 没记录 | `logger.error("batch write failed", exc_info=True, extra={"rowcount": cur.rowcount, "sql": sql[:200]})` |
| `_load_urls` (URL 加载) | 静默 except 吞掉 URL 加载失败 | `logger.error("url load failed", exc_info=True, extra={"site": site, "batch_size": n})` |
| `_cleanup_leftovers` (遗留清理) | 静默 except 吞掉清理失败 | `logger.error("cleanup failed", exc_info=True, extra={"stuck_count": n})` |
| `except: continue` (cron 主循环) | 整个 cron 任务静默失败 | `logger.exception("task failed"); sys.exit(1)` |

### 排查时间线

```
24h=0 检测 → 查 cron log → 0 输出
         → 查 cron stdout → 0 输出
         → ssh 进 prod 手动跑 → 仍 0 输出 (静默)
         → 加 print debug → 2h 后定位到 _batch_write
         → 改 logger.error → 立即看到 DB 报错 "connection timeout"
```

**根因**: 一连串静默 except 让程序"假装在工作", 输出全无. 排查时只能逐函数 print 试探.

### 教训

- **每个 except 必须有 logger.error + 上下文** (这是 4 类 silent error 的通用修复)
- **关键路径必须有 logger.info 状态点** (round 启动/关闭, bulk_write rowcount, ingest 涨/跌)
- **没用 logger 的 print 必须迁移** — 不是 nice-to-have, 是排查基础设施

---

## Logger 配置建议 (stdlib + journald 集成)

> **推荐 stdlib logging** — 零新增依赖, 与 systemd journald 集成好 (项目用 systemd 时). kb 项目完整实例 (unit 文件 / logger 命名): 见 `projects/kb.md`.

### 模块级 logger 命名约定

```python
# 反模式: 用 root logger
logging.info("hello")  # 污染所有 logger

# 正模式: 模块级命名空间 (<域>.<模块>; 域 = 短服务前缀, 每项目定 1 个)
import logging
log = logging.getLogger("app.crawler")      # crawler 模块
log = logging.getLogger("app.cron")          # cron 脚本
log = logging.getLogger("app.scheduler")     # 调度器
log = logging.getLogger(f"app.{__name__}")   # 子模块自动命名
```

### systemd journald 集成配置

```python
# /etc/systemd/system/<app>-<worker>.service  (unit 文件模板)
[Service]
ExecStart=/usr/bin/python3 <repo 内模块入口, 绝对路径>
StandardOutput=journal
StandardError=journal
SyslogIdentifier=<app>-<worker>

# Python 端: 用 SysLogHandler 或 stdlib journal
import logging
from logging.handlers import SysLogHandler

handler = SysLogHandler(address="/dev/log")
handler.ident = "<app>-<worker> "  # journald 显示
formatter = logging.Formatter("%(name)s: %(levelname)s %(message)s")
handler.setFormatter(formatter)

log = logging.getLogger("app.crawler")   # 与模块级命名约定一致
log.addHandler(handler)
log.setLevel(logging.INFO)
```

### 文件 + journald 双输出

```python
import logging
from logging.handlers import SysLogHandler, RotatingFileHandler

# journald (systemd 环境)
journal = SysLogHandler(address="/dev/log")
journal.ident = "<app>-<worker> "

# 文件 (log rotation, 保留 7 天)
file_h = RotatingFileHandler(
    "/var/log/<app>/<worker>.log",
    maxBytes=100 * 1024 * 1024,  # 100MB
    backupCount=7,
)
file_h.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
))

log = logging.getLogger("app.crawler")
log.addHandler(journal)
log.addHandler(file_h)
log.setLevel(logging.INFO)
```

### 结构化字段 (与 trace_id 联动)

```python
# 项目若已有 trace_id helper (contextvar 透传), 但 logger 没用到 → 整合:
import logging

def log_with_trace(msg: str, level: int = logging.INFO, **fields):
    """统一入口: 自动带 trace_id"""
    trace_id = get_current_trace_id()  # 从 contextvar 取
    log.log(level, msg, extra={"trace_id": trace_id, **fields})

# 用法
log_with_trace("round started", round_id=rid, site_count=n)
```

### 验证

```bash
# 跑一个 round, 看 log 是否含结构化字段
journalctl -u <app>-<worker> -n 100 | grep -E "trace_id|round_id"
# 期望: 每个 log 行都有 trace_id + round_id

# 触发错误, 看是否含 traceback + 上下文
journalctl -u <app>-<worker> --since "1h ago" | grep -A 20 "ERROR"
# 期望: 每个 ERROR 都跟 traceback 行 + 上下文 (rowcount / sql / batch_size 等)
```