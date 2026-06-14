"""
Deterministic gate: public-test passage check.
NO LLM imports. This file must remain import-graph-clean.
"""
from .sandbox import run_pytest, SandboxResult


def passes_public_tests(
    task,
    code: str,
    *,
    use_docker: bool = True,
    cpu_sec: int = 30,
    mem_mb: int = 512,
    timeout: int = 60,
) -> tuple[bool, SandboxResult]:
    """
    Returns (passed: bool, result: SandboxResult).
    A valid_attack requires passed == True.
    """
    result = run_pytest(
        code,
        task.public_tests_path,
        use_docker=use_docker,
        cpu_sec=cpu_sec,
        mem_mb=mem_mb,
        timeout=timeout,
    )
    return result.all_passed, result
