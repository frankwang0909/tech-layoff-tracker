"""
Configuration for the layoffs.fyi scraper.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class ScraperConfig:
    """Configuration settings for the scraper."""

    # Primary Airtable Embed URL
    LAYOFFS_FYI_AIRTABLE_URL: str = (
        "https://airtable.com/embed/shrqYt5kSqMzHV9R5?backgroundColor=green"
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
