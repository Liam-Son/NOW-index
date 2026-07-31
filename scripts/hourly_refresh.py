#!/usr/bin/env python3
"""
Hourly Refresh Script — Downloads new data, recalculates scores,
updates rankings, and commits results.
"""

import sys
import os
from pathlib import Path

# Ensure we can import from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import NOWScorer, AssetRegistry, SimulatedDataProvider
from engine.ranking import Ranker
from database import SQLiteStore


def main():
    print("=" * 60)
    print("NOW Index — Hourly Refresh")
    print("=" * 60)

    # Initialize engine
    scorer = NOWScorer()
    registry = AssetRegistry()
    data_provider = SimulatedDataProvider()
    ranker = Ranker(scorer, registry, data_provider)
    store = SQLiteStore("data/now_index.db")

    # Load registry
    count = registry.seed_default_assets()
    print(f"Loaded {count} assets")

    # Refresh rankings
    scored = ranker.refresh()
    print(f"Scored {scored} assets")

    # Save snapshot
    scores = ranker.get_all_scores()
    saved = store.save_snapshot([s.to_dict() for s in scores])
    print(f"Saved {saved} scores to database")

    # Print summary
    if scores:
        print(f"\nTop 5:")
        for s in scores[:5]:
            print(f"  #{s.rank} {s.ticker:6s} {s.score:6.1f}  {s.name}")

        print(f"\nTop score: {scores[0].ticker} ({scores[0].score:.1f})")
        print(f"Avg score: {sum(s.score for s in scores) / len(scores):.1f}")
        print(f"Total assets: {len(scores)}")

    print("\n✓ Hourly refresh complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
