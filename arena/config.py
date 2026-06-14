"""
config.py — load and validate config.yaml.
All other modules import their settings from here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CodexConfig:
    timeout_sec: int = 300
    attempts_per_trial: int = 1


@dataclass
class MemoryConfig:
    max_items: int = 20


@dataclass
class SandboxConfig:
    use_docker: bool = True
    cpu_sec: int = 30
    mem_mb: int = 512


@dataclass
class Config:
    rounds: int = 30
    tasks_dir: str = "tasks/"
    clean_samples_per_round: int = 1
    codex: CodexConfig = field(default_factory=CodexConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    seeds: list[int] = field(default_factory=lambda: [1, 2, 3])

    # resolved at load time
    tasks_dir_abs: Path = field(init=False)

    def __post_init__(self):
        self.tasks_dir_abs = Path(self.tasks_dir).resolve()

    def validate(self):
        assert self.rounds >= 1, "rounds must be >= 1"
        assert self.clean_samples_per_round >= 0
        assert self.codex.attempts_per_trial >= 1
        assert self.memory.max_items >= 0
        assert self.sandbox.cpu_sec >= 1
        assert self.sandbox.mem_mb >= 64
        assert len(self.seeds) >= 1


def load(path: str | Path = "config.yaml") -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with open(path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    codex_raw = raw.get("codex", {})
    mem_raw = raw.get("memory", {})
    sb_raw = raw.get("sandbox", {})

    cfg = Config(
        rounds=raw.get("rounds", 30),
        tasks_dir=raw.get("tasks_dir", "tasks/"),
        clean_samples_per_round=raw.get("clean_samples_per_round", 1),
        codex=CodexConfig(
            timeout_sec=codex_raw.get("timeout_sec", 300),
            attempts_per_trial=codex_raw.get("attempts_per_trial", 1),
        ),
        memory=MemoryConfig(
            max_items=mem_raw.get("max_items", 20),
        ),
        sandbox=SandboxConfig(
            use_docker=sb_raw.get("use_docker", True),
            cpu_sec=sb_raw.get("cpu_sec", 30),
            mem_mb=sb_raw.get("mem_mb", 512),
        ),
        seeds=raw.get("seeds", [1, 2, 3]),
    )
    cfg.validate()
    return cfg
