"""config-base tools check/install script.

Manages supporting tools that repo-medic sub-skills depend on.

Usage:
    python tools.py check              # detect all tools, report table
    python tools.py check --json       # JSON output
    python tools.py install <name>     # install specific tool (user-confirmed)
    python tools.py install --all      # install all missing (with --yes flag)

Stdlib only (no yaml dep). Edit TOOLS dict to add tools.

Cross-platform: detects OS, picks install command per platform.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    check_cmd: list[str]
    min_version: str | None  # None = skip version check
    install_cmd_linux: list[str] | None = None
    install_cmd_macos: list[str] | None = None
    install_cmd_windows: list[str] | None = None
    category: str = "general"  # python | node | db | system | mcp


# Tool manifest. Edit here when adding new dependencies.
TOOLS: list[Tool] = [
    # Python core + lint/type/test (py-improve)
    Tool("python", ["python", "--version"], "3.12", category="python"),
    Tool("uv", ["uv", "--version"], None, install_cmd_linux=["uv", "pip", "install", "--system", "ruff", "mypy", "vulture", "bandit", "radon"], category="python"),
    Tool("ruff", ["ruff", "--version"], "0.3", install_cmd_linux=["uv", "pip", "install", "--system", "ruff"], category="python"),
    Tool("mypy", ["mypy", "--version"], "1.8", install_cmd_linux=["uv", "pip", "install", "--system", "mypy"], category="python"),
    Tool("vulture", ["vulture", "--version"], "2.0", install_cmd_linux=["uv", "pip", "install", "--system", "vulture"], category="python"),
    Tool("bandit", ["bandit", "--version"], "1.7", install_cmd_linux=["uv", "pip", "install", "--system", "bandit"], category="python"),
    Tool("radon", ["radon", "--version"], "6.0", install_cmd_linux=["uv", "pip", "install", "--system", "radon"], category="python"),
    Tool("pyright", ["pyright", "--version"], "1.1", install_cmd_linux=["uv", "pip", "install", "--system", "pyright"], category="python"),
    Tool("pytest", ["pytest", "--version"], "8.0", install_cmd_linux=["uv", "pip", "install", "--system", "pytest", "pytest-asyncio"], category="python"),
    # Node + Vue toolchain (vue-improve)
    Tool("node", ["node", "--version"], "18.0", category="node"),
    Tool("npm", ["npm", "--version"], "9.0", category="node"),
    Tool("pnpm", ["pnpm", "--version"], "8.0", category="node"),
    # codegraph (py-improve)
    Tool("codegraph", ["codegraph", "--version"], "3.0", install_cmd_linux=["npm", "install", "-g", "@optave/codegraph"], category="system"),
    # ripgrep (doc-reorg + general)
    Tool("rg", ["rg", "--version"], "13.0", install_cmd_linux=["apt-get", "install", "-y", "ripgrep"], install_cmd_macos=["brew", "install", "ripgrep"], category="system"),
    Tool("tree", ["tree", "--version"], None, install_cmd_linux=["apt-get", "install", "-y", "tree"], install_cmd_macos=["brew", "install", "tree"], category="system"),
    # PostgreSQL client (db-tweak)
    Tool("psql", ["psql", "--version"], "14.0", install_cmd_linux=["apt-get", "install", "-y", "postgresql-client"], install_cmd_macos=["brew", "install", "libpq", "--link"], category="db"),
    # MCP python deps (py-improve via mcp_servers/python_refactor_server.py)
    Tool("mcp", ["python", "-c", "import mcp; print(mcp.__version__)"], "1.0", install_cmd_linux=["uv", "pip", "install", "--system", "mcp", "fastapi", "uvicorn"], category="mcp"),
]


def _version_tuple(s: str) -> tuple[int, ...]:
    """Parse first version-like string in output → tuple of ints."""
    m = re.search(r"(\d+(?:\.\d+)*)", s)
    if not m:
        return (0,)
    return tuple(int(x) for x in m.group(1).split("."))


def _resolve_cmd(cmd: list[str]) -> tuple[list[str] | str, dict]:
    """Resolve cmd + run_kwargs for current OS.

    Windows quirks handled:
    - .cmd/.bat/.com files need shell=True (cmd.exe interprets)
    - shutil.which may return path with .cmd extension; pass through
    - non-UTF8 output (e.g. tree.com on Chinese Windows uses GBK):
      use errors='replace' in subprocess.run text decode
    """
    if sys.platform != "win32":
        return cmd, {}
    exe = cmd[0]
    resolved = shutil.which(exe) or exe
    needs_shell = resolved.lower().endswith((".cmd", ".bat", ".com"))
    final: list[str] | str
    if needs_shell:
        # shell=True requires string form
        final = " ".join(f'"{a}"' if " " in a else a for a in cmd)
        return final, {"shell": True, "errors": "replace"}
    return cmd, {"errors": "replace"}


def _check(tool: Tool) -> dict:
    """Run tool's check_cmd, return status dict."""
    cmd, run_kwargs = _resolve_cmd(tool.check_cmd)
    exe = cmd[0] if isinstance(cmd, list) else cmd.split()[0].strip('"')
    if shutil.which(exe) is None:
        return {"name": tool.name, "installed": False, "version": None, "ok": False, "category": tool.category}

    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, **run_kwargs
        )
        ver_str = (out.stdout + out.stderr).strip().split("\n")[0]
    except (subprocess.TimeoutExpired, OSError) as e:
        return {"name": tool.name, "installed": True, "version": None, "ok": False, "error": str(e), "category": tool.category}

    if tool.min_version is None:
        return {"name": tool.name, "installed": True, "version": ver_str, "ok": True, "category": tool.category}

    actual = _version_tuple(ver_str)
    required = _version_tuple(tool.min_version)
    ok = actual >= required if actual and required else True
    return {
        "name": tool.name,
        "installed": True,
        "version": ver_str,
        "required": tool.min_version,
        "ok": ok,
        "category": tool.category,
    }


def _install_cmd(tool: Tool) -> list[str] | None:
    sys_plat = sys.platform
    if sys_plat.startswith("linux") and tool.install_cmd_linux:
        return tool.install_cmd_linux
    if sys_plat == "darwin" and tool.install_cmd_macos:
        return tool.install_cmd_macos
    if sys_plat == "win32" and tool.install_cmd_windows:
        return tool.install_cmd_windows
    return None


def cmd_check(args: argparse.Namespace) -> int:
    results = [_check(t) for t in TOOLS]

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    # Table output
    print(f"{'TOOL':<14} {'CAT':<6} {'STATUS':<8} {'VERSION':<20} {'REQUIRED':<10}")
    print("-" * 65)
    by_status = {"ok": 0, "missing": 0, "outdated": 0, "error": 0}
    for r in results:
        if not r["installed"]:
            status = "MISSING"
            version = "-"
            required = t_min(r["name"]) or "-"
            by_status["missing"] += 1
        elif r.get("ok"):
            status = "OK"
            version = (r.get("version") or "-")[:20]
            required = r.get("required") or "-"
            by_status["ok"] += 1
        elif "error" in r:
            status = "ERROR"
            version = r.get("error", "")[:20]
            required = t_min(r["name"]) or "-"
            by_status["error"] += 1
        else:
            status = "OUTDATED"
            version = (r.get("version") or "-")[:20]
            required = r.get("required") or "-"
            by_status["outdated"] += 1
        print(f"{r['name']:<14} {r.get('category', '-'):<6} {status:<8} {version:<20} {required:<10}")

    print("-" * 65)
    print(
        f"Total: {len(results)}  OK={by_status['ok']}  "
        f"MISSING={by_status['missing']}  OUTDATED={by_status['outdated']}  "
        f"ERROR={by_status['error']}"
    )
    return 0


def t_min(name: str) -> str | None:
    """Look up min_version for tool by name."""
    for t in TOOLS:
        if t.name == name:
            return t.min_version
    return None


def cmd_install(args: argparse.Namespace) -> int:
    targets = TOOLS if args.all else [t for t in TOOLS if t.name == args.name]
    if not targets:
        print(f"unknown tool: {args.name}", file=sys.stderr)
        print("run `python tools.py check` to list all tools", file=sys.stderr)
        return 1

    if not args.yes:
        names = ", ".join(t.name for t in targets)
        print(f"Will install: {names}")
        print(f"Platform: {sys.platform}")
        print("Use --yes to proceed")
        return 0

    failed = []
    for tool in targets:
        cmd = _install_cmd(tool)
        if cmd is None:
            print(f"[skip] {tool.name}: no install command for platform {sys.platform}")
            continue
        print(f"[install] {tool.name}: {' '.join(cmd)}")
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            print(f"  FAIL exit={rc}", file=sys.stderr)
            failed.append(tool.name)
        else:
            print(f"  OK")

    if failed:
        print(f"\nFailed: {failed}", file=sys.stderr)
        return 1
    print("\nAll done. Run `python tools.py check` to verify.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="repo-medic config-base tool manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="detect installed tools")
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=cmd_check)

    p_install = sub.add_parser("install", help="install missing tools")
    p_install.add_argument("name", nargs="?", default=None, help="tool name (or --all)")
    p_install.add_argument("--all", action="store_true")
    p_install.add_argument("--yes", "-y", action="store_true", help="actually run install")
    p_install.set_defaults(func=cmd_install)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
