# Critical dependencies must raise, not silently fall back — grade failures by blast radius

**Principle**: a `non-fatal except` + auto-fallback turns faults into silent degradation. Users find it before developers do. Fallbacks must be graded by blast radius — critical deps raise; expected transient chains use debug logging + degrade flag.

**Symptom (any of)**:
- Local service died 4 days ago, fallback silently took over, no alert
- Rerank/embed auth failure logs only "warning" for 6 months
- Cache hid wrong-shape responses for hours

**Fix**:
- Critical deps (auth / rerank / embed / DB / persistence / heartbeat) local failure → `raise` with 5xx + trace_id
- If fallback is intentional: `logger.warning` + caller-visible degrade flag (response header / status field)
- Each fallback path must declare retirement conditions ("remove SiliconFlow fallback once local llama-server P99 < 200ms for 7d")
- PR review rule: each `except: pass` / `non-fatal except` must justify "expected transient on path X"

## Sources

- `commit:ef9d91c4`
- `work-note:docs/work-note/2026-09-06-qa-rerank-silent-timeout.md`

## Frequency

Very high (nearly every codebase has at least one silent fallback path)

## Triggers

fallback, silent failure, non-fatal except, degrade flag, rerank, embed, observability, health check 200 ≠ working

## Related hard constraints

#8 (宁缺勿伪 — observable truth, not comfortable degradation)