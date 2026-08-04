#!/usr/bin/env python3
"""
Export NOW Index data to a static JSON file for GitHub Pages hosting.

The Momentum Please site normally relies on the FastAPI backend for all data.
GitHub Pages cannot run Python, so this script pre-computes the full dataset
(scored assets, leaderboards, stats, per-company profiles with history) into a
single static_data/now_data.json. The frontend then falls back to this file
when the live API is unavailable.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure we can import from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import (
    NOWScorer, AssetClass, AssetRegistry, SimulatedDataProvider,
    register_default_custom_factors,
)
from engine.ranking import Ranker
from database import SQLiteStore


def export_static(output_path: str = "static_data/now_data.json") -> Path:
    """Generate the complete static dataset for the website."""
    print("=" * 60)
    print("NOW Index — Static Export")
    print("=" * 60)

    # Initialize engine (mirrors api/main.py)
    scorer = NOWScorer()
    registry = AssetRegistry()
    data_provider = SimulatedDataProvider()
    ranker = Ranker(scorer, registry, data_provider)
    store = SQLiteStore("data/now_index.db")

    # Register custom factors
    from engine.factors import FactorRegistry
    factor_registry = FactorRegistry()
    register_default_custom_factors(factor_registry)

    # Seed and score
    seeded = registry.seed_default_assets()
    print(f"Seeded {seeded} assets")
    scored_count = ranker.refresh()
    print(f"Scored {scored_count} assets")

    scores = ranker.get_all_scores()
    scored_list = [s.to_dict() for s in scores]

    # Save a fresh snapshot to the DB (for history + reports)
    try:
        store.save_snapshot(scored_list)
        print("Snapshot saved to database")
    except Exception as exc:
        print(f"Note: could not save DB snapshot: {exc}")

    # ─── Stats ────────────────────────────────────────────────────────────
    avg_score = sum(s["score"] for s in scored_list) / len(scored_list) if scored_list else 0
    top_score = max((s["score"] for s in scored_list), default=0)
    top_ticker = scored_list[0]["ticker"] if scored_list else None

    distribution = {
        "excellent_90_100": sum(1 for s in scored_list if s["score"] >= 90),
        "strong_80_89": sum(1 for s in scored_list if 80 <= s["score"] < 90),
        "good_70_79": sum(1 for s in scored_list if 70 <= s["score"] < 80),
        "fair_60_69": sum(1 for s in scored_list if 60 <= s["score"] < 70),
        "moderate_50_59": sum(1 for s in scored_list if 50 <= s["score"] < 60),
        "weak_below_50": sum(1 for s in scored_list if s["score"] < 50),
    }

    stats = {
        "total_assets": len(scored_list),
        "avg_score": round(avg_score, 2),
        "top_score": round(top_score, 2),
        "top_ticker": top_ticker,
        "distribution": distribution,
        "asset_class_breakdown": {
            ac.value: registry.count(ac) for ac in AssetClass
        },
        "last_refresh": datetime.now(timezone.utc).isoformat(),
    }

    # ─── Leaderboards ─────────────────────────────────────────────────────
    leaderboard = {
        "top_10": [s.to_dict() for s in ranker.get_top(10)],
        "top_25": [s.to_dict() for s in ranker.get_top(25)],
        "top_50": [s.to_dict() for s in ranker.get_top(50)],
        "top_100": [s.to_dict() for s in ranker.get_top(100)],
        "most_improved_today": [s.to_dict() for s in ranker.get_most_improved("daily", 10)],
        "most_improved_week": [s.to_dict() for s in ranker.get_most_improved("weekly", 10)],
        "most_improved_month": [s.to_dict() for s in ranker.get_most_improved("monthly", 10)],
        "highest_quality": [s.to_dict() for s in ranker.get_best_in_factor("quality", 10)],
        "highest_value": [s.to_dict() for s in ranker.get_best_in_factor("value", 10)],
        "highest_growth": [s.to_dict() for s in ranker.get_best_in_factor("growth", 10)],
        "highest_momentum": [s.to_dict() for s in ranker.get_best_in_factor("momentum", 10)],
        "lowest_risk": [s.to_dict() for s in ranker.get_best_in_factor("low_risk", 10)],
        "most_undervalued": [s.to_dict() for s in ranker.get_best_in_factor("undervalued", 10)],
        "best_long_term": [s.to_dict() for s in ranker.get_best_in_factor("long_term", 10)],
        "best_dividend": [s.to_dict() for s in ranker.get_best_in_factor("dividend", 10)],
        "best_innovation": [s.to_dict() for s in ranker.get_best_in_factor("innovation", 10)],
        "best_financial_strength": [s.to_dict() for s in ranker.get_best_in_factor("financial_strength", 10)],
    }

    # ─── Company profiles (with history) ──────────────────────────────────
    companies = {}
    for score in scored_list:
        asset = registry.get_by_ticker(score["ticker"])
        if asset is None:
            continue
        history = store.get_history(score["asset_id"], days=365)
        if not history:
            # Generate a small synthetic history so charts render
            history = _synthetic_history(score, store, days=90)

        companies[score["ticker"]] = {
            "profile": asset,
            "now_score": score,
            "history": history,
        }

    # ─── Health ───────────────────────────────────────────────────────────
    health = {
        "status": "ok",
        "version": "1.0.0",
        "assets_count": len(scored_list),
        "last_refresh": stats["last_refresh"],
        "timestamp": stats["last_refresh"],
    }

    # ─── Assemble payload ─────────────────────────────────────────────────
    payload = {
        "source": "NOW Index Static Export",
        "generated_at": stats["last_refresh"],
        "health": health,
        "stats": stats,
        "leaderboard": leaderboard,
        "companies": companies,
        "all_scores": scored_list,
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Exported {len(scored_list)} scored assets to {out}")
    print(f"  - Stats keys: {len(stats)}")
    print(f"  - Leaderboard categories: {len(leaderboard)}")
    print(f"  - Company profiles: {len(companies)}")
    return out


def _synthetic_history(score, store, days: int = 90) -> list[dict]:
    """Build a plausible score history so the company chart isn't empty on first deploy."""
    import random
    rng = random.Random(hash(score["ticker"]) & 0xFFFFFFFF)
    base = max(score["score"] - rng.uniform(5, 15), 1.0)
    history = []
    now = datetime.now(timezone.utc)
    for i in range(days, 0, -1):
        ts = (now - timedelta(days=i)).isoformat()
        drift = (score["score"] - base) * (1 - i / days)
        noise = rng.uniform(-0.8, 0.8)
        history.append({
            "timestamp": ts,
            "score": round(max(min(base + drift + noise, 100), 0), 2),
            "rank": None,
        })
    history.append({
        "timestamp": now.isoformat(),
        "score": score["score"],
        "rank": score["rank"],
    })
    return history


if __name__ == "__main__":
    export_static()

