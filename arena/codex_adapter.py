"""
codex_adapter.py — the ONLY file in this project that touches an LLM.

All calls to Codex go through call_codex(). Nothing else in the codebase
imports or invokes any LLM API.

# CODEX BINARY
  Set the CODEX_BIN environment variable to the full path of your Codex CLI.
  If unset, 'codex' must be on PATH.
  Example: export CODEX_BIN=/Applications/Codex.app/Contents/Resources/codex

# SECURITY WARNING — --dangerously-bypass-approvals-and-sandbox
  This flag disables Codex's built-in approval prompts and sandbox isolation.
  It is intentional here because our prompts never ask Codex to execute shell
  commands. If you adapt this code, review whether this flag is appropriate for
  your prompts. Always run in an isolated environment: Docker container,
  throwaway VM, or a dedicated unprivileged user. Never use this flag with
  prompts that could instruct the model to run arbitrary shell commands.

# MOCK MODE
  Set env var ARENA_MOCK=1 to bypass real Codex calls (useful for
  testing gate/judge/orchestrator without a Codex install).
  Attacker mock: returns a trivially off-by-one tampered JSON.
  Defender mock: returns alternating labels with confidence 60.
"""

import json
import os
import re
import subprocess
from dataclasses import dataclass


# Codex binary: override via CODEX_BIN env var; falls back to 'codex' on PATH.
_CODEX_BIN: str = os.environ.get("CODEX_BIN", "codex")

# SECURITY: --dangerously-bypass-approvals-and-sandbox disables Codex approval
# prompts and sandbox protection. Safe here (prompts never exec shell commands),
# but run in an isolated environment. See module docstring for details.
CMD_PREFIX: list[str] = [_CODEX_BIN, "exec", "--dangerously-bypass-approvals-and-sandbox"]

_MOCK_MODE: bool = os.environ.get("ARENA_MOCK", "").strip() not in ("", "0", "false")
_mock_defender_toggle: bool = False  # alternates label between calls


@dataclass
class CodexResult:
    raw: str
    ok: bool
    error: str = ""


def call_codex(prompt: str, *, timeout: int = 300) -> CodexResult:
    """
    Invoke Codex CLI once, non-interactively, and return raw stdout.
    Callers should use parse_json_block() on .raw.
    On timeout or non-zero exit, .ok is False and .error is set.
    """
    if _MOCK_MODE:
        return _mock_codex(prompt)

    cmd = CMD_PREFIX + [prompt]
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if p.returncode != 0:
            return CodexResult(
                raw=p.stdout,
                ok=False,
                error=f"codex exit {p.returncode}: {p.stderr[:300]}",
            )
        return CodexResult(raw=p.stdout, ok=True)
    except FileNotFoundError:
        return CodexResult(
            raw="",
            ok=False,
            error=(
                "codex CLI not found. Install it and verify CMD_PREFIX "
                "in arena/codex_adapter.py, or set ARENA_MOCK=1 for dry runs."
            ),
        )
    except subprocess.TimeoutExpired:
        return CodexResult(raw="", ok=False, error="codex call timed out")
    except Exception as e:
        return CodexResult(raw="", ok=False, error=str(e))


def parse_json_block(raw: str) -> dict:
    """
    Strip ```json fences and surrounding prose, then parse the first
    JSON object found. Raises ValueError if no object is found or if
    JSON is malformed — callers record this as parse_error.
    """
    s = raw.strip()
    # Remove code fences
    s = re.sub(r"```json\s*", "", s)
    s = re.sub(r"```\s*", "", s)
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in codex output: {raw[:300]!r}")
    return json.loads(s[start : end + 1])


# ── Mock implementations ─────────────────────────────────────────────────────

def _mock_codex(prompt: str) -> CodexResult:
    """
    Returns canned JSON so the full pipeline can be exercised without Codex.
    Detects role by looking for keywords in the prompt.
    """
    if '"injected_bug"' in prompt or "偽造師" in prompt or "attacker" in prompt.lower():
        raw = _mock_attacker_response()
    else:
        raw = _mock_defender_response()
    return CodexResult(raw=raw, ok=True)


def _mock_attacker_response() -> str:
    # Injects an off-by-one: loop goes one index too far
    code = (
        "def binary_search(arr, target):\n"
        "    lo, hi = 0, len(arr)  # BUG: should be len(arr)-1\n"
        "    result = -1\n"
        "    while lo <= hi:\n"
        "        mid = (lo + hi) // 2\n"
        "        if arr[mid] == target:\n"
        "            result = mid\n"
        "            hi = mid - 1\n"
        "        elif arr[mid] < target:\n"
        "            lo = mid + 1\n"
        "        else:\n"
        "            hi = mid - 1\n"
        "    return result\n"
    )
    return json.dumps({
        "code": code,
        "injected_bug": {
            "class": "off_by_one",
            "location_hint": "binary_search, initial hi bound, line 2",
            "rationale": (
                "Setting hi=len(arr) instead of len(arr)-1 causes an "
                "IndexError on arr[mid] when arr is non-empty and lo==hi==len(arr), "
                "but this path is not exercised by the public tests which only "
                "search for present elements in small lists."
            ),
        },
    })


def _mock_defender_response() -> str:
    global _mock_defender_toggle
    label = "tampered" if _mock_defender_toggle else "clean"
    _mock_defender_toggle = not _mock_defender_toggle
    return json.dumps({
        "label": label,
        "confidence": 60,
        "suspect_lines": [2] if label == "tampered" else [],
        "reason": "Mock defender alternates labels for testing.",
    })
