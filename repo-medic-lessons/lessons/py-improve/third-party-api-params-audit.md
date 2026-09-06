# Third-party API params need per-param official-doc audit + A/B test

**Symptom**: ZenRows calls sent `wait_for=cf_turnstile` unconditionally → sites without Turnstile element timed out; example.com unreachable; 2h debugging (proxy → target-hardness → A/B test pinpointed).

**Cause**: `wait_for` semantics = wait for CSS selector to appear; when target lacks that element, API waits full timeout. Selector-class params are per-target, not global.

**Fix**:
- For each new third-party API: read official docs for EACH param (semantic: conditional / global / side-effect), only pass with clear justification
- A/B test (same URL ± one param) to isolate param-level effects
- Default to MINIMAL param set; add params per target as needed
- Vendor's own claims of success rates / pricing are self-evaluated and conflicting — always verify with own benchmark

## Sources

- `commit:1c5c116` — fix(fetch): remove ZenRows unconditional wait_for=cf_turnstile

## Frequency

1 (debug cost 2h)

## Triggers

wait_for, selector timeout, API param semantics, vendor self-claim, A/B test, conditional param

## Related hard constraints

#1 (YAGNI — don't add params for assumed risks)
