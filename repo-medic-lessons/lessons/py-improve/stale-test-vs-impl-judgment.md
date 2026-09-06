# Stale test vs impl: find evolution evidence first; documented evolution → fix test, undocumented drift → check git history

**Symptom**: 6 tests failing (threshold 0.55 vs source 0.40, cache key missing uid, TTL 300 vs 60, old merge marker).

**Cause**: implementation evolved intentionally (comments + work-notes documented the change) but tests weren't kept in sync; "fix the implementation" would revert to a known-bad state.

**Fix**:
- Failing test + documented evolution in source/work-note/commit → update test assertions, record the evolution history, add a regression guard
- Failing test + NO documented evolution → `git log -p` to find the change, suspect bug only if change wasn't justified
- Never assume "test is the truth" or "impl is the truth" without checking evidence chain first

## Sources

- `commit:b219525c`

## Frequency

1 (but recurring in any long-lived codebase)

## Triggers

stale test, threshold drift, assertion rot, test debt, evolution evidence, git history

## Related hard constraints

#8 (宁缺勿伪 — verify the claim is justified before "fixing" it)