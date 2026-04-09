"""
generate_charts.py
==================
Reads processed JSON data and renders an interactive ECharts dashboard
as a standalone HTML file.

Uses Jinja2 templating to dynamically embed data into the HTML.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────── #
#  HTML Template (ECharts + Glassmorphism Dark Theme)
# ───────────────────────────────────────────────────────────── #
CHART_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Layoff Tracker 2025-2026 | Global Tech Industry Layoffs Dashboard (layoffs.fyi data)</title>
    <meta name="description" content="Interactive tech layoff tracker and dashboard for 2025-2026. Real-time data on global tech industry layoffs, startup downsizing, and corporate restructuring. Alternative to layoffs.fyi with deep insights and visualization.">
    <meta name="keywords" content="tech layoffs 2025, tech layoffs 2026, layoffs.fyi tracker, global tech layoff list, startup layoff tracker, silicon valley layoffs, industry restructuring, workforce optimization, tech job market trend, software engineer layoffs">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://tech.debugcanada.com/">
    <meta property="og:title" content="Global Tech Layoff Tracker 2025-2026 | Industry Insights">
    <meta property="og:description" content="Track live tech layoffs across the globe. Interactive charts, industry breakdowns, and company-specific data for 2025 and 2026.">
    <meta property="og:image" content="https://tech.debugcanada.com/docs/images/dashboard_en.png">

    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://tech.debugcanada.com/">
    <meta property="twitter:title" content="Tech Layoff Tracker 2025-2026 | Global Dashboard">
    <meta property="twitter:description" content="Real-time tracking of tech industry layoffs. Data-driven insights into global workforce trends.">
    <meta property="twitter:image" content="https://tech.debugcanada.com/docs/images/dashboard_en.png">

    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-E96QTV0M7W"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-E96QTV0M7W');
    </script>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

        html, body {
            overflow-x: hidden;
            width: 100%;
        }

        body {
            background: #0a0f1e;
            color: #e2e8f0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            min-height: 100vh;
            padding: 2rem 1rem;
        }

        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 20% 80%, rgba(56, 189, 248, 0.05) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(129, 140, 252, 0.05) 0%, transparent 50%),
                        radial-gradient(circle at 50% 50%, rgba(192, 132, 252, 0.03) 0%, transparent 50%);
            animation: bgPulse 15s ease-in-out infinite;
            z-index: -1;
        }
        @keyframes bgPulse {
            0%, 100% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.1) rotate(3deg); }
        }

        .container { max-width: 1280px; margin: 0 auto; width: 100%; }

        header {
            text-align: center;
            padding: 3rem 0 2rem;
            position: relative;
        }
        header h1 {
            font-size: clamp(1.75rem, 5vw, 3.5rem);
            font-weight: 900;
            background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc, #f472b6);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: gradientShift 5s ease infinite;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        header .subtitle {
            color: #64748b;
            font-size: 1.1rem;
            margin-top: 0.75rem;
            font-weight: 300;
        }
        header .badge {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.35rem 1rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.3);
        }

        /* Language Toggle */
        .lang-toggle {
            position: absolute;
            top: 1.5rem;
            right: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 999px;
            padding: 0.3rem;
            cursor: pointer;
            user-select: none;
            transition: box-shadow 0.3s ease;
        }
        .lang-toggle:hover {
            box-shadow: 0 0 20px rgba(129, 140, 252, 0.2);
        }
        .lang-btn {
            padding: 0.4rem 0.85rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748b;
            transition: all 0.3s ease;
            border: none;
            background: transparent;
            cursor: pointer;
            letter-spacing: 0.03em;
        }
        .lang-btn.active {
            background: linear-gradient(135deg, #818cf8, #c084fc);
            color: #fff;
            box-shadow: 0 2px 12px rgba(129, 140, 252, 0.4);
        }

        .glass {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 1.25rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
                        inset 0 1px 0 rgba(255, 255, 255, 0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .glass:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5),
                        inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
            margin: 2rem 0;
        }
        .kpi-card { padding: 1.75rem; text-align: center; }
        .kpi-card .label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #64748b;
            margin-bottom: 0.5rem;
        }
        .kpi-card .value { font-size: 2.75rem; font-weight: 800; line-height: 1; }
        .kpi-card .hint { font-size: 0.7rem; color: #475569; margin-top: 0.5rem; }
        .kpi-rose .value { color: #f43f5e; }
        .kpi-amber .value { color: #f59e0b; }
        .kpi-sky .value { color: #38bdf8; }
        .kpi-purple .value { color: #a78bfa; }

        .chart-grid { display: grid; gap: 1.25rem; margin: 1.25rem 0; }
        .chart-grid-2 { grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); }
        .chart-grid-1 { grid-template-columns: 1fr; }
        .chart-panel { padding: 1.5rem; }
        .chart-panel h2 {
            font-size: 1.05rem;
            font-weight: 600;
            color: #cbd5e1;
            margin-bottom: 1rem;
            padding-left: 0.5rem;
            border-left: 3px solid #818cf8;
        }
        .chart-container { width: 100%; height: 420px; }
        .chart-container-tall { height: 500px; }

        .table-panel { overflow: hidden; }
        .table-wrap {
            overflow-x: auto;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 1rem;
            width: 100%;
        }
        .recent-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 860px;
        }
        .recent-table th,
        .recent-table td {
            padding: 0.85rem 0.9rem;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            font-size: 0.85rem;
        }
        .recent-table th {
            color: #cbd5e1;
            font-weight: 700;
            background: rgba(15, 23, 42, 0.92);
            position: sticky;
            top: 0;
            z-index: 1;
        }
        .recent-table td {
            color: #94a3b8;
            word-break: break-word;
        }
        .recent-table tr:nth-child(even) td {
            background: rgba(15, 23, 42, 0.35);
        }
        .recent-table a {
            color: #38bdf8;
            text-decoration: none;
        }
        .recent-table a:hover {
            text-decoration: underline;
        }

        footer {
            text-align: center;
            padding: 3rem 0 1rem;
            color: #475569;
            font-size: 0.75rem;
            line-height: 1.8;
        }
        footer a { color: #818cf8; text-decoration: none; }
        footer a:hover { text-decoration: underline; }

        @media (max-width: 768px) {
            body { padding: 1rem 0.5rem; }
            .container { padding: 0 0.5rem; }
            header { padding: 2rem 0 1.5rem; }
            header h1 { font-size: 1.75rem; }
            .lang-toggle { position: static; margin: 0 auto 1.5rem; width: fit-content; }
            
            .kpi-grid { grid-template-columns: 1fr 1fr; gap: 0.75rem; margin: 1rem 0; }
            .kpi-card { padding: 1rem; }
            .kpi-card .value { font-size: 1.5rem; }
            .kpi-card .label { font-size: 0.6rem; }
            
            .chart-grid-2 { grid-template-columns: 1fr; }
            .chart-panel { padding: 1rem; border-radius: 1rem; }
            .chart-container { height: 320px; }
            .chart-container-tall { height: 400px; }
            
            .recent-table th, .recent-table td { padding: 0.6rem 0.5rem; font-size: 0.75rem; }
        }

        @media (max-width: 480px) {
            .kpi-grid { grid-template-columns: 1fr; }
            header h1 { font-size: 1.5rem; }
        }
    </style>
</head>
<body>

<div class="container">
    <header>
        <!-- Language Toggle -->
        <div class="lang-toggle" id="langToggle">
            <button class="lang-btn active" id="btnEN" onclick="switchLang('en')">EN</button>
            <button class="lang-btn" id="btnCN" onclick="switchLang('zh')">中文</button>
        </div>

        <h1 id="pageTitle"></h1>
        <p class="subtitle" id="pageSubtitle"></p>
        <span class="badge" id="pageBadge"></span>
    </header>

    <!-- KPI Cards -->
    <div class="kpi-grid">
        <div class="glass kpi-card kpi-rose">
            <div class="label" id="kpi1Label"></div>
            <div class="value">{{ stats.total_2025 | format_number }}</div>
            <div class="hint" id="kpi1Hint"></div>
        </div>
        <div class="glass kpi-card kpi-amber">
            <div class="label" id="kpi2Label"></div>
            <div class="value">{{ stats.total_2026 | format_number }}</div>
            <div class="hint" id="kpi2Hint"></div>
        </div>
        <div class="glass kpi-card kpi-sky">
            <div class="label" id="kpi3Label"></div>
            <div class="value">{{ stats.num_companies }}</div>
            <div class="hint" id="kpi3Hint"></div>
        </div>
        <div class="glass kpi-card kpi-purple">
            <div class="label" id="kpi4Label"></div>
            <div class="value">{{ stats.total_laid_off | format_number }}</div>
            <div class="hint">{{ stats.date_range.start }} – {{ stats.date_range.end }}</div>
        </div>
    </div>

    <!-- Charts -->
    <div class="chart-grid chart-grid-2">
        <div class="glass chart-panel">
            <h2 id="chartTitle1"></h2>
            <div id="companyChart" class="chart-container"></div>
        </div>
        <div class="glass chart-panel">
            <h2 id="chartTitle2"></h2>
            <div id="industryChart" class="chart-container"></div>
        </div>
    </div>
    <div class="chart-grid chart-grid-1">
        <div class="glass chart-panel">
            <h2 id="chartTitle3"></h2>
            <div id="monthlyChart" class="chart-container"></div>
        </div>
    </div>
    <div class="chart-grid chart-grid-2">
        <div class="glass chart-panel">
            <h2 id="chartTitle4"></h2>
            <div id="countryChart" class="chart-container"></div>
        </div>
        <div class="glass chart-panel">
            <h2 id="chartTitle5"></h2>
            <div id="reasonChart" class="chart-container"></div>
        </div>
    </div>
    <div class="chart-grid chart-grid-2">
        <div class="glass chart-panel">
            <h2 id="chartTitle6"></h2>
            <div id="monthlyCompareChart" class="chart-container"></div>
        </div>
        <div class="glass chart-panel">
            <h2 id="chartTitle7"></h2>
            <div id="percentageChart" class="chart-container"></div>
        </div>
    </div>
    <div class="chart-grid chart-grid-1">
        <div class="glass chart-panel table-panel">
            <h2 id="tableTitle1"></h2>
            <div class="table-wrap">
                <table class="recent-table">
                    <thead>
                        <tr>
                            <th id="recentHeadDate"></th>
                            <th id="recentHeadCompany"></th>
                            <th id="recentHeadLayoffs"></th>
                            <th id="recentHeadPct"></th>
                            <th id="recentHeadIndustry"></th>
                            <th id="recentHeadCountry"></th>
                            <th id="recentHeadStage"></th>
                            <th id="recentHeadSource"></th>
                        </tr>
                    </thead>
                    <tbody id="recentLayoffsBody"></tbody>
                </table>
            </div>
        </div>
    </div>
    <div class="chart-grid chart-grid-1">
        <div class="glass chart-panel">
            <h2 id="chartTitle8"></h2>
            <div id="stageHeatmapChart" class="chart-container chart-container-tall"></div>
        </div>
    </div>

    <footer id="pageFooter"></footer>
</div>

<script>
// ═══════════════════════════════════════════════════════
//  i18n Translation Dictionary
// ═══════════════════════════════════════════════════════
const i18n = {
    en: {
        title: 'Global Tech Layoff Insights',
        subtitle: '{{ subtitle_en }}',
        badge: '🔴 LIVE DATA · Auto-scraped',
        kpi1Label: '2025 TOTAL LAYOFFS',
        kpi1Hint: 'Highest on record in tech history',
        kpi2Label: '2026 YTD LAYOFFS',
        kpi2Hint: 'Over 50% YoY increase',
        kpi3Label: 'COMPANIES AFFECTED',
        kpi3Hint: 'Across ' + {{ stats.num_countries }} + ' countries',
        kpi4Label: 'TOTAL IMPACTED',
        chartTitle1: 'Top Tech Companies by Total Layoffs',
        chartTitle2: 'Layoffs by Industry',
        chartTitle3: 'Monthly Layoff Trend',
        chartTitle4: 'Layoffs by Region',
        chartTitle5: 'Key Drivers of Layoffs',
        chartTitle6: '2025 vs 2026 Monthly Comparison',
        chartTitle7: 'Layoff % Distribution',
        chartTitle8: 'Stage × Layoff Size Heatmap',
        tableTitle1: 'Recent Layoffs',
        recentHeadDate: 'Date',
        recentHeadCompany: 'Company',
        recentHeadLayoffs: 'Laid Off',
        recentHeadPct: 'Layoff %',
        recentHeadIndustry: 'Industry',
        recentHeadCountry: 'Country',
        recentHeadStage: 'Stage',
        recentHeadSource: 'Source',
        recentNoData: 'No recent layoff records available.',
        recentSourceLink: 'Open',
        footer: 'Data Sources: <a href="https://layoffs.fyi/" target="_blank">layoffs.fyi</a> · RationalFX · Major tech media<br>Disclaimer: Some figures are estimates or planned reductions<br><br>Built with Python · BeautifulSoup · Pandas · ECharts &nbsp;|&nbsp;<a href="https://github.com/frankwang0909/tech-layoff-tracker" target="_blank">⭐ View on GitHub</a> &nbsp;|&nbsp; <a href="https://layoffscanada.com" target="_blank">Layoffs Canada</a> &nbsp;|&nbsp; <a href="https://debugcanada.com" target="_blank">Debug Canada</a>',
        yAxisName: 'Layoffs',
        seriesBar: 'Layoffs',
        seriesLine: 'Trend',
        series2025: '2025',
        series2026: '2026',
        heatmapLegend: 'Event Count',
        monthLabels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        reasons: [
            { value: 45, name: 'Economic Uncertainty & Inflation' },
            { value: 30, name: 'AI Transformation & Automation' },
            { value: 15, name: 'Post-Pandemic Overhire Correction' },
            { value: 10, name: 'Business Restructuring' }
        ]
    },
    zh: {
        title: '全球科技公司裁员全景洞察',
        subtitle: '{{ subtitle_zh }}',
        badge: '🔴 实时数据 · 自动爬取',
        kpi1Label: '2025年 总裁员',
        kpi1Hint: '科技史上最高纪录之一',
        kpi2Label: '2026年初至今',
        kpi2Hint: '同比增速超过 50%',
        kpi3Label: '涉及公司数量',
        kpi3Hint: '遍布 ' + {{ stats.num_countries }} + ' 个国家/地区',
        kpi4Label: '总计受影响人数',
        chartTitle1: '各大科技巨头累计裁员人数 (Top 15)',
        chartTitle2: '裁员行业分布',
        chartTitle3: '逐月裁员趋势变化',
        chartTitle4: '裁员地区分布',
        chartTitle5: '裁员核心驱动因素拆解',
        chartTitle6: '2025 与 2026 月度对比',
        chartTitle7: '裁员比例分布',
        chartTitle8: '融资阶段 × 裁员规模热力图',
        tableTitle1: '最近裁员记录',
        recentHeadDate: '日期',
        recentHeadCompany: '公司',
        recentHeadLayoffs: '裁员人数',
        recentHeadPct: '裁员比例',
        recentHeadIndustry: '行业',
        recentHeadCountry: '国家',
        recentHeadStage: '阶段',
        recentHeadSource: '来源',
        recentNoData: '暂无最近裁员记录。',
        recentSourceLink: '查看',
        footer: '数据来源: <a href="https://layoffs.fyi/" target="_blank">layoffs.fyi</a> · RationalFX · 各大科技媒体公开报道<br>免责声明: 部分数据为估计值或分阶段实施的计划裁员人数<br><br>Built with Python · BeautifulSoup · Pandas · ECharts &nbsp;|&nbsp;<a href="https://github.com/frankwang0909/tech-layoff-tracker" target="_blank">⭐ View on GitHub</a> &nbsp;|&nbsp; <a href="https://layoffscanada.com" target="_blank">Layoffs Canada</a> &nbsp;|&nbsp; <a href="https://debugcanada.com" target="_blank">Debug Canada</a>',
        yAxisName: '裁员人数',
        seriesBar: '裁员人数',
        seriesLine: '趋势线',
        series2025: '2025年',
        series2026: '2026年',
        heatmapLegend: '事件数',
        monthLabels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
        reasons: [
            { value: 45, name: '经济不确定性与通胀' },
            { value: 30, name: 'AI转型与自动化升级' },
            { value: 15, name: '疫情后过度扩张修正' },
            { value: 10, name: '业务重组与效率提升' }
        ]
    }
};

let currentLang = 'en';

// ═══════════════════════════════════════════════════════
//  Chart Setup
// ═══════════════════════════════════════════════════════
const TX = '#94a3b8';
const AX = '#1e293b';
const TOOLTIP = {
    backgroundColor: 'rgba(10, 15, 30, 0.95)',
    borderColor: '#334155',
    textStyle: { color: '#f8fafc', fontSize: 13 },
    borderWidth: 1,
};
const reasonColors = ['#64748b', '#818cf8', '#38bdf8', '#c084fc'];

function initChart(id) {
    return echarts.init(document.getElementById(id), null, { renderer: 'canvas' });
}

// Helper to determine if we are on a small screen
function isMobile() {
    return window.innerWidth <= 768;
}

const companyData = {{ company_summary | tojson }};
const industryData = {{ industry_breakdown | tojson }};
const monthlyData = {{ monthly_trend | tojson }};
const countryData = {{ country_breakdown | tojson }};
const monthlyComparisonData = {{ monthly_comparison | tojson }};
const stageHeatmapData = {{ stage_size_heatmap | tojson }};
const layoffPctDistribution = {{ layoff_pct_distribution | tojson }};
const recentLayoffs = {{ recent_layoffs | tojson }};
const industryColors = ['#818cf8','#38bdf8','#c084fc','#f472b6','#34d399','#fbbf24','#fb923c','#64748b','#94a3b8','#475569'];

const companyChart = initChart('companyChart');
const industryChart = initChart('industryChart');
const monthlyChart = initChart('monthlyChart');
const countryChart = initChart('countryChart');
const reasonChart = initChart('reasonChart');
const monthlyCompareChart = initChart('monthlyCompareChart');
const percentageChart = initChart('percentageChart');
const stageHeatmapChart = initChart('stageHeatmapChart');

function formatCount(value) {
    return value == null ? '—' : Number(value).toLocaleString();
}

function formatPct(value) {
    if (value == null || Number.isNaN(Number(value))) return '—';
    const pct = Number(value) * 100;
    return Number.isInteger(pct) ? `${pct}%` : `${pct.toFixed(1)}%`;
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function renderRecentLayoffs(t) {
    const body = document.getElementById('recentLayoffsBody');
    if (!recentLayoffs.length) {
        body.innerHTML = `<tr><td colspan="8">${t.recentNoData}</td></tr>`;
        return;
    }

    body.innerHTML = recentLayoffs.map(row => `
        <tr>
            <td>${row.date}</td>
            <td>${row.company}</td>
            <td>${formatCount(row.num_laid_off)}</td>
            <td>${formatPct(row.percentage_laid_off)}</td>
            <td>${row.industry}</td>
            <td>${row.country}</td>
            <td>${row.stage}</td>
            <td>${/^https?:\/\//.test(row.source)
                ? `<a href="${escapeHtml(row.source)}" target="_blank" rel="noopener noreferrer">${t.recentSourceLink}</a>`
                : escapeHtml(row.source || '—')}</td>
        </tr>
    `).join('');
}

// ═══════════════════════════════════════════════════════
//  Render Charts (language-aware)
// ═══════════════════════════════════════════════════════
function renderCharts(t) {
    const mobile = isMobile();

    companyChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: {type: 'shadow'}, ...TOOLTIP },
        grid: { left: '2%', right: mobile ? '15%' : '12%', top: '4%', bottom: '4%', containLabel: true },
        xAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: AX, type: 'dashed' } },
            axisLabel: { color: TX, formatter: v => v >= 1000 ? (v/1000)+'k' : v, fontSize: mobile ? 10 : 12 }
        },
        yAxis: {
            type: 'category',
            data: companyData.map(d => d.company).reverse(),
            axisLabel: { color: TX, fontWeight: 600, fontSize: mobile ? 10 : 12 },
            axisLine: { show: false },
            axisTick: { show: false }
        },
        series: [{
            type: 'bar',
            data: companyData.map(d => d.total_laid_off).reverse(),
            itemStyle: {
                color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
                    { offset: 0, color: '#38bdf8' },
                    { offset: 1, color: '#818cf8' }
                ]),
                borderRadius: [0, 6, 6, 0]
            },
            label: {
                show: true, position: 'right', color: '#94a3b8', fontSize: mobile ? 10 : 12,
                formatter: p => p.value.toLocaleString()
            },
            emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(56,189,248,0.3)' } }
        }]
    });

    industryChart.setOption({
        tooltip: { trigger: 'item', ...TOOLTIP, formatter: '{b}: {c} ({d}%)' },
        legend: {
            orient: mobile ? 'horizontal' : 'vertical',
            right: mobile ? 'center' : 10,
            bottom: mobile ? 0 : 'auto',
            top: mobile ? 'auto' : 'middle',
            textStyle: { color: TX, fontSize: 10 },
            itemWidth: 10, itemHeight: 10, itemGap: 8
        },
        series: [{
            type: 'pie',
            radius: mobile ? ['35%', '60%'] : ['40%', '72%'],
            center: mobile ? ['50%', '40%'] : ['40%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 8, borderColor: '#0a0f1e', borderWidth: 3 },
            label: { show: false },
            emphasis: {
                label: { show: true, fontSize: mobile ? 12 : 16, fontWeight: 700, color: '#f8fafc' },
                scaleSize: 6
            },
            data: industryData.map((d, i) => ({
                name: d.industry,
                value: d.total_laid_off,
                itemStyle: { color: industryColors[i % industryColors.length] }
            }))
        }]
    });

    monthlyChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross', label: { backgroundColor: '#1e293b' } }, ...TOOLTIP },
        grid: { left: '3%', right: '4%', top: '12%', bottom: mobile ? '15%' : '10%', containLabel: true },
        xAxis: {
            type: 'category',
            data: monthlyData.map(d => d.month),
            axisLabel: { color: TX, rotate: 45, fontSize: mobile ? 9 : 11 },
            axisLine: { lineStyle: { color: AX } },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            name: t.yAxisName,
            nameTextStyle: { color: TX, fontSize: mobile ? 10 : 12 },
            axisLabel: { color: TX, formatter: v => v >= 1000 ? (v/1000)+'k' : v, fontSize: mobile ? 10 : 12 },
            splitLine: { lineStyle: { color: AX, type: 'dashed' } }
        },
        series: [
            {
                name: t.seriesBar,
                type: 'bar',
                data: monthlyData.map(d => d.total_laid_off),
                barWidth: '50%',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#f43f5e' },
                        { offset: 1, color: '#881337' }
                    ]),
                    borderRadius: [6, 6, 0, 0]
                },
                emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(244,63,94,0.3)' } }
            },
            {
                name: t.seriesLine,
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 6,
                data: monthlyData.map(d => d.total_laid_off),
                lineStyle: { color: '#c084fc', width: 2.5 },
                itemStyle: { color: '#c084fc', borderWidth: 2, borderColor: '#0a0f1e' },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(192, 132, 252, 0.25)' },
                        { offset: 1, color: 'rgba(192, 132, 252, 0)' }
                    ])
                }
            }
        ]
    });

    countryChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...TOOLTIP },
        grid: { left: '3%', right: '12%', top: '4%', bottom: '4%', containLabel: true },
        xAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: AX, type: 'dashed' } },
            axisLabel: { color: TX, formatter: v => v >= 1000 ? (v/1000)+'k' : v, fontSize: mobile ? 10 : 12 }
        },
        yAxis: {
            type: 'category',
            data: countryData.map(d => d.country).reverse(),
            axisLabel: { color: TX, fontWeight: 500, fontSize: mobile ? 10 : 12 },
            axisLine: { show: false },
            axisTick: { show: false }
        },
        series: [{
            type: 'bar',
            data: countryData.map(d => d.total_laid_off).reverse(),
            itemStyle: {
                color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
                    { offset: 0, color: '#34d399' },
                    { offset: 1, color: '#059669' }
                ]),
                borderRadius: [0, 6, 6, 0]
            },
            label: {
                show: true, position: 'right', color: '#94a3b8', fontSize: mobile ? 10 : 12,
                formatter: p => p.value.toLocaleString()
            }
        }]
    });

    reasonChart.setOption({
        tooltip: { trigger: 'item', ...TOOLTIP, formatter: '{b}: {d}%' },
        legend: {
            orient: 'horizontal',
            bottom: 0,
            left: 'center',
            textStyle: { color: TX, fontSize: 10 },
            itemWidth: 10, itemHeight: 10, itemGap: 10
        },
        series: [{
            type: 'pie',
            radius: mobile ? ['35%', '60%'] : ['40%', '72%'],
            center: mobile ? ['50%', '40%'] : ['38%', '50%'],
            itemStyle: { borderRadius: 8, borderColor: '#0a0f1e', borderWidth: 3 },
            label: {
                show: !mobile,
                position: 'outside',
                formatter: '{b}\n{d}%',
                color: '#cbd5e1',
                fontSize: 11,
                fontWeight: 500
            },
            emphasis: {
                label: { show: true, fontSize: mobile ? 13 : 16, fontWeight: 700, color: '#f8fafc' },
                scaleSize: 6
            },
            data: t.reasons.map((r, i) => ({
                ...r,
                itemStyle: { color: reasonColors[i] }
            }))
        }]
    });

    monthlyCompareChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...TOOLTIP },
        legend: {
            top: 0,
            textStyle: { color: TX, fontSize: mobile ? 10 : 12 },
            itemWidth: 12, itemHeight: 12
        },
        grid: { left: '3%', right: '4%', top: '16%', bottom: mobile ? '10%' : '10%', containLabel: true },
        xAxis: {
            type: 'category',
            data: t.monthLabels,
            axisLabel: { color: TX, fontSize: mobile ? 9 : 11 },
            axisLine: { lineStyle: { color: AX } },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: TX, formatter: v => v >= 1000 ? (v/1000)+'k' : v, fontSize: mobile ? 10 : 12 },
            splitLine: { lineStyle: { color: AX, type: 'dashed' } }
        },
        series: [
            {
                name: t.series2025,
                type: 'bar',
                data: monthlyComparisonData.map(d => d.layoffs_2025),
                itemStyle: { color: '#38bdf8', borderRadius: [4, 4, 0, 0] }
            },
            {
                name: t.series2026,
                type: 'bar',
                data: monthlyComparisonData.map(d => d.layoffs_2026),
                itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] }
            }
        ]
    });

    percentageChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...TOOLTIP },
        grid: { left: '3%', right: '4%', top: '10%', bottom: '8%', containLabel: true },
        xAxis: {
            type: 'category',
            data: layoffPctDistribution.map(d => d.bucket),
            axisLabel: { color: TX, fontSize: mobile ? 10 : 12 },
            axisLine: { lineStyle: { color: AX } },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: TX, fontSize: mobile ? 10 : 12 },
            splitLine: { lineStyle: { color: AX, type: 'dashed' } }
        },
        series: [{
            type: 'bar',
            data: layoffPctDistribution.map(d => d.event_count),
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: '#22c55e' },
                    { offset: 1, color: '#14b8a6' }
                ]),
                borderRadius: [6, 6, 0, 0]
            },
            label: {
                show: true,
                position: 'top',
                color: '#94a3b8',
                fontSize: mobile ? 10 : 12,
                formatter: p => p.value.toLocaleString()
            }
        }]
    });

    stageHeatmapChart.setOption({
        tooltip: {
            position: 'top',
            ...TOOLTIP,
            formatter: params => {
                const cell = stageHeatmapData.cells[params.dataIndex];
                return `${cell.stage}<br>${cell.size_bucket}: ${cell.event_count.toLocaleString()} ${t.heatmapLegend.toLowerCase()}`;
            }
        },
        grid: { left: '3%', right: '3%', top: '10%', bottom: '15%', containLabel: true },
        xAxis: {
            type: 'category',
            data: stageHeatmapData.size_buckets,
            splitArea: { show: true },
            axisLabel: { color: TX, fontSize: mobile ? 9 : 11, rotate: mobile ? 30 : 0 },
            axisLine: { lineStyle: { color: AX } },
        },
        yAxis: {
            type: 'category',
            data: stageHeatmapData.stages,
            splitArea: { show: true },
            axisLabel: { color: TX, fontSize: mobile ? 9 : 11 },
            axisLine: { lineStyle: { color: AX } },
        },
        visualMap: {
            min: 0,
            max: Math.max(...stageHeatmapData.cells.map(c => c.event_count), 1),
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: 0,
            itemWidth: mobile ? 10 : 20,
            itemHeight: mobile ? 100 : 140,
            textStyle: { color: TX, fontSize: 10 },
        },
        series: [{
            name: t.heatmapLegend,
            type: 'heatmap',
            data: stageHeatmapData.cells.map(cell => ([
                stageHeatmapData.size_buckets.indexOf(cell.size_bucket),
                stageHeatmapData.stages.indexOf(cell.stage),
                cell.event_count,
            ])),
            label: {
                show: true,
                color: '#f8fafc',
                fontSize: mobile ? 9 : 11,
                formatter: params => params.value[2] ? params.value[2].toLocaleString() : ''
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.4)',
                }
            }
        }]
    });
}

// ═══════════════════════════════════════════════════════
//  Language Switching
// ═══════════════════════════════════════════════════════
function switchLang(lang) {
    currentLang = lang;
    const t = i18n[lang];

    // Update HTML lang attribute
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';

    // Toggle button styles
    document.getElementById('btnEN').classList.toggle('active', lang === 'en');
    document.getElementById('btnCN').classList.toggle('active', lang === 'zh');

    // Update page text
    document.getElementById('pageTitle').textContent = t.title;
    document.getElementById('pageSubtitle').textContent = t.subtitle;
    document.getElementById('pageBadge').textContent = t.badge;

    // KPI cards
    document.getElementById('kpi1Label').textContent = t.kpi1Label;
    document.getElementById('kpi1Hint').textContent = t.kpi1Hint;
    document.getElementById('kpi2Label').textContent = t.kpi2Label;
    document.getElementById('kpi2Hint').textContent = t.kpi2Hint;
    document.getElementById('kpi3Label').textContent = t.kpi3Label;
    document.getElementById('kpi3Hint').textContent = t.kpi3Hint;
    document.getElementById('kpi4Label').textContent = t.kpi4Label;

    // Chart titles
    document.getElementById('chartTitle1').textContent = t.chartTitle1;
    document.getElementById('chartTitle2').textContent = t.chartTitle2;
    document.getElementById('chartTitle3').textContent = t.chartTitle3;
    document.getElementById('chartTitle4').textContent = t.chartTitle4;
    document.getElementById('chartTitle5').textContent = t.chartTitle5;
    document.getElementById('chartTitle6').textContent = t.chartTitle6;
    document.getElementById('chartTitle7').textContent = t.chartTitle7;
    document.getElementById('chartTitle8').textContent = t.chartTitle8;
    document.getElementById('tableTitle1').textContent = t.tableTitle1;
    document.getElementById('recentHeadDate').textContent = t.recentHeadDate;
    document.getElementById('recentHeadCompany').textContent = t.recentHeadCompany;
    document.getElementById('recentHeadLayoffs').textContent = t.recentHeadLayoffs;
    document.getElementById('recentHeadPct').textContent = t.recentHeadPct;
    document.getElementById('recentHeadIndustry').textContent = t.recentHeadIndustry;
    document.getElementById('recentHeadCountry').textContent = t.recentHeadCountry;
    document.getElementById('recentHeadStage').textContent = t.recentHeadStage;
    document.getElementById('recentHeadSource').textContent = t.recentHeadSource;

    // Footer (uses innerHTML for links)
    document.getElementById('pageFooter').innerHTML = t.footer;

    // Re-render charts with translated labels
    renderCharts(t);
    renderRecentLayoffs(t);
}

// ═══════════════════════════════════════════════════════
//  Init
// ═══════════════════════════════════════════════════════
switchLang('en');

window.addEventListener('resize', () => {
    [companyChart, industryChart, monthlyChart, countryChart, reasonChart, monthlyCompareChart, percentageChart, stageHeatmapChart].forEach(c => c.resize());
});
</script>
</body>
</html>"""


LEGACY_REDIRECT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Layoff Tracker</title>
    <link rel="canonical" href="/" />
    <meta http-equiv="refresh" content="0; url=/">
    <script>
        window.location.replace("/" + window.location.search + window.location.hash);
    </script>
</head>
<body>
    <p>Redirecting to <a href="/">Tech Layoff Tracker</a>...</p>
</body>
</html>
"""


def format_number(value: int | float) -> str:
    """Format large numbers with comma separator."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def build_subtitles(stats: dict) -> tuple[str, str]:
    """Build localized subtitle strings from the actual processed date range."""
    date_range = stats.get("date_range", {})

    try:
        start_dt = datetime.fromisoformat(date_range["start"])
        end_dt = datetime.fromisoformat(date_range["end"])
    except (KeyError, TypeError, ValueError):
        return (
            "Latest available range | Industry Restructuring & Workforce Optimization",
            "最新可用数据范围 ｜ 科技行业深度洗牌与结构优化分析",
        )

    subtitle_en = (
        f"{start_dt.strftime('%b %Y')} – {end_dt.strftime('%b %Y')} | "
        "Industry Restructuring & Workforce Optimization"
    )
    subtitle_zh = (
        f"{start_dt.year}年{start_dt.month}月 – {end_dt.year}年{end_dt.month}月 ｜ "
        "科技行业深度洗牌与结构优化分析"
    )
    return subtitle_en, subtitle_zh


def generate_chart(data_dir: str = "data/processed", output_path: str = "index.html"):
    """
    Load processed JSON data and render the interactive HTML dashboard.

    Args:
        data_dir: Path to the directory containing processed JSON files.
        output_path: Path to write the output HTML file.
    """
    data_dir = Path(data_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("\n🎨 Generating interactive chart...")

    # Load processed data
    def load_json(name: str) -> dict | list:
        path = data_dir / f"{name}.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    company_summary = load_json("company_summary")
    monthly_trend = load_json("monthly_trend")
    industry_breakdown = load_json("industry_breakdown")
    country_breakdown = load_json("country_breakdown")
    monthly_comparison = load_json("monthly_comparison")
    stage_size_heatmap = load_json("stage_size_heatmap")
    layoff_pct_distribution = load_json("layoff_pct_distribution")
    recent_layoffs = load_json("recent_layoffs")
    stats = load_json("stats")
    subtitle_en, subtitle_zh = build_subtitles(stats)

    logger.info(f"   📂 Loaded data: {len(company_summary)} companies, {len(monthly_trend)} months")

    # Render template with Jinja2 Environment (for filter support)
    env = Environment()
    env.filters["format_number"] = format_number
    template = env.from_string(CHART_TEMPLATE)

    html = template.render(
        company_summary=company_summary,
        monthly_trend=monthly_trend,
        industry_breakdown=industry_breakdown,
        country_breakdown=country_breakdown,
        monthly_comparison=monthly_comparison,
        stage_size_heatmap=stage_size_heatmap,
        layoff_pct_distribution=layoff_pct_distribution,
        recent_layoffs=recent_layoffs,
        stats=stats,
        subtitle_en=subtitle_en,
        subtitle_zh=subtitle_zh,
    )

    output_path.write_text(html, encoding="utf-8")
    logger.info(f"   💾 Chart saved to: {output_path}")

    # Preserve old entry points so existing links keep working after moving the
    # dashboard to the homepage.
    legacy_paths = [
        Path("layoff_chart.html"),
        Path("visualization/layoff_chart.html"),
    ]
    for legacy_path in legacy_paths:
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_text(LEGACY_REDIRECT_TEMPLATE, encoding="utf-8")
        logger.info(f"   ↪ Legacy redirect written to: {legacy_path}")

    logger.info("✅ Chart generation complete.")

    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_chart()
