"""
data_processor.py
=================
Processes raw layoff data into structured, analysis-ready aggregations.

Produces:
  - company_summary.json   → Top companies by total layoff count
  - monthly_trend.json     → Month-by-month layoff counts
  - industry_breakdown.json → Layoffs by industry
  - country_breakdown.json  → Layoffs by country
"""

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Cleans raw scraped data and generates aggregated JSON datasets
    for chart rendering.
    """

    def __init__(self, raw_csv_path: str, output_dir: str = "data/processed"):
        self.raw_csv_path = Path(raw_csv_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.df: pd.DataFrame | None = None

    def run(self) -> dict:
        """
        Execute the full processing pipeline.
        Returns a dict of all aggregated datasets.
        """
        logger.info("\n🔧 Starting data processing pipeline...")

        self._load()
        self._clean()

        results = {
            "company_summary": self._aggregate_by_company(),
            "monthly_trend": self._aggregate_by_month(),
            "industry_breakdown": self._aggregate_by_industry(),
            "country_breakdown": self._aggregate_by_country(),
            "stats": self._compute_stats(),
        }

        # Save each result to JSON
        for name, data in results.items():
            output_path = self.output_dir / f"{name}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"   💾 Saved: {output_path}")

        logger.info("✅ Data processing complete.")
        return results

    def _load(self):
        """Load the raw CSV into a DataFrame."""
        logger.info(f"   📂 Loading raw data from: {self.raw_csv_path}")
        self.df = pd.read_csv(self.raw_csv_path)
        logger.info(f"   ✓ Loaded {len(self.df)} records.")

    def _clean(self):
        """Clean and standardize the data."""
        df = self.df

        # Ensure numeric
        df["num_laid_off"] = pd.to_numeric(df["num_laid_off"], errors="coerce")
        df = df.dropna(subset=["num_laid_off"])
        df["num_laid_off"] = df["num_laid_off"].astype(int)

        # Parse dates
        df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
        df = df.dropna(subset=["date"])

        # Extract year-month
        df["year_month"] = df["date"].dt.to_period("M").astype(str)
        df["year"] = df["date"].dt.year

        # Fill missing industry/country
        df["industry"] = df.get("industry", pd.Series(["Unknown"] * len(df))).fillna("Other")
        df["country"] = df.get("country", pd.Series(["Unknown"] * len(df))).fillna("Unknown")

        # Standardize company names
        df["company"] = df["company"].str.strip()

        self.df = df.reset_index(drop=True)
        logger.info(f"   🧹 Cleaned: {len(self.df)} valid records.")

    def _aggregate_by_company(self) -> list[dict]:
        """Top 15 companies by total layoff count."""
        grouped = (
            self.df.groupby("company")["num_laid_off"]
            .sum()
            .sort_values(ascending=False)
            .head(15)
        )
        result = [
            {"company": company, "total_laid_off": int(count)}
            for company, count in grouped.items()
        ]
        logger.info(f"   📊 Company summary: top {len(result)} companies.")
        return result

    def _aggregate_by_month(self) -> list[dict]:
        """Monthly layoff counts, sorted chronologically."""
        grouped = (
            self.df.groupby("year_month")["num_laid_off"]
            .sum()
            .sort_index()
        )
        result = [
            {"month": month, "total_laid_off": int(count)}
            for month, count in grouped.items()
        ]
        logger.info(f"   📊 Monthly trend: {len(result)} months.")
        return result

    def _aggregate_by_industry(self) -> list[dict]:
        """Layoffs broken down by industry."""
        grouped = (
            self.df.groupby("industry")["num_laid_off"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        result = [
            {"industry": industry, "total_laid_off": int(count)}
            for industry, count in grouped.items()
        ]
        logger.info(f"   📊 Industry breakdown: {len(result)} industries.")
        return result

    def _aggregate_by_country(self) -> list[dict]:
        """Layoffs broken down by country/region."""
        grouped = (
            self.df.groupby("country")["num_laid_off"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        result = [
            {"country": country, "total_laid_off": int(count)}
            for country, count in grouped.items()
        ]
        logger.info(f"   📊 Country breakdown: {len(result)} countries/regions.")
        return result

    def _compute_stats(self) -> dict:
        """Compute high-level summary statistics."""
        total = int(self.df["num_laid_off"].sum())
        total_2025 = int(
            self.df[self.df["year"] == 2025]["num_laid_off"].sum()
        )
        total_2026 = int(
            self.df[self.df["year"] == 2026]["num_laid_off"].sum()
        )
        num_companies = self.df["company"].nunique()
        num_countries = self.df["country"].nunique()

        stats = {
            "total_laid_off": total,
            "total_2025": total_2025,
            "total_2026": total_2026,
            "num_companies": num_companies,
            "num_countries": num_countries,
            "date_range": {
                "start": str(self.df["date"].min().date()),
                "end": str(self.df["date"].max().date()),
            },
        }
        logger.info(f"   📈 Stats: {total:,} total layoffs across {num_companies} companies.")
        return stats
