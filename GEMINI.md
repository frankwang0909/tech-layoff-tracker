# GEMINI.md

## Project Overview
**Tech Layoff Tracker** is an automated data pipeline that scrapes, processes, and visualizes global tech industry layoff data for the 2025–2026 period. It provides a bilingual (English/Chinese) interactive dashboard with high-level insights into industry trends, geographical distribution, and major company impacts.

### Main Technologies
- **Language:** Python 3.10+
- **Data Collection:** `requests`, `BeautifulSoup4`, `lxml`
- **Data Processing:** `pandas`
- **Visualization:** `ECharts 5.x`, `Jinja2` (templating), Vanilla CSS (Glassmorphism design)
- **Deployment:** Docker, GitHub Actions (Daily automated updates)

### Architecture
- `main.py`: The single-command entry point coordinating the full pipeline.
- `scraper/`: Implements a 3-tier collection strategy (Google Sheet CSV → HTML Parsing → Offline Fallback).
- `analysis/`: Cleans raw data and generates aggregated JSON summaries (companies, months, industries, countries).
- `visualization/`: Renders the `layoff_chart.html` dashboard using data-driven Jinja2 templates.
- `data/`: Contains `raw/` CSV and `processed/` JSON datasets.
- `server.py`: A simple local server to host the generated dashboard.

---

## Building and Running

### Prerequisites
- Python 3.10+
- Virtual environment (recommended)

### Installation
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Execution Commands
- **Run Full Pipeline:** `python main.py` (Scrape → Process → Visualize)
- **Skip Scraping:** `python main.py --skip-scrape` (Use existing local raw data)
- **Serve Dashboard:** `python server.py` (Starts server at `http://localhost:8080`)
- **Docker Deployment:** `docker compose up`

---

## Development Conventions

### Data Pipeline Flow
1. **Scrape:** Data is fetched and stored in `data/raw/layoffs_raw.csv`.
2. **Process:** `DataProcessor` cleans the CSV and exports multiple JSON files to `data/processed/`.
3. **Visualize:** `generate_charts.py` reads JSONs and produces `visualization/layoff_chart.html`.

### Coding Standards
- **Scraper Reliability:** Always implement fallback strategies and polite crawling (use `REQUEST_DELAY` and `USER_AGENT` from `scraper/config.py`).
- **Data Integrity:** Column normalization in `scraper/layoffs_fyi_scraper.py` is critical for handling varied source schemas.
- **Bilingual Support:** The dashboard template in `visualization/generate_charts.py` uses a JavaScript `i18n` dictionary for EN/ZH switching.
- **Environment:** Use `.venv` for local development; dependencies are managed via `requirements.txt`.

### Testing & Validation
- Ensure `python main.py` runs to completion without errors before committing data changes.
- Verify dashboard responsiveness and language toggling in `visualization/layoff_chart.html`.
