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
#  Common UI Components
# ───────────────────────────────────────────────────────────── #
COMMON_NAV_HTML = r"""<nav class="top-nav" aria-label="Primary">
    <a href="/">Dashboard</a>
    <a href="/trend-report.html">Trend Report</a>
    <a href="/reports/">Reports</a>
</nav>"""

COMMON_FOOTER_EN = r"""Data Sources: <a href="https://layoffs.fyi/" target="_blank">layoffs.fyi</a> · RationalFX · Major tech media<br>
Disclaimer: Some figures are estimates or planned reductions<br><br>
<a href="https://github.com/frankwang0909/tech-layoff-tracker" target="_blank">⭐ View on GitHub</a> &nbsp;|&nbsp;
<a href="https://layoffscanada.com" target="_blank">Layoffs Canada</a> &nbsp;|&nbsp;
<a href="https://debugcanada.com" target="_blank">Debug Canada</a>"""

COMMON_FOOTER_ZH = r"""数据来源: <a href="https://layoffs.fyi/" target="_blank">layoffs.fyi</a> · RationalFX · 各大科技媒体公开报道<br>
免责声明: 部分数据为估计值或分阶段实施的计划裁员人数<br><br>
<a href="https://github.com/frankwang0909/tech-layoff-tracker" target="_blank">⭐ View on GitHub</a> &nbsp;|&nbsp;
<a href="https://layoffscanada.com" target="_blank">Layoffs Canada</a> &nbsp;|&nbsp;
<a href="https://debugcanada.com" target="_blank">Debug Canada</a>"""


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
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-60H1FN74DN"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-60H1FN74DN');
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
            padding: 4.5rem 1rem 2rem;
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
        .top-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 0.6rem 1rem;
            background: rgba(10, 15, 30, 0.88);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .top-nav a {
            color: #cbd5e1;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.45rem 0.85rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.4);
            white-space: nowrap;
            transition: color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .top-nav a:hover {
            color: #fff;
            border-color: rgba(56, 189, 248, 0.55);
            box-shadow: 0 0 18px rgba(56, 189, 248, 0.16);
        }
        .top-nav a.active {
            background: linear-gradient(135deg, #818cf8, #c084fc);
            color: #fff;
            border-color: transparent;
            box-shadow: 0 2px 12px rgba(129, 140, 252, 0.4);
        }

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
            body { padding: 4rem 0.5rem 1rem; }
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
    <nav class="top-nav" aria-label="Primary">
        <a href="/" class="active">Dashboard</a>
        <a href="/trend-report.html">Trend Report</a>
        <a href="/reports/">Reports</a>
    </nav>

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
        footer: {{ COMMON_FOOTER_EN | tojson }},
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
        footer: '数据来源: <a href="https://layoffs.fyi/" target="_blank">layoffs.fyi</a> · RationalFX · 各大科技媒体公开报道<br>免责声明: 部分数据为估计值或分阶段实施的计划裁员人数<br><br> &nbsp;|&nbsp;<a href="https://github.com/frankwang0909/tech-layoff-tracker" target="_blank">⭐ View on GitHub</a> &nbsp;|&nbsp; <a href="https://layoffscanada.com" target="_blank">Layoffs Canada</a> &nbsp;|&nbsp; <a href="https://debugcanada.com" target="_blank">Debug Canada</a>',
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

TREND_REPORT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Layoffs Trend Report 2025-2026 | Industry, Country and Company Analysis</title>
    <meta name="description" content="Explore global tech layoff trends for 2025-2026 with monthly charts, industry breakdowns, country comparisons, company rankings, funding-stage analysis, and data-driven insights.">
    <link rel="canonical" href="https://tech.debugcanada.com/trend-report.html">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://tech.debugcanada.com/trend-report.html">
    <meta property="og:title" content="Tech Layoffs Trend Report 2025-2026">
    <meta property="og:description" content="Monthly trend, industry, country, company, funding-stage, and layoff intensity analysis based on public tech layoff records.">
    <meta property="og:image" content="https://tech.debugcanada.com/docs/images/dashboard_charts.png">
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:title" content="Tech Layoffs Trend Report 2025-2026">
    <meta property="twitter:description" content="Data-driven analysis of global tech layoffs by month, industry, country, company, and funding stage.">
    <meta property="twitter:image" content="https://tech.debugcanada.com/docs/images/dashboard_charts.png">
    <link rel="alternate" type="application/json" href="/ai-summary.json" title="AI-readable tech layoffs summary">
    <link rel="alternate" type="text/plain" href="/llms.txt" title="LLM guidance for Tech Layoff Tracker">
    <script type="application/ld+json">{{ article_jsonld | tojson }}</script>
    <script type="application/ld+json">{{ dataset_jsonld | tojson }}</script>
    <script type="application/ld+json">{{ faq_jsonld | tojson }}</script>
    <script type="application/ld+json">{{ breadcrumb_jsonld | tojson }}</script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding-top: 4rem;
            color: #e2e8f0;
            background: #0a0f1e;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
            line-height: 1.6;
        }
        a { color: #38bdf8; text-decoration: none; }
        a:hover { color: #fff; text-decoration: underline; }
        .wrap { width: min(1120px, calc(100% - 32px)); margin: 0 auto; }
        .top-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 0.6rem 1rem;
            background: rgba(10, 15, 30, 0.88);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .top-nav a {
            color: #cbd5e1;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.45rem 0.85rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.4);
            white-space: nowrap;
            transition: color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .top-nav a:hover {
            color: #fff;
            border-color: rgba(56, 189, 248, 0.55);
            box-shadow: 0 0 18px rgba(56, 189, 248, 0.16);
            text-decoration: none;
        }
        .top-nav a.active {
            background: linear-gradient(135deg, #818cf8, #c084fc);
            color: #fff;
            border-color: transparent;
            box-shadow: 0 2px 12px rgba(129, 140, 252, 0.4);
        }
        .hero {
            padding: 42px 0 32px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            background: transparent;
        }
        .eyebrow {
            margin: 0 0 12px;
            color: #f87171;
            font-size: 13px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        h1 {
            max-width: 920px;
            margin: 0;
            font-size: clamp(36px, 6vw, 72px);
            line-height: 0.98;
            letter-spacing: 0;
        }
        .dek {
            max-width: 850px;
            margin: 18px 0 0;
            color: #94a3b8;
            font-size: 20px;
        }
        .meta {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 22px;
            color: #64748b;
            font-size: 14px;
        }
        .kpis {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 28px 0 0;
        }
        .kpi {
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 18px;
            background: rgba(15, 23, 42, 0.6);
        }
        .kpi span {
            display: block;
            color: #64748b;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
        }
        .kpi strong {
            display: block;
            margin-top: 6px;
            font-size: 30px;
            line-height: 1.1;
            color: #f8fafc;
        }
        main { padding: 32px 0 56px; }
        section {
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        h2 {
            margin: 0 0 12px;
            font-size: clamp(26px, 4vw, 40px);
            line-height: 1.08;
            letter-spacing: 0;
            color: #f8fafc;
        }
        h3 { margin: 22px 0 8px; font-size: 22px; }
        p { max-width: 860px; }
        .summary-list {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin: 20px 0 0;
            padding: 0;
            list-style: none;
        }
        .summary-list li {
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 16px;
            background: rgba(15, 23, 42, 0.6);
        }
        .chart {
            width: 100%;
            height: 420px;
            margin: 18px 0;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.6);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            text-align: left;
            vertical-align: top;
            font-size: 14px;
            color: #e2e8f0;
        }
        th { color: #94a3b8; background: rgba(255,255,255,0.04); }
        tr:last-child td { border-bottom: 0; }
        .note {
            color: #64748b;
            font-size: 14px;
        }
        .answer-box {
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 18px;
            background: rgba(15, 23, 42, 0.6);
        }
        .facts {
            display: grid;
            grid-template-columns: 220px 1fr;
            gap: 8px 18px;
            margin: 16px 0 0;
        }
        .facts dt { color: #94a3b8; font-weight: 800; }
        .facts dd { margin: 0; color: #94a3b8; }
        .faq details {
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 14px 16px;
            margin: 10px 0;
            background: rgba(15, 23, 42, 0.6);
        }
        .faq summary { cursor: pointer; font-weight: 800; }
        footer {
            text-align: center;
            padding: 3rem 0 1rem;
            color: #475569;
            font-size: 0.75rem;
            line-height: 1.8;
        }
        footer a { color: #818cf8; text-decoration: none; }
        footer a:hover { text-decoration: underline; }
        @media (max-width: 760px) {
            .kpis, .summary-list, .facts { grid-template-columns: 1fr; }
            .chart { height: 280px; }
            .hero { padding: 20px 0 16px; }
            .dek { font-size: 15px; }
            .kpi strong { font-size: 22px; }
            h2 { font-size: 22px; }
            table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
            th, td { padding: 8px 10px; font-size: 13px; white-space: nowrap; }
        }
    </style>
</head>
<body>
    <div class="hero">
        <div class="wrap">
            <nav class="top-nav" aria-label="Primary">
                <a href="/">Dashboard</a>
                <a href="/trend-report.html" class="active">Trend Report</a>
                <a href="/reports/">Reports</a>
            </nav>
            <p class="eyebrow">Global tech layoffs analysis</p>
            <h1>Tech Layoffs Trend Report 2025-2026</h1>
            <p class="dek">A data-driven report on global technology layoffs by month, industry, country, company, funding stage, and layoff intensity.</p>
            <div class="meta">
                <span>Data range: {{ stats.date_range.start }} to {{ stats.date_range.end }}</span>
                <span>Based on public layoff records</span>
            </div>
            <div class="kpis" aria-label="Report key metrics">
                <div class="kpi"><span>Total layoffs</span><strong>{{ stats.total_laid_off | format_number }}</strong></div>
                <div class="kpi"><span>2026 YTD layoffs</span><strong>{{ stats.total_2026 | format_number }}</strong></div>
                <div class="kpi"><span>Companies affected</span><strong>{{ stats.num_companies | format_number }}</strong></div>
                <div class="kpi"><span>Countries / regions</span><strong>{{ stats.num_countries | format_number }}</strong></div>
            </div>
        </div>
    </div>

    <main class="wrap">
        <section id="executive-summary">
            <h2>Summary</h2>
            <p>{{ executive_summary }}</p>
            <ul class="summary-list">
                {% for insight in insights %}
                <li>{{ insight }}</li>
                {% endfor %}
            </ul>
        </section>

        <section id="monthly-trend">
            <h2>Monthly Layoff Trend</h2>
            <p>The monthly trend shows whether the market is moving through isolated large events or a broader sequence of layoffs. The current peak month in this dataset is <strong>{{ peak_month.month }}</strong>, with <strong>{{ peak_month.total_laid_off | format_number }}</strong> reported layoffs.</p>
            <div id="monthlyTrendChart" class="chart" aria-label="Monthly tech layoff trend chart"></div>
            <p class="note">Note: Monthly totals can spike when a single large company announces mass cuts. Check the company breakdown alongside this chart for a fuller picture.</p>
        </section>

        <section id="industry-breakdown">
            <h2>Industry Breakdown</h2>
            <p>The industry with the most reported layoffs is <strong>{{ top_industry.industry }}</strong>, accounting for <strong>{{ top_industry.total_laid_off | format_number }}</strong> reported layoffs.</p>
            <div id="industryChart" class="chart" aria-label="Tech layoffs by industry chart"></div>
        </section>

        <section id="country-breakdown">
            <h2>Country and Region Breakdown</h2>
            <p>The geographic view helps separate local labor market pressure from global technology restructuring. The top country or region in the dataset is <strong>{{ top_country.country }}</strong>, with <strong>{{ top_country.total_laid_off | format_number }}</strong> reported layoffs.</p>
            <div id="countryChart" class="chart" aria-label="Tech layoffs by country chart"></div>
        </section>

        <section id="company-ranking">
            <h2>Company Ranking and Concentration</h2>
            <p>Company rankings identify whether layoffs are concentrated in a few major employers or spread across the broader startup and technology market. The leading company in this dataset is <strong>{{ top_company.company }}</strong>, with <strong>{{ top_company.total_laid_off | format_number }}</strong> reported layoffs.</p>
            <div id="companyChart" class="chart" aria-label="Top companies by tech layoffs chart"></div>
        </section>

        <section id="funding-stage">
            <h2>Funding Stage and Layoff Size</h2>
            <p>Funding stage analysis helps distinguish public-company restructuring from private-company pressure. The heatmap counts layoff events by stage and size bucket rather than summing headcount.</p>
            <div id="stageHeatmapChart" class="chart" aria-label="Funding stage by layoff size heatmap"></div>
        </section>

        <section id="layoff-intensity">
            <h2>Layoff Intensity</h2>
            <p>Layoff percentage is available only for records where the source data includes it. When available, it gives a clearer picture of company-level stress than raw headcount alone.</p>
            <div id="percentageChart" class="chart" aria-label="Layoff percentage distribution chart"></div>
        </section>

        <section id="recent-events">
            <h2>Recent Layoff Events</h2>
            <p>Recent events provide source-level context for the trend data. Records without reported headcount can still appear here when they have valid dates.</p>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Company</th>
                        <th>Laid off</th>
                        <th>Industry</th>
                        <th>Country</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in recent_layoffs %}
                    <tr>
                        <td>{{ row.date }}</td>
                        <td>{{ row.company }}</td>
                        <td>{{ row.num_laid_off | format_optional_number }}</td>
                        <td>{{ row.industry }}</td>
                        <td>{{ row.country }}</td>
                        <td>{% if row.source and row.source.startswith("http") %}<a href="{{ row.source }}" rel="nofollow noopener noreferrer" target="_blank">Source</a>{% else %}{{ row.source or "N/A" }}{% endif %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>

        <section id="methodology">
            <h2>Methodology</h2>
            <p>This report is based on public tech layoff records. Entries with invalid dates are excluded from time-series charts. Entries without a reported headcount are excluded from totals but may still appear in event lists if a valid date is available.</p>
            <p class="note">Data source coverage changes over time, and some fields such as layoff percentage, funding stage, and funds raised are incomplete. The report should be read as a structured public-record analysis, not as a complete labor-market census.</p>
        </section>

        <section id="faq" class="faq">
            <h2>FAQ</h2>
            {% for item in faqs %}
            <details>
                <summary>{{ item.question }}</summary>
                <p>{{ item.answer }}</p>
            </details>
            {% endfor %}
        </section>
    </main>

    <footer class="wrap">
        {{ COMMON_FOOTER_EN }}
    </footer>

<script>
const monthlyData = {{ monthly_trend | tojson }};
const industryData = {{ industry_breakdown | tojson }};
const countryData = {{ country_breakdown | tojson }};
const companyData = {{ company_summary | tojson }};
const stageHeatmapData = {{ stage_size_heatmap | tojson }};
const layoffPctDistribution = {{ layoff_pct_distribution | tojson }};
const tooltip = { backgroundColor: '#0a0f1e', borderColor: '#1e293b', textStyle: { color: '#e2e8f0' } };
const TX = '#94a3b8', AX = '#1e293b';
function init(id) { return echarts.init(document.getElementById(id), null, { renderer: 'canvas' }); }
function shortNumber(v) { return v >= 1000 ? `${Math.round(v / 100) / 10}k` : v; }

const monthlyChart = init('monthlyTrendChart');
monthlyChart.setOption({
    tooltip: { trigger: 'axis', ...tooltip },
    grid: { left: 54, right: 24, top: 28, bottom: 70 },
    xAxis: { type: 'category', data: monthlyData.map(d => d.month), axisLabel: { rotate: 45, color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { formatter: shortNumber, color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
    series: [
        { type: 'bar', name: 'Layoffs', data: monthlyData.map(d => d.total_laid_off), itemStyle: { color: '#38bdf8' } },
        { type: 'line', name: 'Trend', data: monthlyData.map(d => d.total_laid_off), smooth: true, itemStyle: { color: '#c084fc' }, lineStyle: { color: '#c084fc' } }
    ]
});
const industryChart = init('industryChart');
industryChart.setOption({
    tooltip: { trigger: 'axis', ...tooltip },
    grid: { left: 150, right: 24, top: 24, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { formatter: shortNumber, color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
    yAxis: { type: 'category', data: industryData.map(d => d.industry).reverse(), axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    series: [{ type: 'bar', data: industryData.map(d => d.total_laid_off).reverse(), itemStyle: { color: '#0e9384' } }]
});
const countryChart = init('countryChart');
countryChart.setOption({
    tooltip: { trigger: 'axis', ...tooltip },
    grid: { left: 150, right: 24, top: 24, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { formatter: shortNumber, color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
    yAxis: { type: 'category', data: countryData.map(d => d.country).reverse(), axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    series: [{ type: 'bar', data: countryData.map(d => d.total_laid_off).reverse(), itemStyle: { color: '#7a5af8' } }]
});
const companyChart = init('companyChart');
companyChart.setOption({
    tooltip: { trigger: 'axis', ...tooltip },
    grid: { left: 150, right: 24, top: 24, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { formatter: shortNumber, color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
    yAxis: { type: 'category', data: companyData.map(d => d.company).reverse(), axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    series: [{ type: 'bar', data: companyData.map(d => d.total_laid_off).reverse(), itemStyle: { color: '#f43f5e' } }]
});
const stageHeatmapChart = init('stageHeatmapChart');
stageHeatmapChart.setOption({
    tooltip: {
        position: 'top',
        ...tooltip,
        formatter: params => {
            const cell = stageHeatmapData.cells[params.dataIndex];
            return `${cell.stage}<br>${cell.size_bucket}: ${cell.event_count} events`;
        }
    },
    grid: { left: 110, right: 30, top: 30, bottom: 90 },
    xAxis: { type: 'category', data: stageHeatmapData.size_buckets, axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    yAxis: { type: 'category', data: stageHeatmapData.stages, axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    visualMap: {
        min: 0,
        max: Math.max(...stageHeatmapData.cells.map(c => c.event_count), 1),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 16,
        textStyle: { color: TX }
    },
    series: [{
        type: 'heatmap',
        data: stageHeatmapData.cells.map(cell => [
            stageHeatmapData.size_buckets.indexOf(cell.size_bucket),
            stageHeatmapData.stages.indexOf(cell.stage),
            cell.event_count
        ]),
        label: { show: true, color: '#f8fafc' }
    }]
});
const percentageChart = init('percentageChart');
percentageChart.setOption({
    tooltip: { trigger: 'axis', ...tooltip },
    grid: { left: 54, right: 24, top: 28, bottom: 42 },
    xAxis: { type: 'category', data: layoffPctDistribution.map(d => d.bucket), axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
    series: [{ type: 'bar', data: layoffPctDistribution.map(d => d.event_count), itemStyle: { color: '#f59e0b' } }]
});
window.addEventListener('resize', () => {
    [monthlyChart, industryChart, countryChart, companyChart, stageHeatmapChart, percentageChart].forEach(chart => chart.resize());
});
</script>
</body>
</html>"""


REPORTS_INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Layoffs Reports Archive | Daily, Weekly, Monthly and Quarterly Reports</title>
    <meta name="description" content="Browse tech layoff trend reports, including daily, weekly, monthly, and quarterly analysis archives.">
    <link rel="canonical" href="https://tech.debugcanada.com/reports/">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://tech.debugcanada.com/reports/">
    <meta property="og:title" content="Tech Layoffs Reports Archive">
    <meta property="og:description" content="Browse the latest tech layoffs trend reports and analysis archive.">
    <script type="application/ld+json">{{ breadcrumb_jsonld | tojson }}</script>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding-top: 4rem;
            color: #e2e8f0;
            background: #0a0f1e;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
            line-height: 1.6;
        }
        a { color: #38bdf8; text-decoration: none; }
        a:hover { color: #fff; text-decoration: underline; }
        .wrap { width: min(1040px, calc(100% - 32px)); margin: 0 auto; }
        .top-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 0.6rem 1rem;
            background: rgba(10, 15, 30, 0.88);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .top-nav a {
            color: #cbd5e1;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.45rem 0.85rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.4);
            white-space: nowrap;
            transition: color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .top-nav a:hover {
            color: #fff;
            border-color: rgba(56, 189, 248, 0.55);
            box-shadow: 0 0 18px rgba(56, 189, 248, 0.16);
            text-decoration: none;
        }
        .top-nav a.active {
            background: linear-gradient(135deg, #818cf8, #c084fc);
            color: #fff;
            border-color: transparent;
            box-shadow: 0 2px 12px rgba(129, 140, 252, 0.4);
        }
        .hero { padding: 44px 0 30px; background: transparent; border-bottom: 1px solid rgba(255,255,255,0.06); }
        h1 { margin: 0; font-size: clamp(36px, 6vw, 68px); line-height: 1; letter-spacing: 0; }
        .dek { max-width: 760px; color: #94a3b8; font-size: 20px; }
        .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin: 30px 0 56px; }
        .card { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 20px; }
        .card h2 { margin: 0 0 8px; font-size: 24px; color: #f8fafc; }
        .card p { color: #94a3b8; margin: 0 0 14px; }
        .badge { display: inline-block; color: #64748b; font-size: 13px; font-weight: 700; }
        footer { text-align: center; padding: 3rem 0 1rem; color: #475569; font-size: 0.75rem; line-height: 1.8; }
        footer a { color: #818cf8; text-decoration: none; }
        footer a:hover { text-decoration: underline; }
        @media (max-width: 720px) {
            .grid { grid-template-columns: 1fr; }
            .hero { padding: 20px 0 16px; }
            .dek { font-size: 15px; }
            h1 { font-size: clamp(28px, 8vw, 48px); }
        }
    </style>
</head>
<body>
    <header class="hero">
        <div class="wrap">
            <nav class="top-nav" aria-label="Primary">
                <a href="/">Dashboard</a>
                <a href="/trend-report.html">Trend Report</a>
                <a href="/reports/" class="active">Reports</a>
            </nav>
            <h1>Tech Layoffs Reports Archive</h1>
            <p class="dek">Explore tech layoff trends with reports ranging from weekly snapshots to full-year summaries — covering industries, countries, and top companies.</p>
            <p class="badge">Current data range: {{ stats.date_range.start }} to {{ stats.date_range.end }}</p>
        </div>
    </header>
    <main class="wrap">
        <div class="grid">
            <article class="card">
                <h2>Weekly Reports</h2>
                <p>Weekly trend summaries comparing the latest week with the previous period and recent weekly baseline.</p>
                {% if latest_weekly %}
                <a href="{{ latest_weekly.canonical_url }}">Open latest weekly report</a>
                <span class="badge">Latest: {{ latest_weekly.period }}</span>
                {% else %}
                <span class="badge">Planned path: /reports/weekly/YYYY-Www.html</span>
                {% endif %}
            </article>
            <article class="card">
                <h2>Monthly Reports</h2>
                <p>Monthly summaries of notable layoff events, top affected companies, and key trends for each calendar month.</p>
                {% if latest_monthly %}
                <a href="{{ latest_monthly.canonical_url }}">Open latest monthly report</a>
                <span class="badge">Latest: {{ latest_monthly.period }}</span>
                {% else %}
                <span class="badge">Planned path: /reports/monthly/YYYY-MM.html</span>
                {% endif %}
            </article>
            <article class="card">
                <h2>Quarterly Reports</h2>
                <p>Quarterly analysis of market structure, company concentration, and industry shifts across three-month periods.</p>
                {% if latest_quarterly %}
                <a href="{{ latest_quarterly.canonical_url }}">Open latest quarterly report</a>
                <span class="badge">Latest: {{ latest_quarterly.period }}</span>
                {% else %}
                <span class="badge">Planned path: /reports/quarterly/YYYY-Qn.html</span>
                {% endif %}
            </article>
            <article class="card">
                <h2>Yearly Reports</h2>
                <p>Full-year and year-to-date summaries of global tech layoff trends, updated continuously as new data arrives.</p>
                {% if latest_yearly %}
                <a href="{{ latest_yearly.canonical_url }}">Open latest yearly report</a>
                <span class="badge">Latest: {{ latest_yearly.period }}</span>
                {% else %}
                <span class="badge">Planned path: /reports/yearly/YYYY.html</span>
                {% endif %}
            </article>
            <article class="card">
                <h2>Industry Pages</h2>
                <p>Focused pages summarize layoffs by industry with topic-specific trends, companies, and recent events.</p>
                {% if top_industry_page %}
                <a href="{{ top_industry_page.canonical_url }}">Open top industry page</a>
                <span class="badge">{{ top_industry_page.name }}</span>
                {% endif %}
            </article>
            <article class="card">
                <h2>Country Pages</h2>
                <p>Country and region pages summarize geographic layoff exposure and recent public records.</p>
                {% if top_country_page %}
                <a href="{{ top_country_page.canonical_url }}">Open top country page</a>
                <span class="badge">{{ top_country_page.name }}</span>
                {% endif %}
            </article>
        </div>
    </main>
    <footer class="wrap">
        {{ COMMON_FOOTER_EN }}
    </footer>
</body>
</html>"""


PERIOD_REPORT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | Tech Layoff Tracker</title>
    <meta name="description" content="{{ description }}">
    <link rel="canonical" href="https://tech.debugcanada.com{{ report.canonical_url }}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://tech.debugcanada.com{{ report.canonical_url }}">
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ description }}">
    <meta property="twitter:card" content="summary">
    <meta name="robots" content="{{ robots }}">
    <script type="application/ld+json">{{ article_jsonld | tojson }}</script>
    <script type="application/ld+json">{{ breadcrumb_jsonld | tojson }}</script>
    <script type="application/ld+json">{{ faq_jsonld | tojson }}</script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding-top: 4rem;
            color: #e2e8f0;
            background: #0a0f1e;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
            line-height: 1.6;
        }
        a { color: #38bdf8; text-decoration: none; }
        a:hover { color: #fff; text-decoration: underline; }
        .wrap { width: min(1080px, calc(100% - 32px)); margin: 0 auto; }
        .top-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 0.6rem 1rem;
            background: rgba(10, 15, 30, 0.88);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .top-nav a {
            color: #cbd5e1;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.45rem 0.85rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.4);
            white-space: nowrap;
            transition: color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .top-nav a:hover {
            color: #fff;
            border-color: rgba(56, 189, 248, 0.55);
            box-shadow: 0 0 18px rgba(56, 189, 248, 0.16);
            text-decoration: none;
        }
        .top-nav a.active {
            background: linear-gradient(135deg, #818cf8, #c084fc);
            color: #fff;
            border-color: transparent;
            box-shadow: 0 2px 12px rgba(129, 140, 252, 0.4);
        }
        .hero { padding: 42px 0 30px; background: transparent; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .eyebrow { margin: 0 0 12px; color: #f87171; font-size: 13px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
        h1 { margin: 0; font-size: clamp(34px, 6vw, 64px); line-height: 1; letter-spacing: 0; }
        .dek { max-width: 820px; color: #94a3b8; font-size: 20px; }
        .meta { display: flex; flex-wrap: wrap; gap: 10px 16px; color: #64748b; font-size: 14px; }
        .kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 26px 0 0; }
        .kpi { border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 16px; background: rgba(15, 23, 42, 0.6); }
        .kpi span { display: block; color: #64748b; font-size: 12px; font-weight: 800; text-transform: uppercase; }
        .kpi strong { display: block; margin-top: 6px; font-size: 28px; line-height: 1.1; color: #f8fafc; }
        main { padding: 30px 0 54px; }
        section { padding: 28px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
        h2 { margin: 0 0 12px; font-size: clamp(25px, 4vw, 38px); line-height: 1.1; color: #f8fafc; }
        .insights { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 16px 0 0; padding: 0; list-style: none; }
        .insights li { border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 15px; background: rgba(15, 23, 42, 0.6); }
        .chart-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
        .chart { width: 100%; height: 380px; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; background: rgba(15, 23, 42, 0.6); }
        .period-nav {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin: 20px 0 0;
        }
        .period-nav a, .period-nav span {
            display: block;
            flex: 1;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 12px 14px;
            background: rgba(15, 23, 42, 0.6);
            color: #e2e8f0;
            font-weight: 800;
        }
        .period-nav span { color: #475569; }
        .period-nav .next { text-align: right; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.06); }
        th, td { padding: 11px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); text-align: left; vertical-align: top; font-size: 14px; color: #e2e8f0; }
        th { color: #94a3b8; background: rgba(255,255,255,0.04); }
        tr:last-child td { border-bottom: 0; }
        .note { color: #64748b; font-size: 14px; }
        .faq details {
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 14px 16px;
            margin: 10px 0;
            background: rgba(15, 23, 42, 0.6);
        }
        .faq summary { cursor: pointer; font-weight: 800; }
        footer { text-align: center; padding: 3rem 0 1rem; color: #475569; font-size: 0.75rem; line-height: 1.8; }
        footer a { color: #818cf8; text-decoration: none; }
        footer a:hover { text-decoration: underline; }
        @media (max-width: 760px) {
            .kpis, .insights, .chart-grid { grid-template-columns: 1fr; }
            .chart { height: 280px; }
            .hero { padding: 20px 0 16px; }
            .dek { font-size: 15px; }
            .kpi strong { font-size: 22px; }
            h2 { font-size: 22px; }
            .period-nav { flex-direction: column; }
            .period-nav .next { text-align: left; }
            table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
            th, td { padding: 8px 10px; font-size: 13px; white-space: nowrap; }
        }
    </style>
</head>
<body>
    <header class="hero">
        <div class="wrap">
            <nav class="top-nav" aria-label="Primary">
                <a href="/">Dashboard</a>
                <a href="/trend-report.html">Trend Report</a>
                <a href="/reports/" class="active">Reports</a>
            </nav>
            <p class="eyebrow">{{ report_type_label }} report</p>
            <h1>{{ title }}</h1>
            <p class="dek">{{ description }}</p>
            <div class="meta">
                <span>Data range: {{ report.date_range.start }} to {{ report.date_range.end }}</span>
                <span>Status: {{ report.status }}</span>
                <span>Updated: {{ report.updated_at }}</span>
            </div>
            <div class="kpis" aria-label="Report key metrics">
                <div class="kpi"><span>Total layoffs</span><strong>{{ report.kpis.total_laid_off | format_number }}</strong></div>
                <div class="kpi"><span>Events</span><strong>{{ report.kpis.event_count | format_number }}</strong></div>
                <div class="kpi"><span>Companies</span><strong>{{ report.kpis.company_count | format_number }}</strong></div>
                <div class="kpi"><span>High intensity</span><strong>{{ report.kpis.high_intensity_event_count | format_number }}</strong></div>
            </div>
        </div>
    </header>

    <main class="wrap">
        <section id="summary">
            <h2>Summary</h2>
            <p>{{ summary }}</p>
            <ul class="insights">
                {% for insight in report.insights %}
                <li>{{ insight }}</li>
                {% endfor %}
            </ul>
            <nav class="period-nav" aria-label="Period navigation">
                {% if previous_report %}
                <a href="{{ previous_report.canonical_url }}">Previous: {{ previous_report.period }}</a>
                {% else %}
                <span>Previous report unavailable</span>
                {% endif %}
                {% if next_report %}
                <a class="next" href="{{ next_report.canonical_url }}">Next: {{ next_report.period }}</a>
                {% else %}
                <span class="next">Next report unavailable</span>
                {% endif %}
            </nav>
        </section>

        <section id="comparisons">
            <h2>Comparisons</h2>
            <p>{{ comparison_summary }}</p>
            <table>
                <thead>
                    <tr>
                        <th>Comparison</th>
                        <th>Period</th>
                        <th>Layoff delta</th>
                        <th>Layoff % change</th>
                        <th>Event delta</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Previous period</td>
                        <td>{{ report.comparisons.previous_period.period or "N/A" }}</td>
                        <td>{{ report.comparisons.previous_period.total_laid_off_delta | format_optional_number }}</td>
                        <td>{{ report.comparisons.previous_period.total_laid_off_pct_change | format_pct_change }}</td>
                        <td>{{ report.comparisons.previous_period.event_count_delta | format_optional_number }}</td>
                    </tr>
                    <tr>
                        <td>Same period last year</td>
                        <td>{{ report.comparisons.same_period_last_year.period or "N/A" }}</td>
                        <td>{{ report.comparisons.same_period_last_year.total_laid_off_delta | format_optional_number }}</td>
                        <td>{{ report.comparisons.same_period_last_year.total_laid_off_pct_change | format_pct_change }}</td>
                        <td>{{ report.comparisons.same_period_last_year.event_count_delta | format_optional_number }}</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <section id="breakdowns">
            <h2>Breakdowns</h2>
            <div class="chart-grid">
                <div id="companyChart" class="chart" aria-label="Top companies by layoffs"></div>
                <div id="industryChart" class="chart" aria-label="Top industries by layoffs"></div>
                <div id="countryChart" class="chart" aria-label="Top countries by layoffs"></div>
                <div id="pctChart" class="chart" aria-label="Layoff percentage distribution"></div>
            </div>
        </section>

        <section id="largest-events">
            <h2>Largest Events</h2>
            <p>Sorted by reported headcount. Events where no headcount was publicly disclosed are not shown.</p>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Company</th>
                        <th>Laid off</th>
                        <th>Industry</th>
                        <th>Country</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in report.tables.largest_events %}
                    <tr>
                        <td>{{ row.date }}</td>
                        <td>{{ row.company }}</td>
                        <td>{{ row.num_laid_off | format_optional_number }}</td>
                        <td>{{ row.industry }}</td>
                        <td>{{ row.country }}</td>
                        <td>{% if row.source and row.source.startswith("http") %}<a href="{{ row.source }}" rel="nofollow noopener noreferrer" target="_blank">Source</a>{% else %}{{ row.source or "N/A" }}{% endif %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>

        <section id="methodology">
            <h2>Methodology</h2>
            {% for note in report.methodology_notes %}
            <p class="note">{{ note }}</p>
            {% endfor %}
        </section>

        <section id="faq" class="faq">
            <h2>FAQ</h2>
            {% for item in faqs %}
            <details>
                <summary>{{ item.question }}</summary>
                <p>{{ item.answer }}</p>
            </details>
            {% endfor %}
        </section>
    </main>

    <footer class="wrap">
        {{ COMMON_FOOTER_EN }}
    </footer>

<script>
const report = {{ report | tojson }};
const tooltip = { backgroundColor: '#0a0f1e', borderColor: '#1e293b', textStyle: { color: '#e2e8f0' } };
const TX = '#94a3b8', AX = '#1e293b';
function init(id) { return echarts.init(document.getElementById(id), null, { renderer: 'canvas' }); }
function shortNumber(v) { return v >= 1000 ? `${Math.round(v / 100) / 10}k` : v; }
function horizontalBar(id, rows, labelKey, valueKey, color) {
    const chart = init(id);
    chart.setOption({
        tooltip: { trigger: 'axis', ...tooltip },
        grid: { left: 120, right: 24, top: 24, bottom: 30 },
        xAxis: { type: 'value', axisLabel: { formatter: shortNumber, color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
        yAxis: { type: 'category', data: rows.map(d => d[labelKey]).reverse(), axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
        series: [{ type: 'bar', data: rows.map(d => d[valueKey]).reverse(), itemStyle: { color } }]
    });
    return chart;
}
const charts = [
    horizontalBar('companyChart', report.charts.company_top, 'company', 'total_laid_off', '#38bdf8'),
    horizontalBar('industryChart', report.charts.industry_top, 'industry', 'total_laid_off', '#0e9384'),
    horizontalBar('countryChart', report.charts.country_top, 'country', 'total_laid_off', '#7a5af8')
];
const pctChart = init('pctChart');
pctChart.setOption({
    tooltip: { trigger: 'axis', ...tooltip },
    grid: { left: 46, right: 24, top: 24, bottom: 40 },
    xAxis: { type: 'category', data: report.charts.layoff_pct_distribution.map(d => d.bucket), axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
    series: [{ type: 'bar', data: report.charts.layoff_pct_distribution.map(d => d.event_count), itemStyle: { color: '#f59e0b' } }]
});
charts.push(pctChart);
window.addEventListener('resize', () => charts.forEach(chart => chart.resize()));
</script>
</body>
</html>"""


LLMS_TXT_TEMPLATE = """# Tech Layoff Tracker

> Public tech layoff dashboard and trend report generated from processed layoff records.

Canonical pages:
- Dashboard: https://tech.debugcanada.com/
- Trend report: https://tech.debugcanada.com/trend-report.html
- Reports archive: https://tech.debugcanada.com/reports/
- AI-readable summary: https://tech.debugcanada.com/ai-summary.json

Current dataset:
- Data range: {{ stats.date_range.start }} to {{ stats.date_range.end }}
- Total reported layoffs: {{ stats.total_laid_off | format_number }}
- 2026 YTD reported layoffs: {{ stats.total_2026 | format_number }}
- Companies affected: {{ stats.num_companies | format_number }}
- Countries or regions: {{ stats.num_countries | format_number }}
- Peak month: {{ peak_month.month }} with {{ peak_month.total_laid_off | format_number }} reported layoffs
- Top company: {{ top_company.company }} with {{ top_company.total_laid_off | format_number }} reported layoffs
- Leading named industry: {{ top_industry.industry }} with {{ top_industry.total_laid_off | format_number }} reported layoffs
- Leading country or region: {{ top_country.country }} with {{ top_country.total_laid_off | format_number }} reported layoffs

Recommended citation:
Use "Tech Layoff Tracker, data range {{ stats.date_range.start }} to {{ stats.date_range.end }}" and link to https://tech.debugcanada.com/trend-report.html.

Methodology notes:
- Rows with invalid dates are excluded from time-series analysis.
- Rows without num_laid_off are excluded from headcount totals but may appear as events.
- Layoff percentage, funding stage, and funds raised fields are incomplete in the source data.
- The dataset tracks public records and does not prove causal claims such as AI directly causing layoffs.

Useful data files:
- /data/processed/stats.json
- /data/processed/monthly_trend.json
- /data/processed/company_summary.json
- /data/processed/industry_breakdown.json
- /data/processed/country_breakdown.json
- /data/processed/reports/index.json
- /data/processed/industry_pages.json
- /data/processed/country_pages.json
"""


TOPIC_PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page.title }} | Tech Layoff Tracker</title>
    <meta name="description" content="{{ description }}">
    <link rel="canonical" href="https://tech.debugcanada.com{{ page.canonical_url }}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://tech.debugcanada.com{{ page.canonical_url }}">
    <meta property="og:title" content="{{ page.title }}">
    <meta property="og:description" content="{{ description }}">
    <meta name="robots" content="index, follow">
    <script type="application/ld+json">{{ article_jsonld | tojson }}</script>
    <script type="application/ld+json">{{ breadcrumb_jsonld | tojson }}</script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding-top: 4rem;
            color: #e2e8f0;
            background: #0a0f1e;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
            line-height: 1.6;
        }
        a { color: #38bdf8; text-decoration: none; }
        a:hover { color: #fff; text-decoration: underline; }
        .wrap { width: min(1080px, calc(100% - 32px)); margin: 0 auto; }
        .top-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 0.6rem 1rem;
            background: rgba(10, 15, 30, 0.88);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .top-nav a {
            color: #cbd5e1;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.45rem 0.85rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.4);
            white-space: nowrap;
            transition: color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .top-nav a:hover {
            color: #fff;
            border-color: rgba(56, 189, 248, 0.55);
            box-shadow: 0 0 18px rgba(56, 189, 248, 0.16);
            text-decoration: none;
        }
        .top-nav a.active {
            background: linear-gradient(135deg, #818cf8, #c084fc);
            color: #fff;
            border-color: transparent;
            box-shadow: 0 2px 12px rgba(129, 140, 252, 0.4);
        }
        .hero { padding: 42px 0 30px; background: transparent; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .eyebrow { margin: 0 0 12px; color: #f87171; font-size: 13px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
        h1 { margin: 0; font-size: clamp(34px, 6vw, 64px); line-height: 1; letter-spacing: 0; }
        .dek { max-width: 820px; color: #94a3b8; font-size: 20px; }
        .meta { display: flex; flex-wrap: wrap; gap: 10px 16px; color: #64748b; font-size: 14px; }
        .kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 26px 0 0; }
        .kpi { border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 16px; background: rgba(15, 23, 42, 0.6); }
        .kpi span { display: block; color: #64748b; font-size: 12px; font-weight: 800; text-transform: uppercase; }
        .kpi strong { display: block; margin-top: 6px; font-size: 28px; line-height: 1.1; color: #f8fafc; }
        main { padding: 30px 0 54px; }
        section { padding: 28px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
        h2 { margin: 0 0 12px; font-size: clamp(25px, 4vw, 38px); line-height: 1.1; color: #f8fafc; }
        .chart-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
        .chart { width: 100%; height: 380px; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; background: rgba(15, 23, 42, 0.6); }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.06); }
        th, td { padding: 11px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); text-align: left; vertical-align: top; font-size: 14px; color: #e2e8f0; }
        th { color: #94a3b8; background: rgba(255,255,255,0.04); }
        tr:last-child td { border-bottom: 0; }
        .note { color: #64748b; font-size: 14px; }
        footer { text-align: center; padding: 3rem 0 1rem; color: #475569; font-size: 0.75rem; line-height: 1.8; }
        footer a { color: #818cf8; text-decoration: none; }
        footer a:hover { text-decoration: underline; }
        @media (max-width: 760px) {
            .kpis, .chart-grid { grid-template-columns: 1fr; }
            .chart { height: 280px; }
            .hero { padding: 20px 0 16px; }
            .dek { font-size: 15px; }
            .kpi strong { font-size: 22px; }
            h2 { font-size: 22px; }
            table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
            th, td { padding: 8px 10px; font-size: 13px; white-space: nowrap; }
        }
    </style>
</head>
<body>
    <header class="hero">
        <div class="wrap">
            <nav class="top-nav" aria-label="Primary">
                <a href="/" class="active">Dashboard</a>
                <a href="/trend-report.html">Trend Report</a>
                <a href="/reports/">Reports</a>
            </nav>
            <p class="eyebrow">{{ topic_label }} analysis</p>
            <h1>{{ page.title }}</h1>
            <p class="dek">{{ page.summary }}</p>
            <div class="meta">
                <span>Data range: {{ page.date_range.start }} to {{ page.date_range.end }}</span>
                <span>Based on public layoff records</span>
            </div>
            <div class="kpis" aria-label="Topic key metrics">
                <div class="kpi"><span>Total layoffs</span><strong>{{ page.kpis.total_laid_off | format_number }}</strong></div>
                <div class="kpi"><span>Events</span><strong>{{ page.kpis.event_count | format_number }}</strong></div>
                <div class="kpi"><span>Companies</span><strong>{{ page.kpis.company_count | format_number }}</strong></div>
                <div class="kpi"><span>High intensity</span><strong>{{ page.kpis.high_intensity_event_count | format_number }}</strong></div>
            </div>
        </div>
    </header>

    <main class="wrap">
        <section id="summary">
            <h2>Summary</h2>
            <p>{{ description }}</p>
            <p class="note">This page is generated as a focused topic page. It should be interpreted with the same methodology limits as the main trend report.</p>
        </section>

        <section id="charts">
            <h2>Trend and Companies</h2>
            <div class="chart-grid">
                <div id="monthlyChart" class="chart" aria-label="Monthly trend chart"></div>
                <div id="companyChart" class="chart" aria-label="Top companies chart"></div>
            </div>
        </section>

        <section id="recent-events">
            <h2>Recent Events</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Company</th>
                        <th>Laid off</th>
                        <th>Industry</th>
                        <th>Country</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in page.tables.recent_events %}
                    <tr>
                        <td>{{ row.date }}</td>
                        <td>{{ row.company }}</td>
                        <td>{{ row.num_laid_off | format_optional_number }}</td>
                        <td>{{ row.industry }}</td>
                        <td>{{ row.country }}</td>
                        <td>{% if row.source and row.source.startswith("http") %}<a href="{{ row.source }}" rel="nofollow noopener noreferrer" target="_blank">Source</a>{% else %}{{ row.source or "N/A" }}{% endif %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
    </main>

    <footer class="wrap">
        {{ COMMON_FOOTER_EN }}
    </footer>

<script>
const page = {{ page | tojson }};
const tooltip = { backgroundColor: '#0a0f1e', borderColor: '#1e293b', textStyle: { color: '#e2e8f0' } };
const TX = '#94a3b8', AX = '#1e293b';
function init(id) { return echarts.init(document.getElementById(id), null, { renderer: 'canvas' }); }
function shortNumber(v) { return v >= 1000 ? `${Math.round(v / 100) / 10}k` : v; }
const monthlyChart = init('monthlyChart');
monthlyChart.setOption({
    tooltip: { trigger: 'axis', ...tooltip },
    grid: { left: 54, right: 24, top: 28, bottom: 70 },
    xAxis: { type: 'category', data: page.charts.monthly_trend.map(d => d.month), axisLabel: { rotate: 45, color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { formatter: shortNumber, color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
    series: [{ type: 'bar', data: page.charts.monthly_trend.map(d => d.total_laid_off), itemStyle: { color: '#38bdf8' } }]
});
const companyChart = init('companyChart');
companyChart.setOption({
    tooltip: { trigger: 'axis', ...tooltip },
    grid: { left: 130, right: 24, top: 28, bottom: 36 },
    xAxis: { type: 'value', axisLabel: { formatter: shortNumber, color: TX }, splitLine: { lineStyle: { color: AX, type: 'dashed' } } },
    yAxis: { type: 'category', data: page.charts.company_top.map(d => d.company).reverse(), axisLabel: { color: TX }, axisLine: { lineStyle: { color: AX } }, axisTick: { show: false } },
    series: [{ type: 'bar', data: page.charts.company_top.map(d => d.total_laid_off).reverse(), itemStyle: { color: '#0e9384' } }]
});
window.addEventListener('resize', () => [monthlyChart, companyChart].forEach(chart => chart.resize()));
</script>
</body>
</html>"""


def format_number(value: int | float) -> str:
    """Format large numbers with comma separator."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def format_optional_number(value: int | float | None) -> str:
    """Format optional numeric values for report tables."""
    if value is None:
        return "N/A"
    return format_number(value)


def format_pct_change(value: int | float | None) -> str:
    """Format a decimal percent change for report comparison tables."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value) * 100:+.1f}%"
    except (ValueError, TypeError):
        return "N/A"


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


def safe_first(items: list[dict], fallback: dict) -> dict:
    """Return the first item from a list, or a fallback for empty datasets."""
    return items[0] if items else fallback


def first_named_category(
    items: list[dict],
    name_key: str,
    fallback: dict,
    excluded: set[str] | None = None,
) -> dict:
    """Return the first item whose category name is useful for narrative copy."""
    excluded = excluded or {"Other", "Unknown", ""}
    for item in items:
        name = str(item.get(name_key, "")).strip()
        if name not in excluded:
            return item
    return safe_first(items, fallback)


def build_report_context(
    company_summary: list[dict],
    monthly_trend: list[dict],
    industry_breakdown: list[dict],
    country_breakdown: list[dict],
    stage_size_heatmap: dict,
    layoff_pct_distribution: list[dict],
    recent_layoffs: list[dict],
    industry_pages: list[dict],
    country_pages: list[dict],
    stats: dict,
) -> dict:
    """Build text, insights, and JSON-LD context for SEO report pages."""
    top_company = safe_first(company_summary, {"company": "N/A", "total_laid_off": 0})
    top_industry = first_named_category(
        industry_breakdown,
        "industry",
        {"industry": "N/A", "total_laid_off": 0},
    )
    top_country = safe_first(country_breakdown, {"country": "N/A", "total_laid_off": 0})
    peak_month = max(
        monthly_trend,
        key=lambda row: row.get("total_laid_off", 0),
        default={"month": "N/A", "total_laid_off": 0},
    )
    date_range = stats.get("date_range", {})
    start_date = date_range.get("start", "the earliest available record")
    end_date = date_range.get("end", "the latest available record")

    total = stats.get("total_laid_off", 0)
    total_2026 = stats.get("total_2026", 0)
    companies = stats.get("num_companies", 0)
    countries = stats.get("num_countries", 0)

    executive_summary = (
        f"From {start_date} to {end_date}, public records track "
        f"{format_number(total)} reported tech layoffs across {format_number(companies)} "
        f"companies and {format_number(countries)} countries or regions. "
        f"The 2026 year-to-date total is {format_number(total_2026)}, while the largest "
        f"monthly spike in the current dataset is {peak_month['month']}."
    )
    answer_engine_summary = (
        f"Tech Layoff Tracker reports {format_number(total)} public tech layoffs from "
        f"{start_date} to {end_date}. The dataset covers {format_number(companies)} "
        f"companies across {format_number(countries)} countries or regions. "
        f"The largest month is {peak_month['month']} with "
        f"{format_number(peak_month['total_laid_off'])} reported layoffs. "
        f"The top company is {top_company['company']}; the leading named industry is "
        f"{top_industry['industry']}; and the leading country or region is {top_country['country']}."
    )
    ai_facts = [
        {"name": "Canonical analysis URL", "value": "https://tech.debugcanada.com/trend-report.html"},
        {"name": "Data range", "value": f"{start_date} to {end_date}"},
        {"name": "Total reported layoffs", "value": format_number(total)},
        {"name": "2026 YTD reported layoffs", "value": format_number(total_2026)},
        {"name": "Companies affected", "value": format_number(companies)},
        {"name": "Countries or regions", "value": format_number(countries)},
        {
            "name": "Peak month",
            "value": f"{peak_month['month']} ({format_number(peak_month['total_laid_off'])} layoffs)",
        },
        {
            "name": "Top company",
            "value": f"{top_company['company']} ({format_number(top_company['total_laid_off'])} layoffs)",
        },
        {
            "name": "Leading named industry",
            "value": f"{top_industry['industry']} ({format_number(top_industry['total_laid_off'])} layoffs)",
        },
        {
            "name": "Leading country or region",
            "value": f"{top_country['country']} ({format_number(top_country['total_laid_off'])} layoffs)",
        },
    ]

    insights = [
        (
            f"{top_company['company']} is the highest-ranked company by reported layoffs "
            f"in the current company summary, with {format_number(top_company['total_laid_off'])} layoffs."
        ),
        (
            f"{top_industry['industry']} is the largest industry category, accounting for "
            f"{format_number(top_industry['total_laid_off'])} reported layoffs."
        ),
        (
            f"{top_country['country']} is the leading country or region in the current dataset, "
            f"with {format_number(top_country['total_laid_off'])} reported layoffs."
        ),
        (
            f"The peak month is {peak_month['month']}, with "
            f"{format_number(peak_month['total_laid_off'])} reported layoffs."
        ),
    ]

    faqs = [
        {
            "question": "What is the latest tech layoff trend?",
            "answer": (
                f"The current data covers {start_date} to {end_date}. "
                f"The month with the highest reported layoff total is {peak_month['month']}."
            ),
        },
        {
            "question": "Which tech company had the most layoffs in this dataset?",
            "answer": (
                f"{top_company['company']} ranks first in the current company summary with "
                f"{format_number(top_company['total_laid_off'])} reported layoffs."
            ),
        },
        {
            "question": "Which industry is most affected by tech layoffs?",
            "answer": (
                f"{top_industry['industry']} is the largest industry category in the current "
                f"this data, with {format_number(top_industry['total_laid_off'])} reported layoffs."
            ),
        },
        {
            "question": "Does this report prove that AI caused tech layoffs?",
            "answer": (
                "No. The structured dataset tracks public layoff records and related dimensions, "
                "but it does not contain a complete causal field for AI. Any AI-related discussion "
                "should be treated as source attribution or market context, not as a direct causal proof."
            ),
        },
        {
            "question": "How often is the data updated?",
            "answer": (
                "Data is updated daily from public layoff records. The report shows the current date range "
                "so you can verify how recent the data is."
            ),
        },
    ]

    site_url = "https://tech.debugcanada.com"
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Tech Layoffs Trend Report 2025-2026",
        "description": (
            "Global tech layoffs analysis by month, industry, country, company, "
            "funding stage, and layoff intensity."
        ),
        "datePublished": end_date,
        "dateModified": end_date,
        "author": {"@type": "Person", "name": "Frank Wang"},
        "publisher": {
            "@type": "Organization",
            "name": "Tech Layoff Tracker",
            "url": site_url,
        },
        "mainEntityOfPage": f"{site_url}/trend-report.html",
    }
    dataset_jsonld = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Tech Layoff Tracker Processed Dataset",
        "description": (
            "Processed public technology layoff records used for trend reports "
            "and dashboard visualizations."
        ),
        "temporalCoverage": f"{start_date}/{end_date}",
        "spatialCoverage": "Global",
        "variableMeasured": [
            "company",
            "date",
            "num_laid_off",
            "industry",
            "country",
            "funding stage",
            "percentage laid off",
        ],
        "isBasedOn": "https://layoffs.fyi/",
    }
    faq_jsonld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"],
                },
            }
            for item in faqs
        ],
    }
    breadcrumb_jsonld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Dashboard",
                "item": site_url,
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Trend Report",
                "item": f"{site_url}/trend-report.html",
            },
        ],
    }

    return {
        "company_summary": company_summary,
        "monthly_trend": monthly_trend,
        "industry_breakdown": industry_breakdown,
        "country_breakdown": country_breakdown,
        "stage_size_heatmap": stage_size_heatmap,
        "layoff_pct_distribution": layoff_pct_distribution,
        "recent_layoffs": recent_layoffs,
        "stats": stats,
        "executive_summary": executive_summary,
        "answer_engine_summary": answer_engine_summary,
        "ai_facts": ai_facts,
        "insights": insights,
        "faqs": faqs,
        "top_company": top_company,
        "top_industry": top_industry,
        "top_country": top_country,
        "peak_month": peak_month,
        "article_jsonld": article_jsonld,
        "dataset_jsonld": dataset_jsonld,
        "faq_jsonld": faq_jsonld,
        "breadcrumb_jsonld": breadcrumb_jsonld,
        "ai_summary": {
            "name": "Tech Layoff Tracker AI Summary",
            "canonical_url": "https://tech.debugcanada.com/trend-report.html",
            "generated_from": "data/processed/*.json",
            "data_range": {"start": start_date, "end": end_date},
            "summary": answer_engine_summary,
            "facts": ai_facts,
            "insights": insights,
            "faq": faqs,
            "methodology_notes": [
                "Rows with invalid dates are excluded from time-series analysis.",
                "Rows without num_laid_off are excluded from headcount totals but may appear as events.",
                "The dataset tracks public records and should not be used as proof of causal claims.",
            ],
            "source_files": [
                "/data/processed/stats.json",
                "/data/processed/monthly_trend.json",
                "/data/processed/company_summary.json",
                "/data/processed/industry_breakdown.json",
                "/data/processed/country_breakdown.json",
                "/data/processed/reports/index.json",
                "/data/processed/industry_pages.json",
                "/data/processed/country_pages.json",
            ],
            "topic_pages": {
                "industries": [
                    {
                        "name": page["name"],
                        "canonical_url": f"https://tech.debugcanada.com{page['canonical_url']}",
                        "total_laid_off": page["kpis"]["total_laid_off"],
                        "event_count": page["kpis"]["event_count"],
                    }
                    for page in industry_pages[:10]
                ],
                "countries": [
                    {
                        "name": page["name"],
                        "canonical_url": f"https://tech.debugcanada.com{page['canonical_url']}",
                        "total_laid_off": page["kpis"]["total_laid_off"],
                        "event_count": page["kpis"]["event_count"],
                    }
                    for page in country_pages[:10]
                ],
            },
        },
        "industry_pages": industry_pages,
        "country_pages": country_pages,
        "COMMON_FOOTER_EN": COMMON_FOOTER_EN,
        "COMMON_FOOTER_ZH": COMMON_FOOTER_ZH,
    }


def write_report_pages(env: Environment, context: dict, report_data_dir: Path) -> None:
    """Render SEO report pages using already-loaded processed data."""
    period_reports = render_period_report_pages(env, report_data_dir)
    topic_pages = render_topic_pages(
        env=env,
        industry_pages=context["industry_pages"],
        country_pages=context["country_pages"],
    )
    latest_weekly = latest_report_meta(period_reports, "weekly")
    latest_monthly = latest_report_meta(period_reports, "monthly")
    latest_quarterly = latest_report_meta(period_reports, "quarterly")
    latest_yearly = latest_report_meta(period_reports, "yearly")

    trend_path = Path("trend-report.html")
    trend_html = env.from_string(TREND_REPORT_TEMPLATE).render(**context)
    trend_path.write_text(trend_html, encoding="utf-8")
    logger.info(f"   📝 Trend report saved to: {trend_path}")

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    reports_index_path = reports_dir / "index.html"
    reports_index_html = env.from_string(REPORTS_INDEX_TEMPLATE).render(
        stats=context["stats"],
        latest_weekly=latest_weekly,
        latest_monthly=latest_monthly,
        latest_quarterly=latest_quarterly,
        latest_yearly=latest_yearly,
        top_industry_page=context["industry_pages"][0] if context["industry_pages"] else None,
        top_country_page=context["country_pages"][0] if context["country_pages"] else None,
        COMMON_FOOTER_EN=COMMON_FOOTER_EN,
        COMMON_FOOTER_ZH=COMMON_FOOTER_ZH,
        breadcrumb_jsonld={
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Dashboard",
                    "item": "https://tech.debugcanada.com/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Reports",
                    "item": "https://tech.debugcanada.com/reports/",
                },
            ],
        },
    )
    reports_index_path.write_text(reports_index_html, encoding="utf-8")
    logger.info(f"   🗂 Reports index saved to: {reports_index_path}")

    ai_summary_path = Path("ai-summary.json")
    ai_summary_path.write_text(
        json.dumps(context["ai_summary"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"   🤖 AI summary saved to: {ai_summary_path}")

    llms_path = Path("llms.txt")
    llms_text = env.from_string(LLMS_TXT_TEMPLATE).render(**context)
    llms_path.write_text(llms_text, encoding="utf-8")
    logger.info(f"   🤖 LLM guidance saved to: {llms_path}")

    write_sitemap_and_robots(
        stats=context["stats"],
        period_reports=period_reports,
        topic_pages=topic_pages,
    )


def render_topic_pages(
    env: Environment,
    industry_pages: list[dict],
    country_pages: list[dict],
) -> list[dict]:
    """Render industry and country topic pages."""
    generated = []
    for page in industry_pages + country_pages:
        html_path = Path(page["canonical_url"].lstrip("/"))
        html_path.parent.mkdir(parents=True, exist_ok=True)
        context = build_topic_page_context(page)
        html = env.from_string(TOPIC_PAGE_TEMPLATE).render(**context)
        html_path.write_text(html, encoding="utf-8")
        generated.append({
            "type": page["type"],
            "name": page["name"],
            "canonical_url": page["canonical_url"],
            "date_range": page["date_range"],
        })

    if generated:
        logger.info(f"   🧩 Topic pages saved: {len(generated)} industry/country pages")
    return generated


def build_topic_page_context(page: dict) -> dict:
    """Build template context and structured data for one topic page."""
    topic_label = "Industry" if page["type"] == "industry" else "Country"
    description = (
        f"{page['name']} tech layoffs analysis: "
        f"{format_number(page['kpis']['total_laid_off'])} reported layoffs across "
        f"{format_number(page['kpis']['event_count'])} public events from "
        f"{page['date_range']['start']} to {page['date_range']['end']}."
    )
    site_url = "https://tech.debugcanada.com"
    topic_collection_path = "industries" if page["type"] == "industry" else "countries"
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": page["title"],
        "description": description,
        "datePublished": page["date_range"]["end"],
        "dateModified": page["date_range"]["end"],
        "author": {"@type": "Person", "name": "Frank Wang"},
        "publisher": {
            "@type": "Organization",
            "name": "Tech Layoff Tracker",
            "url": site_url,
        },
        "mainEntityOfPage": f"{site_url}{page['canonical_url']}",
    }
    breadcrumb_jsonld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Dashboard", "item": site_url},
            {
                "@type": "ListItem",
                "position": 2,
                "name": topic_label,
                "item": f"{site_url}/{topic_collection_path}/",
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": page["name"],
                "item": f"{site_url}{page['canonical_url']}",
            },
        ],
    }
    return {
        "page": page,
        "topic_label": topic_label,
        "description": description,
        "article_jsonld": article_jsonld,
        "breadcrumb_jsonld": breadcrumb_jsonld,
        "COMMON_FOOTER_EN": COMMON_FOOTER_EN,
        "COMMON_FOOTER_ZH": COMMON_FOOTER_ZH,
    }


def render_period_report_pages(env: Environment, report_data_dir: Path) -> list[dict]:
    """Render selected period report HTML pages from processed report JSON."""
    generated = []
    for report_type in ["yearly", "monthly", "quarterly", "weekly", "daily"]:
        data_dir = report_data_dir / report_type
        if not data_dir.exists():
            continue

        reports = []
        for json_path in sorted(data_dir.glob("*.json")):
            with open(json_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            reports.append(report)

        selected_reports = select_reports_for_html(report_type, reports)
        for index, report in enumerate(selected_reports):
            previous_report = selected_reports[index - 1] if index > 0 else None
            next_report = selected_reports[index + 1] if index < len(selected_reports) - 1 else None

            html_path = Path(report["canonical_url"].lstrip("/"))
            html_path.parent.mkdir(parents=True, exist_ok=True)
            context = build_period_page_context(
                report=report,
                previous_report=previous_report,
                next_report=next_report,
            )
            html = env.from_string(PERIOD_REPORT_TEMPLATE).render(**context)
            html_path.write_text(html, encoding="utf-8")

            generated.append({
                "report_type": report_type,
                "period": report["period"],
                "canonical_url": report["canonical_url"],
                "status": report["status"],
                "date_range": report["date_range"],
                "include_in_sitemap": context["include_in_sitemap"],
            })

    if generated:
        logger.info(f"   🗓 Period report pages saved: {len(generated)} selected period pages")
    return generated


def select_reports_for_html(report_type: str, reports: list[dict]) -> list[dict]:
    """Select which reports should get HTML pages."""
    if report_type in {"yearly", "monthly", "quarterly"}:
        return reports
    if report_type == "weekly":
        return reports[-12:]
    if report_type == "daily":
        return [
            report for report in reports
            if is_significant_daily_report(report)
        ]
    return []


def is_significant_daily_report(report: dict) -> bool:
    """Decide whether a daily report is worth a noindex HTML page."""
    kpis = report.get("kpis", {})
    return (
        kpis.get("total_laid_off", 0) >= 1000
        or kpis.get("high_intensity_event_count", 0) > 0
    )


def build_period_page_context(
    report: dict,
    previous_report: dict | None,
    next_report: dict | None,
) -> dict:
    """Build title, summary, and structured data for one period page."""
    report_type = report["report_type"]
    period = report["period"]
    report_type_label = {
        "daily": "Daily",
        "weekly": "Weekly",
        "monthly": "Monthly",
        "quarterly": "Quarterly",
        "yearly": "Yearly",
    }.get(report_type, "Period")
    title = f"Tech Layoffs {report_type_label} Report: {period}"
    kpis = report["kpis"]
    description = (
        f"{report_type_label} tech layoffs report for {period}: "
        f"{format_number(kpis['total_laid_off'])} reported layoffs across "
        f"{format_number(kpis['event_count'])} public events and "
        f"{format_number(kpis['company_count'])} companies."
    )
    summary = (
        f"During {period}, the dataset recorded {format_number(kpis['total_laid_off'])} "
        f"reported tech layoffs across {format_number(kpis['event_count'])} public events. "
        f"The report covers {format_number(kpis['company_count'])} companies, "
        f"{format_number(kpis['industry_count'])} industries, and "
        f"{format_number(kpis['country_count'])} countries or regions."
    )
    comparison_summary = build_comparison_summary(report)
    site_url = "https://tech.debugcanada.com"
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": report["date_range"]["end"],
        "dateModified": report["updated_at"],
        "author": {"@type": "Person", "name": "Frank Wang"},
        "publisher": {
            "@type": "Organization",
            "name": "Tech Layoff Tracker",
            "url": site_url,
        },
        "mainEntityOfPage": f"{site_url}{report['canonical_url']}",
    }
    breadcrumb_jsonld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Dashboard", "item": site_url},
            {"@type": "ListItem", "position": 2, "name": "Reports", "item": f"{site_url}/reports/"},
            {
                "@type": "ListItem",
                "position": 3,
                "name": title,
                "item": f"{site_url}{report['canonical_url']}",
            },
        ],
    }
    faqs = build_period_faqs(report, report_type_label)
    faq_jsonld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faqs
        ],
    }
    return {
        "report": report,
        "title": title,
        "description": description,
        "summary": summary,
        "comparison_summary": comparison_summary,
        "report_type_label": report_type_label,
        "robots": "noindex, follow" if report_type == "daily" else "index, follow",
        "include_in_sitemap": report_type != "daily",
        "previous_report": previous_report,
        "next_report": next_report,
        "faqs": faqs,
        "article_jsonld": article_jsonld,
        "breadcrumb_jsonld": breadcrumb_jsonld,
        "faq_jsonld": faq_jsonld,
        "COMMON_FOOTER_EN": COMMON_FOOTER_EN,
        "COMMON_FOOTER_ZH": COMMON_FOOTER_ZH,
    }


def build_period_faqs(report: dict, report_type_label: str) -> list[dict]:
    """Build FAQ content for generated period reports."""
    period = report["period"]
    kpis = report["kpis"]
    top_company = report["charts"]["company_top"][0] if report["charts"]["company_top"] else None
    top_industry = first_named_category(
        report["charts"]["industry_top"],
        "industry",
        {"industry": "N/A", "total_laid_off": 0},
    )
    company_answer = (
        f"{top_company['company']} had the highest reported layoff total in {period}, "
        f"with {format_number(top_company['total_laid_off'])} layoffs."
        if top_company else f"No company ranking is available for {period}."
    )
    return [
        {
            "question": f"How many tech layoffs were reported in {period}?",
            "answer": (
                f"The {report_type_label.lower()} report for {period} includes "
                f"{format_number(kpis['total_laid_off'])} reported layoffs across "
                f"{format_number(kpis['event_count'])} public events."
            ),
        },
        {
            "question": f"Which company had the most layoffs in {period}?",
            "answer": company_answer,
        },
        {
            "question": f"Which industry was most affected in {period}?",
            "answer": (
                f"The leading named industry in {period} is {top_industry['industry']}, "
                f"with {format_number(top_industry['total_laid_off'])} reported layoffs."
            ),
        },
        {
            "question": "How should this report be interpreted?",
            "answer": (
                "This report is generated from public layoff records. Rows without reported "
                "headcount can count as events but are excluded from headcount totals, and "
                "the dataset should not be treated as proof of causal claims."
            ),
        },
    ]


def build_comparison_summary(report: dict) -> str:
    """Build readable comparison text from period report comparison data."""
    previous = report["comparisons"]["previous_period"]
    year_ago = report["comparisons"]["same_period_last_year"]
    parts = []
    if previous.get("note") is None:
        parts.append(
            f"Compared with {previous['period']}, reported layoffs changed by "
            f"{format_optional_number(previous['total_laid_off_delta'])} "
            f"({format_pct_change(previous['total_laid_off_pct_change'])})."
        )
    else:
        parts.append(f"Previous-period comparison is unavailable for {report['period']}.")

    if year_ago.get("note") is None:
        parts.append(
            f"Compared with {year_ago['period']}, reported layoffs changed by "
            f"{format_optional_number(year_ago['total_laid_off_delta'])} "
            f"({format_pct_change(year_ago['total_laid_off_pct_change'])})."
        )
    else:
        parts.append(f"Year-over-year comparison is unavailable for {report['period']}.")
    return " ".join(parts)


def latest_report_meta(period_reports: list[dict], report_type: str) -> dict | None:
    """Return the latest generated report metadata for a given report type."""
    reports = [report for report in period_reports if report["report_type"] == report_type]
    return reports[-1] if reports else None


def write_sitemap_and_robots(
    stats: dict,
    period_reports: list[dict],
    topic_pages: list[dict],
) -> None:
    """Write sitemap index, child sitemaps, and robots.txt for SEO discovery."""
    site_url = "https://tech.debugcanada.com"
    lastmod = stats.get("date_range", {}).get("end", "")
    main_urls = [
        {"loc": f"{site_url}/", "lastmod": lastmod, "priority": "1.0"},
        {"loc": f"{site_url}/trend-report.html", "lastmod": lastmod, "priority": "0.9"},
        {"loc": f"{site_url}/reports/", "lastmod": lastmod, "priority": "0.8"},
        {"loc": f"{site_url}/llms.txt", "lastmod": lastmod, "priority": "0.5"},
        {"loc": f"{site_url}/ai-summary.json", "lastmod": lastmod, "priority": "0.5"},
    ]
    report_urls = []
    for report in period_reports:
        if not report.get("include_in_sitemap", True):
            continue
        priority = {
            "yearly": "0.85",
            "quarterly": "0.8",
            "monthly": "0.7",
            "weekly": "0.6",
        }.get(report["report_type"], "0.5")
        report_urls.append({
            "loc": f"{site_url}{report['canonical_url']}",
            "lastmod": report["date_range"]["end"],
            "priority": priority,
        })
    topic_urls = [
        {
            "loc": f"{site_url}{page['canonical_url']}",
            "lastmod": page["date_range"]["end"],
            "priority": "0.65",
        }
        for page in topic_pages
    ]

    write_urlset_sitemap(Path("sitemap-main.xml"), main_urls)
    write_urlset_sitemap(Path("sitemap-reports.xml"), report_urls)
    write_urlset_sitemap(Path("sitemap-topics.xml"), topic_urls)

    sitemap_index = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <sitemap>\n"
        f"    <loc>{site_url}/sitemap-main.xml</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        "  </sitemap>\n"
        "  <sitemap>\n"
        f"    <loc>{site_url}/sitemap-reports.xml</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        "  </sitemap>\n"
        "  <sitemap>\n"
        f"    <loc>{site_url}/sitemap-topics.xml</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        "  </sitemap>\n"
        "</sitemapindex>\n"
    )
    Path("sitemap.xml").write_text(sitemap_index, encoding="utf-8")
    logger.info(
        f"   🧭 Sitemap index saved to: sitemap.xml "
        f"({len(main_urls)} main URLs, {len(report_urls)} report URLs, "
        f"{len(topic_urls)} topic URLs)"
    )

    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "Sitemap: https://tech.debugcanada.com/sitemap.xml\n"
        "Host: https://tech.debugcanada.com\n"
    )
    Path("robots.txt").write_text(robots, encoding="utf-8")
    logger.info("   🧭 Robots file saved to: robots.txt")


def write_urlset_sitemap(path: Path, urls: list[dict]) -> None:
    """Write one URL set sitemap file."""
    url_items = "\n".join(
        "  <url>\n"
        f"    <loc>{item['loc']}</loc>\n"
        f"    <lastmod>{item['lastmod']}</lastmod>\n"
        "    <changefreq>weekly</changefreq>\n"
        f"    <priority>{item['priority']}</priority>\n"
        "  </url>"
        for item in urls
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{url_items}\n"
        "</urlset>\n"
    )
    path.write_text(sitemap, encoding="utf-8")


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
    industry_pages = load_json("industry_pages")
    country_pages = load_json("country_pages")
    stats = load_json("stats")
    subtitle_en, subtitle_zh = build_subtitles(stats)

    logger.info(f"   📂 Loaded data: {len(company_summary)} companies, {len(monthly_trend)} months")

    # Render template with Jinja2 Environment (for filter support)
    env = Environment()
    env.filters["format_number"] = format_number
    env.filters["format_optional_number"] = format_optional_number
    env.filters["format_pct_change"] = format_pct_change
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
        COMMON_FOOTER_EN=COMMON_FOOTER_EN,
        COMMON_FOOTER_ZH=COMMON_FOOTER_ZH,
    )

    output_path.write_text(html, encoding="utf-8")
    logger.info(f"   💾 Chart saved to: {output_path}")

    report_context = build_report_context(
        company_summary=company_summary,
        monthly_trend=monthly_trend,
        industry_breakdown=industry_breakdown,
        country_breakdown=country_breakdown,
        stage_size_heatmap=stage_size_heatmap,
        layoff_pct_distribution=layoff_pct_distribution,
        recent_layoffs=recent_layoffs,
        industry_pages=industry_pages,
        country_pages=country_pages,
        stats=stats,
    )
    write_report_pages(env, report_context, data_dir / "reports")

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
