#!/usr/bin/env python3
"""Wrapper: run loser-cohort event scanner from repo root."""
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(
    str(ROOT / "backtests/elliott_fibo/run_loser_cohort_event_scanner.py"),
    run_name="__main__",
)
