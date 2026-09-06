# Long-lived services must be systemd unit-ized; bare nohup dies silently

**Symptom**: `llama-server` rerank process exited after 210 tasks, no systemd unit to restart, silent for 4 days; user noticed when QA rerank went 500.

**Cause**: bare processes have no restart policy, no monitoring hook, fallback layer (`SiliconFlow rerank` API) silently takes over so death isn't noticed.

**Fix**:
- Any long-running service process → `systemd --user` unit with `Restart=on-failure` + `enable --now`
- Health check must reach the actual endpoint (not "/health 200" if health doesn't exercise the real call path)
- "It ran before" ≠ "it's running now" — query `pgrep` / `systemctl is-active` periodically

## Sources

- `work-note:docs/work-note/2026-09-06-search-cold-query-iter3.md`

## Frequency

2 (this + silent-fallback-hides-outage cascade)

## Triggers

nohup, systemd unit, Restart=on-failure, long-lived service, silent death, pgrep

## Related hard constraints

#14 (verify the actually-running product)