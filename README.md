<div align="center">
  <h1>⟁ NOW Index</h1>
  <p><strong>Open Platform & Public Ranking System</strong></p>
  <p>
    <a href="https://github.com/Liam-Son/NOW-index"><img src="https://img.shields.io/github/stars/Liam-Son/NOW-index?style=social" alt="Stars" /></a>
    <a href="https://github.com/Liam-Son/NOW-index/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
    <a href="https://github.com/Liam-Son/NOW-index/actions"><img src="https://img.shields.io/github/actions/workflow/status/Liam-Son/NOW-index/ci.yml?branch=main" alt="CI" /></a>
    <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python" />
    <img src="https://img.shields.io/badge/assets-50%2B-brightgreen" alt="Assets" />
  </p>
  <p>
    <strong>Website:</strong> <a href="https://momentum-please.com">Momentum Please</a> ·
    <strong>API:</strong> <code>https://api.now-index.com</code> ·
    <strong>Docs:</strong> <a href="/api/docs">Swagger UI</a> · <a href="/api/redoc">ReDoc</a>
  </p>
  <p>
    <strong>Related project:</strong> <a href="https://github.com/Liam-Son/Quant_NOW_Performance">Quant_NOW Performance</a> — public performance dashboard and investment calculator for the NOW Index.
  </p>
  <br/>
</div>

---

## � Related Repositories

- [NOW Index](https://github.com/Liam-Son/NOW-index) — core quant ranking engine, scoring framework, and API foundation
- [Quant_NOW Performance](https://github.com/Liam-Son/Quant_NOW_Performance) — public performance dashboard and investment calculator for the NOW Index

## �📊 Overview

The **NOW Quant Framework** is an open-source, multi-factor quantitative ranking engine that evaluates global financial assets across 20+ asset classes. It powers the **NOW Index** — a public ranking system that scores assets from 0-100 based on 10 independent factors.

Built for quantitative researchers, hedge funds, and individual investors, the framework is designed to be:

- **Extensible** — New asset classes and factors can be added without modifying the core engine
- **Scalable** — Designed for 100,000+ assets and millions of users
- **Transparent** — Every score is fully explainable with factor breakdown
- **Open** — MIT licensed, community-driven

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Factor Scoring** | 10 factors across Quality, Value, Growth, Momentum, Risk, and more |
| **20+ Asset Classes** | US stocks, international stocks, ETFs, REITs, crypto, bonds, and more |
| **Live Leaderboards** | Top 10/25/50/100, Most Improved, Best in Class |
| **REST API** | Full API for programmatic access to rankings and scores |
| **Historical Data** | Track NOW Score history daily, weekly, monthly, yearly |
| **Interactive Website** | Bloomberg Terminal-inspired dark mode UI ("Momentum Please") |
| **Hourly Refresh** | Automated data download, scoring, ranking, and deployment |
| **Docker Support** | One-command deployment with Docker Compose |
| **CI/CD Pipeline** | GitHub Actions for testing, validation, and deployment |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Momentum Please Website                   │
│           (Dark-mode UI, Charts, Leaderboards)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     REST API (FastAPI)                       │
│  /company  /ranking  /top10  /leaderboard  /compare  /search │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    NOW Scoring Engine                        │
│  10 Factors: Quality · Value · Growth · Momentum · Risk     │
│   Undervalued · Long-Term · Dividend · Innovation · FinStr  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Asset Registry & Data Layer                 │
│   20+ Asset Classes · Plugin System · Data Providers        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Database (SQLite / PostgreSQL)                  │
│    Historical Scores · Rankings · Asset Metadata            │
└─────────────────────────────────────────────────────────────┘
```

### 📁 Project Structure

```
now-index/
├── engine/                  # Core scoring engine
│   ├── __init__.py
│   ├── scoring.py           # NOWScorer — 10-factor scoring
│   ├── registry.py          # AssetRegistry — manages all assets
│   ├── factors.py           # FactorRegistry — plugin system
│   ├── data.py              # DataProvider interface
│   └── ranking.py           # Ranker — leaderboards & filtering
├── api/                     # REST API
│   ├── __init__.py
│   └── main.py              # FastAPI application
├── database/                # Persistence layer
│   ├── __init__.py
│   └── store.py             # SQLiteStore, InMemoryStore
├── website/                 # Public website
│   ├── index.html           # Momentum Please homepage
│   ├── css/styles.css       # Dark-mode theme
│   └── js/app.js            # Interactive dashboard
├── scripts/                 # Automation scripts
│   ├── hourly_refresh.py    # Hourly scoring pipeline
│   ├── validate.py          # Data validation
│   └── generate_reports.py  # Daily/weekly/monthly reports
├── tests/                   # Test suite
│   ├── test_scoring.py      # Engine tests
│   └── test_api.py          # API integration tests
├── .github/workflows/       # CI/CD pipelines
│   ├── ci.yml               # Continuous integration
│   └── deploy.yml           # Hourly deployment
├── docs/                    # Documentation
│   └── examples/            # Example notebooks
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🔧 Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Liam-Son/NOW-index.git
cd NOW-index

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser to **http://localhost:8000** to see the Momentum Please website.

### Docker

```bash
docker compose up -d
```

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check & system status |
| `GET` | `/api/company/{ticker}` | Company profile & NOW Score |
| `GET` | `/api/asset/{id}` | Asset details by ID |
| `GET` | `/api/ranking` | Paginated full ranking |
| `GET` | `/api/top10` | Top 10 assets |
| `GET` | `/api/top25` | Top 25 assets |
| `GET` | `/api/top50` | Top 50 assets |
| `GET` | `/api/top100` | Top 100 assets |
| `GET` | `/api/leaderboard` | All leaderboard categories |
| `GET` | `/api/leaderboard/{category}` | Specific leaderboard category |
| `GET` | `/api/search?q={query}` | Search assets by ticker/name |
| `GET` | `/api/filter` | Filtered ranking by country, sector, etc. |
| `GET` | `/api/compare?tickers=AAPL,MSFT` | Compare multiple assets |
| `GET` | `/api/history?ticker=AAPL&days=365` | Historical scores |
| `GET` | `/api/asset-classes` | List supported asset classes |
| `GET` | `/api/stats` | Platform statistics |
| `POST` | `/api/refresh` | Trigger ranking refresh |

### Example Response

```json
GET /api/company/AAPL
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "score": 87.5,
  "rank": 1,
  "factors": {
    "quality": 13.2,
    "value": 11.0,
    "growth": 10.5,
    "momentum": 9.8,
    "low_risk": 7.5,
    "undervalued": 8.0,
    "long_term": 6.5,
    "dividend": 4.0,
    "innovation": 5.5,
    "financial_strength": 5.0
  }
}
```

---

## 📈 NOW Score Methodology

The NOW Score is a composite of 10 independent factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Quality** | 15% | ROE, profit margins, earnings stability |
| **Value** | 15% | P/E, P/B, P/S, P/CF ratios |
| **Growth** | 12% | Revenue, EPS, forward estimate growth |
| **Momentum** | 12% | 1m, 3m, 6m, 12m price momentum |
| **Low Risk** | 10% | Beta, volatility, drawdown, Sharpe ratio |
| **Undervalued** | 10% | Intrinsic value, PEG ratio, DCF premium |
| **Long-Term** | 8% | Competitive moat, TAM growth, tailwinds |
| **Dividend** | 6% | Yield, growth, payout ratio, history |
| **Innovation** | 6% | AI exposure, patents, R&D intensity |
| **Financial Strength** | 6% | Current ratio, D/E, FCF yield, coverage |

### Rating Scale

| Rating | Score | Description |
|--------|-------|-------------|
| Excellent | 90-100 | Top-tier investment quality |
| Strong | 80-89 | Above-average quality |
| Good | 70-79 | Solid fundamentals |
| Fair | 60-69 | Adequate with some concerns |
| Moderate | 50-59 | Below average, caution warranted |
| Weak | <50 | Significant risk factors |

---

## 🚢 Supported Asset Classes

| Asset Class | Example | Status |
|-------------|---------|--------|
| US Stocks | AAPL, MSFT, NVDA | ✅ |
| Canadian Stocks | SHOP, TD | ✅ |
| European Stocks | SAP, ASML | ✅ |
| UK Stocks | HSBC, BP | ✅ |
| Australian Stocks | BHP, CBA | ✅ |
| Japanese Stocks | SONY, TM | ✅ |
| Korean Stocks | 005930.KS, 000660.KS | ✅ |
| Hong Kong Stocks | 0700.HK | ✅ |
| Chinese Stocks | TSM, BABA | ✅ |
| ETFs | SPY, QQQ, IVV | ✅ |
| REITs | PLD, AMT, EQIX | ✅ |
| Closed-End Funds | - | ✅ |
| Indices | ^GSPC, ^IXIC | ✅ |
| Cryptocurrencies | BTC, ETH, SOL | ✅ |
| Commodity ETFs | GLD, SLV, USO | ✅ |
| Bonds | BND, TLT | ✅ |
| Money Market ETFs | SHV, BIL | ✅ |
| Sector ETFs | XLF, XLK, XLV | ✅ |
| Country ETFs | EEM, VWO | ✅ |
| Preferred Shares | - | ✅ |

---

## 🤝 Contributing

We welcome contributions from the community! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/Liam-Son/NOW-index.git
cd NOW-index
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

### Running Tests

```bash
python -m pytest tests/ -v --tb=short
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by quantitative frameworks from hedge funds and academic research
- Built with [FastAPI](https://fastapi.tiangolo.com/), [NumPy](https://numpy.org/), [ApexCharts](https://apexcharts.com/)
- Website design inspired by Bloomberg Terminal, TradingView, and Morningstar

---

<div align="center">
  <p>Made with ❤️ by the NOW Quant Framework Team</p>
  <p>
    <a href="https://github.com/Liam-Son/NOW-index">GitHub</a> ·
    <a href="https://momentum-please.com">Website</a> ·
    <a href="/api/docs">API Docs</a>
  </p>
</div>
