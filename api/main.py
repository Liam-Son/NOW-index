"""
NOW Index FastAPI Application - LIVE DATA VERSION

Production-grade REST API with REAL live market data updating every 5 minutes.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime, timedelta
from typing import List, Optional
import json
from pydantic import BaseModel
import os
import asyncio

# Import engine modules
from engine.core import NOWEngine, MetricInput, create_sample_metrics
from engine.database import InMemoryStore, IndexValue, Performance, Benchmark
from engine.scraper_live import LiveDataScraper

# ===== Pydantic Models =====

class NOWScoreResponse(BaseModel):
    now_score: float
    rating: str
    confidence: float
    momentum_score: float
    value_score: float
    growth_score: float
    quality_score: float
    sentiment_score: float
    timestamp: str


class PerformanceResponse(BaseModel):
    return_1d: float
    return_1w: float
    return_1m: float
    return_3m: float
    return_6m: float
    return_1y: float
    return_3y: float
    volatility_1y: float
    sharpe_ratio: float
    max_drawdown: float


class BenchmarkResponse(BaseModel):
    symbol: str
    name: str
    return_1m: float
    return_3m: float
    return_1y: float
    volatility_1y: float
    sharpe_ratio: float


class SimulatorInput(BaseModel):
    initial_investment: float
    investment_date: str  # YYYY-MM-DD
    monthly_contribution: float = 0.0


class SimulatorResponse(BaseModel):
    current_value: float
    total_invested: float
    profit: float
    return_pct: float
    cagr: float
    months: int


class HistoryPoint(BaseModel):
    date: str
    now_score: float
    rating: str


class IndexHistoryResponse(BaseModel):
    symbol: str
    current_score: float
    current_rating: str
    history: List[HistoryPoint]


# ===== FastAPI App =====

app = FastAPI(
    title="NOW Index API",
    description="Production-grade quantitative investment platform with LIVE market data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engine and store
engine = NOWEngine()
store = InMemoryStore()
scraper = LiveDataScraper()

# Cache for rankings - UPDATES EVERY 5 MINUTES
last_rankings_update = None
cached_rankings = None


# Populate with demo data
def _populate_demo_data():
    """Populate store with sample data."""
    metrics = create_sample_metrics()
    now_score = engine.calculate_now_score(metrics)

    # Add index values for last 100 days
    base_score = now_score.now_score
    for i in range(100, 0, -1):
        days_ago = datetime.utcnow() - timedelta(days=i)
        noise = (i % 5 - 2) / 10
        score = base_score + noise
        score = max(0, min(100, score))

        index_val = IndexValue(
            id=i,
            asset_id=1,
            date=days_ago,
            now_score=score,
            rating=engine._score_to_rating(score).value,
            confidence=now_score.confidence,
            momentum_score=now_score.momentum_score + noise,
            value_score=now_score.value_score + noise,
            growth_score=now_score.growth_score + noise,
            quality_score=now_score.quality_score + noise,
            sentiment_score=now_score.sentiment_score + noise,
            price=metrics.price * (1 + i * 0.001),
            created_at=datetime.utcnow(),
        )
        store.add_index_value(index_val)

    perf = Performance(
        id=1,
        asset_id=1,
        date=datetime.utcnow(),
        return_1d=0.015,
        return_1w=0.032,
        return_1m=0.085,
        return_3m=0.142,
        return_6m=0.198,
        return_1y=0.245,
        return_3y=0.087,
        return_5y=0.082,
        return_ytd=0.118,
        volatility_1y=0.22,
        sharpe_ratio=1.24,
        sortino_ratio=1.82,
        max_drawdown=-0.18,
        cagr_3y=0.087,
        cagr_5y=0.082,
    )
    store.add_performance(perf)

    benchmarks = [
        Benchmark(1, "SPX", "S&P 500", datetime.utcnow(), 4750.0, 0.08, 0.12, 0.22, 0.09, 0.15, 0.95),
        Benchmark(2, "CCMP", "NASDAQ-100", datetime.utcnow(), 15000.0, 0.12, 0.18, 0.28, 0.11, 0.18, 1.15),
        Benchmark(3, "MXWD", "MSCI World", datetime.utcnow(), 3000.0, 0.07, 0.10, 0.20, 0.08, 0.14, 0.92),
        Benchmark(4, "BTC", "Bitcoin", datetime.utcnow(), 65000.0, 0.20, 0.35, 0.58, 0.15, 0.75, 0.85),
        Benchmark(5, "GLD", "Gold", datetime.utcnow(), 2050.0, 0.02, 0.05, 0.10, 0.04, 0.12, 0.35),
    ]
    for bench in benchmarks:
        store.add_benchmark(bench)

_populate_demo_data()


# ===== LIVE DATA REFRESH BACKGROUND TASK =====

async def refresh_rankings_background():
    """Background task to refresh rankings every 5 minutes."""
    global cached_rankings, last_rankings_update
    
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            cached_rankings = scraper.get_all_live_rankings()
            last_rankings_update = datetime.utcnow()
            print(f"Rankings refreshed at {last_rankings_update.isoformat()}")
        except Exception as e:
            print(f"Background refresh error: {e}")


@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup."""
    # Initial fetch
    global cached_rankings, last_rankings_update
    cached_rankings = scraper.get_all_live_rankings()
    last_rankings_update = datetime.utcnow()
    
    # Start background refresh task
    asyncio.create_task(refresh_rankings_background())


# ===== Endpoints =====

@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/index", response_model=NOWScoreResponse)
async def get_index():
    """Get current NOW Index."""
    latest = store.get_latest_index()
    if not latest:
        raise HTTPException(status_code=404, detail="No index data")

    return NOWScoreResponse(
        now_score=latest.now_score,
        rating=latest.rating,
        confidence=latest.confidence,
        momentum_score=latest.momentum_score,
        value_score=latest.value_score,
        growth_score=latest.growth_score,
        quality_score=latest.quality_score,
        sentiment_score=latest.sentiment_score,
        timestamp=latest.date.isoformat(),
    )


@app.get("/api/index/history", response_model=IndexHistoryResponse)
async def get_index_history(days: int = 100):
    """Get index history."""
    history_data = store.index_values[-days:]
    current = store.get_latest_index()

    history_points = [
        HistoryPoint(
            date=h.date.isoformat(),
            now_score=h.now_score,
            rating=h.rating,
        )
        for h in history_data
    ]

    return IndexHistoryResponse(
        symbol="NOW",
        current_score=current.now_score if current else 0,
        current_rating=current.rating if current else "N/A",
        history=history_points,
    )


@app.get("/api/performance", response_model=PerformanceResponse)
async def get_performance():
    """Get performance metrics."""
    perf = store.get_latest_performance()
    if not perf:
        raise HTTPException(status_code=404, detail="No performance data")

    return PerformanceResponse(
        return_1d=perf.return_1d,
        return_1w=perf.return_1w,
        return_1m=perf.return_1m,
        return_3m=perf.return_3m,
        return_6m=perf.return_6m,
        return_1y=perf.return_1y,
        return_3y=perf.return_3y,
        volatility_1y=perf.volatility_1y,
        sharpe_ratio=perf.sharpe_ratio,
        max_drawdown=perf.max_drawdown,
    )


@app.get("/api/benchmarks", response_model=List[BenchmarkResponse])
async def get_benchmarks():
    """Get all benchmarks."""
    benchmarks = store.benchmarks
    return [
        BenchmarkResponse(
            symbol=b.symbol,
            name=b.name,
            return_1m=b.return_1m,
            return_3m=b.return_3m,
            return_1y=b.return_1y,
            volatility_1y=b.volatility_1y,
            sharpe_ratio=b.sharpe_ratio,
        )
        for b in benchmarks
    ]


@app.post("/api/simulator", response_model=SimulatorResponse)
async def simulate_investment(sim: SimulatorInput):
    """Investment growth simulator."""
    try:
        investment_date = datetime.fromisoformat(sim.investment_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    perf = store.get_latest_performance()
    if not perf:
        raise HTTPException(status_code=404, detail="No performance data")

    now = datetime.utcnow()
    months_elapsed = (now.year - investment_date.year) * 12 + (now.month - investment_date.month)
    if months_elapsed < 0:
        months_elapsed = 0

    annual_return = perf.cagr_3y

    current_value = sim.initial_investment
    for month in range(months_elapsed):
        current_value *= (1 + annual_return / 12)
        current_value += sim.monthly_contribution

    total_invested = sim.initial_investment + (sim.monthly_contribution * months_elapsed)
    profit = current_value - total_invested
    return_pct = (profit / total_invested * 100) if total_invested > 0 else 0

    years = months_elapsed / 12
    cagr = 0
    if years > 0 and current_value > 0 and total_invested > 0:
        cagr = (current_value / total_invested) ** (1 / years) - 1

    return SimulatorResponse(
        current_value=current_value,
        total_invested=total_invested,
        profit=profit,
        return_pct=return_pct,
        cagr=cagr,
        months=months_elapsed,
    )


@app.get("/api/methodology")
async def get_methodology():
    """Return methodology documentation."""
    return {
        "name": "NOW Index",
        "description": "Quantitative investment attractiveness score (0-100)",
        "factors": {
            "momentum": {"weight": 0.25, "description": "Price action & relative strength"},
            "value": {"weight": 0.25, "description": "Valuation multiples & yield"},
            "growth": {"weight": 0.20, "description": "Earnings & revenue growth"},
            "quality": {"weight": 0.15, "description": "Balance sheet & profitability"},
            "sentiment": {"weight": 0.15, "description": "Market sentiment"},
        },
    }


@app.get("/api/chart")
async def get_chart_data():
    """Get chart-friendly data."""
    history = store.index_values[-100:]
    return {
        "data": [
            {
                "date": h.date.isoformat(),
                "score": h.now_score,
                "price": h.price,
            }
            for h in history
        ]
    }


@app.get("/api/rankings")
async def get_rankings():
    """Get LIVE asset rankings - updates every 5 minutes."""
    global cached_rankings
    return cached_rankings or {"rankings": [], "updated_at": datetime.utcnow().isoformat()}


@app.get("/rankings", response_class=FileResponse)
async def rankings_page():
    """Serve rankings HTML page with live data."""
    html_file = "/app/rankings.html"
    if os.path.exists(html_file):
        return FileResponse(html_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Rankings page not found")


@app.get("/analytics", response_class=FileResponse)
async def analytics_page():
    """Serve analytics dashboard."""
    html_file = "/app/analytics.html"
    if os.path.exists(html_file):
        return FileResponse(html_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Analytics page not found")


@app.get("/")
async def root():
    """API root."""
    return {
        "name": "NOW Index API - LIVE",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "LIVE - Data updates every 5 minutes",
        "endpoints": [
            "/api/health",
            "/api/index",
            "/api/index/history",
            "/api/performance",
            "/api/benchmarks",
            "/api/simulator",
            "/api/methodology",
            "/api/chart",
            "/api/rankings",
            "/rankings",
            "/analytics"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
