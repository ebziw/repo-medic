# Logging Observability Subflow (project-doctor sub-workflow)

> Trigger: user says "log observability" / "structured logging" / "swallowed errors" / "silent error" / "logging audit" / "add logs for troubleshooting"
> Scope: logging only (swallowed-error detection + structuring + critical-path state points); no business-logic changes
> **Core principle**: logs must strictly reflect whether the program runs as designed. **Never swallow errors silently**. Troubleshoot by grep, not by guessing.

## Table of Contents

1. [Core Iron Rules](#core-iron-rules)
2. [Phase 1: Swallowed-Error Detection](#phase-1-swallowed-error-detection)
3. [Phase 2: Critical-Path State Points](#phase-2-critical-path-state-points)
4. [Phase 3: Structured Logging Upgrade](#phase-3-structured-logging-upgrade)
5. [Phase 4: Log Level Conventions](#phase-4-log-level-conventions)
6. [Phase 5: Verification](#phase-5-verification)

---

## Core Iron Rules

> **Silently swallowed errors = a troubleshooting nightmare**. When a program swallows exceptions without recording them, a failure leaves zero clues and debugging degenerates into "guessing what broke".
>
> **Correct approach**: every except must be logged (with traceback + context) so the program "speaks" what it saw.

**Anti-patterns (zero tolerance)**:
- ❌ `try: ... except: pass` — swallows everything
- ❌ `try: ... except Exception: continue` — swallows without logging
- ❌ `try: ... except: return None` — swallows; the caller never knows
- ❌ `print(...)` in prod paths instead of a logger — no level / no timestamp / no location
- ❌ No logger at all on critical paths — a failure can only be reproduced

**Positive patterns**:
- ✅ `except Exception as e: logger.error("xxx failed", exc_info=True, extra={"ctx": ctx})`
- ✅ Critical decision points always carry `logger.info("processing X", extra={"id": x})`
- ✅ Boundary conditions (external IO / user input / config files) always carry `logger.warning("unexpected input: ...")`

---

## Phase 1: Swallowed-Error Detection

**Scan**: find every swallowed error / silent failure.

```bash
# 1.1 Python: bare except / except pass
grep -rnE "except\s*:\s*(pass|continue|return\s+None|return\s+\"\")" ${REPO_ROOT}/ --include="*.py"
grep -rnE "except\s+Exception\s*:\s*(pass|continue)" ${REPO_ROOT}/ --include="*.py"
grep -rnE "except\s+.*\s+as\s+\w+\s*:\s*$" ${REPO_ROOT}/ --include="*.py" -A1 | grep -B1 "pass\|continue\|return None"

# 1.2 Python: print in prod paths (exclude test / script / docs)
grep -rnE "^\s*print\(" ${REPO_ROOT}/ --include="*.py" \
  | grep -v "/tests/" | grep -v "/scripts/" | grep -v "/docs/"

# 1.3 Go: ignored errors (Go's special brand of swallowing)
grep -rnE "_\s*=\s*\w+\(" ${REPO_ROOT}/ --include="*.go" \
  | xargs -I{} echo "{} | grep -E '_\s*=\s*\w+Err\|_\s*=\s*\w+\.\w*'"

# 1.4 Go: log.Print vs log.Fatal vs slog
grep -rnE "log\.Print(ln)?\(" ${REPO_ROOT}/ --include="*.go"

# 1.5 Node/TS: console.log in prod paths
grep -rnE "console\.(log|error|warn)" ${REPO_ROOT}/ --include="*.ts" --include="*.js" \
  | grep -v "/tests/" | grep -v "/scripts/"

# 1.6 Empty catch blocks / console-only
grep -rnE "catch\s*\([^)]*\)\s*\{\s*\}" ${REPO_ROOT}/ --include="*.ts" --include="*.js"
grep -rnE "catch\s*\([^)]*\)\s*\{[^}]*console\.(log|error)" ${REPO_ROOT}/ --include="*.ts" --include="*.js"
```

**deliverable**: `docs/audit/<date>-logging-gaps.md` containing:
- Swallowed-error site list (file:line + context)
- print-in-prod-path list
- Go `_` ignored-error list
- Grading: Critical (swallowed error) / Warning (print) / Info (add logging)

---

## Phase 2: Critical-Path State Points

**Critical path definition**: the program's core business flow; on failure it must be possible to pinpoint "which step was reached".

```bash
# 2.1 Find main entry functions / key business flows
# e.g. backend: API handler / job runner / scheduler
#     frontend: route handler / state mutator / API call wrapper
grep -rnE "def\s+(process|handle|run|execute|main|start|dispatch)" ${REPO_ROOT}/ --include="*.py" | head -20

# 2.2 Do these function bodies lack logging?
# check: function entry / each branch / before external IO / before return
```

**Key state-point template** (mandatory in every main-flow function):

```python
def process_order(order_id: str, items: list[Item]) -> OrderResult:
    # entry: log parameters + counts
    logger.info("processing order", extra={
        "order_id": order_id,
        "item_count": len(items),
        "user_id": current_user.id,
    })

    try:
        # critical IO: log the start
        logger.debug("validating items")
        validated = validate_items(items)

        # critical decision: log the branch
        if validated.has_hazardous:
            logger.warning("hazardous items detected", extra={
                "order_id": order_id,
                "hazardous_types": validated.hazardous_types,
            })

        # critical IO done: log the result
        logger.debug("payment started")
        payment = charge_payment(order_id, validated.total)
        logger.info("payment succeeded", extra={
            "order_id": order_id,
            "amount": payment.amount,
            "txn_id": payment.txn_id,
        })

        return OrderResult(success=True, order_id=order_id)

    except PaymentError as e:
        # failure: log full context + traceback
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

**Minimum logging requirements**:
1. **Entry**: `logger.info` with the main parameters
2. **Every except**: `logger.error/warning` with context + `exc_info=True`
3. **Before external IO**: `logger.debug` marks the start
4. **After external IO**: `logger.info/debug` marks the result
5. **Critical decision points**: `logger.info/warning` records the branch taken
6. **Before exit**: at least 1 `logger.info` stating success/failure

---

## Phase 3: Structured Logging Upgrade

**Goal**: make logs greppable / parseable / aggregatable, not just human-readable.

### Python: structlog / loguru

```python
# recommended: loguru (zero config, auto-structured)
from loguru import logger

# recommended: stdlib logging + JSON handler (no new dependency)
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
slog.Error("payment failed", "order_id", orderID, "err", err)  // err carries the traceback automatically
```

### Node/TS: pino (fastest JSON logger)

```typescript
import pino from 'pino';
const logger = pino({ level: 'info' });

logger.info({ order_id, item_count: items.length }, 'processing order');
logger.error({ err, order_id }, 'payment failed');  // err auto-serialized
```

**Unified field conventions** (cross-language):
- `timestamp` (ISO 8601)
- `level` (debug/info/warning/error)
- `message` (short human-readable sentence)
- `module` / `logger` (source identifier)
- Business fields: `order_id` / `user_id` / `txn_id` / `request_id` (snake_case, identical across languages)
- Errors: `err` / `error` + the raw exception object (with traceback)

---

## Phase 4: Log Level Conventions

| Level | When to use | Production default |
|------|--------|----------|
| **DEBUG** | Detailed diagnostics, can be turned off after go-live | ❌ off |
| **INFO** | Critical state points / business events | ✅ on |
| **WARNING** | Abnormal but the program continues (retries, degradation, edge-case input) | ✅ on |
| **ERROR** | Current request failed, but the service survives | ✅ on |
| **CRITICAL/FATAL** | Service unavailable, alert immediately | ✅ on + alert |

**Decision criteria**:
- User-visible impact -> ERROR
- Program can recover -> WARNING
- Program cannot recover -> CRITICAL/FATAL + process exit
- State change -> INFO
- Troubleshooting -> DEBUG (on in dev, off in production)

**Anti-patterns**:
- ❌ INFO used for bug hunting (noise; belongs in DEBUG)
- ❌ WARNING used as ERROR (the user-facing operation already failed, not "might fail")
- ❌ ERROR without `exc_info` (loses the traceback)
- ❌ Everything logged as ERROR (drowns real alerts)

---

## Phase 5: Verification

```bash
# 5.1 Swallowed-error sites: 0 hits
grep -rnE "except\s*:\s*(pass|continue)" ${REPO_ROOT}/ --include="*.py" | wc -l  # should be 0

# 5.2 print in prod paths: 0 hits
grep -rnE "^\s*print\(" ${REPO_ROOT}/ --include="*.py" | grep -v test | wc -l  # should be 0

# 5.3 Every critical function has entry logging
# sample 5-10 main-flow functions; each has at least 1 logger.info/info

# 5.4 Every except has a logger
grep -rnE "except\s+\w+(\s+as\s+\w+)?\s*:" ${REPO_ROOT}/ --include="*.py" -A2 \
  | grep -B1 "logger\.(error|warning)" | wc -l
# should be ~= the total except count (a few genuinely silent cases are allowed: e.g. re-raised KeyboardInterrupt)

# 5.5 Structured field names consistent (sample 5 logger calls; inspect extra dict field naming)
# expected: order_id / user_id / txn_id / request_id in consistent snake_case

# 5.6 Run the tests, trigger some errors, inspect the log output
${TEST_RUNNER} 2>&1 | grep -E "ERROR|CRITICAL" | head -20
# expected: every ERROR has traceback + context

# 5.7 Performance: logging must not block the main flow
# run 1 hour in prod; p99 latency must not increase by more than 5%
```

**Done criteria**:
- 0 swallowed-error sites (except re-raised KeyboardInterrupt / SystemExit)
- 0 print in prod paths
- Critical functions have entry + exit + exception logs
- Log format structured (JSON / consistent fields)
- ${TEST_RUNNER} all green
- Log aggregation (Loki / ELK) can grep every ERROR

---

## YAGNI Notes (zero upfront defense)

> From generic hard constraint #1: do not design defense mechanisms for risks that have never occurred.

- ❌ Do not add a "trace log" to every function (too much useless logging)
- ❌ Do not add dynamic context injection for "possible future extension"
- ❌ Do not add a separate audit log channel for "security auditing" (unless a compliance requirement truly exists)
- ✅ **Patch only problems that have happened**: a user reports "cannot tell why it failed" -> add ERROR logging
- ✅ **Critical paths suffice**: not every function needs logs — main flows + boundaries + exceptions do

---

## Known Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Too much logging masks errors instead | ERROR drowned by INFO | Production default INFO, DEBUG off, ERROR routed to the alert channel |
| Logs contain sensitive data (password / token) | Compliance problem | No secrets in logger fields, or use a secret redaction filter |
| Async logging drops messages | Logs lost at process exit | sync mode + flush on shutdown, or accept the risk (business-recoverable) |
| Cross-process trace breaks | Microservice call chain severed | Use trace_id (OpenTelemetry / custom header propagation) |
| Log timezone wrong | Multi-timezone confusion | Store uniformly in UTC + localize display |
| `exc_info=True` omitted | ERROR without traceback | Linter rule: every except must have exc_info or logger.exception |

---

## Field Case: Crawler Job 24h=0 Bug (silent error lesson)

> **Real-case teaching**. The 24h ingest suddenly hit 0; troubleshooting burned an extra 2h to locate the root cause — nothing but silent excepts swallowing errors.
> Case source (real kb symbol names / paths): see `projects/kb.md`.

### Bug Root Cause (4 kinds of silent error)

| Location | Anti-pattern | Fix |
|------|--------|------|
| `_batch_write` (bulk DB write) | Silent `except: pass` swallows DB errors, rowcount never logged | `logger.error("batch write failed", exc_info=True, extra={"rowcount": cur.rowcount, "sql": sql[:200]})` |
| `_load_urls` (URL loading) | Silent except swallows URL load failures | `logger.error("url load failed", exc_info=True, extra={"site": site, "batch_size": n})` |
| `_cleanup_leftovers` (leftover cleanup) | Silent except swallows cleanup failures | `logger.error("cleanup failed", exc_info=True, extra={"stuck_count": n})` |
| `except: continue` (cron main loop) | The entire cron job fails silently | `logger.exception("task failed"); sys.exit(1)` |

### Troubleshooting Timeline

```
24h=0 detected → check cron log → 0 output
         → check cron stdout → 0 output
         → ssh into prod, run manually → still 0 output (silent)
         → add print debug → 2h later pinpoints _batch_write
         → switch to logger.error → DB error "connection timeout" appears immediately
```

**Root cause**: a chain of silent excepts lets the program "pretend to work" with zero output. Troubleshooting is reduced to probing function by function with print.

### Lessons

- **Every except must carry logger.error + context** (the universal fix for all 4 kinds of silent error)
- **Critical paths must have logger.info state points** (round start/stop, bulk_write rowcount, ingest up/down)
- **print that bypasses the logger must be migrated** — not a nice-to-have, but troubleshooting infrastructure

---

## Logger Configuration Guidance (stdlib + journald integration)

> **stdlib logging recommended** — zero new dependencies and integrates well with systemd journald (when the project runs on systemd). Complete kb project example (unit file / logger naming): see `projects/kb.md`.

### Module-level Logger Naming Convention

```python
# anti-pattern: use the root logger
logging.info("hello")  # pollutes every logger

# positive pattern: module-level namespace (<domain>.<module>; domain = short service prefix, 1 per project)
import logging
log = logging.getLogger("app.crawler")      # crawler module
log = logging.getLogger("app.cron")          # cron script
log = logging.getLogger("app.scheduler")     # scheduler
log = logging.getLogger(f"app.{__name__}")   # auto-named submodule
```

### systemd journald Integration Config

```python
# /etc/systemd/system/<app>-<worker>.service  (unit file template)
[Service]
ExecStart=/usr/bin/python3 <module entry inside the repo, absolute path>
StandardOutput=journal
StandardError=journal
SyslogIdentifier=<app>-<worker>

# Python side: use SysLogHandler or the stdlib journal
import logging
from logging.handlers import SysLogHandler

handler = SysLogHandler(address="/dev/log")
handler.ident = "<app>-<worker> "  # shown by journald
formatter = logging.Formatter("%(name)s: %(levelname)s %(message)s")
handler.setFormatter(formatter)

log = logging.getLogger("app.crawler")   # matches the module-level naming convention
log.addHandler(handler)
log.setLevel(logging.INFO)
```

### File + journald Dual Output

```python
import logging
from logging.handlers import SysLogHandler, RotatingFileHandler

# journald (systemd environment)
journal = SysLogHandler(address="/dev/log")
journal.ident = "<app>-<worker> "

# file (log rotation, 7-day retention)
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

### Structured Fields (tied to trace_id)

```python
# if the project already has a trace_id helper (contextvar propagation) but the logger ignores it -> integrate:
import logging

def log_with_trace(msg: str, level: int = logging.INFO, **fields):
    """Unified entry point: attaches trace_id automatically"""
    trace_id = get_current_trace_id()  # read from the contextvar
    log.log(level, msg, extra={"trace_id": trace_id, **fields})

# usage
log_with_trace("round started", round_id=rid, site_count=n)
```

### Verification

```bash
# run one round; check whether the logs contain the structured fields
journalctl -u <app>-<worker> -n 100 | grep -E "trace_id|round_id"
# expected: every log line carries trace_id + round_id

# trigger errors; check for traceback + context
journalctl -u <app>-<worker> --since "1h ago" | grep -A 20 "ERROR"
# expected: every ERROR is followed by traceback lines + context (rowcount / sql / batch_size, etc.)
```
