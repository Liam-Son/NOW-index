#!/usr/bin/env python3
"""
Validation script — Runs quality checks on the NOW Index data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import NOWScorer, AssetRegistry, SimulatedDataProvider
from engine.ranking import Ranker
from database import SQLiteStore


def validate():
    errors = []
    warnings = []

    # 1. Check database
    store = SQLiteStore("data/now_index.db")
    scores = store.get_latest_snapshot()
    if not scores:
        warnings.append("No scores in database yet")
    else:
        print(f"✓ Database has {len(scores)} scores")

        # Check for NaN/Inf scores
        for s in scores:
            if s.get("score") is None or s["score"] < 0 or s["score"] > 100:
                errors.append(f"Invalid score {s.get('score')} for {s.get('ticker')}")

    # 2. Check scoring engine
    scorer = NOWScorer()
    registry = AssetRegistry()
    data_provider = SimulatedDataProvider()
    ranker = Ranker(scorer, registry, data_provider)

    registry.seed_default_assets()
    ranker.refresh()
    all_scores = ranker.get_all_scores()

    if not all_scores:
        errors.append("Scoring engine produced no results")
    else:
        print(f"✓ Scoring engine scored {len(all_scores)} assets")

        # Check score distribution
        scores_above_90 = sum(1 for s in all_scores if s.score >= 90)
        scores_below_10 = sum(1 for s in all_scores if s.score <= 10)
        if scores_above_90 == 0:
            warnings.append("No assets with score >= 90 (possible scoring issue)")
        if scores_below_10 > 0:
            warnings.append(f"{scores_below_10} assets with score <= 10 (possible edge case)")

        # Check ranking integrity
        for i, s in enumerate(all_scores):
            if s.rank != i + 1:
                errors.append(f"Rank mismatch: {s.ticker} should be #{i + 1} but is #{s.rank}")

    # 3. Report
    print(f"\n{'='*40}")
    print(f"Validation Results")
    print(f"{'='*40}")
    print(f"Errors:   {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    for e in errors:
        print(f"  ✗ ERROR: {e}")
    for w in warnings:
        print(f"  ⚠ WARNING: {w}")

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(validate())
