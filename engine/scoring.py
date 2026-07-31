"""
NOW Score — Core Ranking Engine

The NOW Score is a multi-factor quantitative ranking that evaluates global
financial assets across 10 dimensions:

  1. Quality (15%)
  2. Value (15%)
  3. Growth (12%)
  4. Momentum (12%)
  5. Low Risk (10%)
  6. Undervalued (10%)
  7. Long-Term Opportunity (8%)
  8. Dividend Opportunity (6%)
  9. Innovation (6%)
  10. Financial Strength (6%)

Total = 100% composite score (0-100)
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

import numpy as np


class AssetClass(str, enum.Enum):
    US_STOCK = "us_stock"
    CANADIAN_STOCK = "canadian_stock"
    EUROPEAN_STOCK = "european_stock"
    UK_STOCK = "uk_stock"
    AUSTRALIAN_STOCK = "australian_stock"
    JAPANESE_STOCK = "japanese_stock"
    KOREAN_STOCK = "korean_stock"
    HONG_KONG_STOCK = "hong_kong_stock"
    CHINESE_STOCK = "chinese_stock"
    ETF = "etf"
    REIT = "reit"
    CEF = "closed_end_fund"
    INDEX = "index"
    CRYPTOCURRENCY = "cryptocurrency"
    COMMODITY_ETF = "commodity_etf"
    BOND = "bond"
    MONEY_MARKET_ETF = "money_market_etf"
    SECTOR_ETF = "sector_etf"
    COUNTRY_ETF = "country_etf"
    PREFERRED_SHARE = "preferred_share"


# Asset class groups for extensibility
ASSET_CLASS_GROUPS: dict[str, list[AssetClass]] = {
    "equity": [
        AssetClass.US_STOCK, AssetClass.CANADIAN_STOCK,
        AssetClass.EUROPEAN_STOCK, AssetClass.UK_STOCK,
        AssetClass.AUSTRALIAN_STOCK, AssetClass.JAPANESE_STOCK,
        AssetClass.KOREAN_STOCK, AssetClass.HONG_KONG_STOCK,
        AssetClass.CHINESE_STOCK,
    ],
    "etf": [
        AssetClass.ETF, AssetClass.SECTOR_ETF,
        AssetClass.COUNTRY_ETF, AssetClass.COMMODITY_ETF,
        AssetClass.MONEY_MARKET_ETF,
    ],
    "income": [
        AssetClass.REIT, AssetClass.CEF, AssetClass.BOND,
        AssetClass.PREFERRED_SHARE,
    ],
    "alternative": [
        AssetClass.CRYPTOCURRENCY, AssetClass.INDEX,
    ],
}


@dataclass
class FactorScores:
    """Individual factor scores that comprise the NOW Score."""
    quality: float = 0.0          # 0-15
    value: float = 0.0            # 0-15
    growth: float = 0.0           # 0-12
    momentum: float = 0.0         # 0-12
    low_risk: float = 0.0         # 0-10
    undervalued: float = 0.0      # 0-10
    long_term: float = 0.0        # 0-8
    dividend: float = 0.0         # 0-6
    innovation: float = 0.0       # 0-6
    financial_strength: float = 0.0  # 0-6

    @property
    def total(self) -> float:
        return round(
            self.quality + self.value + self.growth + self.momentum
            + self.low_risk + self.undervalued + self.long_term
            + self.dividend + self.innovation + self.financial_strength,
            2,
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "quality": self.quality,
            "value": self.value,
            "growth": self.growth,
            "momentum": self.momentum,
            "low_risk": self.low_risk,
            "undervalued": self.undervalued,
            "long_term": self.long_term,
            "dividend": self.dividend,
            "innovation": self.innovation,
            "financial_strength": self.financial_strength,
            "total": self.total,
        }


@dataclass
class NOWScore:
    """Complete NOW Score result for a single asset."""
    asset_id: str
    ticker: str
    name: str
    asset_class: AssetClass
    score: float  # 0-100 composite
    factors: FactorScores
    rank: int = 0
    previous_rank: int | None = None
    rank_change: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Historical context
    score_yesterday: float | None = None
    score_last_week: float | None = None
    score_last_month: float | None = None
    score_last_year: float | None = None

    # Additional metadata
    country: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float | None = None
    exchange: str = ""
    currency: str = "USD"

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "ticker": self.ticker,
            "name": self.name,
            "asset_class": self.asset_class.value,
            "score": self.score,
            "factors": self.factors.to_dict(),
            "rank": self.rank,
            "previous_rank": self.previous_rank,
            "rank_change": self.rank_change,
            "timestamp": self.timestamp.isoformat(),
            "score_yesterday": self.score_yesterday,
            "score_last_week": self.score_last_week,
            "score_last_month": self.score_last_month,
            "score_last_year": self.score_last_year,
            "country": self.country,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "exchange": self.exchange,
            "currency": self.currency,
        }


class NOWScorer:
    """
    Core scoring engine that computes the NOW Score for any asset.

    The scorer is designed to be asset-class-agnostic. New asset classes can
    be added by implementing factor calculators that map raw data to the
    10 factor dimensions.
    """

    FACTOR_WEIGHTS = {
        "quality": 15.0,
        "value": 15.0,
        "growth": 12.0,
        "momentum": 12.0,
        "low_risk": 10.0,
        "undervalued": 10.0,
        "long_term": 8.0,
        "dividend": 6.0,
        "innovation": 6.0,
        "financial_strength": 6.0,
    }

    def __init__(self) -> None:
        self._factor_calculators: dict[str, Callable] = {}
        self._register_default_factors()

    def _register_default_factors(self) -> None:
        """Register default factor calculation methods."""
        self._factor_calculators = {
            "quality": self._calc_quality,
            "value": self._calc_value,
            "growth": self._calc_growth,
            "momentum": self._calc_momentum,
            "low_risk": self._calc_low_risk,
            "undervalued": self._calc_undervalued,
            "long_term": self._calc_long_term,
            "dividend": self._calc_dividend,
            "innovation": self._calc_innovation,
            "financial_strength": self._calc_financial_strength,
        }

    def register_calculator(self, factor: str, calculator: Callable) -> None:
        """Register a custom factor calculator for extensibility."""
        self._factor_calculators[factor] = calculator

    def score(self, data: dict[str, Any]) -> FactorScores:
        """Compute factor scores from raw asset data."""
        scores = FactorScores()
        for factor, calculator in self._factor_calculators.items():
            try:
                raw_score = calculator(data)
                max_weight = self.FACTOR_WEIGHTS.get(factor, 5.0)
                setattr(scores, factor, min(max(raw_score, 0.0), max_weight))
            except Exception:
                setattr(scores, factor, 0.0)
        return scores

    def _calc_quality(self, data: dict) -> float:
        """Quality score (0-15). Based on ROE, profit margins, earnings stability."""
        roe = data.get("return_on_equity", 0.0)
        margin = data.get("profit_margin", 0.0)
        earnings_stability = data.get("earnings_stability", 0.5)

        score = 0.0
        # ROE contribution (max 6)
        if roe > 0.20: score += 6.0
        elif roe > 0.15: score += 5.0
        elif roe > 0.10: score += 4.0
        elif roe > 0.05: score += 2.0
        elif roe > 0: score += 1.0

        # Margin contribution (max 5)
        if margin > 0.25: score += 5.0
        elif margin > 0.15: score += 4.0
        elif margin > 0.10: score += 3.0
        elif margin > 0.05: score += 2.0
        elif margin > 0: score += 1.0

        # Earnings stability (max 4)
        score += earnings_stability * 4.0

        return min(score, 15.0)

    def _calc_value(self, data: dict) -> float:
        """Value score (0-15). Based on P/E, P/B, P/S, P/CF."""
        pe = data.get("pe_ratio", 30.0)
        pb = data.get("pb_ratio", 3.0)
        ps = data.get("ps_ratio", 5.0)
        pcf = data.get("pcf_ratio", 20.0)

        score = 0.0
        # P/E (max 5)
        if 0 < pe < 10: score += 5.0
        elif 10 <= pe < 15: score += 4.0
        elif 15 <= pe < 20: score += 3.0
        elif 20 <= pe < 30: score += 2.0
        elif pe <= 0: score += 0.0
        else: score += 1.0

        # P/B (max 4)
        if 0 < pb < 1: score += 4.0
        elif 1 <= pb < 2: score += 3.0
        elif 2 <= pb < 3: score += 2.0
        elif 3 <= pb < 5: score += 1.0
        elif pb <= 0: score += 0.0
        else: score += 0.5

        # P/S (max 3)
        if 0 < ps < 1: score += 3.0
        elif 1 <= ps < 2: score += 2.0
        elif 2 <= ps < 5: score += 1.0
        elif ps <= 0: score += 0.0

        # P/CF (max 3)
        if 0 < pcf < 10: score += 3.0
        elif 10 <= pcf < 15: score += 2.0
        elif 15 <= pcf < 25: score += 1.0
        elif pcf <= 0: score += 0.0

        return min(score, 15.0)

    def _calc_growth(self, data: dict) -> float:
        """Growth score (0-12). Revenue growth, earnings growth, forward estimates."""
        rev_growth = data.get("revenue_growth", 0.0)
        eps_growth = data.get("eps_growth", 0.0)
        forward_eps = data.get("forward_eps_growth", 0.0)

        score = 0.0
        # Revenue growth (max 5)
        if rev_growth > 0.30: score += 5.0
        elif rev_growth > 0.20: score += 4.0
        elif rev_growth > 0.10: score += 3.0
        elif rev_growth > 0.05: score += 2.0
        elif rev_growth > 0: score += 1.0

        # EPS growth (max 4)
        if eps_growth > 0.30: score += 4.0
        elif eps_growth > 0.20: score += 3.0
        elif eps_growth > 0.10: score += 2.0
        elif eps_growth > 0: score += 1.0

        # Forward estimates (max 3)
        if forward_eps > 0.25: score += 3.0
        elif forward_eps > 0.15: score += 2.0
        elif forward_eps > 0.05: score += 1.0

        return min(score, 12.0)

    def _calc_momentum(self, data: dict) -> float:
        """Momentum score (0-12). Price momentum over various periods."""
        mom_1m = data.get("momentum_1m", 0.0)
        mom_3m = data.get("momentum_3m", 0.0)
        mom_6m = data.get("momentum_6m", 0.0)
        mom_12m = data.get("momentum_12m", 0.0)
        rsi = data.get("rsi", 50.0)

        score = 0.0
        # 1-month (max 2)
        if mom_1m > 0.10: score += 2.0
        elif mom_1m > 0.05: score += 1.5
        elif mom_1m > 0: score += 1.0
        elif mom_1m > -0.05: score += 0.5

        # 3-month (max 3)
        if mom_3m > 0.15: score += 3.0
        elif mom_3m > 0.10: score += 2.0
        elif mom_3m > 0.05: score += 1.5
        elif mom_3m > 0: score += 1.0

        # 6-month (max 3)
        if mom_6m > 0.20: score += 3.0
        elif mom_6m > 0.10: score += 2.0
        elif mom_6m > 0.05: score += 1.5
        elif mom_6m > 0: score += 1.0

        # 12-month (max 2)
        if mom_12m > 0.25: score += 2.0
        elif mom_12m > 0.10: score += 1.5
        elif mom_12m > 0: score += 1.0

        # RSI confirmation (max 2)
        if 40 <= rsi <= 60: score += 2.0
        elif 30 <= rsi <= 70: score += 1.0

        return min(score, 12.0)

    def _calc_low_risk(self, data: dict) -> float:
        """Low Risk score (0-10). Beta, volatility, drawdown."""
        beta = data.get("beta", 1.0)
        volatility = data.get("volatility", 0.25)
        max_drawdown = data.get("max_drawdown", 0.30)
        sharpe = data.get("sharpe_ratio", 0.5)

        score = 0.0
        # Beta (max 3)
        if 0 < beta < 0.5: score += 3.0
        elif 0.5 <= beta < 0.8: score += 2.5
        elif 0.8 <= beta < 1.2: score += 2.0
        elif 1.2 <= beta < 1.5: score += 1.0
        else: score += 0.5

        # Volatility (max 3)
        if volatility < 0.15: score += 3.0
        elif volatility < 0.20: score += 2.5
        elif volatility < 0.30: score += 2.0
        elif volatility < 0.40: score += 1.0
        else: score += 0.5

        # Max drawdown (max 2)
        if max_drawdown < 0.15: score += 2.0
        elif max_drawdown < 0.25: score += 1.5
        elif max_drawdown < 0.35: score += 1.0
        else: score += 0.5

        # Sharpe ratio (max 2)
        if sharpe > 2.0: score += 2.0
        elif sharpe > 1.5: score += 1.5
        elif sharpe > 1.0: score += 1.0
        elif sharpe > 0.5: score += 0.5

        return min(score, 10.0)

    def _calc_undervalued(self, data: dict) -> float:
        """Undervalued score (0-10). Based on intrinsic value vs market price."""
        intrinsic_value = data.get("intrinsic_value", 0.0)
        market_price = data.get("market_price", 1.0)
        peg_ratio = data.get("peg_ratio", 2.0)
        dcf_value = data.get("dcf_value", 0.0)

        score = 0.0
        # Price vs Intrinsic (max 5)
        if intrinsic_value > 0 and market_price > 0:
            ratio = intrinsic_value / market_price
            if ratio > 1.5: score += 5.0
            elif ratio > 1.3: score += 4.0
            elif ratio > 1.1: score += 3.0
            elif ratio > 0.9: score += 2.0
            else: score += 1.0

        # PEG ratio (max 3)
        if 0 < peg_ratio < 0.5: score += 3.0
        elif 0.5 <= peg_ratio < 1.0: score += 2.5
        elif 1.0 <= peg_ratio < 1.5: score += 2.0
        elif 1.5 <= peg_ratio < 2.0: score += 1.0

        # DCF premium (max 2)
        if dcf_value > 0 and market_price > 0:
            premium = (dcf_value - market_price) / market_price
            if premium > 0.50: score += 2.0
            elif premium > 0.25: score += 1.5
            elif premium > 0.10: score += 1.0
            elif premium > 0: score += 0.5

        return min(score, 10.0)

    def _calc_long_term(self, data: dict) -> float:
        """Long-Term Opportunity score (0-8). Based on competitive advantages,
        TAM growth, and secular tailwinds."""
        competitive_moat = data.get("competitive_moat", 0.0)
        tam_growth = data.get("tam_growth", 0.0)
        secular_tailwind = data.get("secular_tailwind", 0.0)
        r_and_d = data.get("r_and_d_spending", 0.0)

        score = 0.0
        # Competitive moat (max 3)
        score += min(competitive_moat, 1.0) * 3.0

        # TAM growth (max 2)
        if tam_growth > 0.20: score += 2.0
        elif tam_growth > 0.10: score += 1.5
        elif tam_growth > 0.05: score += 1.0
        elif tam_growth > 0: score += 0.5

        # Secular tailwind (max 2)
        score += min(secular_tailwind, 1.0) * 2.0

        # R&D spending (max 1)
        if r_and_d > 0.15: score += 1.0
        elif r_and_d > 0.10: score += 0.7
        elif r_and_d > 0.05: score += 0.5

        return min(score, 8.0)

    def _calc_dividend(self, data: dict) -> float:
        """Dividend Opportunity score (0-6). Yield, growth, payout ratio."""
        div_yield = data.get("dividend_yield", 0.0)
        div_growth = data.get("dividend_growth", 0.0)
        payout_ratio = data.get("payout_ratio", 0.0)
        div_years = data.get("dividend_years", 0)

        score = 0.0
        # Yield (max 2)
        if div_yield > 0.06: score += 2.0
        elif div_yield > 0.04: score += 1.5
        elif div_yield > 0.02: score += 1.0
        elif div_yield > 0.01: score += 0.5

        # Dividend growth (max 2)
        if div_growth > 0.15: score += 2.0
        elif div_growth > 0.10: score += 1.5
        elif div_growth > 0.05: score += 1.0
        elif div_growth > 0: score += 0.5

        # Payout ratio (max 1)
        if 0.2 <= payout_ratio <= 0.5: score += 1.0
        elif 0.1 <= payout_ratio <= 0.6: score += 0.5

        # Dividend history (max 1)
        if div_years >= 25: score += 1.0
        elif div_years >= 10: score += 0.7
        elif div_years >= 5: score += 0.5

        return min(score, 6.0)

    def _calc_innovation(self, data: dict) -> float:
        """Innovation score (0-6). R&D intensity, patent portfolio, AI exposure."""
        ai_exposure = data.get("ai_exposure", 0.0)
        patent_count = data.get("patent_count", 0)
        r_and_d_intensity = data.get("r_and_d_spending", 0.0)
        innovation_award = data.get("innovation_score", 0.0)

        score = 0.0
        # AI exposure (max 2)
        score += min(ai_exposure, 1.0) * 2.0

        # Patent portfolio (max 1.5)
        if patent_count > 10000: score += 1.5
        elif patent_count > 1000: score += 1.0
        elif patent_count > 100: score += 0.5

        # R&D intensity (max 1.5)
        if r_and_d_intensity > 0.20: score += 1.5
        elif r_and_d_intensity > 0.15: score += 1.0
        elif r_and_d_intensity > 0.10: score += 0.7
        elif r_and_d_intensity > 0.05: score += 0.5

        # Innovation score (max 1)
        score += min(innovation_award, 1.0) * 1.0

        return min(score, 6.0)

    def _calc_financial_strength(self, data: dict) -> float:
        """Financial Strength score (0-6). Current ratio, debt/equity, cash flow."""
        current_ratio = data.get("current_ratio", 1.0)
        debt_equity = data.get("debt_to_equity", 1.0)
        fcf_yield = data.get("fcf_yield", 0.0)
        interest_coverage = data.get("interest_coverage", 5.0)

        score = 0.0
        # Current ratio (max 1.5)
        if current_ratio > 2.5: score += 1.5
        elif current_ratio > 1.5: score += 1.0
        elif current_ratio > 1.0: score += 0.5

        # Debt/Equity (max 1.5)
        if debt_equity < 0.3: score += 1.5
        elif debt_equity < 0.5: score += 1.0
        elif debt_equity < 1.0: score += 0.7
        elif debt_equity < 2.0: score += 0.3

        # FCF Yield (max 1.5)
        if fcf_yield > 0.10: score += 1.5
        elif fcf_yield > 0.06: score += 1.0
        elif fcf_yield > 0.03: score += 0.5

        # Interest coverage (max 1.5)
        if interest_coverage > 15: score += 1.5
        elif interest_coverage > 10: score += 1.0
        elif interest_coverage > 5: score += 0.5

        return min(score, 6.0)

    def compute(self, asset_id: str, ticker: str, name: str,
                asset_class: AssetClass, data: dict[str, Any],
                **kwargs) -> NOWScore:
        """Compute the full NOW Score for an asset."""
        factors = self.score(data)
        now_score = NOWScore(
            asset_id=asset_id,
            ticker=ticker,
            name=name,
            asset_class=asset_class,
            score=factors.total,
            factors=factors,
            country=kwargs.get("country", ""),
            sector=kwargs.get("sector", ""),
            industry=kwargs.get("industry", ""),
            market_cap=kwargs.get("market_cap"),
            exchange=kwargs.get("exchange", ""),
            currency=kwargs.get("currency", "USD"),
        )
        return now_score
