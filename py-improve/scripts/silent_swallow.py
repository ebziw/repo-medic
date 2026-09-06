#!/usr/bin/env python3
"""silent_swallow.py — Phase 13.1 静默吞错扫描 (含 Phase 13.2 context-aware 过滤).

找 `except ...: pass|continue` 模式 (1 行或 2 行). 命中 = 应改 log 或 raise.
不包含 `except X: log; pass` (有 log 的不算吞错).

Phase 13.2 context-aware 过滤 (排除 false positive 类):
- `except StopIteration: pass` — generator 关闭句柄 (Python 惯用法)
- `except OSError: pass` 在 `unlink(missing_ok=True)` 之后 — race 防御
- 父行含 `shutil.rmtree` / cleanup / finalizer — shutdown cleanup
- 同函数内 `logger.debug` 紧邻 — 已有 log, 不算吞错

用法:
    python3 scripts/audit/silent_swallow.py                # 扫全仓 (含过滤)
    python3 scripts/audit/silent_swallow.py --raw         # 不过滤, 看全部
    python3 scripts/audit/silent_swallow.py --limit 50
    python3 scripts/audit/silent_swallow.py backend/
    # Python-only: 只扫 *.py. 无参数 = git ls-files 探测顶层源码目录;
    # 显式路径不存在 → WARNING 跳过 (继续其他), 全无效 → return 1 (不静默干净).

退出码: 0=0 命中, 1=有命中 (CI gate).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def _find_repo_root() -> Path:
    """从本脚本位置向上 walk, 找含 .git 目录的最近祖先."""
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


# 单行:  except X:    \n   pass|continue
SINGLE = re.compile(
    r"^\s*except[^:]*:\s*(pass|continue)\s*$",
    re.M,
)
# 2行:   except X:\n     pass|continue
TWO_LINE = re.compile(
    r"except[^\n]*:\s*\n\s+(pass|continue)\b",
)

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv", "build", "dist", ".codegraph"}

# Phase 13.2 context-aware 过滤关键词 (上下文行有这些 → false positive)
FP_CONTEXT = (
    # generator 关闭
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
    """检查 line_num 上下 5 行是否命中 FP context 关键词."""
    lines = file_text.splitlines()
    ctx_start = max(0, line_num - 6)
    ctx_end = min(len(lines), line_num + 4)
    ctx = "\n".join(lines[ctx_start:ctx_end])
    for pat in FP_CONTEXT:
        if re.search(pat, ctx):
            return True
    return False


def scan(paths: list[Path], *, filter_fp: bool = True) -> list[tuple[Path, int, str]]:
    """返回去重 (file, line) 列表, kind 标 single/two-line.

    filter_fp=True: 排除 false positive 类 (Phase 13.2 context-aware).
    """
    out: list[tuple[Path, int, str]] = []
    seen: set[tuple[Path, int]] = set()
    for root in paths:
        for py in root.rglob("*.py"):
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
    """不过滤, 返所有 (含 defensive)."""
    return scan(paths, filter_fp=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("paths", nargs="*", default=None,
                    help="paths to scan (relative to repo root; 默认 git ls-files 探测)")
    ap.add_argument("--limit", type=int, default=50, help="max findings to display")
    ap.add_argument("--raw", action="store_true",
                    help="不过滤 false positive (Phase 13.2)")
    args = ap.parse_args()

    given = list(args.paths) if args.paths else _detect_source_dirs()
    if given is None:
        return 1
    # 显式/探测目录逐一确认存在; 缺失 → WARNING 跳过 (仍扫其余)
    paths: list[Path] = []
    for p in given:
        full = REPO_ROOT / p
        if full.is_dir():
            paths.append(full)
        else:
            print(f"WARNING: 目录不存在, 跳过: {p}")
    if not paths:
        print("WARNING: 无有效目录可扫 (全部不存在或探测为空), 未扫描任何路径")
        return 1

    filter_fp = not args.raw
    findings = scan(paths, filter_fp=filter_fp)
    raw_count = len(scan_raw(paths)) if filter_fp else len(findings)

    if not findings:
        if filter_fp:
            print(f"✓ 无 silent swallow (raw {raw_count} 已过滤 {raw_count - 0} defensive)")
        else:
            print(f"✓ 无 silent swallow ({sum(1 for _ in paths)} paths 扫完)")
        return 0

    mode = "(raw, 不过滤)" if args.raw else f"(过滤后, raw {raw_count})"
    print(f"✗ 发现 {len(findings)} 处 silent swallow {mode} (前 {args.limit}):")
    for fpath, line, kind in findings[: args.limit]:
        print(f"  {fpath}:{line}  [{kind}]")
    if len(findings) > args.limit:
        print(f"  ... 还有 {len(findings) - args.limit} 处未显示")
    print()
    print(f"修法模板: `except X as e: log.exception(...)` 或 `raise` (必须让 caller 看到)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
