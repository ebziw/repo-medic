# Before splitting a god-fn, write characterization tests to lock undocumented behavior

**Symptom**: `_maybe_rerank` F(45) 370 lines, splitting risked changing sort / backfill semantics that even the test author had to guess.

**Cause**: undocumented god-fn behavior — e.g. "candidates go to rerank ordered by hybrid desc, scores aligned by position"; "docs dropped by rerank's internal top_k return with their hybrid original score for backfill"; "docs outside cap don't participate in backfill". Each assumption was wrong somewhere.

**Fix**:
- Before any split: write characterization tests (mock external deps) capturing current behavior → tests must go GREEN first
- After split: tests still GREEN = behavioral equivalence proven
- Where tests reveal "guessed wrong": that's undocumented behavior — add docstring AND fix tests to assert the actual behavior
- Don't refactor + add features simultaneously; one change at a time

## Sources

- `commit:38777f54`
- `work-note:docs/work-note/2026-09-06-maybe-rerank-split.md`

## Frequency

1 (high-impact when missed)

## Triggers

god function, refactor, split, characterization, behavioral equivalence, undocumented behavior

## Related hard constraints

#6 (commit 前全绿)