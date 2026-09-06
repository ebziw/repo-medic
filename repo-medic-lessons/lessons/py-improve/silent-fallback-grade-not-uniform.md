# Silent fallback must be graded, not uniform — critical deps raise, expected chains debug

**Symptom**: SiliconFlow rerank fallback silently took over for 4 days; nobody noticed local llama-server died. QA rerank 500 logged only "warning" for 6 months. SQLite embed cache masked iGPU schema break (17% success).

**Cause**: `non-fatal except` + auto-fallback turns faults into silent degradation — no alert, no log line user sees, user finds it before developer does.

**Fix**:
- Critical deps (rerank / embed / DB / auth) local failure → `raise` with 5xx + trace_id, no silent fallback
- If fallback is intentional: at minimum `logger.warning` + degrade flag visible to caller
- Each fallback path must declare retirement conditions (e.g. "remove SiliconFlow fallback once local llama-server P99 < 200ms for 7d")
- "non-fatal except" linter rule: PR review must justify each one with "expected transient on path X"

## Sources

- `commit:ef9d91c4`
- `work-note:docs/work-note/2026-09-06-qa-rerank-silent-timeout.md`

## Frequency

3 (highest in this batch — combine with bare-nohup + shared-backend-change)

## Triggers

fallback, silent failure, non-fatal except, degrade flag, rerank, embed, observability

## Related hard constraints

#8 (宁缺勿伪)