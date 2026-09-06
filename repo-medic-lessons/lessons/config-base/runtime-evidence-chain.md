# Runtime behavior: trust `systemctl cat` + `ps aux` + `/proc/<pid>/cwd`, not unit main file

**Symptom**: kb-crawl / kb-feed unit main file ExecStart pointed at `/home/kb/prod/...`, actual process ran `/home/kb/test/...`; following main file misled debugging 20 min.

**Cause**: unit has drop-in override (`/etc/systemd/system/<unit>.d/*.conf`) that overrides ExecStart; `systemctl status` shows main, `systemctl cat` shows synthesized view. Plus secondary drift via sys.path (see L6).

**Fix**:
- Step 0 of runtime debugging: `systemctl cat <unit>` (synthesized view) + `ps aux | grep <proc>` (real binary) + `readlink /proc/<pid>/cwd` (real working dir)
- Trust process table over unit main file
- If unit main and override disagree: fix the source of truth (which file is authoritative), don't just patch the visible one

## Sources

- `work-note:fetch-unlock.md` — 附带发现

## Frequency

2 (this + sys.path drift)

## Triggers

systemctl cat, drop-in override, ExecStart drift, /proc/<pid>/cwd, unit main vs reality

## Related hard constraints

#14 (验证实际生效产物)
