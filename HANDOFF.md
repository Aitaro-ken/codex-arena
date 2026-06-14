# Codex Adversarial Arena — Handoff

## What this project is

Adversarial self-play experiment where one Codex instance (attacker) injects bugs that pass public tests but violate the spec, and another Codex instance (defender) tries to detect them. Judge and gate are deterministic code only — no LLM in the scoring pipeline. This is **not** a GAN; there is no gradient signal, only win/loss outcomes per round.

Entry point: `python3 run_arena.py`

---

## Act 1 results (run: `runs/20260613_120354/`)

- **537 trials** across 3 seeds × 30 rounds × 3 tasks
- **attacker_win = 0** (0.0%) — defender dominated completely
- Defender: precision 100%, recall 91%, F1 95.3%
- Gate pass rate: 99.3% (attacker's bugs mostly survived the public-test gate)

**Why the arms race never happened:**

The attacker converged on `float_comparison`-style bugs (off-by-epsilon, wrong rounding), but this class is nearly ineffective on `moving_average` — the task's public tests catch exact-value mismatches. Per-task evasion rates tell the story:

| Task           | Evasion rate |
|----------------|-------------|
| moving_average | **40.4%**   |
| stack          | 3.0%        |
| binary_search  | 1.3%        |

Moving average had the highest evasion (attacker succeeded 40% of the time there), but `attacker_win` requires evading AND the defender failing — and the defender caught those anyway. The attacker's bug vocabulary was mismatched to the task space overall.

---

## Act 2 — what to do next

**Goal:** replace or augment tasks so the attacker has a genuine winning path.

**Planned new task:** `tasks/variance/` — population vs. sample variance (`1/N` vs `1/(N-1)`). Float sensitivity is inherent, public tests are easy to make non-trivial, and a plausible bug (dividing by N instead of N-1) passes naive tests but fails on edge cases the defender can probe.

**Key principle:** the public test gate must be _hard to pass accidentally_ but the secret judge must be _exploitable_ by a subtle bug. That tension is what was missing in Act 1.

**Harness and prompts: do not change.** Only swap or add tasks under `tasks/`.

**Before running:**
1. Design `tasks/variance/` (or another task with a clear attacker win path)
2. Review the task spec, public tests, and judge logic manually
3. Run a 2-round mock first: `ARENA_MOCK=1 python3 run_arena.py --rounds 2`
4. Only then do a full seeded run

---

## Constraints (non-negotiable)

- Public tests must not be trivially weak — they should catch obvious wrong answers
- Judge is deterministic code; no LLM calls allowed in `gate.py` or `judge.py`
- Always review new tasks before running a full experiment (no blind runs)

---

## Directory structure

```
codex-arena/
├── run_arena.py          # entry point
├── config.yaml           # rounds, seeds, sandbox mode
├── SPEC.md               # full project spec + safety checklist
├── arena/
│   ├── attacker.py       # prompt generation + output parse
│   ├── defender.py
│   ├── codex_adapter.py  # only file that touches LLM; ARENA_MOCK=1 for mock
│   ├── gate.py           # deterministic public-test gate
│   ├── judge.py          # deterministic secret judge
│   ├── orchestrator.py   # round loop
│   ├── memory.py         # per-role memory / lesson accumulation
│   ├── metrics.py
│   └── viz.py            # generates 4 figures per run
├── tasks/
│   ├── binary_search/
│   ├── stack/
│   └── moving_average/
├── prompts/              # attacker / defender prompt templates
└── runs/
    └── 20260613_120354/  # Act 1 full-run results
        ├── metrics.json  # aggregate + per_task + per_round stats
        ├── figures/      # 4 plots
        ├── seed_1/
        ├── seed_2/
        └── seed_3/
```

---

## Quick commands

```bash
# Mock run (no real LLM, fast sanity check)
ARENA_MOCK=1 python3 run_arena.py --rounds 2

# Full run (requires Codex CLI configured in codex_adapter.py CMD_PREFIX)
python3 run_arena.py
```
