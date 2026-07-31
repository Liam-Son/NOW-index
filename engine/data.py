"""
Data Fetcher — Abstract data layer for the NOW scoring engine.

Provides a pluggable interface for fetching asset data from various sources.
New data sources can be added without modifying the scoring engine.
"""

from __future__ import annotations

import abc
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np


@dataclass
class AssetData:
    """Normalized data for a single asset."""
    ticker: str
    name: str
    market_price: float = 0.0
    market_cap: float = 0.0
    currency: str = "USD"

    # Valuation
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    ps_ratio: float = 0.0
    pcf_ratio: float = 0.0
    peg_ratio: float = 0.0
    dividend_yield: float = 0.0
    payout_ratio: float = 0.0
    dividend_growth: float = 0.0
    dividend_years: int = 0

    # Profitability
    return_on_equity: float = 0.0
    return_on_assets: float = 0.0
    profit_margin: float = 0.0
    operating_margin: float = 0.0
    fcf_yield: float = 0.0
    earnings_stability: float = 0.5

    # Growth
    revenue_growth: float = 0.0
    eps_growth: float = 0.0
    forward_eps_growth: float = 0.0
    earnings_growth_5y: float = 0.0

    # Risk
    beta: float = 1.0
    volatility: float = 0.25
    max_drawdown: float = 0.30
    sharpe_ratio: float = 0.5
    sortino_ratio: float = 0.7
    current_ratio: float = 1.5
    debt_to_equity: float = 1.0
    interest_coverage: float = 5.0

    # Momentum
    momentum_1m: float = 0.0
    momentum_3m: float = 0.0
    momentum_6m: float = 0.0
    momentum_12m: float = 0.0
    rsi: float = 50.0
    sma_50_pct: float = 0.0
    sma_200_pct: float = 0.0

    # Valuation context
    intrinsic_value: float = 0.0
    dcf_value: float = 0.0

    # Qualitative
    competitive_moat: float = 0.5
    tam_growth: float = 0.05
    secular_tailwind: float = 0.5
    r_and_d_spending: float = 0.05
    patent_count: int = 0
    ai_exposure: float = 0.0
    innovation_score: float = 0.5
    insider_buying_ratio: float = 0.5
    insider_shares_bought: int = 0

    # Metadata
    sector: str = ""
    industry: str = ""
    country: str = ""
    exchange: str = ""
    description: str = ""
    business_segment: str = ""

    # Price history for custom factors
    price_history: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


class DataProvider(abc.ABC):
    """Abstract base class for data providers."""

    @abc.abstractmethod
    def fetch(self, ticker: str) -> AssetData | None:
        """Fetch data for a single ticker."""
        ...

    @abc.abstractmethod
    def fetch_batch(self, tickers: list[str]) -> dict[str, AssetData]:
        """Fetch data for multiple tickers."""
        ...


class SimulatedDataProvider(DataProvider):
    """
    Simulated data provider for development and testing.

    Generates realistic-looking financial data for any ticker.
    """

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self._np_rng = np.random.default_rng(seed)

    def _generate_price_history(self, days: int = 252) -> list[float]:
        """Generate synthetic price history."""
        price = 100.0
        prices = [price]
        for _ in range(days):
            ret = self._np_rng.normal(0.0005, 0.015)
            price *= (1 + ret)
            prices.append(price)
        return prices

    def fetch(self, ticker: str) -> AssetData | None:
        prices = self._generate_price_history()

        # Generate realistic random-ish data
        roe = self._rng.uniform(0.05, 0.35)
        margin = self._rng.uniform(0.03, 0.30)

        data = AssetData(
            ticker=ticker,
            name=f"{ticker} Corporation",
            market_price=prices[-1],
            market_cap=self._rng.uniform(1e9, 3e12),
            pe_ratio=self._rng.uniform(5, 40),
            pb_ratio=self._rng.uniform(0.5, 10),
            ps_ratio=self._rng.uniform(0.5, 15),
            pcf_ratio=self._rng.uniform(5, 30),
            peg_ratio=self._rng.uniform(0.3, 3.0),
            dividend_yield=self._rng.uniform(0, 0.06),
            payout_ratio=self._rng.uniform(0, 0.6),
            dividend_growth=self._rng.uniform(0, 0.15),
            dividend_years=self._rng.randint(0, 30),
            return_on_equity=roe,
            return_on_assets=self._rng.uniform(0.02, 0.15),
            profit_margin=margin,
            operating_margin=self._rng.uniform(0.02, 0.25),
            fcf_yield=self._rng.uniform(0, 0.12),
            earnings_stability=self._rng.uniform(0.3, 0.95),
            revenue_growth=self._rng.uniform(-0.05, 0.35),
            eps_growth=self._rng.uniform(-0.10, 0.40),
            forward_eps_growth=self._rng.uniform(0, 0.30),
            earnings_growth_5y=self._rng.uniform(0, 0.25),
            beta=self._rng.uniform(0.2, 2.0),
            volatility=self._rng.uniform(0.10, 0.50),
            max_drawdown=self._rng.uniform(0.10, 0.45),
            sharpe_ratio=self._rng.uniform(0.2, 2.5),
            sortino_ratio=self._rng.uniform(0.3, 3.0),
            current_ratio=self._rng.uniform(0.5, 4.0),
            debt_to_equity=self._rng.uniform(0, 3.0),
            interest_coverage=self._rng.uniform(2, 20),
            momentum_1m=self._rng.uniform(-0.10, 0.15),
            momentum_3m=self._rng.uniform(-0.15, 0.25),
            momentum_6m=self._rng.uniform(-0.20, 0.35),
            momentum_12m=self._rng.uniform(-0.25, 0.50),
            rsi=self._rng.uniform(20, 80),
            sma_50_pct=self._rng.uniform(-0.15, 0.20),
            sma_200_pct=self._rng.uniform(-0.20, 0.30),
            intrinsic_value=prices[-1] * self._rng.uniform(0.5, 2.0),
            dcf_value=prices[-1] * self._rng.uniform(0.6, 1.8),
            competitive_moat=self._rng.uniform(0, 1),
            tam_growth=self._rng.uniform(0, 0.25),
            secular_tailwind=self._rng.uniform(0, 1),
            r_and_d_spending=self._rng.uniform(0, 0.25),
            patent_count=self._rng.randint(0, 5000),
            ai_exposure=self._rng.uniform(0, 1),
            innovation_score=self._rng.uniform(0, 1),
            insider_buying_ratio=self._rng.uniform(0, 1),
            insider_shares_bought=self._rng.randint(0, 500000),
            sector=self._rng.choice(["Technology", "Healthcare", "Financial",
                                      "Consumer Cyclical", "Consumer Defensive",
                                      "Energy", "Industrials", "Utilities"]),
            industry=self._rng.choice(["Software", "Semiconductors", "Banking",
                                        "Biotech", "Retail", "Insurance"]),
            country=self._rng.choice(["US", "Japan", "UK", "Germany", "Canada"]),
            exchange=self._rng.choice(["NASDAQ", "NYSE", "LSE", "TSE"]),
            description=f"{ticker} is a leading company in its sector.",
            price_history=prices,
        )
        return data

    def fetch_batch(self, tickers: list[str]) -> dict[str, AssetData]:
        return {t: self.fetch(t) for t in tickers}
