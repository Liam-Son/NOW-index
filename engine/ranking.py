"""
Ranking System — Computes and maintains live rankings of all scored assets.

Supports multiple leaderboard categories and historical trend comparison.
"""

from __future__ import annotations

import bisect
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .scoring import NOWScore, NOWScorer, AssetClass
from .registry import AssetRegistry
from .data import DataProvider, AssetData


class Ranker:
    """
    Maintains ranked list of all assets based on NOW Scores.

    Supports leaderboard categories:
    - Top 10/25/50/100
    - Most Improved (daily/weekly/monthly)
    - Best in each factor dimension
    - Filterable by country, sector, industry, market cap, exchange, asset class
    """

    def __init__(self, scorer: NOWScorer, registry: AssetRegistry,
                 data_provider: DataProvider) -> None:
        self._scorer = scorer
        self._registry = registry
        self._data_provider = data_provider
        self._scores: dict[str, NOWScore] = {}
        self._historical: dict[str, list[tuple[datetime, float]]] = {}
        self._last_refresh: datetime | None = None

    def refresh(self) -> int:
        """Recompute NOW Scores for all registered assets. Returns count."""
        assets = self._registry.list()
        new_scores: dict[str, NOWScore] = {}

        for asset in assets:
            asset_id = asset["asset_id"]
            ticker = asset["ticker"]
            name = asset["name"]
            asset_class_str = asset["asset_class"]

            try:
                asset_class = AssetClass(asset_class_str)
            except ValueError:
                asset_class = asset_class_str

            raw_data = self._data_provider.fetch(ticker)
            if raw_data is None:
                continue

            # Preserve previous scores for comparison
            prev = self._scores.get(asset_id)

            now_score = self._scorer.compute(
                asset_id=asset_id,
                ticker=ticker,
                name=name,
                asset_class=asset_class,
                data=raw_data.to_dict(),
                country=asset.get("country", ""),
                sector=asset.get("sector", ""),
                industry=asset.get("industry", ""),
                market_cap=asset.get("market_cap"),
                exchange=asset.get("exchange", ""),
                currency=asset.get("currency", "USD"),
            )

            # Carry over historical scores
            if prev:
                now_score.previous_rank = prev.rank
                now_score.score_yesterday = self._get_historical(asset_id, days=1)
                now_score.score_last_week = self._get_historical(asset_id, days=7)
                now_score.score_last_month = self._get_historical(asset_id, days=30)
                now_score.score_last_year = self._get_historical(asset_id, days=365)

            new_scores[asset_id] = now_score

            # Store historical
            if asset_id not in self._historical:
                self._historical[asset_id] = []
            self._historical[asset_id].append(
                (now_score.timestamp, now_score.score)
            )

        # Assign ranks
        sorted_assets = sorted(new_scores.values(), key=lambda s: s.score, reverse=True)
        for i, score in enumerate(sorted_assets):
            score.rank = i + 1
            if score.previous_rank is not None:
                score.rank_change = score.previous_rank - score.rank

        self._scores = new_scores
        self._last_refresh = datetime.now(timezone.utc)
        return len(self._scores)

    def _get_historical(self, asset_id: str, days: int) -> float | None:
        """Get score from N days ago."""
        if asset_id not in self._historical:
            return None
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        for ts, score in reversed(self._historical[asset_id]):
            if ts <= cutoff:
                return score
        return None

    def get_all_scores(self) -> list[NOWScore]:
        """Return all scores sorted by rank."""
        return sorted(self._scores.values(), key=lambda s: s.rank)

    def get_top(self, n: int = 10) -> list[NOWScore]:
        """Get top N ranked assets."""
        return self.get_all_scores()[:n]

    def get_most_improved(self, period: str = "daily",
                          limit: int = 10) -> list[NOWScore]:
        """Get assets with the biggest score improvement."""
        scores = self.get_all_scores()
        if period == "daily":
            key = lambda s: (s.score or 0) - (s.score_yesterday or 0)
        elif period == "weekly":
            key = lambda s: (s.score or 0) - (s.score_last_week or 0)
        elif period == "monthly":
            key = lambda s: (s.score or 0) - (s.score_last_month or 0)
        else:
            key = lambda s: s.rank_change or 0

        sorted_by_improvement = sorted(scores, key=key, reverse=True)
        return sorted_by_improvement[:limit]

    def get_best_in_factor(self, factor: str, limit: int = 10) -> list[NOWScore]:
        """Get top assets for a specific factor."""
        scores = self.get_all_scores()
        sorted_scores = sorted(
            scores,
            key=lambda s: getattr(s.factors, factor, 0.0),
            reverse=True,
        )
        return sorted_scores[:limit]

    def filter(self, country: str | None = None, sector: str | None = None,
               industry: str | None = None, asset_class: str | None = None,
               exchange: str | None = None,
               market_cap_min: float | None = None,
               market_cap_max: float | None = None,
               limit: int = 100) -> list[NOWScore]:
        """Filter ranked assets by various criteria."""
        scores = self.get_all_scores()
        filtered = []

        for s in scores:
            if country and s.country.lower() != country.lower():
                continue
            if sector and s.sector.lower() != sector.lower():
                continue
            if industry and s.industry.lower() != industry.lower():
                continue
            if asset_class and s.asset_class.value != asset_class:
                continue
            if exchange and s.exchange.lower() != exchange.lower():
                continue
            if market_cap_min and (s.market_cap or 0) < market_cap_min:
                continue
            if market_cap_max and (s.market_cap or 0) > market_cap_max:
                continue
            filtered.append(s)

        return filtered[:limit]

    def get_leaderboard_categories(self) -> dict[str, list[NOWScore]]:
        """Generate all leaderboard categories at once."""
        all_scores = self.get_all_scores()
        return {
            "top_10": all_scores[:10],
            "top_25": all_scores[:25],
            "top_50": all_scores[:50],
            "top_100": all_scores[:100],
            "most_improved_today": self.get_most_improved("daily", 10),
            "most_improved_week": self.get_most_improved("weekly", 10),
            "most_improved_month": self.get_most_improved("monthly", 10),
            "highest_quality": self.get_best_in_factor("quality", 10),
            "highest_value": self.get_best_in_factor("value", 10),
            "highest_growth": self.get_best_in_factor("growth", 10),
            "highest_momentum": self.get_best_in_factor("momentum", 10),
            "lowest_risk": self.get_best_in_factor("low_risk", 10),
            "most_undervalued": self.get_best_in_factor("undervalued", 10),
            "best_long_term": self.get_best_in_factor("long_term", 10),
            "best_dividend": self.get_best_in_factor("dividend", 10),
            "best_innovation": self.get_best_in_factor("innovation", 10),
            "best_financial_strength": self.get_best_in_factor("financial_strength", 10),
        }
