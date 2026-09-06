# AI-authored Cruft Detector (borrowed from `alint` agent-hygiene ruleset)

AI-coding-era residue that shows up disproportionately in agent-authored commits. Catch these before commit; flag for human review.

## Detected patterns

| Pattern | Why | Severity |
|---|---|---|
| Versioned-duplicate filenames (`foo (1).md`, `foo_v2.md`, `foo_final.md`, `foo_final_FINAL.md`) | Iteration inertia — agent keeps renaming instead of consolidating | warn |
| Scratch / planning docs at repo root (`PLAN.md`, `scratch.md`, `notes.md`, `tmp.md`) | Belongs in `docs/work-note/` or `scratch/` | warn |
| AI-affirmation prose ("Certainly!", "Of course!", "Happy to help!") | Doesn't belong in commits / docs / code comments | warn |
| Debug residue (`debugger;`, `console.log(...)`, `pdb.set_trace()`, `print(...)` outside tests) | Forgotten debug instrumentation | error |
| Model-attributed TODO markers (`# TODO: claude`, `// FIXME: gpt`) | AI left a TODO without human review | info |
| Empty directories (gitignored but tracked?) | Often accidental after git mv | info |

## Implementation

```bash
# Add as pre-commit hook or CI step:
python doc-reorg/scripts/ai_cruft_detector.py --root . --report
```

Emits a report table; non-zero exit if any `error` severity hit (block commit), warns otherwise.

## Sources

- Borrowed from `alint` `agent-hygiene@v1` ruleset (https://github.com/asamarts/alint)
- Modified: tuned for `repo-medic` repo-medic target projects (small-to-medium)

## Why include

- Agent-authored commits accumulate cruft at higher rate than human commits
- Catching it before commit prevents "this is fine" months later when no one knows what `PLAN_v2_FINAL.md` is
- Each detected pattern has an actionable fix (move / consolidate / delete), not just "be careful"

## Related

- Iron Law 8: dead-code proof before delete (grep references before removing files)
- Iron Law 9: prefer absence over fabrication (better to delete cruft than to leave it)