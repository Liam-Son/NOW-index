"""
Factor Registry — Plugin system for factor calculators.

Allows new factors to be added without modifying the core scoring engine.
"""

from __future__ import annotations

import enum
from typing import Any, Callable

import numpy as np


class FactorType(str, enum.Enum):
    QUALITY = "quality"
    VALUE = "value"
    GROWTH = "growth"
    MOMENTUM = "momentum"
    LOW_RISK = "low_risk"
    UNDERVALUED = "undervalued"
    LONG_TERM = "long_term"
    DIVIDEND = "dividend"
    INNOVATION = "innovation"
    FINANCIAL_STRENGTH = "financial_strength"
    CUSTOM = "custom"


class FactorRegistry:
    """
    Plugin registry for factor calculators.

    Enables the framework to support new factors without modifying
    the NOWScorer class.
    """

    def __init__(self) -> None:
        self._factors: dict[str, dict[str, Any]] = {}

    def register(self, name: str, calculator: Callable[[dict[str, Any]], float],
                 weight: float, factor_type: FactorType = FactorType.CUSTOM,
                 description: str = "", metadata: dict | None = None) -> None:
        """Register a new factor calculator."""
        self._factors[name] = {
            "name": name,
            "calculator": calculator,
            "weight": weight,
            "factor_type": factor_type,
            "description": description,
            "metadata": metadata or {},
        }

    def unregister(self, name: str) -> bool:
        """Remove a factor from the registry."""
        if name in self._factors:
            del self._factors[name]
            return True
        return False

    def get(self, name: str) -> dict[str, Any] | None:
        return self._factors.get(name)

    def list(self, factor_type: FactorType | None = None) -> list[dict[str, Any]]:
        if factor_type:
            return [f for f in self._factors.values() if f["factor_type"] == factor_type]
        return list(self._factors.values())

    def compute_all(self, data: dict[str, Any]) -> dict[str, float]:
        """Compute all registered factors for given data."""
        results = {}
        for name, factor in self._factors.items():
            try:
                score = factor["calculator"](data)
                results[name] = min(max(float(score), 0.0), factor["weight"])
            except Exception:
                results[name] = 0.0
        return results

    def compute_weighted_score(self, data: dict[str, Any]) -> float:
        """Compute weighted total score from all registered factors."""
        scores = self.compute_all(data)
        total = sum(scores.values())
        return round(total, 2)


# Pre-built custom factor examples

def create_momentum_factor(period_days: int = 63, weight: float = 3.0) -> tuple[str, Callable]:
    """Create a custom momentum factor for a specific period."""
    factor_name = f"momentum_{period_days}d"

    def calculator(data: dict) -> float:
        price_history = data.get("price_history", [])
        if len(price_history) < period_days:
            return 0.0
        start_price = price_history[-period_days]
        end_price = price_history[-1]
        if start_price <= 0:
            return 0.0
        ret = (end_price - start_price) / start_price
        # Score: 0 to weight
        if ret > 0.30: return weight
        if ret > 0.20: return weight * 0.8
        if ret > 0.10: return weight * 0.6
        if ret > 0.05: return weight * 0.4
        if ret > 0: return weight * 0.2
        return 0.0

    return factor_name, calculator


def create_ai_exposure_factor(weight: float = 5.0) -> tuple[str, Callable]:
    """Create a factor for AI/ML company exposure."""
    factor_name = "ai_exposure_score"

    AI_KEYWORDS = [
        "artificial intelligence", "machine learning", "deep learning",
        "neural network", "large language model", "generative ai",
        "computer vision", "natural language processing", "autonomous",
        "robotics", "ai", "gpt", "transformer", "diffusion model",
    ]

    def calculator(data: dict) -> float:
        description = (data.get("description", "") or "").lower()
        business_segment = (data.get("business_segment", "") or "").lower()
        r_and_d = data.get("r_and_d_spending", 0.0)

        text = f"{description} {business_segment}"
        matches = sum(1 for kw in AI_KEYWORDS if kw in text)
        score = min(matches / len(AI_KEYWORDS), 1.0) * weight * 0.6

        # R&D intensity bonus
        if r_and_d > 0.20:
            score += weight * 0.4
        elif r_and_d > 0.15:
            score += weight * 0.3
        elif r_and_d > 0.10:
            score += weight * 0.2

        return min(score, weight)

    return factor_name, calculator


def create_insider_buying_factor(weight: float = 5.0) -> tuple[str, Callable]:
    """Create a factor for insider buying activity."""
    factor_name = "insider_buying_score"

    def calculator(data: dict) -> float:
        insider_ratio = data.get("insider_buying_ratio", 0.0)
        insider_shares = data.get("insider_shares_bought", 0)
        market_cap = data.get("market_cap", 1e12)

        # Insider buying ratio (buys / total transactions)
        score = 0.0
        if insider_ratio > 0.8:
            score += weight * 0.5
        elif insider_ratio > 0.6:
            score += weight * 0.3
        elif insider_ratio > 0.4:
            score += weight * 0.15

        # Dollar volume of insider buying
        dollar_value = insider_shares * data.get("market_price", 100)
        if dollar_value > 10_000_000:
            score += weight * 0.5
        elif dollar_value > 1_000_000:
            score += weight * 0.3
        elif dollar_value > 100_000:
            score += weight * 0.15

        return min(score, weight)

    return factor_name, calculator


# Register default custom factors
def register_default_custom_factors(registry: FactorRegistry) -> None:
    """Register the built-in custom factors."""
    name, calc = create_momentum_factor(period_days=63, weight=3.0)
    registry.register(name, calc, 3.0, FactorType.MOMENTUM,
                      "3-month momentum factor")

    name, calc = create_ai_exposure_factor(weight=5.0)
    registry.register(name, calc, 5.0, FactorType.CUSTOM,
                      "AI/ML company exposure score")

    name, calc = create_insider_buying_factor(weight=5.0)
    registry.register(name, calc, 5.0, FactorType.CUSTOM,
                      "Insider buying activity score")
