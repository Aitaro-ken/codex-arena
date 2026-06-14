"""
orchestrator.py — round loop, sample pool construction, co-evolution.

This is the main entry point for one experimental run (one seed).
No direct LLM calls here; all LLM access goes through attacker/defender modules.
"""
from __future__ import annotations

import dataclasses
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from . import attacker, defender
from .config import Config
from .gate import passes_public_tests
from .judge import fails_hidden_tests, score
from .memory import RoleMemory, attacker_lessons, defender_lessons
from .record import Recorder


@dataclass
class Task:
    task_id: str
    spec: str
    public_tests_src: str
    clean_code: str
    public_tests_path: str
    hidden_tests_path: str


@dataclass
class Sample:
    task_id: str
    code: str
    truth: str              # "clean" | "tampered"
    injected: dict | None   # attacker metadata; hidden from defender


def load_tasks(tasks_dir: Path) -> list[Task]:
    tasks = []
    for task_dir in sorted(tasks_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        spec_path = task_dir / "spec.md"
        clean_path = task_dir / "clean_solution.py"
        pub_path = task_dir / "public_tests.py"
        hid_path = task_dir / "hidden_tests.py"
        if not all(p.exists() for p in [spec_path, clean_path, pub_path, hid_path]):
            continue
        tasks.append(Task(
            task_id=task_dir.name,
            spec=spec_path.read_text(),
            public_tests_src=pub_path.read_text(),
            clean_code=clean_path.read_text(),
            public_tests_path=str(pub_path),
            hidden_tests_path=str(hid_path),
        ))
    return tasks


def run(cfg: Config, run_dir: Path, seed: int) -> None:
    rng = random.Random(seed)
    tasks = load_tasks(cfg.tasks_dir_abs)
    if not tasks:
        raise RuntimeError(f"No tasks found in {cfg.tasks_dir_abs}")

    atk_mem = RoleMemory(max_items=cfg.memory.max_items)
    def_mem = RoleMemory(max_items=cfg.memory.max_items)

    sb_kwargs = dict(
        use_docker=cfg.sandbox.use_docker,
        cpu_sec=cfg.sandbox.cpu_sec,
        mem_mb=cfg.sandbox.mem_mb,
        timeout=cfg.sandbox.cpu_sec * 2 + 10,
    )

    with Recorder(run_dir) as rec:
        for round_num in range(1, cfg.rounds + 1):
            print(f"\n{'='*60}")
            print(f"  Round {round_num}/{cfg.rounds}  seed={seed}")
            print(f"{'='*60}")

            # ── Attack phase ─────────────────────────────────────────────
            pool: list[Sample] = []

            for task in tasks:
                for _attempt in range(cfg.codex.attempts_per_trial):
                    print(f"  [ATK] task={task.task_id} round={round_num}")
                    atk_out = attacker.run(
                        spec=task.spec,
                        public_tests=task.public_tests_src,
                        clean_code=task.clean_code,
                        memory_text=atk_mem.render(),
                        timeout=cfg.codex.timeout_sec,
                    )

                    base_record = {
                        "round": round_num,
                        "seed": seed,
                        "task_id": task.task_id,
                        "role": "attacker",
                        "injected_class": atk_out.injected_bug.get("class", ""),
                        "injected_location": atk_out.injected_bug.get("location_hint", ""),
                    }

                    if atk_out.error:
                        rec.append({**base_record, "status": "attacker_error",
                                     "error": atk_out.error})
                        continue

                    passed, gate_result = passes_public_tests(task, atk_out.code, **sb_kwargs)
                    if not passed:
                        rec.append({**base_record, "status": "gate_rejected",
                                     "gate_report": gate_result.report[:500]})
                        print(f"    gate REJECTED")
                        continue

                    pool.append(Sample(
                        task_id=task.task_id,
                        code=atk_out.code,
                        truth="tampered",
                        injected=atk_out.injected_bug,
                    ))
                    print(f"    gate PASSED → added to pool")

            # Mix in clean samples ────────────────────────────────────────
            for task in tasks:
                for _ in range(cfg.clean_samples_per_round):
                    pool.append(Sample(
                        task_id=task.task_id,
                        code=task.clean_code,
                        truth="clean",
                        injected=None,
                    ))

            rng.shuffle(pool)
            print(f"  Pool size: {len(pool)} ({sum(s.truth=='tampered' for s in pool)} tampered, "
                  f"{sum(s.truth=='clean' for s in pool)} clean)")

            # ── Defence phase ─────────────────────────────────────────────
            verdicts: list[dict] = []
            for sample in pool:
                task = next(t for t in tasks if t.task_id == sample.task_id)
                print(f"  [DEF] task={sample.task_id} truth={sample.truth}")
                def_out = defender.run(
                    code=sample.code,
                    spec=task.spec,
                    public_tests=task.public_tests_src,
                    memory_text=def_mem.render(),
                    timeout=cfg.codex.timeout_sec,
                )
                verdicts.append({
                    "label": def_out.label,
                    "confidence": def_out.confidence,
                    "suspect_lines": def_out.suspect_lines,
                    "reason": def_out.reason,
                    "error": def_out.error,
                })
                print(f"    verdict={def_out.label} conf={def_out.confidence}")

            # ── Judge phase (deterministic) ───────────────────────────────
            round_scores: list[dict] = []
            for sample, verdict in zip(pool, verdicts):
                task = next(t for t in tasks if t.task_id == sample.task_id)

                if verdict["label"] == "parse_error":
                    rec.append({
                        "round": round_num, "seed": seed,
                        "task_id": sample.task_id, "status": "defender_parse_error",
                        "error": verdict["error"],
                    })
                    continue

                real_bug = False
                if sample.truth == "tampered":
                    real_bug, _ = fails_hidden_tests(task, sample.code, **sb_kwargs)

                s = score(
                    truth=sample.truth,
                    verdict=verdict,
                    real_bug=real_bug,
                    injected=sample.injected,
                )
                s.update({
                    "round": round_num,
                    "seed": seed,
                    "task_id": sample.task_id,
                    "status": "scored",
                })
                rec.append(s)
                round_scores.append(s)

                label = "WIN" if s["attacker_win"] else ("  " if s["truth"] == "clean" else "LOSS")
                print(f"    [{label}] truth={s['truth']} pred={s['pred']} "
                      f"real_bug={s['real_bug']} correct={s['correct']}")

            # ── Co-evolution: update memories ─────────────────────────────
            atk_lessons = attacker_lessons(round_scores)
            def_lessons = defender_lessons(round_scores)
            atk_mem.update(atk_lessons)
            def_mem.update(def_lessons)
            if atk_lessons:
                print(f"  ATK lessons: {atk_lessons}")
            if def_lessons:
                print(f"  DEF lessons: {def_lessons}")

    print(f"\nDone. Results: {run_dir / 'results.jsonl'}")
