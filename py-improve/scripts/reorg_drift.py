#!/usr/bin/env python3
"""reorg_drift.py — reorg 漂移检测 (Phase 13.2).

2026-09-03 起源: kb@245 watchlist session 修 2 broken import (reorg 删 module
但 caller 引用):
- commit 4646799cf 删 backend/domains/qa/quality.py 508 行, 但
  backend/core/direct_upload.py:506 仍 `from backend.core.quality import
  (QUALITY_THRESHOLD_LOW, ...)` → ImportError, _process_one_doc_direct broken.
- commit 471ea8d24 删 summarize_with_title_zh, 但
  crawler/feed_to_kb.py:1895 仍 import → 同样 ImportError.

检测方法: `git log --diff-filter=D` 找 reorg 删的文件 → 扫现存的 `from X
import | import X` → 找引用残留 → 列 file:line.

限制: 只检本仓库 Python 源码 (默认 git ls-files 探测顶层源码目录,
Python-only). 跨仓库引用 (e.g. 别的项目 pip install) 检不到, 但本机场景够用.

用法:
    python3 scripts/audit/reorg_drift.py                        # 检全仓 (默认探测)
    python3 scripts/audit/reorg_drift.py --dirs backend crawler # 显式指定源码目录
    python3 scripts/audit/reorg_drift.py --since 30             # 检 30 天内删的
    python3 scripts/audit/reorg_drift.py --no-color             # CI 模式

退出码: 0=无漂移, 1=有引用残留 (caller 引用了不存在的 module/symbol).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# 仓库根: 用 git rev-parse 找 (skill 可能放任意位置, parents[N] 不可靠)
def _find_repo_root() -> Path:
    """从本脚本位置向上 walk, 找含 .git 目录的最近祖先."""
    p = Path(__file__).resolve().parent
    for cand in [p, *p.parents]:
        if (cand / ".git").exists():
            return cand
    # 兜底: 走 git rev-parse (cwd 是 repo 内)
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, check=False)
    if r.returncode == 0:
        return Path(r.stdout.strip())
    return p  # 兜底: 脚本所在目录


REPO_ROOT = _find_repo_root()

# 排除
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv",
                "build", "dist", ".codegraph"}


def _detect_source_dirs() -> list[str] | None:
    """默认目录探测: `git ls-files "*.py"` (cwd=REPO_ROOT) → 每路径第一段 →
    去 EXCLUDE_DIRS → 去非目录段 → 排序.

    无 .py 跟踪文件或无有效顶层目录 → print WARNING + 返回 None
    (调用方 return 1, 不静默过).
    """
    r = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO_ROOT,
                       capture_output=True, text=True, check=False)
    lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    segs = sorted({ln.split("/")[0] for ln in lines} - EXCLUDE_DIRS)
    dirs = [s for s in segs if (REPO_ROOT / s).is_dir()]
    if not lines or not dirs:
        print("WARNING: 未从 git ls-files 探测到源码目录, 用 --dirs 指定")
        return None
    return dirs


def _run_git_log_deleted(since_days: int | None) -> list[str]:
    """返回最近 N 天 reorg 删的 *.py 文件路径 (相对 REPO_ROOT)."""
    cmd = ["git", "log", "--diff-filter=D", "--name-only", "--pretty=format:"]
    if since_days is not None:
        cmd.extend([f"--since={since_days} days ago"])
    cmd.append("--")  # 仅 .py
    cmd.append("*.py")
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                       check=False)
    return [p.strip() for p in r.stdout.splitlines() if p.strip()]


def _imports_in_repo(dirs: list[str]) -> list[tuple[Path, int, str]]:
    """扫指定顶层目录, 返回 (file, line, import_str) 三元组 list.

    只扫 dirs, 排除 EXCLUDE_DIRS.
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
                    help="top-level 源码目录 (默认: git ls-files 探测)")
    ap.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    args = ap.parse_args()

    dirs = args.dirs
    if not dirs:
        dirs = _detect_source_dirs()
        if dirs is None:
            return 1

    deleted = _run_git_log_deleted(args.since)
    if not deleted:
        print(f"无 reorg 删的 .py 文件" + (f" (--since={args.since}d)" if args.since else ""))
        return 0

    print(f"reorg 删的 .py 文件: {len(deleted)}")
    for d in deleted:
        print(f"  - {d}")
    print()

    # 把删除的文件名转 module 名 (e.g. backend/core/quality.py → backend.core.quality)
    raw_deleted_mods = {d[:-3].replace("/", ".") for d in deleted if d.endswith(".py")}

    # 过滤: 如果当前 git 还跟踪同名 .py (NoOp compat wrapper 或重新引入), 跳过
    # 这些不算 "caller 引用了不存在 module", 真正删除 = 不在 ls-files
    current_py = subprocess.run(
        ["git", "ls-files", "*.py"],
        capture_output=True, text=True, check=False, cwd=str(REPO_ROOT),
    ).stdout.splitlines()
    current_mods = {p[:-3].replace("/", ".") for p in current_py if p.endswith(".py")}
    deleted_mods = raw_deleted_mods - current_mods
    if raw_deleted_mods - deleted_mods:
        skipped = sorted(raw_deleted_mods - deleted_mods)
        print(f"(跳过 {len(skipped)} 个有 compat wrapper 替代: {', '.join(skipped[:5])}{'...' if len(skipped)>5 else ''})")
    print()

    # 扫现存引用
    findings: list[tuple[Path, int, str, str]] = []  # file, line, import, deleted_mod
    for fpath, line, target in _imports_in_repo(dirs):
        for dm in deleted_mods:
            if target == dm or target.startswith(dm + "."):
                findings.append((fpath, line, target, dm))
                break

    if not findings:
        print("✓ 无引用残留 (reorg 干净)")
        return 0

    print(f"✗ 发现 {len(findings)} 处引用残留 (caller 引用了 reorg 删的 module):")
    seen: set[tuple[str, int, str]] = set()
    for fpath, line, target, dm in findings:
        key = (str(fpath), line, target)
        if key in seen:
            continue
        seen.add(key)
        print(f"  {fpath}:{line}  import {target!r}  →  删 {dm!r}")
    print()
    print(f"修法: 删 caller 引用, 或 import 别名 (e.g. compat wrapper).")
    print(f"      跑 pyright 也可捕: pyright {' '.join(dirs)} --level error")
    return 1


if __name__ == "__main__":
    sys.exit(main())
