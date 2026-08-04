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

## 🔗 Related Repositories

- [NOW Index](https://github.com/Liam-Son/NOW-index) — core quant ranking engine, scoring framework, and API foundation
- [Quant_NOW Performance](https://github.com/Liam-Son/Quant_NOW_Performance) — public performance dashboard and investment calculator for the NOW Index

## 🎯 Scope & Definition

**What is the NOW Index?** A clearly defined, multi-factor composite ranking that scores financial assets from **0 to 100** by combining **10 weighted factors** (Quality, Value, Growth, Momentum, Low Risk, Undervalued, Long-Term, Dividend, Innovation, Financial Strength). The score is a **relative rank** within the tracked model universe — not a price target, not an absolute "fair value," and not a standalone buy/sell signal.

**What problem does it solve?** It collapses a large, heterogeneous set of financial data points into a single, explainable, comparable score so investors and researchers can *screen* candidates, *compare* assets within a peer set, and *track* changes over time — then apply their own valuation, risk, and time-horizon judgment.

**What is NOT in scope (v1):**

- It is **not** a recommendation engine or "magic buy number."
- It is **not** investment advice and is explicitly labeled as such.
- It does **not** currently consume live market data — see [Data Sources](docs/DATA_SOURCES.md) for the honest status and the live-data roadmap.

**How is credibility maintained?** The engine ships with a deterministic simulated data layer (for reproducible, end-to-end CI), a validation script (`scripts/validate.py`), and a reproducible backtest/accuracy benchmark (`scripts/backtest.py` + [Backtesting docs](docs/BACKTESTING.md)).

---

## 📊 Overview





The **NOW Quant Framework** is an open-source, multi-factor quantitative ranking engine that evaluates global financial assets across 20+ asset classes. It powers the **NOW Index** — a public ranking system that scores assets from 0-100 based on 10 independent factors. In this context, the score is a relative composite ranking used to compare assets within the model universe; it is not a standalone recommendation to buy or sell a security.

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
│   ├── backtest.py          # Reproducible backtest/accuracy benchmark
│   ├── export_static.py     # Export static JSON for GitHub Pages
│   └── generate_reports.py  # Daily/weekly/monthly reports
├── tests/                   # Test suite
│   ├── test_scoring.py      # Engine tests
│   └── test_api.py          # API integration tests
├── .github/workflows/       # CI/CD pipelines
│   ├── ci.yml               # Continuous integration
│   ├── deploy.yml           # Hourly deployment
│   └── pages.yml            # GitHub Pages static deployment
├── docs/                    # Documentation
│   ├── DATA_SOURCES.md      # Data layer & live-data roadmap
│   ├── BACKTESTING.md       # Backtest methodology & validation
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

## ❓ What Score Should I Buy? — How to Read the NOW Score

> **TL;DR — There is no single "magic number" to buy.** The NOW Score is a *relative composite ranking* (0–100), not an absolute measure of value, not a price target, and not a standalone buy/sell signal. A score only has meaning *within the peer universe it is ranked against* and *given the factor mix that produced it*.

The most common question people ask when they see a 0–100 score is: *"What score should I buy for the stock?"* This section explains the logic properly.

### 1. The core principle: it's a ranking, not a verdict

Every score is computed by the **NOWScorer** from 10 weighted factors (see the table above). Assets are then **sorted by score and ranked**. So:

- A **score of 80** does *not* mean "the stock is 80% cheap" or "you have an 80% chance of profit."
- It means **the asset's combined factor profile ranks in the ~80th percentile of the current model universe** on the weighted dimensions the model cares about.
- The same numerical score can imply *different things at different times*:
  - If the whole universe is strong, a score of 65 might be **bottom-half**.
  - If the whole universe is weak, a score of 65 might be **top-10**.

Because the absolute number shifts with the universe, **rank and factor composition always matter more than the raw number.** This is why the site shows both the score *and* the rank (#1, #25, #87…) together.

### 2. Reading the rating bands as an initial filter

Think of the rating scale as a **screening filter**, not a trigger:

| Rating | Score | What it suggests for a potential buyer | Not a substitute for… |
|--------|-------|----------------------------------------|------------------------|
| Excellent | 90–100 | Top-conviction candidates — strong on almost every factor. Still verify the **valuation level and entry timing** before buying. | Entry point, position sizing, future earnings revisions |
| Strong | 80–89 | High-conviction names worth deep research. Open a watchlist and do the factor deep-dive below. | Due diligence on moat, management, competitive position |
| Good | 70–79 | Solid fundamentals, but **check which factors are pulling the score down** and whether they matter to your strategy. | Understanding *why* the score isn't higher |
| Fair | 60–69 | Adequate with some concerns — requires extra due diligence and usually a *valuation or risk discount*. | The specific weakness (e.g., low growth, high beta) |
| Moderate | 50–59 | Below-average composite — caution warranted. Often only suitable for **tactical or contrarian** reasons. | A clear, falsifiable thesis for why the model is wrong |
| Weak | <50 | Significant risk factors on the composite. Generally **avoid** unless you have strong independent reasons that the model is missing. | Independent research that overrides the model |

> ⚠️ **High score ≠ cheap, and low score ≠ expensive.** Momentum, Quality, and Growth carry heavy weight, so a high-score asset can be *expensive* on valuation. Conversely, a low-score asset can be statistically cheap (value factor) but struggling on quality/momentum — the classic "value trap" profile.

### 3. The 4 things that matter more than the number

If someone asks *"what score should I buy?"*, the honest answer is: **no fixed threshold — but here is what to check before buying:**

1. **Factor composition** — *Why* is the score what it is? Open the company profile and look at the 10-factor breakdown.
   - Is it a high-score stock driven mostly by **Momentum**? That's fragile — momentum can reverse fast.
   - Is it driven by **Quality + Financial Strength**? That's more durable.
   - Does the factor mix match **your** investing style (growth vs. value vs. income vs. low-risk)?

2. **Score trend** — Is the score *rising* or *falling*?
   - Rising scores (see **Most Improved** leaderboards and the history chart) mean the composite is strengthening.
   - Falling scores mean the composite is deteriorating — even a currently "good" score may be a warning.

3. **Context** — Same score, different meaning:
   - A 75 **REIT** is not directly comparable to a 75 **crypto** or 75 **US mega-cap**.
   - Always compare within the same **asset class / sector / peer group** (use the filter and compare tools).

4. **The universe itself** — Top-100 *rank* tells you the asset is strong *relative to the tracked universe*. The rank is the more stable, interpretable signal than the raw number.

### 4. A step-by-step decision framework

A practical "should I even consider buying?" checklist for any stock with a NOW Score:

| Step | Action | Tool on the site |
|------|--------|------------------|
| 1. Screen | Start with **Top 100 / Strong (80+) / Excellent (90+)** bands as a watchlist, not an order ticket. | Leaderboards, Full Ranking |
| 2. Factor breakdown | Open the company page; confirm the score is driven by factors that fit your strategy (quality/value vs. momentum). | Company Profile → Factor Breakdown |
| 3. Check trend | Is the score rising or falling over 1W / 1M / 1Y? Rising = stronger composite. | Company Profile → Historical Scores, Most Improved |
| 4. Compare peers | Compare the asset to its asset-class and sector peers, not across unrelated classes. | Compare Tool, Filter |
| 5. Align horizon & risk | High-momentum scores suit shorter horizons; quality/financial-strength scores suit longer horizons. Match to your time horizon and risk tolerance. | Methodology |
| 6. Independent confirmation | Verify with your own analysis: valuation, competitive position, macro context, and your portfolio allocation. **The score is a decision-support tool, not financial advice.** | — |

### Bottom line

> **Use the score as a first-class screen, then as a hypothesis to verify — not as a buy order.** A reasonable rule of thumb used by many NOW users:
>
> - **≥ 80 (Strong/Excellent)** → worth researching seriously; enter only with your own valuation & timing check.
> - **70–79 (Good)** → worth a watchlist; buy only if the factor mix and trend justify it.
> - **< 70** → generally requires a specific, well-supported reason before buying.
>
> And always remember: the NOW Score is a **relative composite ranking** that changes as the market and the model universe change. There is no fixed "buy above X" rule — and anyone who tells you there is, is not reading the score correctly.

*The NOW Score is provided for research and educational purposes. It is not individualized investment advice. Always do your own due diligence and consider consulting a licensed financial advisor before making investment decisions.*

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

## 🧪 Backtesting & Validation

Quantitative tools rely on credibility. This repository ships with a
reproducible validation pipeline so results are auditable and trustworthy:

| Tool | Purpose |
|------|---------|
| [`scripts/validate.py`](scripts/validate.py) | Hard integrity checks: score bounds, no NaN, rank contiguity, distribution sanity (wired into CI) |
| [`scripts/backtest.py`](scripts/backtest.py) | Reproducible accuracy benchmark — rank stability (Kendall tau), score drift, and per-factor drift across snapshots |
| [`docs/BACKTESTING.md`](docs/BACKTESTING.md) | Methodology, metrics, and how to interpret results |
| [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) | Honest data-layer status and the roadmap to live market data |

### Run the backtest

```bash
python scripts/backtest.py
# or write a Markdown report
python scripts/backtest.py --out docs/reports/backtest_report.md
```

> **Note:** The engine currently ships with a deterministic
> `SimulatedDataProvider` so the full stack is reproducible end-to-end. The
> backtest measures *mechanical stability* (is the pipeline deterministic and
> stable?), not predictive alpha. When a live data provider is wired in (see
> [Data Sources](docs/DATA_SOURCES.md)), the same harness should be extended
> with forward-return analysis.

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
