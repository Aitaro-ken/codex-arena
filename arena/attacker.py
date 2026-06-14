"""
Attacker: generate tampered code via Codex.
Only interacts with LLM through codex_adapter.call_codex().
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .codex_adapter import call_codex, parse_json_block, CodexResult


_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "attacker_system.md"
_SYSTEM_PROMPT: str = _SYSTEM_PROMPT_PATH.read_text()


@dataclass
class AttackerOutput:
    code: str
    injected_bug: dict        # {class, location_hint, rationale}
    raw: str = ""
    error: str = ""


def run(
    spec: str,
    public_tests: str,
    clean_code: str,
    memory_text: str,
    *,
    timeout: int = 300,
) -> AttackerOutput:
    """
    Ask Codex to inject one bug into clean_code.
    Returns AttackerOutput; on any failure sets .error (code is empty string).
    """
    prompt = _build_prompt(spec, public_tests, clean_code, memory_text)
    result: CodexResult = call_codex(prompt, timeout=timeout)

    if not result.ok:
        return AttackerOutput(code="", injected_bug={}, raw=result.raw, error=result.error)

    try:
        parsed = parse_json_block(result.raw)
    except (ValueError, Exception) as e:
        return AttackerOutput(
            code="", injected_bug={}, raw=result.raw,
            error=f"parse_error: {e}",
        )

    code = parsed.get("code", "")
    injected = parsed.get("injected_bug", {})

    if not code:
        return AttackerOutput(
            code="", injected_bug={}, raw=result.raw,
            error="parse_error: 'code' field missing or empty",
        )

    return AttackerOutput(code=code, injected_bug=injected, raw=result.raw)


def _build_prompt(spec: str, public_tests: str, clean_code: str, memory_text: str) -> str:
    memory_section = (
        f"\nMEMORY:\n{memory_text}" if memory_text.strip() else "\nMEMORY:\n(none yet)"
    )
    return (
        f"{_SYSTEM_PROMPT}\n\n"
        f"SPEC:\n{spec}\n\n"
        f"PUBLIC_TESTS:\n{public_tests}\n\n"
        f"CLEAN_SOLUTION:\n{clean_code}"
        f"{memory_section}"
    )
