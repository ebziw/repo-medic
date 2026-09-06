#!/usr/bin/env python3
"""config_drift.py — config drift 检测 (systemd unit / crontab / .env).

比 live config dir vs git-tracked deploy/ source, 找未入 git 的 live-only
config 文件. 这些是 deploy 漂移的 root cause (改 live 不入 git → 部署丢改动).

语言/项目无关: repo root 用 `git rev-parse` 从 cwd 探测 (或 --repo 指定),
live systemd dir 默认 `~/.config/systemd/user` (可 --systemd-dir 覆盖).

用法:
    cd /path/to/repo && python3 scripts/audit/config_drift.py        # systemd unit
    python3 scripts/audit/config_drift.py --crontab                  # crontab
    python3 scripts/audit/config_drift.py --env                      # 项目根 .env
    python3 scripts/audit/config_drift.py --all
    python3 scripts/audit/config_drift.py --repo /srv/proj --systemd-dir /etc/systemd/system

退出码: 0=无 drift, 1=有 drift.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path | None:
    """git rev-parse --show-toplevel 探测 (skill 可放任意位置, 不走硬编码候选)."""
    cwd = start or Path.cwd()
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False, cwd=str(cwd),
    )
    if r.returncode != 0:
        return None
    return Path(r.stdout.strip())


def git_ls_files(repo_root: Path, pattern: str) -> set[str]:
    """返 git index 里匹配 pattern 的文件 (相对 repo root).

    pattern 可多 glob, 空格分隔 (如 "deploy/systemd/*.service deploy/systemd/*.timer").
    用 shlex.split 让 shell 拆分, 再用 glob 在 cwd 展开 (git ls-files pathspec 不展开 shell glob).
    """
    import shlex
    out: set[str] = set()
    for pat in shlex.split(pattern):
        # shell-expand (假设 cwd=repo_root, 实际我们 cd 到 repo_root 再调)
        import glob as _glob
        expanded = _glob.glob(pat)
        if not expanded:
            # 没匹配, 直接传原 pattern 给 git ls-files (pathspec 模式)
            expanded = [pat]
        r = subprocess.run(
            ["git", "ls-files", "--"] + expanded,
            capture_output=True, text=True, check=False, cwd=str(repo_root),
        )
        if r.returncode == 0:
            out |= {p.strip() for p in r.stdout.splitlines() if p.strip()}
    return out


def list_live_dir(live_dir: Path, suffix: str = "*.service") -> set[str]:
    """返 live_dir 下匹配 suffix 的文件名 (相对 live_dir)."""
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
        issues.append(f"[live-only] {live_dir}/{unit} (deploy 会丢)")
    for unit in sorted(git_names - live_names):
        issues.append(f"[git-only] deploy/systemd/{unit} (live 没装)")
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
    """项目根 .env: 是否被 .gitignore 排除 (secret 不入 git 正常) + 有无 .env.example 对照."""
    issues: list[str] = []
    env_path = repo_root / ".env"
    if not env_path.exists():
        return issues
    # .env 是否被 git 忽略 — 忽略 = 正常 (secret); 没忽略 = 危险 (secret 可能入库)
    r = subprocess.run(
        ["git", "check-ignore", "-q", ".env"],
        capture_output=True, text=True, check=False, cwd=str(repo_root),
    )
    if r.returncode != 0:  # 未被忽略
        issues.append(f"[危险] {env_path} 未被 .gitignore 忽略 — secret 可能入库")
    example = repo_root / ".env.example"
    if not example.exists():
        issues.append(f"[warn] 无 {repo_root / '.env.example'} — 新环境无法从模板起")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--systemd", action="store_true", help="检 systemd unit (default)")
    ap.add_argument("--crontab", action="store_true", help="检 crontab")
    ap.add_argument("--env", action="store_true", help="检项目根 .env vs .env.example")
    ap.add_argument("--all", action="store_true", help="全检")
    ap.add_argument("--repo", default=None, help="git repo 路径 (默认 cwd 探测)")
    ap.add_argument("--systemd-dir", default=None,
                    help="live systemd unit 目录 (默认 ~/.config/systemd/user)")
    args = ap.parse_args()

    repo_root = find_repo_root(Path(args.repo)) if args.repo else find_repo_root()
    if repo_root is None:
        print(f"✗ 未找到 git repo root (cwd={Path.cwd()}, 用 --repo 指定)")
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
        print(f"✓ 无 config drift ({repo_root})")
        return 0
    print(f"✗ 发现 {len(all_issues)} 项 config drift ({repo_root}):")
    for i in all_issues:
        print(f"  {i}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
