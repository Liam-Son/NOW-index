# Backtesting & Validation

Quantitative tools live or die on credibility. This document explains how the
NOW Index scores are **validated** and how you can reproduce the accuracy
benchmark yourself.

## What we validate

There are two distinct, and easy-to-confuse, kinds of validation:

1. **Mechanical / pipeline validation** *(currently implemented)* — proves the
   scoring engine is deterministic, stable, and free of bugs. It measures
   *rank persistence* and *score drift* between consecutive snapshots.
2. **Statistical / predictive accuracy** *(requires real data)* — proves the
   model has predictive power against forward returns. This is only meaningful
   with live market data and a sufficiently long history.

This repository currently ships **#1** because the data layer is simulation-first
(see `docs/DATA_SOURCES.md`). Once a real provider is wired in, the same harness
should be extended to produce **#2**.

## The backtest harness

`scripts/backtest.py` reads the SQLite snapshot history and compares each
consecutive pair of snapshots:

| Metric | What it measures | Interpretation |
|--------|------------------|----------------|
| **Kendall tau** | Rank correlation between consecutive snapshots | `1.0` = perfectly stable ranking; low values = unstable/noisy |
| **Mean abs score drift** | Average |score change| between snapshots (0–100 scale) | Small = stable, reproducible scoring |
| **Factor drift** | Mean |Δ| per factor between snapshots | Identifies which factors are most volatile |

### Run it

```bash
# From the repo root
python scripts/backtest.py

# With a minimum snapshot requirement
python scripts/backtest.py --min-snapshots 3

# Write a Markdown report
python scripts/backtest.py --out docs/reports/backtest_report.md
```

### Populate snapshots

The SQLite store is the source of truth for history. Snapshots are appended by:

```bash
python scripts/export_static.py   # seeds + scores + saves a snapshot
python scripts/hourly_refresh.py  # refresh + save a snapshot
```

The CI pipeline (`deploy.yml`) runs `hourly_refresh.py` + `validate.py` on a
schedule, so snapshots accumulate over time.

## Validation checks (`scripts/validate.py`)

In addition to the backtest, `validate.py` runs hard integrity checks:

- Score bounds (every score must be within `[0, 100]`)
- No `NaN`/`Inf` scores
- Rank integrity (ranks are contiguous `1..N`)
- Distribution sanity (e.g., at least one asset ≥ 90)
- Empty-result detection

This is wired into CI so every merge is verified.

## What "good" looks like

For a **stable, deterministic** pipeline:

- **Kendall tau** between consecutive snapshots should be **high** (≥ 0.8)
  unless the market genuinely reorders assets.
- **Mean score drift** should be **small** (a few points at most) on the 0–100
  scale.
- **Factor drift** should be low for quantitative factors (quality, value,
  financial strength) and can be higher for momentum/qualitative factors.

When real data is added, the next milestone is to validate **predictive
accuracy**: do assets with high NOW scores subsequently outperform assets with
low scores? That requires a forward-return comparison and is the proper
"credibility" test the community will look for.

## Roadmap

- [ ] Wire a real `DataProvider` (see `docs/DATA_SOURCES.md`)
- [ ] Add forward-return analysis to the backtest harness
- [ ] Report hit-rate, decile spread, and Sharpe of the top-decile portfolio
- [ ] Publish a rolling historical accuracy report in `docs/reports/`
