#!/usr/bin/env python3
"""config_drift.py — config drift detection (systemd units / crontab / .env).

Compares the live config dir against the git-tracked deploy/ source and finds
live-only config files not committed to git. These are the root cause of deploy
drift (edits made on live but never committed -> changes lost on next deploy).

Language/project agnostic: repo root is detected from cwd via `git rev-parse`
(or pass --repo); live systemd dir defaults to `~/.config/systemd/user`
(override with --systemd-dir).

Usage:
    cd /path/to/repo && python3 scripts/config_drift.py        # systemd units
    python3 scripts/config_drift.py --crontab                  # crontab
    python3 scripts/config_drift.py --env                      # repo-root .env
    python3 scripts/config_drift.py --all
    python3 scripts/config_drift.py --repo /srv/proj --systemd-dir /etc/systemd/system

Exit codes: 0=no drift, 1=drift found.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path | None:
    """Detect via `git rev-parse --show-toplevel` (the skill may live anywhere; no hardcoded candidates)."""
    cwd = start or Path.cwd()
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False, cwd=str(cwd),
    )
    if r.returncode != 0:
        return None
    return Path(r.stdout.strip())


def git_ls_files(repo_root: Path, pattern: str) -> set[str]:
    """Return files in the git index matching pattern (relative to repo root).

    pattern may hold multiple globs, space-separated
    (e.g. "deploy/systemd/*.service deploy/systemd/*.timer").
    Use shlex.split for shell-style splitting, then expand with glob against cwd
    (git ls-files pathspecs do not expand shell globs).
    """
    import shlex
    out: set[str] = set()
    for pat in shlex.split(pattern):
        # shell-expand (assumes cwd=repo_root; in practice we cd to repo_root before calling)
        import glob as _glob
        expanded = _glob.glob(pat)
        if not expanded:
            # no match, pass the original pattern straight to git ls-files (pathspec mode)
            expanded = [pat]
        r = subprocess.run(
            ["git", "ls-files", "--"] + expanded,
            capture_output=True, text=True, check=False, cwd=str(repo_root),
        )
        if r.returncode == 0:
            out |= {p.strip() for p in r.stdout.splitlines() if p.strip()}
    return out


def list_live_dir(live_dir: Path, suffix: str = "*.service") -> set[str]:
    """Return filenames under live_dir matching suffix (relative to live_dir)."""
    if not live_dir.is_dir():
        return set()
    return {p.name for p in live_dir.glob(suffix)}


def check_systemd_units(repo_root: Path, live_dir: Path) -> list[str]:
    """systemd unit: live dir vs git deploy/systemd/."""
    issues: list[str] = []
    git_pattern = "deploy/systemd/*.service deploy/systemd/*.timer"
    git_names = {Path(p).name for p in git_ls_files(repo_root, git_pattern)}
    live_names = list_live_dir(live_dir, "*.service") | list_live_dir(live_dir, "*.timer")

    for unit in sorted(live_names - git_names):
        issues.append(f"[live-only] {live_dir}/{unit} (lost on deploy)")
    for unit in sorted(git_names - live_names):
        issues.append(f"[git-only] deploy/systemd/{unit} (not installed on live)")
    return issues


def check_crontab(repo_root: Path) -> list[str]:
    """crontab: live `crontab -l` vs git tracked cron scripts."""
    issues: list[str] = []
    r = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
    if r.returncode != 0:
        return issues
    live_scripts: set[str] = set()
    for line in r.stdout.splitlines():
        m = re.search(r"(/\S+\.(?:sh|py))", line)
        if m:
            live_scripts.add(m.group(1))
    git_cron = git_ls_files(repo_root, "scripts/cron/*") | git_ls_files(repo_root, "scripts/cron.sh")
    for path_str in live_scripts:
        rel = Path(path_str).relative_to(repo_root) if path_str.startswith(str(repo_root) + "/") else path_str
        if str(rel) not in git_cron:
            issues.append(f"[live-only cron] {path_str}")
    return issues


def check_env(repo_root: Path) -> list[str]:
    """Repo-root .env: whether .gitignore excludes it (secrets out of git is fine) + whether an .env.example exists for reference."""
    issues: list[str] = []
    env_path = repo_root / ".env"
    if not env_path.exists():
        return issues
    # Is .env ignored by git — ignored = fine (secrets); not ignored = risky (secrets may land in git)
    r = subprocess.run(
        ["git", "check-ignore", "-q", ".env"],
        capture_output=True, text=True, check=False, cwd=str(repo_root),
    )
    if r.returncode != 0:  # not ignored
        issues.append(f"[danger] {env_path} is not ignored by .gitignore — secrets may land in git")
    example = repo_root / ".env.example"
    if not example.exists():
        issues.append(f"[warn] missing {repo_root / '.env.example'} — new environments cannot bootstrap from a template")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--systemd", action="store_true", help="check systemd units (default)")
    ap.add_argument("--crontab", action="store_true", help="check crontab")
    ap.add_argument("--env", action="store_true", help="check repo-root .env vs .env.example")
    ap.add_argument("--all", action="store_true", help="check everything")
    ap.add_argument("--repo", default=None, help="git repo path (default: detect from cwd)")
    ap.add_argument("--systemd-dir", default=None,
                    help="live systemd unit dir (default ~/.config/systemd/user)")
    args = ap.parse_args()

    repo_root = find_repo_root(Path(args.repo)) if args.repo else find_repo_root()
    if repo_root is None:
        print(f"✗ git repo root not found (cwd={Path.cwd()}, specify with --repo)")
        return 1
    live_dir = Path(args.systemd_dir) if args.systemd_dir else Path.home() / ".config" / "systemd" / "user"

    all_issues: list[str] = []
    if args.crontab or args.all:
        all_issues += check_crontab(repo_root)
    if args.env or args.all:
        all_issues += check_env(repo_root)
    if (not any([args.crontab, args.env])) or args.systemd or args.all:
        all_issues += check_systemd_units(repo_root, live_dir)

    if not all_issues:
        print(f"✓ no config drift ({repo_root})")
        return 0
    print(f"✗ found {len(all_issues)} config drift issue(s) ({repo_root}):")
    for i in all_issues:
        print(f"  {i}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
