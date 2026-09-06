# Stale test vs implementation drift: find evolution evidence before "fixing" either side

**Principle**: when tests fail, neither side is automatically the truth. Implementation may have evolved intentionally (with documentation); tests may have rotted. "Fixing" the wrong side reverts to known-bad state. Find evidence chain first.

**Symptom (any of)**:
- 6 tests failing with threshold / cache-key / TTL / marker drift from source
- Test "obviously wrong" but production behavior matches source (or vice versa)
- Temptation to "just update the test" or "just update the code" without checking why

**Fix**:
- Failing test + documented evolution (comments / work-note / commit message) → update test assertions, record evolution history, add regression guard
- Failing test + NO documented evolution → `git log -p` to find the change, suspect bug only if change wasn't justified
- Never assume "test is truth" or "impl is truth" without evidence chain
- Evolution history in test file (`# evolved 2026-XX-XX: rationale...`) prevents next-person's confusion

## Sources

- `commit:b219525c`

## Frequency

High (any long-lived codebase accumulates test drift)

## Triggers

stale test, threshold drift, assertion rot, test debt, evolution evidence, git history

## Related hard constraints

#8 (宁缺勿伪 — verify the claim is justified before "fixing" it)