# Before splitting a god-function, write characterization tests to lock undocumented behavior

**Principle**: god-functions accumulate undocumented behavior that even the test author guesses wrong. Refactoring without first locking behavior down is gambling with subtle semantics. Characterization tests are the regression net that proves behavioral equivalence after the split.

**Symptom (any of)**:
- 300+ line function, splitting risks breaking subtle invariants (sort order / backfill / cap behavior)
- Test author admits "I'm not sure exactly what this returns in case X"
- Refactor PRs that claim "no behavior change" with no proof

**Fix**:
- Before any split: write characterization tests (mock external deps) capturing current behavior → tests must go GREEN first
- After split: tests still GREEN = behavioral equivalence proven
- Where tests reveal "guessed wrong": that's undocumented behavior — add docstring AND fix tests to assert actual behavior
- One change at a time: don't refactor + add features + rename in the same PR
- Characterization tests stay as permanent regression net, not deleted after refactor

## Sources

- `commit:38777f54`
- `work-note:docs/work-note/2026-09-06-maybe-rerank-split.md`

## Frequency

Medium (whenever god-functions exist; near-universal in mature codebases)

## Triggers

god function, refactor, split, characterization, behavioral equivalence, undocumented behavior, 370 lines

## Related hard constraints

#6 (commit 前全绿 — the new tests prove equivalence)