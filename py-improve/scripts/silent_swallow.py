#!/usr/bin/env python3
"""silent_swallow.py — Phase 13.1 silent-error scan (with Phase 13.2 context-aware filtering).

Finds `except ...: pass|continue` patterns (1 or 2 lines). A hit = should log or raise instead.
Excludes `except X: log; pass` (logging present = not a silent swallow).

Phase 13.2 context-aware filters (exclude false-positive classes):
- `except StopIteration: pass` — generator close handle (Python idiom)
- `except OSError: pass` right after `unlink(missing_ok=True)` — race defense
- Parent line contains `shutil.rmtree` / cleanup / finalizer — shutdown cleanup
- Sibling `logger.debug` in the same function — already logged, not a swallow

Usage:
    python3 scripts/silent_swallow.py                # scan repo (with filtering)
    python3 scripts/silent_swallow.py --raw         # no filtering, show all
    python3 scripts/silent_swallow.py --limit 50
    python3 scripts/silent_swallow.py backend/
    # Python-only: scans *.py. No args = git ls-files detects top-level source dirs;
    # nonexistent explicit path -> WARNING + skip (continue others); all invalid -> return 1 (never silent-clean).

Exit codes: 0=no hits, 1=hits found (CI gate).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def _find_repo_root() -> Path:
    """Walk upward from this script's location to the nearest ancestor containing a .git dir."""
    p = Path(__file__).resolve().parent
    for cand in [p, *p.parents]:
        if (cand / ".git").exists():
            return cand
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, check=False)
    if r.returncode == 0:
        return Path(r.stdout.strip())
    return p


REPO_ROOT = _find_repo_root()


def _detect_source_dirs() -> list[str] | None:
    """Default dir detection: `git ls-files "*.py"` (cwd=REPO_ROOT) -> first path segment ->
    drop EXCLUDE_DIRS -> drop non-directory segments -> sort.

    No tracked .py files or no valid top-level dir -> print WARNING + return None
    (caller returns 1, never silently passes).
    """
    r = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO_ROOT,
                       capture_output=True, text=True, check=False)
    lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    segs = sorted({ln.split("/")[0] for ln in lines} - EXCLUDE_DIRS)
    dirs = [s for s in segs if (REPO_ROOT / s).is_dir()]
    if not lines or not dirs:
        print("WARNING: no source dirs detected from git ls-files, specify with --dirs")
        return None
    return dirs


# single-line:  except X:    \n   pass|continue
SINGLE = re.compile(
    r"^\s*except[^:]*:\s*(pass|continue)\s*$",
    re.M,
)
# two-line:   except X:\n     pass|continue
TWO_LINE = re.compile(
    r"except[^\n]*:\s*\n\s+(pass|continue)\b",
)

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv", "build", "dist", ".codegraph"}

# Phase 13.2 context-aware filter keywords (a context line containing these -> false positive)
FP_CONTEXT = (
    # generator close
    r"\bStopIteration\b",
    # cleanup / shutdown / finalizer
    r"\bshutil\.(rmtree|copy|move)\b",
    r"\bfinalize\b",
    r"\b__del__\b",
    r"\batexit\b",
    # already have log
    r"\.unlink\(missing_ok=True\)",
    r"\blogger?\.\s*(debug|info|warning|error|exception)",
    r"\b_log(?:ger)?\.\s*(debug|info|warning|error|exception)",
)


def _is_false_positive(file_text: str, line_num: int) -> bool:
    """Check whether the 5 lines around line_num hit any FP context keyword."""
    lines = file_text.splitlines()
    ctx_start = max(0, line_num - 6)
    ctx_end = min(len(lines), line_num + 4)
    ctx = "\n".join(lines[ctx_start:ctx_end])
    for pat in FP_CONTEXT:
        if re.search(pat, ctx):
            return True
    return False


def scan(paths: list[Path], *, filter_fp: bool = True) -> list[tuple[Path, int, str]]:
    """Return a deduped (file, line) list; kind marks single/two-line.

    filter_fp=True: exclude false-positive classes (Phase 13.2 context-aware).
    """
    out: list[tuple[Path, int, str]] = []
    seen: set[tuple[Path, int]] = set()
    for root in paths:
        # Accept a single .py file as well as a directory (explicit file bypasses EXCLUDE_DIRS).
        if root.is_file():
            iterable = [root]
        else:
            iterable = root.rglob("*.py")
        for py in iterable:
            if any(part in EXCLUDE_DIRS for part in py.parts):
                continue
            try:
                text = py.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            try:
                rel = py.relative_to(REPO_ROOT)
            except ValueError:
                rel = py
            for m in SINGLE.finditer(text):
                line = text[: m.start()].count("\n") + 1
                if (rel, line) in seen:
                    continue
                if filter_fp and _is_false_positive(text, line):
                    continue
                seen.add((rel, line))
                out.append((rel, line, "single"))
            for m in TWO_LINE.finditer(text):
                line = text[: m.start()].count("\n") + 1
                if (rel, line) in seen:
                    continue
                if filter_fp and _is_false_positive(text, line):
                    continue
                seen.add((rel, line))
                out.append((rel, line, "two-line"))
    return out


def scan_raw(paths: list[Path]) -> list[tuple[Path, int, str]]:
    """No filtering; return everything (including defensive swallows)."""
    return scan(paths, filter_fp=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("paths", nargs="*", default=None,
                    help="paths to scan (relative to repo root; default: detected via git ls-files)")
    ap.add_argument("--limit", type=int, default=50, help="max findings to display")
    ap.add_argument("--raw", action="store_true",
                    help="do not filter false positives (Phase 13.2)")
    args = ap.parse_args()

    given = list(args.paths) if args.paths else _detect_source_dirs()
    if given is None:
        return 1
    # Verify each explicit/detected path exists; missing -> WARNING + skip (still scan the rest)
    # Accepts directories AND single .py files.
    paths: list[Path] = []
    for p in given:
        full = REPO_ROOT / p
        if full.is_dir() or (full.is_file() and full.suffix == ".py"):
            paths.append(full)
        else:
            print(f"WARNING: path not found or not a .py file, skipping: {p}")
    if not paths:
        print("WARNING: no valid paths to scan (all missing or detection empty), no paths scanned")
        return 1

    filter_fp = not args.raw
    findings = scan(paths, filter_fp=filter_fp)
    raw_count = len(scan_raw(paths)) if filter_fp else len(findings)

    if not findings:
        if filter_fp:
            print(f"✓ no silent swallow (raw {raw_count}, filtered {raw_count - 0} defensive)")
        else:
            print(f"✓ no silent swallow ({sum(1 for _ in paths)} paths scanned)")
        return 0

    mode = "(raw, unfiltered)" if args.raw else f"(after filter, raw {raw_count})"
    print(f"✗ found {len(findings)} silent swallow {mode} (first {args.limit}):")
    for fpath, line, kind in findings[: args.limit]:
        print(f"  {fpath}:{line}  [{kind}]")
    if len(findings) > args.limit:
        print(f"  ... {len(findings) - args.limit} more not shown")
    print()
    print(f"fix template: `except X as e: log.exception(...)` or `raise` (the caller must see it)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
