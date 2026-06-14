#!/usr/bin/env python3
"""
run_arena.py — entry point for a full experimental run.

Usage:
  python run_arena.py [--config config.yaml] [--rounds N] [--mock]

  --mock   sets ARENA_MOCK=1 (bypasses Codex; useful for pipeline testing)
"""
import argparse
import os
import sys
import time
from pathlib import Path

# ensure repo root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from arena import config as cfg_module
from arena import metrics as metrics_module
from arena import orchestrator, record, viz


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--rounds", type=int, default=None,
                        help="Override rounds from config")
    parser.add_argument("--mock", action="store_true",
                        help="Run in mock mode (no real Codex calls)")
    args = parser.parse_args()

    if args.mock:
        os.environ["ARENA_MOCK"] = "1"
        print("[MOCK MODE] Codex calls will be simulated.")

    cfg = cfg_module.load(args.config)
    if args.rounds is not None:
        cfg.rounds = args.rounds

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    runs_root = Path("runs") / timestamp

    all_records: list[dict] = []

    for seed in cfg.seeds:
        run_dir = runs_root / f"seed_{seed}"
        print(f"\n{'#'*70}")
        print(f"  SEED {seed}")
        print(f"{'#'*70}")
        orchestrator.run(cfg, run_dir, seed)

        recs = record.load_results(run_dir / "results.jsonl")
        all_records.extend(recs)

    # Aggregate metrics over all seeds
    metrics = metrics_module.compute(all_records)

    import json
    metrics_path = runs_root / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"\nMetrics: {metrics_path}")

    # Print summary
    print("\n── Summary ──────────────────────────────────")
    print(f"  Scored trials   : {metrics.get('n_scored', 0)}")
    print(f"  Gate pass rate  : {metrics.get('attack_gate_pass_rate', 0):.1%}")
    print(f"  Real bug rate   : {metrics.get('real_bug_rate', 0):.1%}")
    print(f"  Evasion rate    : {metrics.get('evasion_rate', 0):.1%}")
    print(f"  Attacker win    : {metrics.get('attacker_win_rate', 0):.1%}")
    print(f"  Def precision   : {metrics.get('defender_precision', 0):.1%}")
    print(f"  Def recall      : {metrics.get('defender_recall', 0):.1%}")
    print(f"  Def F1          : {metrics.get('defender_f1', 0):.1%}")

    # Generate figures
    figures_dir = runs_root / "figures"
    viz.generate_all(metrics, figures_dir)


if __name__ == "__main__":
    main()
