# Safe-Apply Protocol — undo-script + drift-abort (borrowed from Reorg)

Apply any batch of file operations as a single transactional unit. If anything drifts between plan and execution, abort the whole batch — never partially apply.

## Protocol

```
1. PLAN: enumerate all operations (mv / rm / mkdir) with full source + dest paths
2. SNAPSHOT: write undo.sh that reverses every operation:
   - every `git mv A B` → `git mv B A`
   - every `rm X` → write `X` content to `X.deleted-<ts>` (NOT deleted bytes)
   - every `mkdir D` → `rmdir D`
3. PRE-CHECK: verify every source path still exists + every dest path is free
   - if ANY drift detected (file disappeared, dest occupied) → ABORT, do not apply
4. APPLY: run all operations in plan order
5. VERIFY: re-scan; assert no operation was skipped / partially applied
6. KEEP undo.sh: at `.reorg/undo-<timestamp>.sh` for 30 days
```

## Key invariant

> **Drift aborts the whole batch.** Not "nothing further" — nothing at all.

If between plan and execution, even ONE file's source disappeared or destination became occupied, the entire batch is aborted. Partial application creates zombie state (file moved but its sibling not) that's worse than not starting.

## Implementation

See `scripts/safe_apply.py` — emits `undo.sh` + `apply.sh` from a plan JSON, with pre-check + atomic apply.

## Sources

- Borrowed from `j-256/reorg` `reorg apply --yes` + `--undo` semantics
- Modified: integrates with `git mv` instead of raw `mv` (preserves history per iron law 1)

## Why include

- Reorg's drift-abort prevents the worst class of bug: partial batch state
- Undo script generation removes "remember what we did" cognitive load
- Pre-check is cheap; recovery from partial state is expensive
- Standard rsync-backup is coarser-grained (whole tree) — undo.sh per-batch is precise

## When NOT to use

- Single-file operations (use `git mv` directly)
- Operations whose undo is trivial (renames within same dir)
- Operations on paths outside git tracking (undo.sh can't `git mv` for untracked files)