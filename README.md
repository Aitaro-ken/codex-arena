# Codex Adversarial Arena

An adversarial self-play experiment: two Codex agents compete over 30 rounds. The **attacker** injects subtle bugs into algorithmic tasks; the **defender** inspects the resulting code and decides whether it is clean or tampered. A deterministic test suite acts as judge.

The central finding: across 703 scored trials, `attacker_win = 0`. Effective bugs are always caught; bugs that evade detection are not real spec violations. Effectiveness and stealth are negatively correlated (r ≈ −0.55).

---

## Requirements

- Python 3.10+
- Codex CLI (OpenAI) — **required for real runs only**; mock mode works without it
- Docker — **required for sandboxed execution**; disable in `config.yaml` for local-only runs

```
pip install -r requirements.txt
```

---

## Quick start

### Mock run (no Codex, no Docker)

Verifies the full pipeline — gate, judge, orchestrator, metrics, visualisation — without any LLM or sandbox:

```bash
python3 run_arena.py --mock --rounds 2
```

Expected output: a `runs/<timestamp>/` directory with `results.jsonl`, `metrics.json`, and figures.

### Real run

1. Point the runner at your Codex binary:

   ```bash
   cp .env.example .env
   # edit .env: set CODEX_BIN=/path/to/codex
   source .env
   ```

   Or export directly:

   ```bash
   export CODEX_BIN=/Applications/Codex.app/Contents/Resources/codex
   ```

   If `codex` is already on your PATH, skip this step.

2. Confirm Docker is running (required for sandboxed test execution).

3. Run:

   ```bash
   python3 run_arena.py --rounds 30
   ```

---

## ⚠️ Security warning — `--dangerously-bypass-approvals-and-sandbox`

This project passes `--dangerously-bypass-approvals-and-sandbox` to the Codex CLI. **This flag disables Codex's built-in approval prompts and sandbox isolation.**

It is intentional here because the prompts sent to Codex never ask it to execute shell commands — they ask it to write or review Python code, and all code execution happens inside Docker. However:

- **Do not use this flag with prompts that could instruct the model to run arbitrary shell commands.**
- **Always run in an isolated environment**: Docker container, throwaway VM, or a dedicated unprivileged user account.
- **Never run against untrusted task files or prompts** without auditing them first.

If you adapt this code for other purposes, review whether this flag is appropriate for your prompt design before enabling it.

---

## Project layout

```
run_arena.py          # entry point
config.yaml           # rounds, seeds, sandbox settings
tasks/                # one subdirectory per task
    binary_search/    # spec.md, clean_solution.py, public_tests.py, hidden_tests.py
    moving_average/
    stack/
    variance/
prompts/
    attacker_system.md
    defender_system.md
arena/
    orchestrator.py   # round loop
    attacker.py       # LLM attacker wrapper
    defender.py       # LLM defender wrapper
    codex_adapter.py  # sole LLM interface (set CODEX_BIN here)
    gate.py           # public test gate
    judge.py          # hidden test judge
    sandbox.py        # Docker / subprocess test runner
    metrics.py        # aggregate statistics
    viz.py            # matplotlib figures
    record.py         # JSONL recorder
    memory.py         # per-role episodic memory
    config.py         # config.yaml loader
runs/                 # experiment output (git-ignored)
```

---

## Configuration

`config.yaml` controls all experimental parameters:

| Key | Default | Description |
|-----|---------|-------------|
| `rounds` | 30 | Number of rounds per seed |
| `seeds` | [1, 2, 3] | Random seeds (one full run per seed) |
| `tasks_dir` | tasks/ | Directory scanned for task subdirectories |
| `clean_samples_per_round` | 1 | Clean (unmodified) samples mixed in per round |
| `codex.timeout_sec` | 300 | Per-call Codex timeout |
| `memory.max_items` | 20 | Episodic memory depth; 0 disables memory |
| `sandbox.use_docker` | true | Use Docker for test isolation |
| `sandbox.cpu_sec` | 30 | CPU time limit per sandbox run |
| `sandbox.mem_mb` | 512 | Memory limit per sandbox run |

---

## Adding a task

Create `tasks/<name>/` with four files:

| File | Role |
|------|------|
| `spec.md` | Natural-language specification shown to both agents |
| `clean_solution.py` | Reference implementation (gate baseline) |
| `public_tests.py` | Tests the attacker must pass (the gate) |
| `hidden_tests.py` | Tests used by the judge to confirm a real bug |

The orchestrator picks up new tasks automatically via directory scan.

---

## Output

Each run produces `runs/<timestamp>/`:

```
results.jsonl    # one JSON record per trial
metrics.json     # aggregate and per-round statistics
figures/
    arms_race.png
    calibration.png
    confusion.png
    per_task.png
```

---

## Reproducibility note

All randomness is seeded via `config.yaml → seeds`. LLM outputs are not deterministic, so exact trial-level results will differ between runs. The aggregate structure (attacker_wins = 0, negative effectiveness–stealth correlation) has been replicated across two independent experimental acts with different task sets.
