#!/usr/bin/env python3
"""reorg_drift.py — reorg drift detection (Phase 13.2).

Origin 2026-09-03: kb@245 watchlist session fixed 2 broken imports (reorg
deleted a module but callers still referenced it):
- commit 4646799cf deleted backend/domains/qa/quality.py (508 lines), but
  backend/core/direct_upload.py:506 still had `from backend.core.quality import
  (QUALITY_THRESHOLD_LOW, ...)` → ImportError, _process_one_doc_direct broken.
- commit 471ea8d24 deleted summarize_with_title_zh, but
  crawler/feed_to_kb.py:1895 still imported it → same ImportError.

Detection method: `git log --diff-filter=D` finds files deleted by the reorg →
scan surviving `from X import | import X` → find stale references → list
file:line.

Limitations: only checks Python source in this repo (top-level source dirs are
probed via git ls-files by default, Python-only). Cross-repo references
(e.g. another project installed via pip) cannot be detected, but that is good
enough for this machine.

Usage:
    python3 scripts/reorg_drift.py                        # check whole repo (auto-probe)
    python3 scripts/reorg_drift.py --dirs backend crawler # explicit source dirs
    python3 scripts/reorg_drift.py --since 30             # check deletions in last 30 days
    python3 scripts/reorg_drift.py --no-color             # CI mode

Exit codes: 0=no drift, 1=stale references found (a caller references a
non-existent module/symbol).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Repo root: found via git rev-parse (the skill may live anywhere, parents[N] is unreliable)
def _find_repo_root() -> Path:
    """Walk up from this script's location to the nearest ancestor containing a .git directory."""
    p = Path(__file__).resolve().parent
    for cand in [p, *p.parents]:
        if (cand / ".git").exists():
            return cand
    # Fallback: use git rev-parse (cwd is inside the repo)
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, check=False)
    if r.returncode == 0:
        return Path(r.stdout.strip())
    return p  # Fallback: the directory containing this script


REPO_ROOT = _find_repo_root()

# Exclusions
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv",
                "build", "dist", ".codegraph"}


def _detect_source_dirs() -> list[str] | None:
    """Default directory probing: `git ls-files "*.py"` (cwd=REPO_ROOT) → first
    path segment of each → drop EXCLUDE_DIRS → drop non-directory segments → sort.

    No tracked .py files or no valid top-level dirs → print WARNING + return None
    (caller returns 1, never silently passes).
    """
    r = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO_ROOT,
                       capture_output=True, text=True, check=False)
    lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    segs = sorted({ln.split("/")[0] for ln in lines} - EXCLUDE_DIRS)
    dirs = [s for s in segs if (REPO_ROOT / s).is_dir()]
    if not lines or not dirs:
        print("WARNING: no source dirs probed from git ls-files, specify them with --dirs")
        return None
    return dirs


def _run_git_log_deleted(since_days: int | None) -> list[str]:
    """Return *.py paths deleted by the reorg in the last N days (relative to REPO_ROOT)."""
    cmd = ["git", "log", "--diff-filter=D", "--name-only", "--pretty=format:"]
    if since_days is not None:
        cmd.extend([f"--since={since_days} days ago"])
    cmd.append("--")  # .py files only
    cmd.append("*.py")
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                       check=False)
    return [p.strip() for p in r.stdout.splitlines() if p.strip()]


def _imports_in_repo(dirs: list[str]) -> list[tuple[Path, int, str]]:
    """Scan the given top-level dirs, return a list of (file, line, import_str)
    tuples.

    Only scans dirs, excluding EXCLUDE_DIRS.
    """
    pattern = re.compile(r"^\s*(?:from\s+([\w.]+)|import\s+([\w.]+))(?:\s+import\s+)?", re.M)
    out: list[tuple[Path, int, str]] = []
    for src in dirs:
        for py in (REPO_ROOT / src).rglob("*.py"):
            if any(part in EXCLUDE_DIRS for part in py.parts):
                continue
            try:
                text = py.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                m = pattern.match(line)
                if m:
                    target = (m.group(1) or m.group(2) or "").strip()
                    if target:
                        out.append((py.relative_to(REPO_ROOT), i, target))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--since", type=int, default=None,
                    help="only check files deleted in last N days (default: all)")
    ap.add_argument("--dirs", nargs="*", default=None,
                    help="top-level source dirs (default: probed via git ls-files)")
    ap.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    args = ap.parse_args()

    dirs = args.dirs
    if not dirs:
        dirs = _detect_source_dirs()
        if dirs is None:
            return 1

    deleted = _run_git_log_deleted(args.since)
    if not deleted:
        print(f"no .py files deleted by the reorg" + (f" (--since={args.since}d)" if args.since else ""))
        return 0

    print(f".py files deleted by the reorg: {len(deleted)}")
    for d in deleted:
        print(f"  - {d}")
    print()

    # Convert deleted file paths to module names (e.g. backend/core/quality.py → backend.core.quality)
    raw_deleted_mods = {d[:-3].replace("/", ".") for d in deleted if d.endswith(".py")}

    # Filter: if git still tracks a .py with the same name (NoOp compat wrapper or
    # re-introduced file), skip it. These do not count as "caller references a
    # non-existent module"; truly deleted = not in ls-files
    current_py = subprocess.run(
        ["git", "ls-files", "*.py"],
        capture_output=True, text=True, check=False, cwd=str(REPO_ROOT),
    ).stdout.splitlines()
    current_mods = {p[:-3].replace("/", ".") for p in current_py if p.endswith(".py")}
    deleted_mods = raw_deleted_mods - current_mods
    if raw_deleted_mods - deleted_mods:
        skipped = sorted(raw_deleted_mods - deleted_mods)
        print(f"(skipped {len(skipped)} already replaced by a compat wrapper: {', '.join(skipped[:5])}{'...' if len(skipped)>5 else ''})")
    print()

    # Scan surviving references
    findings: list[tuple[Path, int, str, str]] = []  # file, line, import, deleted_mod
    for fpath, line, target in _imports_in_repo(dirs):
        for dm in deleted_mods:
            if target == dm or target.startswith(dm + "."):
                findings.append((fpath, line, target, dm))
                break

    if not findings:
        print("✓ no stale references (reorg is clean)")
        return 0

    print(f"✗ found {len(findings)} stale references (callers referencing modules deleted by the reorg):")
    seen: set[tuple[str, int, str]] = set()
    for fpath, line, target, dm in findings:
        key = (str(fpath), line, target)
        if key in seen:
            continue
        seen.add(key)
        print(f"  {fpath}:{line}  import {target!r}  →  deleted {dm!r}")
    print()
    print(f"Fix: remove the caller reference, or use an import alias (e.g. a compat wrapper).")
    print(f"      pyright also catches this: pyright {' '.join(dirs)} --level error")
    return 1


if __name__ == "__main__":
    sys.exit(main())
