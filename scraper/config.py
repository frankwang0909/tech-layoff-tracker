"""
Configuration for the layoffs.fyi scraper.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class ScraperConfig:
    """Configuration settings for the scraper."""

    # Target URL — layoffs.fyi exposes data via a publicly accessible Google Sheet
    # which can be exported as CSV. This is the standard approach used by researchers.
    LAYOFFS_FYI_CSV_URL: str = (
        "https://layoffs.fyi/getData/"
    )

    # Fallback: Google Sheets public export URL
    # The underlying data is maintained in a Google Sheet that is publicly readable.
    GOOGLE_SHEET_CSV_URL: str = (
        "https://docs.google.com/spreadsheets/d/"
        "1annGUhBMFRMeFip2sORbbKNkJX1bMPaRi9qiiSfFgTs/"
        "export?format=csv"
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
