"""
generate_charts.py
==================
Reads processed JSON data and renders an interactive ECharts dashboard
as a standalone HTML file.

Uses Jinja2 templating to dynamically embed data into the HTML.
"""

import json
import logging
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
    <title>Tech Layoff Tracker 2025-2026</title>
    <meta name="description" content="Interactive dashboard tracking global tech industry layoffs from Jan 2025 to present, powered by Python scrapers and ECharts.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: #0a0f1e;
            color: #e2e8f0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            min-height: 100vh;
            padding: 2rem 1rem;
            overflow-x: hidden;
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

        .container { max-width: 1280px; margin: 0 auto; }

        header {
            text-align: center;
            padding: 3rem 0 2rem;
            position: relative;
        }
        header h1 {
            font-size: clamp(2rem, 5vw, 3.5rem);
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

        footer {
            text-align: center;
            padding: 3rem 0 1rem;
            color: #475569;
            font-size: 0.75rem;
            line-height: 1.8;
        }
        footer a { color: #818cf8; text-decoration: none; }
        footer a:hover { text-decoration: underline; }

        @media (max-width: 600px) {
            body { padding: 1rem 0.5rem; }
            .chart-container { height: 300px; }
            .kpi-card .value { font-size: 2rem; }
            .lang-toggle { position: static; margin: 0 auto 1rem; }
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

    <footer id="pageFooter"></footer>
</div>

<script>
// ═══════════════════════════════════════════════════════
//  i18n Translation Dictionary
// ═══════════════════════════════════════════════════════
const i18n = {
    en: {
        title: 'Global Tech Layoff Insights',
        subtitle: 'Jan 2025 – Mar 2026 | Industry Restructuring & Workforce Optimization',
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
        footer: 'Data Sources: <a href="https://layoffs.fyi/" target="_blank">layoffs.fyi</a> · RationalFX · Major tech media<br>Disclaimer: Some figures are estimates or planned reductions<br><br>Built with Python · BeautifulSoup · Pandas · ECharts &nbsp;|&nbsp;<a href="https://github.com/frankwang0909/tech-layoff-tracker" target="_blank">⭐ View on GitHub</a>',
        yAxisName: 'Layoffs',
        seriesBar: 'Layoffs',
        seriesLine: 'Trend',
        reasons: [
            { value: 45, name: 'Economic Uncertainty & Inflation' },
            { value: 30, name: 'AI Transformation & Automation' },
            { value: 15, name: 'Post-Pandemic Overhire Correction' },
            { value: 10, name: 'Business Restructuring' }
        ]
    },
    zh: {
        title: '全球科技公司裁员全景洞察',
        subtitle: '2025年1月 – 2026年3月 ｜ 科技行业深度洗牌与结构优化分析',
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
        footer: '数据来源: <a href="https://layoffs.fyi/" target="_blank">layoffs.fyi</a> · RationalFX · 各大科技媒体公开报道<br>免责声明: 部分数据为估计值或分阶段实施的计划裁员人数<br><br>Built with Python · BeautifulSoup · Pandas · ECharts &nbsp;|&nbsp;<a href="https://github.com/frankwang0909/tech-layoff-tracker" target="_blank">⭐ View on GitHub</a>',
        yAxisName: '裁员人数',
        seriesBar: '裁员人数',
        seriesLine: '趋势线',
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

const companyData = {{ company_summary | tojson }};
const industryData = {{ industry_breakdown | tojson }};
const monthlyData = {{ monthly_trend | tojson }};
const countryData = {{ country_breakdown | tojson }};
const industryColors = ['#818cf8','#38bdf8','#c084fc','#f472b6','#34d399','#fbbf24','#fb923c','#64748b','#94a3b8','#475569'];

const companyChart = initChart('companyChart');
const industryChart = initChart('industryChart');
const monthlyChart = initChart('monthlyChart');
const countryChart = initChart('countryChart');
const reasonChart = initChart('reasonChart');

// ═══════════════════════════════════════════════════════
//  Render Charts (language-aware)
// ═══════════════════════════════════════════════════════
function renderCharts(t) {
    companyChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: {type: 'shadow'}, ...TOOLTIP },
        grid: { left: '2%', right: '12%', top: '4%', bottom: '4%', containLabel: true },
        xAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: AX, type: 'dashed' } },
            axisLabel: { color: TX, formatter: v => v >= 1000 ? (v/1000)+'k' : v }
        },
        yAxis: {
            type: 'category',
            data: companyData.map(d => d.company).reverse(),
            axisLabel: { color: TX, fontWeight: 600 },
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
                show: true, position: 'right', color: '#94a3b8', fontSize: 12,
                formatter: p => p.value.toLocaleString()
            },
            emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(56,189,248,0.3)' } }
        }]
    });

    industryChart.setOption({
        tooltip: { trigger: 'item', ...TOOLTIP, formatter: '{b}: {c} ({d}%)' },
        legend: {
            orient: 'vertical', right: 10, top: 'middle',
            textStyle: { color: TX, fontSize: 11 },
            itemWidth: 12, itemHeight: 12, itemGap: 8
        },
        series: [{
            type: 'pie',
            radius: ['40%', '72%'],
            center: ['40%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 8, borderColor: '#0a0f1e', borderWidth: 3 },
            label: { show: false },
            emphasis: {
                label: { show: true, fontSize: 16, fontWeight: 700, color: '#f8fafc' },
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
        grid: { left: '3%', right: '4%', top: '12%', bottom: '10%', containLabel: true },
        xAxis: {
            type: 'category',
            data: monthlyData.map(d => d.month),
            axisLabel: { color: TX, rotate: 30 },
            axisLine: { lineStyle: { color: AX } },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            name: t.yAxisName,
            nameTextStyle: { color: TX },
            axisLabel: { color: TX, formatter: v => v >= 1000 ? (v/1000)+'k' : v },
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
        grid: { left: '3%', right: '10%', top: '4%', bottom: '4%', containLabel: true },
        xAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: AX, type: 'dashed' } },
            axisLabel: { color: TX, formatter: v => v >= 1000 ? (v/1000)+'k' : v }
        },
        yAxis: {
            type: 'category',
            data: countryData.map(d => d.country).reverse(),
            axisLabel: { color: TX, fontWeight: 500 },
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
                show: true, position: 'right', color: '#94a3b8', fontSize: 12,
                formatter: p => p.value.toLocaleString()
            }
        }]
    });

    reasonChart.setOption({
        tooltip: { trigger: 'item', ...TOOLTIP, formatter: '{b}: {d}%' },
        legend: {
            orient: 'vertical', right: 10, top: 'middle',
            textStyle: { color: TX, fontSize: 11 },
            itemWidth: 12, itemHeight: 12, itemGap: 10
        },
        series: [{
            type: 'pie',
            radius: ['40%', '72%'],
            center: ['38%', '50%'],
            itemStyle: { borderRadius: 8, borderColor: '#0a0f1e', borderWidth: 3 },
            label: {
                show: true,
                position: 'outside',
                formatter: '{b}\n{d}%',
                color: '#cbd5e1',
                fontSize: 12,
                fontWeight: 500,
                lineHeight: 18
            },
            labelLine: {
                show: true,
                length: 15,
                length2: 10,
                lineStyle: { color: '#475569', width: 1.5 }
            },
            emphasis: {
                label: { show: true, fontSize: 16, fontWeight: 700, color: '#f8fafc' },
                scaleSize: 6
            },
            data: t.reasons.map((r, i) => ({
                ...r,
                itemStyle: { color: reasonColors[i] }
            }))
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

    // Footer (uses innerHTML for links)
    document.getElementById('pageFooter').innerHTML = t.footer;

    // Re-render charts with translated labels
    renderCharts(t);
}

// ═══════════════════════════════════════════════════════
//  Init
// ═══════════════════════════════════════════════════════
switchLang('en');

window.addEventListener('resize', () => {
    [companyChart, industryChart, monthlyChart, countryChart, reasonChart].forEach(c => c.resize());
});
</script>
</body>
</html>"""


def format_number(value: int | float) -> str:
    """Format large numbers with comma separator."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def generate_chart(data_dir: str = "data/processed", output_path: str = "visualization/layoff_chart.html"):
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
    stats = load_json("stats")

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
        stats=stats,
    )

    output_path.write_text(html, encoding="utf-8")
    logger.info(f"   💾 Chart saved to: {output_path}")
    logger.info("✅ Chart generation complete.")

    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_chart()
