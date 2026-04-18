<div align="center">

# 🔍 Tech Layoff Tracker

### 全球科技行业裁员全景洞察 · 2025–2026

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4-green?style=for-the-badge)](https://www.crummy.com/software/BeautifulSoup/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![ECharts](https://img.shields.io/badge/ECharts-5.x-AA344D?style=for-the-badge)](https://echarts.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Pages_Deploy-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](.github/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br>

**An automated data pipeline that scrapes, processes, and visualizes global tech industry layoff data.**

*一个自动化数据管道，爬取、处理并可视化全球科技行业裁员数据。*

[Quick Start](#-quick-start) · [Features](#-features) · [Architecture](#-architecture) · [Data Sources](#-data-sources)

</div>

---

## 📸 Dashboard Preview

<div align="center">

### 🇺🇸 English Mode (Default)

![Dashboard - English](docs/images/dashboard_en.png)

![Dashboard - Charts](docs/images/dashboard_charts.png)

### 🇨🇳 中文模式

![Dashboard - Chinese](docs/images/dashboard_cn.png)

> 💡 Supports **EN / 中文** language toggle — switch instantly without page reload.

</div>


---

## ✨ Features

| Feature | Description |
|---|---|
| 🕷️ **Web Scraper** | Multi-strategy scraper with live Airtable shared-view extraction, CSV mirror fallback, and offline sample data |
| 🧹 **Data Processing** | Pandas-based pipeline that cleans, normalizes, and aggregates raw data into analysis-ready JSON |
| 📊 **Interactive Dashboard** | Glassmorphism-styled ECharts dashboard with animated gradients, responsive layout, dynamic date-range subtitles, and homepage-first analysis modules |
| 🧭 **SEO Trend Report** | Static `trend-report.html` page with indexable analysis text, chart-backed findings, methodology notes, FAQ, and structured data |
| 🗂️ **Reports Archive** | `/reports/` archive entry designed for daily, weekly, monthly, and quarterly layoff trend reports |
| 🤖 **GEO / AI-Readable Summary** | `llms.txt` and `ai-summary.json` expose canonical facts, data range, methodology, and source files for AI answer engines |
| 🧭 **SEO Discovery Files** | Generated `sitemap.xml` and `robots.txt` expose the dashboard, reports, and AI-readable files to crawlers |
| 🚀 **One-Command Pipeline** | `python main.py` runs the complete scrape → process → visualize workflow |
| 🐳 **Docker Ready** | Multi-stage Dockerfile + Compose — `docker compose up` for instant deployment |
| 🔄 **Offline-Capable** | Built-in curated dataset ensures the project works even without network access |

---

## 🚀 Quick Start

### Option A: Docker (Recommended) 🐳

```bash
# Clone & start — one command!
git clone https://github.com/frankwang0909/tech-layoff-tracker.git
cd tech-layoff-tracker
```

Open **http://localhost:8080/** in your browser. Done! 🎉

### Option B: Local Python

```bash
# Clone the repository
git clone https://github.com/frankwang0909/tech-layoff-tracker.git
cd tech-layoff-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python main.py

# Serve the dashboard locally

```

Open **http://localhost:8080/** or directly open `index.html`.

### CLI Options

```bash
python main.py                  # Full pipeline: Scrape → Process → Chart
python main.py --skip-scrape    # Skip scraping, use existing data
python main.py --verbose        # Debug output
python server.py --port 3000    # Serve on custom port
```

---

## ⚙️ CI/CD: GitHub Pages Deploy

This project uses **GitHub Actions** to deploy the generated static site to **GitHub Pages**:

| Setting | Value |
|---|---|
| 🔄 **Trigger** | Push to `main` and manual dispatch |
| 📦 **Artifact** | Entire repository root (including `index.html` and `visualization/`) |
| 🌐 **Deploy** | GitHub Pages with optional custom domain |
| 🧭 **Entry Point** | Root `index.html` serves the dashboard homepage directly |

### Setup Instructions

1. Push this repo to GitHub
2. Go to **Settings → Pages → Source** and select **GitHub Actions**
3. Push a commit to `main` or run **Actions → Deploy Static Redirects → Run workflow**
4. Your dashboard will be live at:
   ```
   https://frankwang0909.github.io/tech-layoff-tracker/ 
   ```
   If you configure a custom domain, the root path should render the dashboard directly.


## 🏗️ Architecture

```
tech-layoff-tracker/
│
├── index.html                       # 🌐 Generated homepage dashboard
├── trend-report.html                # 🧭 Generated SEO trend report
├── llms.txt                         # 🤖 LLM guidance and canonical facts
├── ai-summary.json                  # 🤖 Machine-readable answer summary
├── sitemap.xml                      # 🧭 Generated sitemap index
├── sitemap-main.xml                 # 🧭 Generated main-page sitemap
├── sitemap-reports.xml              # 🧭 Generated reports sitemap
├── sitemap-topics.xml               # 🧭 Generated industry/country sitemap
├── robots.txt                       # 🧭 Generated crawler directives
├── layoff_chart.html                # ↪ Root-level legacy redirect
├── main.py                          # 🚀 One-command entry point
├── requirements.txt                 # Python dependencies
├── .gitignore
│
├── scraper/                         # 🕷️ Data Collection
│   ├── __init__.py
│   ├── config.py                    # Scraper configuration
│   └── layoffs_fyi_scraper.py       # Multi-strategy web scraper
│
├── analysis/                        # 🔧 Data Processing
│   ├── __init__.py
│   └── data_processor.py            # Clean, aggregate, export JSON
│
├── visualization/                   # 📊 Chart Generation
│   ├── generate_charts.py           # Jinja2 template → HTML dashboard
│   └── layoff_chart.html            # Legacy redirect kept for old links
│
├── data/
│   ├── raw/                         # Raw scraped CSV
│   └── processed/                   # Aggregated JSON files
│       ├── industry_pages.json      # 🧩 Topic data for industry pages
│       └── country_pages.json       # 🧩 Topic data for country pages
│
├── industries/                      # 🧩 Generated industry topic pages
├── countries/                       # 🧩 Generated country/region topic pages
│
└── reports/
    ├── index.html                   # 🗂 Generated reports archive
    ├── daily/                       # 🗓 Generated significant daily report pages (noindex)
    ├── weekly/                      # 🗓 Generated recent weekly report pages
    ├── monthly/                     # 🗓 Generated monthly report pages
    ├── quarterly/                   # 🗓 Generated quarterly report pages
    ├── yearly/                      # 🗓 Generated yearly report pages
    └── layoff_report_2025_2026.md   # Detailed analysis report (中文)
```

### Pipeline Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   SCRAPE     │────▶│   PROCESS    │────▶│  VISUALIZE   │
│              │     │              │     │              │
│ layoffs.fyi  │     │  pandas      │     │  Jinja2 +    │
│ Airtable API │     │  aggregation │     │  ECharts     │
│ + fallbacks  │     │  → JSON      │     │  → HTML      │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## 🕷️ Scraper Design

The scraper uses a **3-tier strategy** for maximum reliability:

| Priority | Strategy | Description |
|---|---|---|
| 1️⃣ | Live Airtable Shared View | Discover the current Airtable iframe from `layoffs.fyi`, then read the shared-view payload exposed to public visitors |
| 2️⃣ | GitHub CSV Mirror | Fallback snapshot from a community-maintained CSV mirror |
| 3️⃣ | Offline Dataset | Curated sample data from verified public reports (always works) |

**Ethical scraping practices:**
- Polite request delays (`REQUEST_DELAY = 1.0s`)
- Proper `User-Agent` header
- Configurable retry with backoff
- Only targets publicly available data
- Preserves current embed rotations by discovering the Airtable URL from the live page first
- Normalizes Airtable UTC timestamps before applying the configured date filter

---

## 📊 Dataset Notes

- The dashboard subtitle is generated from `data/processed/stats.json`, so the displayed range tracks the latest processed snapshot instead of a hard-coded month.
- When the live Airtable source is reachable, `python main.py` now captures current layoffs.fyi records, including post-March 2026 entries.
- If the live source fails or returns an unusable filtered result, the pipeline falls back to the CSV mirror and then to the bundled offline sample dataset.
- The current snapshot metrics can always be read from `data/processed/stats.json`.

## 📈 Homepage Analytics

The homepage dashboard now combines overview KPIs with additional analysis slices generated from `data/processed/`:

- `monthly_comparison.json` powers a side-by-side `2025 vs 2026` monthly comparison chart
- `stage_size_heatmap.json` powers a `Stage × Layoff Size` event heatmap
- `layoff_pct_distribution.json` powers the `Layoff % Distribution` chart
- `recent_layoffs.json` powers the latest layoff events table shown on the homepage

## 🧭 SEO Trend Reports

The pipeline also generates static, crawlable report pages:

- `trend-report.html` provides an indexable trend report with executive summary, key findings, chart-backed sections, methodology, FAQ, and JSON-LD structured data.
- `reports/index.html` is the archive entry for the planned daily, weekly, monthly, and quarterly report system.
- `reports/weekly/*.html` includes the most recent weekly reports and is included in `sitemap.xml`.
- `reports/monthly/*.html` and `reports/quarterly/*.html` are generated from period report JSON for long-tail SEO.
- `reports/yearly/*.html` provides annual and year-to-date summary pages for evergreen SEO.
- `reports/daily/*.html` is generated only for significant daily reports and uses `noindex, follow` to avoid thin-content indexing.
- `industries/*.html` and `countries/*.html` provide focused topic pages for long-tail SEO and AI answer discovery.
- `llms.txt` and `ai-summary.json` provide GEO-friendly canonical facts for AI answer engines and chatbots.
- `sitemap.xml` is a sitemap index pointing to `sitemap-main.xml`, `sitemap-reports.xml`, and `sitemap-topics.xml`.

These pages reuse the existing processed JSON data so they stay aligned with the dashboard after every `python main.py` run.

---

## 📁 Data Sources

- [layoffs.fyi](https://layoffs.fyi/) — Primary tech layoff tracker
- RationalFX Annual Reports
- Major tech press: Reuters, Bloomberg, CNBC, The Verge, TechCrunch
- Company press releases and SEC filings

---

## 🛠️ Tech Stack

- **Scraping**: `requests`, `BeautifulSoup4`, `lxml`
- **Processing**: `pandas`
- **Templating**: `Jinja2`
- **Visualization**: `ECharts 5.x` (client-side)
- **Language**: Python 3.10+

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**If you found this project useful, please consider giving it a ⭐!**

</div>
