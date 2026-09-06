# Third-party configs: always replicate real prod-input dimensions; sample sizes lie

**Symptom**: llama-server `--reranking` returned 500 "input (724 tokens) is too large for current batch size 512" — only triggered on long docs, short sample tests had passed.

**Cause**: llama-server startup with `n_batch=2048, n_ubatch=512` auto-clamped; single rerank request = query+doc pair can exceed 512 tokens; short-doc benchmark didn't catch it.

**Fix**:
- When configuring any batch/budget parameter: use prod-realistic input dimensions in test, not short samples
- For llama.cpp: pass explicit `-b 2048 -ub 2048` (or appropriate) to override clamps
- Restart + re-test with prod-shape input (e.g. 724-token doc) before declaring green
- Long-tail inputs (long queries, long docs, unicode) should be in baseline test fixtures

## Sources

- `work-note:docs/work-note/2026-09-06-qa-rerank-silent-timeout.md`
- `commit:a7c56fd7` (related pptx lesson — same "tool can open ≠ standard can open" root)

## Frequency

1 (silent for months until long doc arrived)

## Triggers

llama.cpp, llama-server, n_ubatch, batch size, reranking, prod-input dimension, baseline fixture

## Related hard constraints

#14 (verify actually-running product with realistic inputs)