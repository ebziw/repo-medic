# Shared backend change → verify every consumer's call shape, not just /health

**Symptom**: switched iGPU embed service; backend's `vectors` field vs consumer's `embeddings` key → search success rate dropped to 17%; short-prefix rerank worked, full-chunk QA went 500; cache masked fault for hours.

**Cause**: one backend, many consumer paths with different shapes (truncation / batch / timeout / field names); `/health` 200 ≠ contract is right; cache hides wrong-shape responses for hours.

**Fix**:
- After backend switch: curl schema contract first, then end-to-end business flow per call shape
- Single canonical schema per field (don't keep "ARM v1 + cloud v2" dual-schema compat — pick one)
- Cache invalidation must happen on backend switch (or you'll validate against stale shape)
- New call shape → must add to baseline suite before merge

## Sources

- `work-note:docs/work-note/2026-09-06-embed-contract-and-env-doc-sync.md`

## Frequency

2 (this + silent-fallback-hides-outage, same debug session)

## Triggers

embed, schema contract, switch backend, field rename, cache invalidation, baseline suite, health check ≠ contract

## Related hard constraints

#14 (verify actually-running product)