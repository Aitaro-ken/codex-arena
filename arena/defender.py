"""
Defender: inspect code samples via Codex.
Only interacts with LLM through codex_adapter.call_codex().
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .codex_adapter import call_codex, parse_json_block, CodexResult


_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "defender_system.md"
_SYSTEM_PROMPT: str = _SYSTEM_PROMPT_PATH.read_text()


@dataclass
class DefenderOutput:
    label: str            # "clean" | "tampered"
    confidence: int       # 0-100
    suspect_lines: list[int]
    reason: str
    raw: str = ""
    error: str = ""


def run(
    code: str,
    spec: str,
    public_tests: str,
    memory_text: str,
    *,
    timeout: int = 300,
) -> DefenderOutput:
    """
    Ask Codex to classify the code as clean or tampered.
    Returns DefenderOutput; on failure sets .error and .label = "parse_error".
    """
    prompt = _build_prompt(code, spec, public_tests, memory_text)
    result: CodexResult = call_codex(prompt, timeout=timeout)

    if not result.ok:
        return DefenderOutput(
            label="parse_error", confidence=-1, suspect_lines=[], reason="",
            raw=result.raw, error=result.error,
        )

    try:
        parsed = parse_json_block(result.raw)
    except (ValueError, Exception) as e:
        return DefenderOutput(
            label="parse_error", confidence=-1, suspect_lines=[], reason="",
            raw=result.raw, error=f"parse_error: {e}",
        )

    label = parsed.get("label", "")
    if label not in ("clean", "tampered"):
        return DefenderOutput(
            label="parse_error", confidence=-1, suspect_lines=[], reason="",
            raw=result.raw, error=f"parse_error: invalid label {label!r}",
        )

    confidence = int(parsed.get("confidence", -1))
    suspect_lines = [int(ln) for ln in parsed.get("suspect_lines", [])]
    reason = parsed.get("reason", "")

    return DefenderOutput(
        label=label,
        confidence=max(0, min(100, confidence)),
        suspect_lines=suspect_lines,
        reason=reason,
        raw=result.raw,
    )


def _build_prompt(code: str, spec: str, public_tests: str, memory_text: str) -> str:
    memory_section = (
        f"\nMEMORY:\n{memory_text}" if memory_text.strip() else "\nMEMORY:\n(none yet)"
    )
    return (
        f"{_SYSTEM_PROMPT}\n\n"
        f"SPEC:\n{spec}\n\n"
        f"PUBLIC_TESTS:\n{public_tests}\n\n"
        f"CODE_UNDER_REVIEW:\n{code}"
        f"{memory_section}"
    )
