#!/usr/bin/env python3
"""
main.py — Tech Layoff Data Pipeline
====================================

One-command entry point that executes the full pipeline:
  1. Scrape  → Fetch layoff data from layoffs.fyi (or use offline samples)
  2. Process → Clean, aggregate, and export structured JSON
  3. Render  → Generate an interactive ECharts HTML dashboard

Usage:
    python main.py                  # Full pipeline (scrape + process + chart)
    python main.py --skip-scrape    # Skip scraping, use existing raw data
    python main.py --help

Author:  Frank Wang
License: MIT
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from scraper.config import ScraperConfig
from scraper.layoffs_fyi_scraper import LayoffsScraper
from analysis.data_processor import DataProcessor
from visualization.generate_charts import generate_chart


def setup_logging(verbose: bool = False):
    """Configure structured logging output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main():
    parser = argparse.ArgumentParser(
        description="🔍 Tech Layoff Data Pipeline — Scrape, Process, Visualize",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  # Full pipeline
  python main.py --skip-scrape    # Use existing data, skip scraping
  python main.py --verbose        # Show detailed debug output
        """,
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip the scraping step and use existing raw CSV data.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (debug) logging.",
    )
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("")
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║   🔍 Tech Layoff Data Pipeline                         ║")
    logger.info("║   Scrape → Process → Visualize                         ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("")

    config = ScraperConfig()
    raw_csv_path = Path(config.RAW_DATA_DIR) / config.RAW_CSV_FILENAME

    # ────────────────────── Step 1: Scrape ──────────────────────
    if not args.skip_scrape:
        logger.info("━━━ STEP 1/3: Data Collection ━━━━━━━━━━━━━━━━━━━━━━━━━━")
        scraper = LayoffsScraper(config)
        scraper.run()
    else:
        logger.info("━━━ STEP 1/3: Scraping SKIPPED (--skip-scrape) ━━━━━━━━━")
        if not raw_csv_path.exists():
            logger.error(
                f"❌ No raw data found at {raw_csv_path}. "
                f"Please run without --skip-scrape first."
            )
            sys.exit(1)

    # ────────────────────── Step 2: Process ─────────────────────
    logger.info("\n━━━ STEP 2/3: Data Processing ━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    processor = DataProcessor(
        raw_csv_path=str(raw_csv_path),
        output_dir=config.PROCESSED_DATA_DIR,
    )
    processor.run()

    # ────────────────────── Step 3: Visualize ──────────────────
    logger.info("\n━━━ STEP 3/3: Chart Generation ━━━━━━━━━━━━━━━━━━━━━━━━━━")
    chart_path = generate_chart(
        data_dir=config.PROCESSED_DATA_DIR,
        output_path="index.html",
    )

    # ────────────────────── Done ───────────────────────────────
    logger.info("")
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║   ✅ Pipeline Complete!                                 ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("")
    logger.info(f"   📊 Open the dashboard: file://{chart_path.resolve()}")
    logger.info(f"   📁 Raw data:   {raw_csv_path}")
    logger.info(f"   📁 Processed:  {config.PROCESSED_DATA_DIR}/")
    logger.info("")


if __name__ == "__main__":
    main()
