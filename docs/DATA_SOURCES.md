# Data Sources

> **Status: Simulation-first.** The NOW Index engine currently ships with a
> deterministic `SimulatedDataProvider` so the entire stack (scoring, ranking,
> API, website, CI) can be run and tested end-to-end without external API keys.
> This document explains exactly what that means, what real data the engine is
> designed to consume, and the roadmap for wiring live sources in.

## What the engine ingests

The scorer is **asset-class-agnostic**: it consumes a normalized, flat set of
numerical fields (see `engine/data.py` → `AssetData`) and maps them onto the 10
NOW factors. The fields fall into five groups:

| Group | Fields | Used by factors |
|-------|--------|-----------------|
| Valuation | `pe_ratio`, `pb_ratio`, `ps_ratio`, `pcf_ratio`, `peg_ratio`, `intrinsic_value`, `dcf_value` | Value, Undervalued |
| Profitability | `return_on_equity`, `return_on_assets`, `profit_margin`, `operating_margin`, `fcf_yield`, `earnings_stability` | Quality, Financial Strength |
| Growth | `revenue_growth`, `eps_growth`, `forward_eps_growth`, `earnings_growth_5y` | Growth, Long-Term |
| Risk / Momentum | `beta`, `volatility`, `max_drawdown`, `sharpe_ratio`, `sortino_ratio`, `momentum_1m/3m/6m/12m`, `rsi` | Low Risk, Momentum |
| Qualitative | `competitive_moat`, `tam_growth`, `secular_tailwind`, `patent_count`, `ai_exposure`, `insider_buying_ratio`, `dividend_*` | Long-Term, Innovation, Dividend |

A **DataProvider** only needs to implement `fetch(ticker) -> AssetData` and
`fetch_batch(tickers) -> dict[str, AssetData]`. The rest of the engine is
agnostic to where the data comes from.

## Current provider: `SimulatedDataProvider`

- Deterministic, seeded RNG (`seed=42`) so results are **reproducible** across
  runs and machines.
- Returns realistic-shaped data for **any** ticker, which makes the scoring
  pipeline, API, and dashboard fully exercisable.
- **It is not live market data.** Scores produced from it are for
  **demonstration and mechanical validation only** — never a real signal.

## Real data source roadmap

The engine is ready for real providers. The plan, in order:

1. **Price & fundamentals** — replace simulated price history / ratios with a
   vendor like **Yahoo Finance** (`yfinance`), **Alpha Vantage**, or **Financial
   Modeling Prep**. Map their API responses into `AssetData` fields.
2. **Risk & momentum** — derive `beta`, `volatility`, `max_drawdown`,
   `sharpe_ratio`, and `momentum_*` from the real price history with
   `numpy`/`pandas` (the same math the simulator currently fakes).
3. **Valuation context** — feed analyst consensus (`peg_ratio`,
   `forward_eps_growth`) and DCF/intrinsic value inputs.
4. **Qualitative** — semi-manual or NLP-tagged inputs for moat, tailwinds,
   and AI exposure.

### Design constraints

- Providers must remain **pluggable** — swapping `SimulatedDataProvider` for
  `YahooFinanceDataProvider` should require **zero changes** to the scorer.
- Every provider should be **rate-limit friendly** (batch fetching + caching).
- Every real provider must be **documented** in this file, including the
  license/TOU, fields mapped, and refresh frequency.

## Data validation & freshness

- `scripts/validate.py` runs integrity checks (score bounds, NaN, rank
  integrity, distribution sanity).
- `scripts/backtest.py` provides the historical accuracy benchmark.
- `data/*.db` (SQLite) stores historical snapshots for trend/accuracy analysis.
- The hourly refresh pipeline (`scripts/hourly_refresh.py`) is what will
  eventually pull live data and commit fresh snapshots.

