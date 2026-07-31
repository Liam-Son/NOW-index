/**
 * Momentum Please — NOW Index Website
 * Interactive Dashboard & Ranking UI
 */

const API_BASE = '/api';

// ─── State ──────────────────────────────────────────────────────────────────
const state = {
    currentView: 'dashboard',
    scores: [],
    leaderboard: {},
    searchResults: [],
    watchlist: JSON.parse(localStorage.getItem('now_watchlist') || '[]'),
    theme: localStorage.getItem('now_theme') || 'dark',
};

// ─── API Client ─────────────────────────────────────────────────────────────
async function apiFetch(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
    }
    return res.json();
}

// ─── Navigation ─────────────────────────────────────────────────────────────
function navigate(view, params = {}) {
    state.currentView = view;
    document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));
    const link = document.querySelector(`.sidebar-link[data-view="${view}"]`);
    if (link) link.classList.add('active');

    const content = document.getElementById('content');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    switch (view) {
        case 'dashboard': renderDashboard(content); break;
        case 'leaderboard': renderLeaderboard(content); break;
        case 'ranking': renderRanking(content); break;
        case 'company': renderCompanySearch(content, params.ticker); break;
        case 'compare': renderCompare(content); break;
        case 'watchlist': renderWatchlist(content); break;
        case 'simulator': renderSimulator(content); break;
        case 'methodology': renderMethodology(content); break;
        case 'blog': renderBlog(content); break;
        case 'docs': renderDocs(content); break;
        default: renderDashboard(content);
    }
}

// ─── Dashboard ──────────────────────────────────────────────────────────────
async function renderDashboard(content) {
    try {
        const [health, stats, top10] = await Promise.all([
            apiFetch('/health'),
            apiFetch('/stats'),
            apiFetch('/top10'),
        ]);

        content.innerHTML = `
            <div class="grid-4" style="margin-bottom:24px;">
                <div class="stat-card">
                    <div class="stat-label">Total Assets</div>
                    <div class="stat-value">${stats.total_assets.toLocaleString()}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Average NOW Score</div>
                    <div class="stat-value">${stats.avg_score.toFixed(1)}</div>
                    <div class="stat-change" style="color:var(--text-muted)">out of 100</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Top Score</div>
                    <div class="stat-value" style="color:var(--accent)">${stats.top_score.toFixed(1)}</div>
                    <div class="stat-change" style="color:var(--text-secondary)">${stats.top_ticker || 'N/A'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Asset Classes</div>
                    <div class="stat-value">${Object.keys(stats.asset_class_breakdown || {}).length}</div>
                    <div class="stat-change" style="color:var(--text-muted)">supported</div>
                </div>
            </div>

            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Top 10 Rankings</div>
                        <button class="btn btn-sm" onclick="navigate('leaderboard')">View All →</button>
                    </div>
                    ${renderRankingTable(top10.results.slice(0, 5))}
                </div>
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Score Distribution</div>
                    </div>
                    <div style="padding:10px;">
                        ${renderDistribution(stats.distribution)}
                    </div>
                </div>
            </div>

            <div class="card" style="margin-top:16px;">
                <div class="card-header">
                    <div class="card-title">Top 10 Asset Scores</div>
                </div>
                <div id="scoreChart" style="height:300px;"></div>
            </div>
        `;

        // Render chart
        const chartData = top10.results.slice(0, 10).reverse();
        const options = {
            chart: { type: 'bar', height: 300, background: 'transparent',
                toolbar: { show: false }, foreColor: '#8899b4' },
            series: [{
                name: 'NOW Score',
                data: chartData.map(s => s.score)
            }],
            xaxis: {
                categories: chartData.map(s => s.ticker),
                labels: { style: { colors: '#8899b4', fontSize: '11px' } }
            },
            yaxis: { max: 100, labels: { style: { colors: '#8899b4', fontSize: '11px' } } },
            colors: ['#00d4aa'],
            plotOptions: {
                bar: { borderRadius: 4, columnWidth: '60%' }
            },
            grid: { borderColor: '#1e3a5f', strokeDashArray: 3 },
            tooltip: {
                theme: 'dark',
                y: { formatter: v => v.toFixed(1) + ' pts' }
            }
        };
        const chart = new ApexCharts(document.getElementById('scoreChart'), options);
        chart.render();
    } catch (err) {
        content.innerHTML = `<div class="card"><p style="color:var(--red)">Error loading dashboard: ${err.message}</p></div>`;
    }
}

function renderDistribution(dist) {
    if (!dist) return '<p style="color:var(--text-muted)">No data</p>';
    const labels = {
        excellent_90_100: { label: 'Excellent (90-100)', color: 'var(--accent)' },
        strong_80_89: { label: 'Strong (80-89)', color: 'var(--accent-secondary)' },
        good_70_79: { label: 'Good (70-79)', color: 'var(--accent-orange)' },
        fair_60_69: { label: 'Fair (60-69)', color: 'var(--accent-purple)' },
        moderate_50_59: { label: 'Moderate (50-59)', color: 'var(--yellow)' },
        weak_below_50: { label: 'Weak (<50)', color: 'var(--red)' },
    };
    const total = Object.values(dist).reduce((a, b) => a + b, 0);
    return Object.entries(dist).map(([key, count]) => {
        const info = labels[key] || { label: key, color: 'var(--text-muted)' };
        const pct = total > 0 ? (count / total * 100).toFixed(1) : 0;
        return `
            <div style="margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                    <span style="color:var(--text-secondary)">${info.label}</span>
                    <span style="color:var(--text-primary);font-weight:600;">${count}</span>
                </div>
                <div style="height:4px;background:var(--bg-tertiary);border-radius:2px;overflow:hidden;">
                    <div style="height:100%;width:${pct}%;background:${info.color};border-radius:2px;transition:width 0.5s;"></div>
                </div>
            </div>
        `;
    }).join('');
}

// ─── Leaderboard ────────────────────────────────────────────────────────────
async function renderLeaderboard(content) {
    try {
        const data = await apiFetch('/leaderboard');
        const categories = [
            { key: 'top_10', label: '🏆 Top 10', icon: 'trophy' },
            { key: 'top_25', label: '📋 Top 25', icon: 'list' },
            { key: 'top_50', label: '📋 Top 50', icon: 'list' },
            { key: 'top_100', label: '📋 Top 100', icon: 'list' },
            { key: 'most_improved_today', label: '📈 Most Improved Today', icon: 'arrow-up' },
            { key: 'most_improved_week', label: '📈 Most Improved This Week', icon: 'arrow-up' },
            { key: 'most_improved_month', label: '📈 Most Improved This Month', icon: 'arrow-up' },
            { key: 'highest_quality', label: '⭐ Highest Quality', icon: 'star' },
            { key: 'highest_value', label: '💎 Highest Value', icon: 'gem' },
            { key: 'highest_growth', label: '🚀 Highest Growth', icon: 'rocket' },
            { key: 'highest_momentum', label: '⚡ Highest Momentum', icon: 'bolt' },
            { key: 'lowest_risk', label: '🛡️ Lowest Risk', icon: 'shield' },
            { key: 'most_undervalued', label: '🔍 Most Undervalued', icon: 'search' },
            { key: 'best_long_term', label: '🌳 Best Long-Term', icon: 'tree' },
            { key: 'best_dividend', label: '💰 Best Dividend', icon: 'money-bill' },
            { key: 'best_innovation', label: '🤖 Best AI/Innovation', icon: 'robot' },
            { key: 'best_financial_strength', label: '🏦 Best Financial Strength', icon: 'bank' },
        ];

        let html = `<div class="card"><div class="card-header"><div class="card-title">Leaderboards</div></div>`;
        html += `<div class="tabs" id="leaderboardTabs">`;
        categories.forEach((cat, i) => {
            html += `<div class="tab ${i === 0 ? 'active' : ''}" data-category="${cat.key}" onclick="switchLeaderboard('${cat.key}')">${cat.label}</div>`;
        });
        html += `</div></div>`;
        html += `<div id="leaderboardContent">${renderRankingTable(data.top_10, 'top_10')}</div>`;
        content.innerHTML = html;

        window.leaderboardData = data;
    } catch (err) {
        content.innerHTML = `<div class="card"><p style="color:var(--red)">Error: ${err.message}</p></div>`;
    }
}

function switchLeaderboard(category) {
    document.querySelectorAll('#leaderboardTabs .tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab[data-category="${category}"]`).classList.add('active');
    const data = window.leaderboardData?.[category];
    document.getElementById('leaderboardContent').innerHTML = data ? renderRankingTable(data, category) : '<p>No data</p>';
}

// ─── Ranking Table ──────────────────────────────────────────────────────────
function renderRankingTable(scores, category) {
    if (!scores || !scores.length) return '<p style="color:var(--text-muted);padding:20px;">No data available</p>';

    const isImprovement = category?.includes('improved');
    const isFactor = category?.includes('highest_') || category?.includes('best_');

    return `
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Ticker</th>
                        <th>Name</th>
                        <th>Score</th>
                        ${isImprovement ? '<th>Change</th>' : '<th>Chg</th>'}
                        <th>Asset Class</th>
                        <th>Country</th>
                        <th>Sector</th>
                    </tr>
                </thead>
                <tbody>
                    ${scores.map((s, i) => {
                        const rankChange = s.rank_change || 0;
                        const changeIcon = rankChange > 0 ? 'fa-caret-up rank-up' : rankChange < 0 ? 'fa-caret-down rank-down' : 'fa-minus rank-same';
                        const scoreClass = s.score >= 85 ? 'score-excellent' : s.score >= 75 ? 'score-strong' : s.score >= 65 ? 'score-good' : s.score >= 55 ? 'score-fair' : 'score-weak';
                        return `
                            <tr class="clickable" onclick="navigate('company', {ticker:'${s.ticker}'})">
                                <td style="font-family:var(--font-mono);font-weight:600;">${s.rank || i + 1}</td>
                                <td style="font-family:var(--font-mono);font-weight:600;color:var(--accent);">${s.ticker}</td>
                                <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${s.name}</td>
                                <td><span class="score-badge ${scoreClass}">${s.score.toFixed(1)}</span></td>
                                <td><i class="fa-solid ${changeIcon}"></i> ${Math.abs(rankChange)}</td>
                                <td style="font-size:12px;color:var(--text-secondary)">${s.asset_class?.replace(/_/g,' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                                <td style="font-size:12px;color:var(--text-secondary)">${s.country || '-'}</td>
                                <td style="font-size:12px;color:var(--text-secondary)">${s.sector || '-'}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ─── Full Ranking ───────────────────────────────────────────────────────────
async function renderRanking(content) {
    try {
        const data = await apiFetch('/ranking?per_page=100');
        content.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Full Ranking <span style="color:var(--text-muted);font-weight:400;font-size:12px;">(${data.total} assets)</span></div>
                    <div class="card-subtitle">Page ${data.page} of ${data.total_pages}</div>
                </div>
                ${renderRankingTable(data.results)}
            </div>
            <div style="display:flex;justify-content:center;gap:8px;margin-top:16px;">
                <button class="btn btn-sm" onclick="loadRankingPage(${data.page - 1})" ${data.page <= 1 ? 'disabled' : ''}>← Previous</button>
                <span style="color:var(--text-muted);font-size:13px;display:flex;align-items:center;">Page ${data.page} / ${data.total_pages}</span>
                <button class="btn btn-sm" onclick="loadRankingPage(${data.page + 1})" ${data.page >= data.total_pages ? 'disabled' : ''}>Next →</button>
            </div>
        `;
    } catch (err) {
        content.innerHTML = `<div class="card"><p style="color:var(--red)">Error: ${err.message}</p></div>`;
    }
}

async function loadRankingPage(page) {
    const content = document.getElementById('content');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    try {
        const data = await apiFetch(`/ranking?per_page=100&page=${page}`);
        content.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Full Ranking <span style="color:var(--text-muted);font-weight:400;font-size:12px;">(${data.total} assets)</span></div>
                    <div class="card-subtitle">Page ${data.page} of ${data.total_pages}</div>
                </div>
                ${renderRankingTable(data.results)}
            </div>
            <div style="display:flex;justify-content:center;gap:8px;margin-top:16px;">
                <button class="btn btn-sm" onclick="loadRankingPage(${data.page - 1})" ${data.page <= 1 ? 'disabled' : ''}>← Previous</button>
                <span style="color:var(--text-muted);font-size:13px;display:flex;align-items:center;">Page ${data.page} / ${data.total_pages}</span>
                <button class="btn btn-sm" onclick="loadRankingPage(${data.page + 1})" ${data.page >= data.total_pages ? 'disabled' : ''}>Next →</button>
            </div>
        `;
    } catch (err) {
        content.innerHTML = `<div class="card"><p style="color:var(--red)">Error: ${err.message}</p></div>`;
    }
}

// ─── Company Profile ───────────────────────────────────────────────────────
async function renderCompanySearch(content, ticker) {
    content.innerHTML = `
        <div class="card">
            <div class="card-header">
                <div class="card-title">Company Profile</div>
            </div>
            <div style="display:flex;gap:8px;margin-bottom:16px;">
                <input type="text" id="companyTicker" value="${ticker || ''}" placeholder="Enter ticker (e.g., AAPL)" style="flex:1;padding:10px 14px;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius);color:var(--text-primary);font-size:14px;font-family:var(--font-mono);" onkeydown="if(event.key==='Enter') loadCompany()" />
                <button class="btn btn-primary" onclick="loadCompany()">Search</button>
            </div>
            <div id="companyResult"></div>
        </div>
    `;
    if (ticker) loadCompany();
}

async function loadCompany() {
    const ticker = document.getElementById('companyTicker')?.value?.trim()?.toUpperCase();
    const resultDiv = document.getElementById('companyResult');
    if (!ticker) return;

    resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const data = await apiFetch(`/company/${ticker}`);
        const s = data.now_score;
        const factors = s.factors;

        resultDiv.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:20px;">
                <div>
                    <h2 style="font-size:22px;font-weight:700;">${s.ticker} <span style="font-size:14px;font-weight:400;color:var(--text-secondary);">${s.name}</span></h2>
                    <div style="display:flex;gap:12px;margin-top:6px;font-size:12px;color:var(--text-muted);">
                        <span>${s.asset_class?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                        <span>${s.country || '-'}</span>
                        <span>${s.sector || '-'}</span>
                        <span>${s.exchange || '-'}</span>
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:36px;font-weight:800;font-family:var(--font-mono);color:${s.score >= 80 ? 'var(--accent)' : s.score >= 60 ? 'var(--accent-orange)' : 'var(--red)'};">${s.score.toFixed(1)}</div>
                    <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;">NOW Score</div>
                    <div style="font-size:11px;margin-top:4px;color:var(--text-secondary);">Rank #${s.rank} ${s.rank_change > 0 ? `<span style="color:var(--green)">↑${s.rank_change}</span>` : s.rank_change < 0 ? `<span style="color:var(--red)">↓${Math.abs(s.rank_change)}</span>` : ''}</div>
                </div>
            </div>

            <div class="grid-2">
                <div class="card">
                    <div class="card-header"><div class="card-title">Factor Breakdown</div></div>
                    <div class="factor-bar-container">
                        ${Object.entries(factors).filter(([k]) => k !== 'total').map(([key, val]) => {
                            const maxWeight = {quality:15,value:15,growth:12,momentum:12,low_risk:10,undervalued:10,long_term:8,dividend:6,innovation:6,financial_strength:6};
                            const max = maxWeight[key] || 10;
                            const pct = (val / max * 100).toFixed(0);
                            const colors = {quality:'#00d4aa',value:'#3b82f6',growth:'#22c55e',momentum:'#f59e0b',low_risk:'#8b5cf6',undervalued:'#ef4444',long_term:'#06b6d4',dividend:'#f97316',innovation:'#a855f7',financial_strength:'#14b8a6'};
                            return `
                                <div class="factor-bar">
                                    <span class="factor-label">${key.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase())}</span>
                                    <div class="factor-track">
                                        <div class="factor-fill" style="width:${pct}%;background:${colors[key] || '#00d4aa'};"></div>
                                    </div>
                                    <span class="factor-value">${val.toFixed(1)}/${max}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <div>
                    <div class="card" style="margin-bottom:16px;">
                        <div class="card-header"><div class="card-title">Historical Scores</div></div>
                        <div id="historyChart" style="height:200px;"></div>
                    </div>

                    <div class="card">
                        <div class="card-header"><div class="card-title">Score Comparison</div></div>
                        <table>
                            <tr><td style="font-size:12px;color:var(--text-muted)">Today</td><td style="font-family:var(--font-mono);font-weight:600;">${s.score.toFixed(1)}</td></tr>
                            <tr><td style="font-size:12px;color:var(--text-muted)">Yesterday</td><td style="font-family:var(--font-mono);">${s.score_yesterday?.toFixed(1) || '-'}</td></tr>
                            <tr><td style="font-size:12px;color:var(--text-muted)">Last Week</td><td style="font-family:var(--font-mono);">${s.score_last_week?.toFixed(1) || '-'}</td></tr>
                            <tr><td style="font-size:12px;color:var(--text-muted)">Last Month</td><td style="font-family:var(--font-mono);">${s.score_last_month?.toFixed(1) || '-'}</td></tr>
                            <tr><td style="font-size:12px;color:var(--text-muted)">Last Year</td><td style="font-family:var(--font-mono);">${s.score_last_year?.toFixed(1) || '-'}</td></tr>
                        </table>
                        <div style="margin-top:12px;">
                            <button class="btn btn-sm" onclick="addToWatchlist('${s.ticker}')"><i class="fa-solid fa-star"></i> Add to Watchlist</button>
                            <button class="btn btn-sm" onclick="navigate('compare', {tickers:'${s.ticker}'})" style="margin-left:4px;"><i class="fa-solid fa-not-equal"></i> Compare</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Render history chart
        const history = data.history || [];
        if (history.length > 0) {
            const histOptions = {
                chart: { type: 'line', height: 200, background: 'transparent',
                    toolbar: { show: false }, foreColor: '#8899b4' },
                series: [{ name: 'NOW Score', data: history.map(h => h.score) }],
                xaxis: {
                    categories: history.map(h => h.timestamp?.slice(0, 10) || ''),
                    labels: { style: { colors: '#8899b4', fontSize: '10px' }, show: history.length <= 30 }
                },
                yaxis: { min: 0, max: 100, labels: { style: { colors: '#8899b4', fontSize: '10px' } } },
                colors: ['#00d4aa'],
                stroke: { curve: 'smooth', width: 2 },
                grid: { borderColor: '#1e3a5f', strokeDashArray: 3 },
                tooltip: { theme: 'dark' }
            };
            new ApexCharts(document.getElementById('historyChart'), histOptions).render();
        }
    } catch (err) {
        resultDiv.innerHTML = `<p style="color:var(--red)">Error: ${err.message}</p>`;
    }
}

// ─── Compare Tool ───────────────────────────────────────────────────────────
async function renderCompare(content, initialTickers) {
    content.innerHTML = `
        <div class="card">
            <div class="card-header"><div class="card-title">Comparison Tool</div></div>
            <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
                <input type="text" id="compareTickers" value="${initialTickers || ''}" placeholder="AAPL,MSFT,GOOGL (comma-separated)" style="flex:1;min-width:200px;padding:10px 14px;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius);color:var(--text-primary);font-size:13px;font-family:var(--font-mono);" onkeydown="if(event.key==='Enter') loadCompare()" />
                <button class="btn btn-primary" onclick="loadCompare()">Compare</button>
            </div>
            <div id="compareResult"></div>
        </div>
    `;
    if (initialTickers) loadCompare();
}

async function loadCompare() {
    const tickers = document.getElementById('compareTickers')?.value?.trim();
    const resultDiv = document.getElementById('compareResult');
    if (!tickers) return;

    resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const data = await apiFetch(`/compare?tickers=${tickers}`);
        const results = data.results.filter(r => !r.error);
        if (results.length < 2) {
            resultDiv.innerHTML = '<p style="color:var(--red)">Need at least 2 valid tickers to compare</p>';
            return;
        }

        const factorKeys = ['quality', 'value', 'growth', 'momentum', 'low_risk', 'undervalued',
            'long_term', 'dividend', 'innovation', 'financial_strength'];

        let html = `
            <div class="compare-grid" style="grid-template-columns:auto ${results.map(() => '1fr').join(' ')};">
                <div class="compare-header">Metric</div>
                ${results.map(r => `<div class="compare-header" style="text-align:center;">${r.ticker}</div>`).join('')}

                <div class="compare-cell" style="font-weight:600;">NOW Score</div>
                ${results.map(r => `
                    <div class="compare-cell" style="justify-content:center;">
                        <span class="score-badge ${r.now_score?.score >= 80 ? 'score-excellent' : r.now_score?.score >= 60 ? 'score-strong' : 'score-fair'}">${r.now_score?.score?.toFixed(1) || '-'}</span>
                    </div>
                `).join('')}

                <div class="compare-cell" style="font-weight:600;">Rank</div>
                ${results.map(r => `
                    <div class="compare-cell" style="justify-content:center;font-family:var(--font-mono);">#${r.now_score?.rank || '-'}</div>
                `).join('')}

                ${factorKeys.map(fk => `
                    <div class="compare-cell" style="font-size:12px;color:var(--text-secondary);">${fk.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase())}</div>
                    ${results.map(r => {
                        const val = r.now_score?.factors?.[fk] || 0;
                        const max = {quality:15,value:15,growth:12,momentum:12,low_risk:10,undervalued:10,long_term:8,dividend:6,innovation:6,financial_strength:6};
                        const pct = (val / (max[fk] || 10) * 100).toFixed(0);
                        return `<div class="compare-cell" style="flex-direction:column;gap:2px;">
                            <span style="font-family:var(--font-mono);font-size:12px;">${val.toFixed(1)}</span>
                            <div style="height:3px;width:100%;background:var(--bg-tertiary);border-radius:2px;overflow:hidden;">
                                <div style="height:100%;width:${pct}%;background:var(--accent);border-radius:2px;"></div>
                            </div>
                        </div>`;
                    }).join('')}
                `).join('')}

                <div class="compare-cell" style="font-weight:600;">Market Cap</div>
                ${results.map(r => `
                    <div class="compare-cell" style="justify-content:center;font-family:var(--font-mono);font-size:12px;">
                        ${r.now_score?.market_cap ? '$' + (r.now_score.market_cap / 1e12).toFixed(2) + 'T' : '-'}
                    </div>
                `).join('')}

                <div class="compare-cell" style="font-weight:600;">Country</div>
                ${results.map(r => `
                    <div class="compare-cell" style="justify-content:center;font-size:12px;">${r.now_score?.country || '-'}</div>
                `).join('')}
            </div>
        `;

        resultDiv.innerHTML = html;
    } catch (err) {
        resultDiv.innerHTML = `<p style="color:var(--red)">Error: ${err.message}</p>`;
    }
}

// ─── Watchlist ──────────────────────────────────────────────────────────────
function renderWatchlist(content) {
    if (state.watchlist.length === 0) {
        content.innerHTML = `
            <div class="card" style="text-align:center;padding:40px;">
                <i class="fa-solid fa-star" style="font-size:40px;color:var(--text-muted);margin-bottom:16px;"></i>
                <h3 style="color:var(--text-secondary);margin-bottom:8px;">Your Watchlist is Empty</h3>
                <p style="color:var(--text-muted);font-size:13px;margin-bottom:16px;">Search for assets and add them to your watchlist to track their NOW Scores.</p>
                <button class="btn btn-primary" onclick="navigate('company')">Search Assets</button>
            </div>
        `;
        return;
    }

    content.innerHTML = `
        <div class="card">
            <div class="card-header">
                <div class="card-title">Your Watchlist <span style="font-weight:400;font-size:12px;color:var(--text-muted);">(${state.watchlist.length} assets)</span></div>
                <button class="btn btn-sm btn-primary" onclick="clearWatchlist()"><i class="fa-solid fa-trash"></i> Clear</button>
            </div>
            <div id="watchlistContent"><div class="loading"><div class="spinner"></div></div></div>
        </div>
    `;

    Promise.all(state.watchlist.map(t => apiFetch(`/company/${t}`).catch(() => null)))
        .then(results => {
            const valid = results.filter(r => r);
            document.getElementById('watchlistContent').innerHTML = renderRankingTable(valid.map(r => r.now_score));
        });
}

function addToWatchlist(ticker) {
    if (!state.watchlist.includes(ticker)) {
        state.watchlist.push(ticker);
        localStorage.setItem('now_watchlist', JSON.stringify(state.watchlist));
        alert(`${ticker} added to watchlist`);
    }
}

function clearWatchlist() {
    state.watchlist = [];
    localStorage.removeItem('now_watchlist');
    navigate('watchlist');
}

// ─── Portfolio Simulator ───────────────────────────────────────────────────
function renderSimulator(content) {
    content.innerHTML = `
        <div class="card">
            <div class="card-header"><div class="card-title">Portfolio Simulator</div></div>
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px;">Build a hypothetical portfolio and see its composite NOW Score.</p>
            <div id="simulatorForm">
                <div style="display:flex;gap:8px;margin-bottom:12px;">
                    <input type="text" id="simTicker" placeholder="Add ticker..." style="flex:1;padding:8px 12px;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius);color:var(--text-primary);font-family:var(--font-mono);" onkeydown="if(event.key==='Enter') addSimAsset()" />
                    <input type="number" id="simWeight" placeholder="Weight %" value="10" min="1" max="100" style="width:100px;padding:8px 12px;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius);color:var(--text-primary);" />
                    <button class="btn btn-sm" onclick="addSimAsset()">Add</button>
                </div>
                <div id="simAssets"></div>
                <div id="simResult" style="margin-top:16px;"></div>
                <button class="btn btn-primary" onclick="calculateSimulator()" style="margin-top:12px;">Calculate Portfolio Score</button>
            </div>
        </div>
    `;
    window.simAssets = [];
}

function addSimAsset() {
    const ticker = document.getElementById('simTicker')?.value?.trim()?.toUpperCase();
    const weight = parseFloat(document.getElementById('simWeight')?.value) || 10;
    if (!ticker) return;

    if (!window.simAssets) window.simAssets = [];
    if (window.simAssets.find(a => a.ticker === ticker)) return;

    window.simAssets.push({ ticker, weight });
    renderSimAssets();
    document.getElementById('simTicker').value = '';
}

function renderSimAssets() {
    const div = document.getElementById('simAssets');
    if (!window.simAssets?.length) {
        div.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No assets added yet. Add tickers above.</p>';
        return;
    }
    const totalWeight = window.simAssets.reduce((s, a) => s + a.weight, 0);
    div.innerHTML = window.simAssets.map((a, i) => `
        <div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);">
            <span style="font-family:var(--font-mono);font-weight:600;width:80px;">${a.ticker}</span>
            <div style="flex:1;height:4px;background:var(--bg-tertiary);border-radius:2px;overflow:hidden;">
                <div style="height:100%;width:${(a.weight / totalWeight * 100).toFixed(0)}%;background:var(--accent);border-radius:2px;"></div>
            </div>
            <span style="font-family:var(--font-mono);font-size:12px;width:60px;text-align:right;">${a.weight}%</span>
            <button class="btn btn-sm" onclick="removeSimAsset(${i})" style="color:var(--red);"><i class="fa-solid fa-xmark"></i></button>
        </div>
    `).join('');
    div.innerHTML += `<div style="text-align:right;font-size:12px;color:var(--text-muted);margin-top:4px;">Total: ${totalWeight}%</div>`;
}

function removeSimAsset(idx) {
    window.simAssets.splice(idx, 1);
    renderSimAssets();
}

async function calculateSimulator() {
    const resultDiv = document.getElementById('simResult');
    if (!window.simAssets?.length) {
        resultDiv.innerHTML = '<p style="color:var(--red)">Add at least one asset</p>';
        return;
    }

    resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const results = await Promise.all(
            window.simAssets.map(a => apiFetch(`/company/${a.ticker}`).catch(() => null))
        );

        const valid = results.filter(r => r);
        const totalWeight = window.simAssets.reduce((s, a) => s + a.weight, 0);
        let weightedScore = 0;

        valid.forEach(r => {
            const asset = window.simAssets.find(a => a.ticker === r.now_score.ticker);
            if (asset) weightedScore += (r.now_score.score * asset.weight / totalWeight);
        });

        resultDiv.innerHTML = `
            <div class="card" style="background:var(--bg-tertiary);">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:12px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">Portfolio NOW Score</div>
                        <div style="font-size:32px;font-weight:800;font-family:var(--font-mono);color:${weightedScore >= 80 ? 'var(--accent)' : weightedScore >= 60 ? 'var(--accent-orange)' : 'var(--red)'};">${weightedScore.toFixed(1)}</div>
                    </div>
                    <div>
                        <div style="font-size:12px;color:var(--text-muted);">Assets: ${valid.length}</div>
                        <div style="font-size:12px;color:var(--text-muted);">Coverage: ${valid.length}/${window.simAssets.length}</div>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        resultDiv.innerHTML = `<p style="color:var(--red)">Error: ${err.message}</p>`;
    }
}

// ─── Methodology ────────────────────────────────────────────────────────────
function renderMethodology(content) {
    content.innerHTML = `
        <div class="card" style="max-width:800px;">
            <div class="card-header"><div class="card-title">NOW Index Methodology</div></div>

            <div class="methodology-section">
                <h2>What is the NOW Score?</h2>
                <p>The NOW Score is a composite quantitative ranking (0-100) that evaluates global financial assets across 10 independent factor dimensions. It is designed to provide a single, comparable measure of investment quality applicable to any asset class.</p>
            </div>

            <div class="methodology-section">
                <h2>The 10 Factors</h2>
                <p>Each factor is scored independently and weighted according to its importance in the overall framework:</p>
                <table class="weight-table">
                    <tr><td style="font-weight:600;">Quality</td><td>15 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:15%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">ROE, profit margins, earnings stability</td></tr>
                    <tr><td style="font-weight:600;">Value</td><td>15 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:15%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">P/E, P/B, P/S, P/CF ratios</td></tr>
                    <tr><td style="font-weight:600;">Growth</td><td>12 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:12%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">Revenue, EPS, forward estimate growth</td></tr>
                    <tr><td style="font-weight:600;">Momentum</td><td>12 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:12%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">1m, 3m, 6m, 12m price momentum</td></tr>
                    <tr><td style="font-weight:600;">Low Risk</td><td>10 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:10%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">Beta, volatility, drawdown, Sharpe ratio</td></tr>
                    <tr><td style="font-weight:600;">Undervalued</td><td>10 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:10%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">Intrinsic value, PEG ratio, DCF premium</td></tr>
                    <tr><td style="font-weight:600;">Long-Term</td><td>8 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:8%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">Moat, TAM growth, secular tailwinds</td></tr>
                    <tr><td style="font-weight:600;">Dividend</td><td>6 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:6%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">Yield, growth, payout ratio, history</td></tr>
                    <tr><td style="font-weight:600;">Innovation</td><td>6 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:6%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">AI exposure, patents, R&D intensity</td></tr>
                    <tr><td style="font-weight:600;">Financial Strength</td><td>6 pts</td><td><div class="weight-bar"><div class="weight-fill" style="width:6%"></div></div></td><td style="color:var(--text-secondary);font-size:12px;">Current ratio, D/E, FCF yield, coverage</td></tr>
                </table>
            </div>

            <div class="methodology-section">
                <h2>Asset Class Support</h2>
                <p>The NOW Index supports 20+ asset classes including US stocks, international stocks, ETFs, REITs, CEFs, indices, cryptocurrencies, commodity ETFs, bonds, money market ETFs, sector ETFs, country ETFs, and preferred shares.</p>
                <p style="margin-top:8px;">New asset classes can be added without modifying the scoring engine — simply register the new class and provide a data provider.</p>
            </div>

            <div class="methodology-section">
                <h2>Refresh Cycle</h2>
                <p>NOW Scores are refreshed every hour. Each cycle:</p>
                <ul style="color:var(--text-secondary);font-size:13px;padding-left:20px;margin-top:4px;">
                    <li>Downloads new market data</li>
                    <li>Recalculates all 10 factors</li>
                    <li>Runs validation checks</li>
                    <li>Updates rankings and leaderboards</li>
                    <li>Stores historical scores in the database</li>
                    <li>Commits data changes and deploys automatically</li>
                </ul>
            </div>

            <div class="methodology-section">
                <h2>Rating Scale</h2>
                <table>
                    <tr><td style="color:var(--accent);font-weight:600;">Excellent</td><td>90-100</td><td style="color:var(--text-secondary)">Top-tier investment quality</td></tr>
                    <tr><td style="color:var(--accent-secondary);font-weight:600;">Strong</td><td>80-89</td><td style="color:var(--text-secondary)">Above-average quality</td></tr>
                    <tr><td style="color:var(--accent-orange);font-weight:600;">Good</td><td>70-79</td><td style="color:var(--text-secondary)">Solid fundamentals</td></tr>
                    <tr><td style="color:var(--accent-purple);font-weight:600;">Fair</td><td>60-69</td><td style="color:var(--text-secondary)">Adequate with some concerns</td></tr>
                    <tr><td style="color:var(--yellow);font-weight:600;">Moderate</td><td>50-59</td><td style="color:var(--text-secondary)">Below average, caution warranted</td></tr>
                    <tr><td style="color:var(--red);font-weight:600;">Weak</td><td><50</td><td style="color:var(--text-secondary)">Significant risk factors</td></tr>
                </table>
            </div>
        </div>
    `;
}

// ─── Blog / Research ────────────────────────────────────────────────────────
function renderBlog(content) {
    const posts = [
        { title: "Introducing the NOW Quant Framework", date: "2025-01-15", summary: "A comprehensive open-source framework for quantitative asset ranking and analysis.", category: "Research" },
        { title: "Multi-Factor Scoring: Beyond Simple Rankings", date: "2025-01-10", summary: "How we combine 10 independent factors into a single comparable score across 20+ asset classes.", category: "Methodology" },
        { title: "The NOW Index: A New Benchmark for Asset Quality", date: "2025-01-05", summary: "Introducing the NOW Index as a public benchmark for global asset quality measurement.", category: "Research" },
        { title: "Building a Scalable Quant Platform", date: "2024-12-20", summary: "Architecture, design decisions, and lessons learned from building the NOW platform.", category: "Engineering" },
        { title: "Factor Analysis: Quality Scoring Deep Dive", date: "2024-12-10", summary: "A detailed look at how we measure quality across ROE, profit margins, and earnings stability.", category: "Methodology" },
    ];

    content.innerHTML = `
        <div class="card">
            <div class="card-header"><div class="card-title">Blog & Research</div><div class="card-subtitle">${posts.length} articles</div></div>
            ${posts.map(post => `
                <div class="blog-card">
                    <div class="meta">${post.category} · ${post.date}</div>
                    <h3>${post.title}</h3>
                    <p>${post.summary}</p>
                </div>
            `).join('')}
        </div>
    `;
}

// ─── API Docs ───────────────────────────────────────────────────────────────
function renderDocs(content) {
    content.innerHTML = `
        <div class="card" style="max-width:800px;">
            <div class="card-header"><div class="card-title">API Documentation</div></div>
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px;">The NOW Index provides a REST API for programmatic access to rankings, scores, and asset data. Future GraphQL support is planned.</p>

            <div class="methodology-section">
                <h3>Base URL</h3>
                <p style="font-family:var(--font-mono);background:var(--bg-tertiary);padding:8px 12px;border-radius:4px;font-size:13px;">https://api.now-index.com/api</p>
            </div>

            <div class="methodology-section">
                <h3>Endpoints</h3>
                ${[
                    { method: 'GET', path: '/health', desc: 'Health check & system status' },
                    { method: 'GET', path: '/company/{ticker}', desc: 'Company profile & NOW Score' },
                    { method: 'GET', path: '/asset/{id}', desc: 'Asset details by ID' },
                    { method: 'GET', path: '/ranking', desc: 'Paginated full ranking' },
                    { method: 'GET', path: '/top10', desc: 'Top 10 assets' },
                    { method: 'GET', path: '/top25', desc: 'Top 25 assets' },
                    { method: 'GET', path: '/top50', desc: 'Top 50 assets' },
                    { method: 'GET', path: '/top100', desc: 'Top 100 assets' },
                    { method: 'GET', path: '/leaderboard', desc: 'All leaderboard categories' },
                    { method: 'GET', path: '/leaderboard/{category}', desc: 'Specific leaderboard category' },
                    { method: 'GET', path: '/search?q={query}', desc: 'Search assets by ticker/name' },
                    { method: 'GET', path: '/filter?country=&sector=&asset_class=', desc: 'Filtered ranking' },
                    { method: 'GET', path: '/compare?tickers=AAPL,MSFT', desc: 'Compare multiple assets' },
                    { method: 'GET', path: '/history?ticker=AAPL&days=365', desc: 'Historical scores' },
                    { method: 'GET', path: '/asset-classes', desc: 'List supported asset classes' },
                    { method: 'GET', path: '/stats', desc: 'Platform statistics' },
                    { method: 'POST', path: '/refresh', desc: 'Trigger ranking refresh' },
                ].map(ep => `
                    <div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;">
                        <span style="padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;background:${ep.method === 'GET' ? 'rgba(59,130,246,0.15)' : 'rgba(0,212,170,0.15)'};color:${ep.method === 'GET' ? '#3b82f6' : '#00d4aa'};">${ep.method}</span>
                        <code style="font-family:var(--font-mono);color:var(--text-primary);">${ep.path}</code>
                        <span style="color:var(--text-muted);font-size:12px;">${ep.desc}</span>
                    </div>
                `).join('')}
            </div>

            <div class="methodology-section">
                <h3>Example Response</h3>
                <pre style="background:var(--bg-tertiary);padding:12px;border-radius:6px;overflow-x:auto;font-size:12px;font-family:var(--font-mono);color:var(--text-secondary);">${JSON.stringify({
                    ticker: 'AAPL',
                    name: 'Apple Inc.',
                    score: 87.5,
                    rank: 1,
                    factors: { quality: 13.2, value: 11.0, growth: 10.5, momentum: 9.8, low_risk: 7.5, undervalued: 8.0, long_term: 6.5, dividend: 4.0, innovation: 5.5, financial_strength: 5.0 }
                }, null, 2)}</pre>
            </div>

            <div class="methodology-section">
                <h3>Interactive Docs</h3>
                <p style="color:var(--text-secondary);font-size:13px;">Full interactive API documentation is available via Swagger UI and ReDoc:</p>
                <div style="display:flex;gap:8px;margin-top:8px;">
                    <a href="/api/docs" target="_blank" class="btn btn-primary">Swagger UI</a>
                    <a href="/api/redoc" target="_blank" class="btn">ReDoc</a>
                </div>
            </div>
        </div>
    `;
}

// ─── Theme Toggle ───────────────────────────────────────────────────────────
function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.body.className = state.theme + '-mode';
    localStorage.setItem('now_theme', state.theme);
    const icon = document.getElementById('themeIcon');
    if (icon) icon.className = state.theme === 'dark' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
}

// ─── Search ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const q = searchInput.value.trim();
            if (q.length < 1) {
                searchResults.classList.remove('active');
                return;
            }
            debounceTimer = setTimeout(async () => {
                try {
                    const data = await apiFetch(`/search?q=${encodeURIComponent(q)}`);
                    if (data.results?.length) {
                        searchResults.innerHTML = data.results.slice(0, 10).map(r => `
                            <div class="search-result-item" onclick="navigate('company', {ticker:'${r.asset.ticker}'}); document.getElementById('searchResults').classList.remove('active');">
                                <div>
                                    <div class="ticker">${r.asset.ticker}</div>
                                    <div class="name">${r.asset.name}</div>
                                </div>
                                <div class="score" style="color:${r.now_score?.score >= 80 ? 'var(--accent)' : 'var(--text-muted)'};">${r.now_score?.score?.toFixed(1) || '-'}</div>
                            </div>
                        `).join('');
                        searchResults.classList.add('active');
                    } else {
                        searchResults.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:13px;">No results found</div>';
                        searchResults.classList.add('active');
                    }
                } catch {
                    searchResults.classList.remove('active');
                }
            }, 300);
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.nav-search')) {
                searchResults.classList.remove('active');
            }
        });
    }
});

// ─── Refresh ────────────────────────────────────────────────────────────────
async function refreshData() {
    try {
        await apiFetch('/refresh');
        const stamp = document.getElementById('refreshTime');
        if (stamp) stamp.textContent = new Date().toLocaleTimeString();
        navigate(state.currentView);
    } catch (err) {
        console.error('Refresh failed:', err);
    }
}

// ─── Auto-refresh ───────────────────────────────────────────────────────────
setInterval(async () => {
    const stamp = document.getElementById('refreshTime');
    if (stamp) stamp.textContent = new Date().toLocaleTimeString();
}, 60000);

// ─── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    navigate('dashboard');
    refreshData();
});
