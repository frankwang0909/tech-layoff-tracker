"""
Configuration for the layoffs.fyi scraper.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class ScraperConfig:
    """Configuration settings for the scraper."""

    # Source page where layoffs.fyi embeds the current Airtable tracker.
    LAYOFFS_FYI_PAGE_URL: str = "https://layoffs.fyi/"

    # Fallback Airtable embed URL discovered from the live page on 2026-04-09.
    # We still prefer parsing the source page first so future embed rotations
    # do not require a code change.
    LAYOFFS_FYI_AIRTABLE_URL: str = (
        "https://airtable.com/embed/app1PaujS9zxVGUZ4/"
        "shroKsHx3SdYYOzeh?backgroundColor=green&viewControls=on"
    )

    # Fallback: Community-maintained GitHub mirror
    # This repository is frequently used for data tutorials and contains a reliable snapshot.
    GITHUB_MIRROR_CSV_URL: str = (
        "https://raw.githubusercontent.com/AlexTheAnalyst/"
        "MySQL-YouTube-Series/main/layoffs.csv"
    )

    # Date range filter
    START_DATE: date = field(default_factory=lambda: date(2025, 1, 1))
    END_DATE: date = field(default_factory=lambda: date.today())

    # Request settings
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY: float = 1.0  # seconds between requests (polite crawling)
    MAX_RETRIES: int = 3

    USER_AGENT: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    # Output paths
    RAW_DATA_DIR: str = "data/raw"
    PROCESSED_DATA_DIR: str = "data/processed"
    RAW_CSV_FILENAME: str = "layoffs_raw.csv"
