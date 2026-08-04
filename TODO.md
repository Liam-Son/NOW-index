# Deploy Momentum Please to GitHub Pages - TODO

## Goal
Make the Momentum Please site (NOW-index repo) live on GitHub Pages by pre-generating all data into static JSON and adding a static-data fallback to the frontend, since GitHub Pages cannot run the FastAPI backend.

## Steps
- [x] 1. Create `scripts/export_static.py`
  - Pre-generate health, stats, all 49 scored assets, leaderboard, ranking, company profiles + history into a single `static_data/now_data.json`
  - ✅ Verified: `python scripts/export_static.py` → 49 assets, 17 leaderboard categories, 49 company profiles
- [x] 2. Edit `website/js/app.js`
  - ✅ `apiFetch` now supports POST + JSON headers; `/refresh` uses `method: 'POST'`
  - ✅ Added static-data fallback: `apiFetch` tries live API first, falls back to `static_data/now_data.json`
  - ✅ `API_BASE` configurable via `window.NOW_API_BASE` for GitHub Pages sub-path
  - ✅ Client-side resolvers for /health, /stats, /top10/25/50/100, /leaderboard, /ranking, /company, /search, /compare, /history
  - ✅ JS syntax verified with `node --check`
- [x] 3. Create `.github/workflows/pages.yml`
  - GitHub Actions workflow to regenerate static data, assemble `_site/`, deploy to GitHub Pages
- [ ] 4. Enable GitHub Pages on `Liam-Son/NOW-index` via `gh api` (build source: workflow)
- [ ] 5. Commit and push to `main`
- [ ] 6. Verify the site is live at https://liam-son.github.io/NOW-index/
