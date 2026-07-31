"""Tests for the NOW Index API."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "assets_count" in data


@pytest.mark.asyncio
async def test_top10(client):
    response = await client.get("/api/top10")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    # Check ordering
    for i in range(len(data["results"]) - 1):
        assert data["results"][i]["score"] >= data["results"][i + 1]["score"]


@pytest.mark.asyncio
async def test_top25(client):
    response = await client.get("/api/top25")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 25


@pytest.mark.asyncio
async def test_top50(client):
    response = await client.get("/api/top50")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 50


@pytest.mark.asyncio
async def test_top100(client):
    response = await client.get("/api/top100")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 100


@pytest.mark.asyncio
async def test_company_profile(client):
    response = await client.get("/api/company/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "now_score" in data
    assert data["now_score"]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_company_profile_not_found(client):
    response = await client.get("/api/company/NONEXISTENT")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ranking(client):
    response = await client.get("/api/ranking?per_page=20")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert len(data["results"]) <= 20
    assert "total" in data
    assert "total_pages" in data


@pytest.mark.asyncio
async def test_leaderboard(client):
    response = await client.get("/api/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert "top_10" in data
    assert "top_25" in data
    assert "top_50" in data
    assert "top_100" in data
    assert "highest_quality" in data
    assert "highest_value" in data
    assert "highest_growth" in data
    assert "highest_momentum" in data
    assert "lowest_risk" in data
    assert "most_undervalued" in data


@pytest.mark.asyncio
async def test_leaderboard_category(client):
    response = await client.get("/api/leaderboard/highest_quality")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "highest_quality"
    assert len(data["results"]) > 0


@pytest.mark.asyncio
async def test_leaderboard_category_invalid(client):
    response = await client.get("/api/leaderboard/invalid_category")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search(client):
    response = await client.get("/api/search?q=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert any("AAPL" in r["asset"]["ticker"] for r in data["results"])


@pytest.mark.asyncio
async def test_filter(client):
    response = await client.get("/api/filter?country=US&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 10


@pytest.mark.asyncio
async def test_compare(client):
    response = await client.get("/api/compare?tickers=AAPL,MSFT")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["ticker"] == "AAPL"
    assert data["results"][1]["ticker"] == "MSFT"


@pytest.mark.asyncio
async def test_compare_too_few(client):
    response = await client.get("/api/compare?tickers=AAPL")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_history(client):
    response = await client.get("/api/history?ticker=AAPL&days=30")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert "history" in data


@pytest.mark.asyncio
async def test_asset_classes(client):
    response = await client.get("/api/asset-classes")
    assert response.status_code == 200
    data = response.json()
    assert "asset_classes" in data
    assert len(data["asset_classes"]) >= 15


@pytest.mark.asyncio
async def test_stats(client):
    response = await client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_assets" in data
    assert "avg_score" in data
    assert "top_score" in data
    assert "distribution" in data


@pytest.mark.asyncio
async def test_refresh(client):
    response = await client.post("/api/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["assets_scored"] > 0
