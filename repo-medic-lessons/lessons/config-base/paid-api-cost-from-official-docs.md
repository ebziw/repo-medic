# Paid API cost model: read official pricing directly, never trust vendor self-claims

**Symptom**: estimated "1 request = 1 credit, 5000 free" → actual config (js_render + premium_proxy) was 25 credits/req → only 200 reqs/month, 12.5× off.

**Cause**: vendor self-evaluated success rates and pricing conflict across providers (BrightData 98% vs Scrapfly 98% vs ZenRows 58% on same target); subagent research picked up vendor numbers without verification.

**Fix**:
- Before integrating paid API: read official pricing/features page and confirm 3 things:
  1. Credit multipliers (which params multiply cost)
  2. Failure billing (do failed requests count?)
  3. Config triggers that change billing rules (e.g. BrightData custom features → 100% billing including failures)
- Real success rate: own 500-URL benchmark on representative targets
- Subagent research: cross-check vendor claims with at least one independent source

## Sources

- `commit:6cc06aa` — perf(fetch): ZenRows credit downshift + BrightData custom headers removed
- `work-note:fetch-unlock.md` — naobao cost model 3 corrections

## Frequency

1 (impact: 5× free quota under-utilization)

## Triggers

credit multiplier, pricing, vendor self-claim, custom features billing, benchmark, js_render, premium_proxy

## Related hard constraints

#8 (宁缺勿伪)
