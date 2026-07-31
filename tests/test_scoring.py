"""Tests for the NOW scoring engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from engine import NOWScorer, AssetClass, FactorRegistry
from engine.factors import FactorType, create_momentum_factor, register_default_custom_factors
from engine.data import SimulatedDataProvider, AssetData
from engine.registry import AssetRegistry
from engine.ranking import Ranker


class TestNOWScorer:
    def setup_method(self):
        self.scorer = NOWScorer()

    def test_score_returns_factor_scores(self):
        data = {
            "return_on_equity": 0.25,
            "profit_margin": 0.20,
            "earnings_stability": 0.8,
            "pe_ratio": 15.0,
            "pb_ratio": 2.0,
            "ps_ratio": 3.0,
            "pcf_ratio": 12.0,
            "revenue_growth": 0.15,
            "eps_growth": 0.20,
            "forward_eps_growth": 0.10,
            "momentum_1m": 0.05,
            "momentum_3m": 0.10,
            "momentum_6m": 0.15,
            "momentum_12m": 0.20,
            "rsi": 55.0,
            "beta": 0.8,
            "volatility": 0.18,
            "max_drawdown": 0.20,
            "sharpe_ratio": 1.5,
            "intrinsic_value": 150.0,
            "market_price": 100.0,
            "peg_ratio": 1.0,
            "dcf_value": 130.0,
            "competitive_moat": 0.8,
            "tam_growth": 0.12,
            "secular_tailwind": 0.7,
            "r_and_d_spending": 0.12,
            "dividend_yield": 0.02,
            "dividend_growth": 0.08,
            "payout_ratio": 0.3,
            "dividend_years": 15,
            "ai_exposure": 0.6,
            "patent_count": 5000,
            "innovation_score": 0.7,
            "current_ratio": 2.0,
            "debt_to_equity": 0.5,
            "fcf_yield": 0.06,
            "interest_coverage": 10.0,
        }
        scores = self.scorer.score(data)
        assert scores.total > 0
        assert scores.total <= 100
        assert scores.quality > 0
        assert scores.value > 0
        assert scores.growth > 0
        assert scores.momentum > 0
        assert scores.low_risk > 0
        assert scores.undervalued > 0
        assert scores.long_term > 0
        assert scores.dividend > 0
        assert scores.innovation > 0
        assert scores.financial_strength > 0

    def test_score_handles_missing_data(self):
        scores = self.scorer.score({})
        assert scores.total >= 0
        assert scores.total <= 100

    def test_score_with_extreme_values(self):
        data = {
            "return_on_equity": 0.50,
            "profit_margin": 0.50,
            "pe_ratio": 50.0,
            "pb_ratio": 10.0,
            "beta": 2.5,
            "volatility": 0.60,
            "max_drawdown": 0.50,
            "sharpe_ratio": 0.1,
            "debt_to_equity": 5.0,
            "current_ratio": 0.3,
        }
        scores = self.scorer.score(data)
        assert scores.total >= 0
        assert scores.total <= 100

    def test_compute_returns_nows_score(self):
        data = {
            "return_on_equity": 0.20,
            "profit_margin": 0.15,
            "pe_ratio": 18.0,
            "pb_ratio": 3.0,
            "revenue_growth": 0.10,
            "eps_growth": 0.12,
            "momentum_1m": 0.03,
            "momentum_3m": 0.08,
            "rsi": 52.0,
            "beta": 1.1,
            "volatility": 0.22,
            "sharpe_ratio": 1.0,
            "intrinsic_value": 110.0,
            "market_price": 100.0,
            "dividend_yield": 0.015,
            "competitive_moat": 0.6,
            "tam_growth": 0.08,
            "current_ratio": 1.8,
            "debt_to_equity": 0.8,
            "fcf_yield": 0.04,
            "interest_coverage": 8.0,
        }
        result = self.scorer.compute(
            asset_id="test-001",
            ticker="TEST",
            name="Test Corp",
            asset_class=AssetClass.US_STOCK,
            data=data,
            country="US",
            sector="Technology",
            industry="Software",
            market_cap=1e12,
            exchange="NASDAQ",
        )
        assert result.asset_id == "test-001"
        assert result.ticker == "TEST"
        assert result.name == "Test Corp"
        assert 0 <= result.score <= 100
        assert result.asset_class == AssetClass.US_STOCK
        assert result.country == "US"
        assert result.sector == "Technology"
        assert result.industry == "Software"
        assert result.market_cap == 1e12
        assert result.exchange == "NASDAQ"
        assert result.currency == "USD"


class TestAssetRegistry:
    def setup_method(self):
        self.registry = AssetRegistry()

    def test_register_and_get(self):
        aid = self.registry.register("AAPL", "Apple Inc.", AssetClass.US_STOCK,
                                      country="US", sector="Technology")
        assert aid is not None
        asset = self.registry.get(aid)
        assert asset["ticker"] == "AAPL"
        assert asset["name"] == "Apple Inc."

    def test_get_by_ticker(self):
        self.registry.register("MSFT", "Microsoft Corp.", AssetClass.US_STOCK)
        asset = self.registry.get_by_ticker("MSFT")
        assert asset is not None
        assert asset["name"] == "Microsoft Corp."

    def test_list_by_asset_class(self):
        self.registry.register("AAPL", "Apple", AssetClass.US_STOCK)
        self.registry.register("SPY", "SPDR S&P 500", AssetClass.ETF)
        us_stocks = self.registry.list(AssetClass.US_STOCK)
        etfs = self.registry.list(AssetClass.ETF)
        assert len(us_stocks) == 1
        assert len(etfs) == 1

    def test_unregister(self):
        aid = self.registry.register("AAPL", "Apple", AssetClass.US_STOCK)
        assert self.registry.unregister(aid)
        asset = self.registry.get(aid)
        assert not asset["active"]


class TestRanker:
    def setup_method(self):
        self.scorer = NOWScorer()
        self.registry = AssetRegistry()
        self.data_provider = SimulatedDataProvider()
        self.ranker = Ranker(self.scorer, self.registry, self.data_provider)

    def test_refresh_with_seeded_assets(self):
        self.registry.seed_default_assets()
        count = self.ranker.refresh()
        assert count > 0
        scores = self.ranker.get_all_scores()
        assert len(scores) == count

    def test_top_n(self):
        self.registry.seed_default_assets()
        self.ranker.refresh()
        top10 = self.ranker.get_top(10)
        assert len(top10) == 10
        # Check ordering
        for i in range(len(top10) - 1):
            assert top10[i].score >= top10[i + 1].score

    def test_leaderboard_categories(self):
        self.registry.seed_default_assets()
        self.ranker.refresh()
        categories = self.ranker.get_leaderboard_categories()
        assert "top_10" in categories
        assert "top_25" in categories
        assert "highest_quality" in categories
        assert "highest_value" in categories
        assert "highest_growth" in categories
        assert "highest_momentum" in categories
        assert "lowest_risk" in categories
        assert "most_undervalued" in categories
        assert "best_long_term" in categories
        assert "best_dividend" in categories
        assert "best_innovation" in categories
        assert "best_financial_strength" in categories

    def test_filter_by_country(self):
        self.registry.seed_default_assets()
        self.ranker.refresh()
        filtered = self.ranker.filter(country="US")
        for s in filtered:
            assert s.country == "US"


class TestFactorRegistry:
    def test_register_and_compute(self):
        registry = FactorRegistry()
        name, calc = create_momentum_factor(period_days=63, weight=3.0)
        registry.register(name, calc, 3.0, FactorType.MOMENTUM, "Test factor")

        factors = registry.list()
        assert len(factors) == 1

        data = {"price_history": [100] * 60 + [150]}
        scores = registry.compute_all(data)
        assert name in scores


class TestSimulatedDataProvider:
    def test_fetch(self):
        provider = SimulatedDataProvider()
        data = provider.fetch("AAPL")
        assert data is not None
        assert data.ticker == "AAPL"
        assert data.market_price > 0
        assert data.pe_ratio > 0
        assert data.beta > 0
        assert len(data.price_history) > 0

    def test_fetch_batch(self):
        provider = SimulatedDataProvider()
        results = provider.fetch_batch(["AAPL", "MSFT", "GOOGL"])
        assert len(results) == 3
        assert "AAPL" in results
        assert "MSFT" in results
        assert "GOOGL" in results
