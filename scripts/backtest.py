#!/usr/bin/env python3
"""
Backtest & Validation Benchmark — NOW Index

Reproducible accuracy benchmark for the NOW scoring engine.

Method:
  For each historical snapshot in the SQLite store, we take the scores as of
  that snapshot and treat them as a "prediction" of the NEXT snapshot. We then
  compare predicted vs actual to measure:
    - Rank persistence (how stable the ranking is between snapshots)
    - Score drift (mean absolute change in score)
    - Rank correlation (Kendall tau between consecutive snapshots)
    - Factor stability per factor dimension

This is a MECHANICAL benchmark: it validates the stability and determinism of
the scoring pipeline, not the alpha of the model. When real data is wired in
(see docs/DATA_SOURCES.md), the same harness should be re-run against live
history to measure statistical accuracy.

Usage:
    python scripts/backtest.py
    python scripts/backtest.py --min-snapshots 3
    python scripts/backtest.py --out docs/reports/backtest_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import SQLiteStore


def _kendall_tau(rank_a: dict[str, int], rank_b: dict[str, int]) -> float:
    """Compute Kendall tau-b rank correlation between two rank mappings."""
    common = [t for t in rank_a if t in rank_b]
    if len(common) < 2:
        return 0.0
    n = len(common)
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            t1, t2 = common[i], common[j]
            a_i, a_j = rank_a[t1], rank_a[t2]
            b_i, b_j = rank_b[t1], rank_b[t2]
            if (a_i - a_j) * (b_i - b_j) > 0:
                concordant += 1
            elif (a_i - a_j) * (b_i - b_j) < 0:
                discordant += 1
    total = concordant + discordant
    if total == 0:
        return 0.0
    return (concordant - discordant) / total


def load_snapshots(store) -> list[dict]:
    """Load all ordered snapshots from the store's history table."""
    conn = store._db_path
    import sqlite3
    db = sqlite3.connect(str(conn))
    cursor = db.execute(
        "SELECT timestamp, snapshot_json FROM score_snapshots ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    db.close()
    snapshots = []
    for ts, snap_json in rows:
        snapshots.append({
            "timestamp": ts,
            "scores": json.loads(snap_json),
        })
    return snapshots


def _factors_by_ticker(scores: list[dict]) -> dict[str, dict]:
    out = {}
    for s in scores:
        out[s["ticker"]] = s.get("factors", {})
    return out


def run_backtest(min_snapshots: int = 2) -> dict:
    store = SQLiteStore("data/now_index.db")
    snapshots = load_snapshots(store)

    if len(snapshots) < min_snapshots:
        return {
            "status": "insufficient_data",
            "snapshots_available": len(snapshots),
            "min_snapshots_required": min_snapshots,
            "message": (
                "Not enough historical snapshots to run a meaningful backtest. "
                "Run: python scripts/hourly_refresh.py (or scripts/export_static.py) "
                "a few times to accumulate snapshots."
            ),
        }

    scores_to_rank = lambda sc: {s["ticker"]: s["rank"] for s in sc}
    score_map = lambda sc: {s["ticker"]: s["score"] for s in sc}

    rank_taus: list[float] = []
    score_drifts: list[float] = []
    factor_drifts: dict[str, list[float]] = {}

    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]["scores"]
        curr = snapshots[i]["scores"]

        prev_ranks = scores_to_rank(prev)
        curr_ranks = scores_to_rank(curr)
        tau = _kendall_tau(prev_ranks, curr_ranks)
        rank_taus.append(tau)

        prev_scores = score_map(prev)
        curr_scores = score_map(curr)
        common = [t for t in prev_scores if t in curr_scores]
        if common:
            drift = sum(abs(curr_scores[t] - prev_scores[t]) for t in common) / len(common)
            score_drifts.append(drift)

        prev_factors = _factors_by_ticker(prev)
        curr_factors = _factors_by_ticker(curr)
        for ticker in common:
            pf = prev_factors.get(ticker, {})
            cf = curr_factors.get(ticker, {})
            for factor in set(pf) | set(cf):
                if factor == "total":
                    continue
                pv = pf.get(factor, 0.0) or 0.0
                cv = cf.get(factor, 0.0) or 0.0
                factor_drifts.setdefault(factor, []).append(abs(cv - pv))

    avg_factor_drift = {
        k: round(sum(v) / len(v), 4) for k, v in factor_drifts.items()
    }

    return {
        "status": "ok",
        "snapshots_analyzed": len(snapshots),
        "comparisons": len(rank_taus),
        "avg_rank_tau": round(sum(rank_taus) / len(rank_taus), 4) if rank_taus else 0.0,
        "min_rank_tau": round(min(rank_taus), 4) if rank_taus else 0.0,
        "avg_score_drift": round(sum(score_drifts) / len(score_drifts), 4) if score_drifts else 0.0,
        "avg_factor_drift": avg_factor_drift,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def render_markdown(result: dict) -> str:
    lines = [
        "# NOW Index — Backtest Report",
        "",
        f"**Generated:** {result.get('generated_at', 'N/A')}",
        "",
    ]
    if result.get("status") != "ok":
        lines.append(f"> ⚠️ {result.get('message', 'Insufficient data')}")
        lines.append("")
        lines.append(f"- Snapshots available: `{result.get('snapshots_available')}`")
        lines.append(f"- Minimum required: `{result.get('min_snapshots_required')}`")
        lines.append("")
        lines.append("## How to populate snapshots")
        lines.append("")
        lines.append("```bash")
        lines.append("python scripts/export_static.py   # appends a snapshot")
        lines.append("python scripts/hourly_refresh.py  # appends a snapshot")
        lines.append("```")
        return "\n".join(lines)

    lines.extend([
        f"> **Note:** This is a *mechanical stability* benchmark. It measures how "
        "deterministic and stable the scoring pipeline is between snapshots — "
        "not the predictive alpha of the model. See `docs/BACKTESTING.md`.",
        "",
        "## Snapshot statistics",
        "",
        f"- Snapshots analyzed: **`{result['snapshots_analyzed']}`**",
        f"- Consecutive comparisons: **`{result['comparisons']}`**",
        "",
        "## Rank stability",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Average Kendall tau | **{result['avg_rank_tau']}** |",
        f"| Minimum Kendall tau | **{result['min_rank_tau']}** |",
        "",
        "> Kendall tau = 1.0 means identical ranking between snapshots; 0 means no "
        "association; -1 means fully reversed. High values indicate a stable, "
        "deterministic ranking.",
        "",
        "## Score drift",
        "",
        f"- Mean absolute score change between snapshots: **`{result['avg_score_drift']}`** "
        "(on a 0–100 scale).",
        "",
        "## Factor drift (mean absolute change per factor)",
        "",
        "| Factor | Mean |∆| |",
        "|--------|------|",
    ])
    for factor, drift in sorted(result.get("avg_factor_drift", {}).items()):
        lines.append(f"| {factor} | {drift} |")
    lines.append("")
    lines.append("---")
    lines.append("*Generated by `scripts/backtest.py`*")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="NOW Index backtest benchmark")
    parser.add_argument("--min-snapshots", type=int, default=2,
                        help="Minimum snapshots required (default 2)")
    parser.add_argument("--out", type=str, default=None,
                        help="Write markdown report to this path")
    args = parser.parse_args()

    result = run_backtest(min_snapshots=args.min_snapshots)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(result), encoding="utf-8")
        print(f"Report written to {out}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
