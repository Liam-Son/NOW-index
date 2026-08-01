"""
NOW Index — REST API Server

FastAPI-based API providing:
- /company/{ticker} — Company profile & NOW Score
- /ranking — Full ranking list
- /top10, /top25, /top50, /top100 — Leaderboards
- /asset/{id} — Asset details
- /history — Historical scores
- /search — Search assets
- /filter — Filtered ranking
- /compare — Compare multiple assets
- /leaderboard — All leaderboard categories
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from engine import (
    NOWScorer, AssetClass, AssetRegistry, FactorRegistry,
    SimulatedDataProvider, register_default_custom_factors,
)
from engine.ranking import Ranker
from database import SQLiteStore, ScoreStore


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan handler — saves an initial snapshot on startup."""
    scores = ranker.get_all_scores()
    if scores:
        store.save_snapshot([s.to_dict() for s in scores])
    yield


app = FastAPI(
    title="NOW Index API",
    version="1.0.0",
    description="Open Platform & Public Ranking System — NOW Quant Framework",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Initialize Engine ───────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

scorer = NOWScorer()
registry = AssetRegistry()
data_provider = SimulatedDataProvider()
ranker = Ranker(scorer, registry, data_provider)
store: ScoreStore = SQLiteStore(DATA_DIR / "now_index.db")

# Register custom factors
factor_registry = FactorRegistry()
register_default_custom_factors(factor_registry)

# Seed default assets
registry.seed_default_assets()

# Initial ranking
ranker.refresh()


# ─── Helper Functions ────────────────────────────────────────────────────────

def _get_asset_or_404(ticker: str) -> dict[str, Any]:
    """Get asset by ticker or raise 404."""
    asset = registry.get_by_ticker(ticker)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{ticker}' not found")
    return asset


def _score_to_response(score) -> dict[str, Any]:
    """Convert NOWScore to API response dict."""
    return score.to_dict()


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "assets_count": registry.count(),
        "last_refresh": ranker._last_refresh.isoformat() if ranker._last_refresh else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Company / Asset Endpoints ───────────────────────────────────────────────

@app.get("/api/company/{ticker}")
def company_profile(ticker: str):
    """Get company profile and NOW Score for a ticker."""
    asset = _get_asset_or_404(ticker)
    scores = ranker.get_all_scores()
    score = next((s for s in scores if s.asset_id == asset["asset_id"]), None)

    if not score:
        raise HTTPException(status_code=404, detail=f"Score not found for '{ticker}'")

    history = store.get_history(asset["asset_id"], days=365)

    return {
        "profile": asset,
        "now_score": _score_to_response(score),
        "history": history,
        "factor_weights": scorer.FACTOR_WEIGHTS,
    }


@app.get("/api/asset/{asset_id}")
def asset_detail(asset_id: str):
    """Get asset details by ID."""
    asset = registry.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    scores = ranker.get_all_scores()
    score = next((s for s in scores if s.asset_id == asset_id), None)

    return {
        "asset": asset,
        "now_score": _score_to_response(score) if score else None,
    }


# ─── Ranking Endpoints ───────────────────────────────────────────────────────

@app.get("/api/ranking")
def get_ranking(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Get paginated ranking of all assets."""
    scores = ranker.get_all_scores()
    start = (page - 1) * per_page
    end = start + per_page
    page_scores = scores[start:end]

    return {
        "page": page,
        "per_page": per_page,
        "total": len(scores),
        "total_pages": (len(scores) + per_page - 1) // per_page,
        "results": [_score_to_response(s) for s in page_scores],
    }


@app.get("/api/top10")
def top10():
    """Get top 10 assets."""
    return {"results": [_score_to_response(s) for s in ranker.get_top(10)]}


@app.get("/api/top25")
def top25():
    """Get top 25 assets."""
    return {"results": [_score_to_response(s) for s in ranker.get_top(25)]}


@app.get("/api/top50")
def top50():
    """Get top 50 assets."""
    return {"results": [_score_to_response(s) for s in ranker.get_top(50)]}


@app.get("/api/top100")
def top100():
    """Get top 100 assets."""
    return {"results": [_score_to_response(s) for s in ranker.get_top(100)]}


# ─── Leaderboard Endpoints ───────────────────────────────────────────────────

@app.get("/api/leaderboard")
def get_leaderboard():
    """Get all leaderboard categories."""
    categories = ranker.get_leaderboard_categories()
    return {
        category: [_score_to_response(s) for s in scores]
        for category, scores in categories.items()
    }


@app.get("/api/leaderboard/{category}")
def get_leaderboard_category(category: str, limit: int = Query(10, ge=1, le=100)):
    """Get a specific leaderboard category."""
    categories = {
        "top_10": ranker.get_top(limit),
        "top_25": ranker.get_top(limit),
        "top_50": ranker.get_top(limit),
        "top_100": ranker.get_top(limit),
        "most_improved_today": ranker.get_most_improved("daily", limit),
        "most_improved_week": ranker.get_most_improved("weekly", limit),
        "most_improved_month": ranker.get_most_improved("monthly", limit),
        "highest_quality": ranker.get_best_in_factor("quality", limit),
        "highest_value": ranker.get_best_in_factor("value", limit),
        "highest_growth": ranker.get_best_in_factor("growth", limit),
        "highest_momentum": ranker.get_best_in_factor("momentum", limit),
        "lowest_risk": ranker.get_best_in_factor("low_risk", limit),
        "most_undervalued": ranker.get_best_in_factor("undervalued", limit),
        "best_long_term": ranker.get_best_in_factor("long_term", limit),
        "best_dividend": ranker.get_best_in_factor("dividend", limit),
        "best_innovation": ranker.get_best_in_factor("innovation", limit),
        "best_financial_strength": ranker.get_best_in_factor("financial_strength", limit),
    }

    if category not in categories:
        valid = list(categories.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid: {', '.join(valid)}",
        )

    return {"category": category, "results": [_score_to_response(s) for s in categories[category]]}


# ─── Search & Filter Endpoints ───────────────────────────────────────────────

@app.get("/api/search")
def search_assets(q: str = Query("", min_length=1)):
    """Search assets by ticker or name."""
    q = q.upper()
    results = []
    for asset in registry.list():
        if q in asset["ticker"] or q in asset["name"].upper():
            scores = ranker.get_all_scores()
            score = next((s for s in scores if s.asset_id == asset["asset_id"]), None)
            results.append({
                "asset": asset,
                "now_score": _score_to_response(score) if score else None,
            })
    return {"query": q, "count": len(results), "results": results}


@app.get("/api/filter")
def filter_ranking(
    country: str | None = Query(None),
    sector: str | None = Query(None),
    industry: str | None = Query(None),
    asset_class: str | None = Query(None),
    exchange: str | None = Query(None),
    market_cap_min: float | None = Query(None),
    market_cap_max: float | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Filter ranked assets by criteria."""
    filtered = ranker.filter(
        country=country,
        sector=sector,
        industry=industry,
        asset_class=asset_class,
        exchange=exchange,
        market_cap_min=market_cap_min,
        market_cap_max=market_cap_max,
        limit=limit,
    )
    return {
        "filters": {
            "country": country,
            "sector": sector,
            "industry": industry,
            "asset_class": asset_class,
            "exchange": exchange,
            "market_cap_min": market_cap_min,
            "market_cap_max": market_cap_max,
        },
        "count": len(filtered),
        "results": [_score_to_response(s) for s in filtered],
    }


# ─── Compare Endpoint ───────────────────────────────────────────────────────

@app.get("/api/compare")
def compare_assets(
    tickers: str = Query(..., description="Comma-separated tickers to compare"),
):
    """Compare multiple assets side by side (e.g., /api/compare?tickers=AAPL,MSFT,GOOGL)."""
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if len(ticker_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 tickers to compare")
    if len(ticker_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 tickers for comparison")

    results = []
    for ticker in ticker_list:
        try:
            asset = _get_asset_or_404(ticker)
            scores = ranker.get_all_scores()
            score = next((s for s in scores if s.asset_id == asset["asset_id"]), None)
            history = store.get_history(asset["asset_id"], days=30)
            results.append({
                "ticker": ticker,
                "profile": asset,
                "now_score": _score_to_response(score) if score else None,
                "history": history,
            })
        except HTTPException:
            results.append({"ticker": ticker, "error": "Not found"})

    return {"tickers": ticker_list, "count": len(results), "results": results}


# ─── History Endpoint ────────────────────────────────────────────────────────

@app.get("/api/history")
def get_history(
    ticker: str = Query(..., description="Ticker symbol"),
    days: int = Query(365, ge=1, le=3650),
):
    """Get historical NOW Scores for an asset."""
    asset = _get_asset_or_404(ticker)
    history = store.get_history(asset["asset_id"], days=days)

    return {
        "ticker": ticker,
        "asset_id": asset["asset_id"],
        "days": days,
        "count": len(history),
        "history": history,
    }


# ─── Asset Classes Endpoint ──────────────────────────────────────────────────

@app.get("/api/asset-classes")
def get_asset_classes():
    """Get list of all supported asset classes."""
    classes = []
    for ac in AssetClass:
        group = None
        for g, members in {
            "equity": ["us_stock", "canadian_stock", "european_stock", "uk_stock",
                       "australian_stock", "japanese_stock", "korean_stock",
                       "hong_kong_stock", "chinese_stock"],
            "etf": ["etf", "sector_etf", "country_etf", "commodity_etf", "money_market_etf"],
            "income": ["reit", "closed_end_fund", "bond", "preferred_share"],
            "alternative": ["cryptocurrency", "index"],
        }.items():
            if ac.value in members:
                group = g
                break

        classes.append({
            "id": ac.value,
            "name": ac.name.replace("_", " ").title(),
            "group": group,
            "count": registry.count(ac),
        })

    return {"asset_classes": classes}


# ─── Refresh Endpoint ────────────────────────────────────────────────────────

@app.post("/api/refresh")
def refresh_ranking():
    """Manually trigger a ranking refresh."""
    count = ranker.refresh()
    scores = ranker.get_all_scores()
    store.save_snapshot([s.to_dict() for s in scores])
    return {
        "status": "ok",
        "assets_scored": count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Stats Endpoint ──────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    """Get overall NOW Index statistics."""
    scores = ranker.get_all_scores()
    if not scores:
        return {"total_assets": 0, "avg_score": 0, "top_score": 0, "distribution": {}}

    avg_score = sum(s.score for s in scores) / len(scores)
    top_score = max(s.score for s in scores)

    # Distribution
    distribution = {
        "excellent_90_100": sum(1 for s in scores if s.score >= 90),
        "strong_80_89": sum(1 for s in scores if 80 <= s.score < 90),
        "good_70_79": sum(1 for s in scores if 70 <= s.score < 80),
        "fair_60_69": sum(1 for s in scores if 60 <= s.score < 70),
        "moderate_50_59": sum(1 for s in scores if 50 <= s.score < 60),
        "weak_below_50": sum(1 for s in scores if s.score < 50),
    }

    return {
        "total_assets": len(scores),
        "avg_score": round(avg_score, 2),
        "top_score": round(top_score, 2),
        "top_ticker": scores[0].ticker if scores else None,
        "distribution": distribution,
        "asset_class_breakdown": {
            ac: registry.count(ac) for ac in AssetClass
        },
        "last_refresh": ranker._last_refresh.isoformat() if ranker._last_refresh else None,
    }


# ─── Serve Static Files ──────────────────────────────────────────────────────

WEBSITE_DIR = Path(__file__).resolve().parent.parent / "website"
if WEBSITE_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEBSITE_DIR), html=True), name="website")


# ─── Startup (handled by lifespan above) ─────────────────────────────────────
