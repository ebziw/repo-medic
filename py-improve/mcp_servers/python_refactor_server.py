"""Local Python Refactor MCP server — replaces broken upstream @slamer59/mcp-python-refactoring.

Wraps ruff / vulture / rope / bandit (all installed locally, no upstream dependency).
Uses FastMCP API (mcp-python-sdk).
"""
import json
import subprocess
import sys

from mcp.server.fastmcp import FastMCP

server = FastMCP("python-refactor-local")


def _run(cmd: list[str], timeout: int = 60) -> str:
    """Run CLI tool, return stdout. stderr appended if non-empty."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        out = result.stdout
        if result.stderr and result.returncode != 0:
            out += "\n[stderr]\n" + result.stderr
        return out
    except FileNotFoundError:
        return f"ERROR: {' '.join(cmd[:2])} not installed"
    except subprocess.TimeoutExpired:
        return f"ERROR: timeout after {timeout}s"
    except subprocess.SubprocessError as e:
        return f"ERROR: {type(e).__name__}: {e}"


@server.tool()
async def ruff_check(path: str, fix: bool = False, unsafe: bool = False) -> str:
    """Run ruff check on a Python path.

    Args:
        path: file or directory to lint
        fix: apply safe auto-fixes
        unsafe: also apply unsafe fixes (review required)
    """
    cmd = ["ruff", "check", path]
    if unsafe or fix:
        cmd.append("--fix")
    return _run(cmd)


@server.tool()
async def ruff_format(path: str, check: bool = False) -> str:
    """Run ruff format on a Python path.

    Args:
        path: file or directory
        check: only check, don't modify
    """
    cmd = ["ruff", "format", path]
    if check:
        cmd.append("--check")
    return _run(cmd)


@server.tool()
async def vulture_scan(path: str, min_confidence: int = 80) -> str:
    """Find dead code with vulture.

    Args:
        path: directory to scan
        min_confidence: minimum confidence (0-100). Below 80 = high false-positive risk.
    """
    return _run(["vulture", path, "--min-confidence", str(min_confidence)])


@server.tool()
async def bandit_scan(path: str, severity: str = "low") -> str:
    """Security scan with bandit.

    Args:
        path: file or directory
        severity: low/medium/high — minimum severity to report
    """
    cmd = ["bandit", "-r", path, "-f", "text", "--severity-level", severity]
    return _run(cmd)


@server.tool()
async def radon_complexity(path: str, min_grade: str = "C") -> str:
    """Cyclomatic complexity with radon.

    Args:
        path: directory
        min_grade: minimum grade (A/B/C/D/F) to report
    """
    return _run(["radon", "cc", path, "-s", "-a", "-n", min_grade])


@server.tool()
async def pyright_check(path: str, strict: bool = False) -> str:
    """Type check + import reachability with pyright (reorg-drift 关键).

    Args:
        path: file or directory
        strict: enable strict mode
    """
    cmd = ["pyright", path]
    if strict:
        cmd.append("--level")
        cmd.append("error")
    return _run(cmd, timeout=180)


@server.tool()
async def list_tools_meta() -> str:
    """Return this server's tool manifest (avoids MCP client caching issues)."""
    return json.dumps({
        "server": "python-refactor-local",
        "tools": [
            "ruff_check", "ruff_format", "vulture_scan", "bandit_scan", "radon_complexity", "pyright_check"
        ],
        "under_tools_required": [
            "ruff", "vulture", "bandit", "radon", "pyright"
        ],
        "python": sys.version.split()[0],
    }, indent=2)


if __name__ == "__main__":
    server.run(transport="stdio")