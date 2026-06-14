"""
Deterministic sandbox for executing untrusted code.
No LLM imports anywhere in this file.

Execution order preference:
  1. Docker (--network=none, read-only FS, CPU/mem limits)  if use_docker=True and docker is available
  2. Subprocess with resource limits (fallback)

run_pytest() writes solution.py to a temp dir, copies the test file,
runs pytest, and returns a result namespace.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SandboxResult:
    all_passed: bool
    report: str
    error: str = ""


_DOCKER_IMAGE = "python:3.11-slim"
_DOCKER_CHECKED: bool | None = None  # None = not yet checked


def _docker_available() -> bool:
    global _DOCKER_CHECKED
    if _DOCKER_CHECKED is not None:
        return _DOCKER_CHECKED
    try:
        r = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5
        )
        _DOCKER_CHECKED = r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        _DOCKER_CHECKED = False
    return _DOCKER_CHECKED


def run_pytest(
    code: str,
    tests_path: str,
    *,
    timeout: int = 60,
    use_docker: bool = True,
    cpu_sec: int = 30,
    mem_mb: int = 512,
) -> SandboxResult:
    """
    Run pytest against `code` (written as solution.py) plus `tests_path`.
    Returns SandboxResult with .all_passed and .report.
    """
    tmpdir = tempfile.mkdtemp(prefix="arena_sandbox_")
    try:
        sol_path = os.path.join(tmpdir, "solution.py")
        with open(sol_path, "w") as f:
            f.write(code)

        tests_src = Path(tests_path)
        if not tests_src.exists():
            return SandboxResult(
                all_passed=False,
                report="",
                error=f"tests_path not found: {tests_path}",
            )
        shutil.copy(tests_src, os.path.join(tmpdir, tests_src.name))

        if use_docker and _docker_available():
            return _run_docker(tmpdir, tests_src.name, timeout, cpu_sec, mem_mb)
        else:
            return _run_subprocess(tmpdir, tests_src.name, timeout, cpu_sec)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _run_docker(
    tmpdir: str, test_filename: str, timeout: int, cpu_sec: int, mem_mb: int
) -> SandboxResult:
    cmd = [
        "docker", "run", "--rm",
        "--network=none",
        "--read-only",
        f"--cpus={cpu_sec}",
        f"--memory={mem_mb}m",
        "--memory-swap=0",
        "-v", f"{tmpdir}:/sandbox:ro",
        "--tmpfs", "/tmp",
        _DOCKER_IMAGE,
        "python", "-m", "pytest",
        f"/sandbox/{test_filename}",
        "--tb=short", "-q",
    ]
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        passed = r.returncode == 0
        return SandboxResult(all_passed=passed, report=r.stdout + r.stderr)
    except subprocess.TimeoutExpired:
        return SandboxResult(
            all_passed=False, report="", error="docker sandbox timeout"
        )
    except Exception as e:
        return SandboxResult(all_passed=False, report="", error=str(e))


def _run_subprocess(
    tmpdir: str, test_filename: str, timeout: int, cpu_sec: int
) -> SandboxResult:
    """
    Fallback: subprocess with resource limits via preexec_fn.
    Works on macOS/Linux. On macOS, RLIMIT_CPU may not SIGKILL reliably,
    so we always rely on subprocess timeout as the hard bound.
    """
    def _setlimits():
        try:
            import resource
            # CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_sec, cpu_sec))
            # Address space: 2× mem_mb for headroom
            mem_bytes = mem_mb * 1024 * 1024 * 2
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except Exception:
            pass  # best-effort; timeout still protects us

    cmd = [
        sys.executable, "-m", "pytest",
        test_filename,
        "--tb=short", "-q",
    ]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tmpdir,
            preexec_fn=_setlimits if sys.platform != "win32" else None,
            env={**os.environ, "PYTHONPATH": tmpdir},
        )
        passed = r.returncode == 0
        return SandboxResult(all_passed=passed, report=r.stdout + r.stderr)
    except subprocess.TimeoutExpired:
        return SandboxResult(
            all_passed=False, report="", error="subprocess sandbox timeout"
        )
    except Exception as e:
        return SandboxResult(all_passed=False, report="", error=str(e))
