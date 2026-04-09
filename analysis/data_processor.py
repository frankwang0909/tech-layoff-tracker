"""
data_processor.py
=================
Processes raw layoff data into structured, analysis-ready aggregations.

Produces:
  - company_summary.json   → Top companies by total layoff count
  - monthly_trend.json     → Month-by-month layoff counts
  - industry_breakdown.json → Layoffs by industry
  - country_breakdown.json  → Layoffs by country
  - monthly_comparison.json → 2025 vs 2026 month-aligned comparison
  - stage_size_heatmap.json → Layoff event counts by stage and size bucket
  - layoff_pct_distribution.json → Event counts by layoff percentage bucket
  - recent_layoffs.json → Latest layoff records for homepage table
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
            "monthly_comparison": self._aggregate_monthly_comparison(),
            "stage_size_heatmap": self._aggregate_stage_size_heatmap(),
            "layoff_pct_distribution": self._aggregate_layoff_pct_distribution(),
            "recent_layoffs": self._recent_layoffs(),
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
        df["date"] = pd.to_datetime(
            df["date"],
            format="mixed",
            errors="coerce",
            utc=True,
        ).dt.tz_localize(None)
        df = df.dropna(subset=["date"])

        # Extract year-month
        df["year_month"] = df["date"].dt.to_period("M").astype(str)
        df["year"] = df["date"].dt.year
        df["month_num"] = df["date"].dt.month

        # Fill missing industry/country
        df["industry"] = df.get("industry", pd.Series(["Unknown"] * len(df))).fillna("Other")
        df["country"] = df.get("country", pd.Series(["Unknown"] * len(df))).fillna("Unknown")
        df["stage"] = df.get("stage", pd.Series(["Unknown"] * len(df))).fillna("Unknown")
        df["location_hq"] = df.get("location_hq", pd.Series(["Unknown"] * len(df))).fillna("Unknown")
        df["source"] = df.get("source", pd.Series([""] * len(df))).fillna("")

        # Standardize optional numeric dimensions
        df["percentage_laid_off"] = pd.to_numeric(
            df.get("percentage_laid_off", pd.Series([None] * len(df))),
            errors="coerce",
        )
        df["funds_raised_millions"] = pd.to_numeric(
            df.get("funds_raised_millions", pd.Series([None] * len(df))),
            errors="coerce",
        )

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

    def _aggregate_monthly_comparison(self) -> list[dict]:
        """Compare 2025 and 2026 layoff totals month by month."""
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        filtered = self.df[self.df["year"].isin([2025, 2026])]
        pivot = (
            filtered.groupby(["month_num", "year"])["num_laid_off"]
            .sum()
            .unstack(fill_value=0)
            .reindex(range(1, 13), fill_value=0)
        )

        result = [
            {
                "month_num": month_num,
                "month_label": month_labels[month_num - 1],
                "layoffs_2025": int(pivot.loc[month_num].get(2025, 0)),
                "layoffs_2026": int(pivot.loc[month_num].get(2026, 0)),
            }
            for month_num in range(1, 13)
        ]
        logger.info("   📊 Monthly comparison: 12 aligned months.")
        return result

    def _aggregate_stage_size_heatmap(self) -> dict:
        """Build a stage × layoff-size matrix using event counts."""
        df = self.df.copy()
        df["stage_group"] = df["stage"].apply(self._normalize_stage_group)
        df["size_bucket"] = pd.cut(
            df["num_laid_off"],
            bins=[0, 99, 499, 999, 4999, float("inf")],
            labels=["<100", "100-499", "500-999", "1k-4.9k", "5k+"],
            include_lowest=True,
        ).astype(str)

        stage_order = [
            "Post-IPO",
            "Series D+",
            "Series A-C",
            "Seed / Early",
            "Acquired / PE",
            "Unknown",
            "Other",
        ]
        size_order = ["<100", "100-499", "500-999", "1k-4.9k", "5k+"]

        grouped = (
            df.groupby(["stage_group", "size_bucket"])
            .size()
            .reindex(
                pd.MultiIndex.from_product([stage_order, size_order]),
                fill_value=0,
            )
        )

        cells = [
            {
                "stage": stage,
                "size_bucket": size_bucket,
                "event_count": int(grouped.loc[(stage, size_bucket)]),
            }
            for stage in stage_order
            for size_bucket in size_order
        ]

        logger.info("   📊 Stage heatmap: stage × layoff-size buckets.")
        return {
            "stages": stage_order,
            "size_buckets": size_order,
            "cells": cells,
        }

    def _aggregate_layoff_pct_distribution(self) -> list[dict]:
        """Bucket events by layoff percentage."""
        df = self.df.dropna(subset=["percentage_laid_off"]).copy()
        if df.empty:
            logger.info("   📊 Layoff % distribution: no percentage data available.")
            return []

        df["pct_bucket"] = pd.cut(
            df["percentage_laid_off"],
            bins=[0, 0.10, 0.25, 0.50, 1.0, float("inf")],
            labels=["<10%", "10-24%", "25-49%", "50-99%", "100%+"],
            include_lowest=True,
            right=False,
        ).astype(str)

        order = ["<10%", "10-24%", "25-49%", "50-99%", "100%+"]
        grouped = (
            df.groupby("pct_bucket")
            .size()
            .reindex(order, fill_value=0)
        )

        result = [
            {"bucket": bucket, "event_count": int(grouped.loc[bucket])}
            for bucket in order
        ]
        logger.info(f"   📊 Layoff % distribution: {len(result)} buckets.")
        return result

    def _recent_layoffs(self) -> list[dict]:
        """Return latest layoff records for homepage table."""
        recent = (
            self.df.sort_values(["date", "num_laid_off"], ascending=[False, False])
            .head(12)
        )
        result = []
        for _, row in recent.iterrows():
            percentage = row.get("percentage_laid_off")
            result.append({
                "date": str(row["date"].date()),
                "company": row["company"],
                "num_laid_off": int(row["num_laid_off"]),
                "percentage_laid_off": float(percentage) if pd.notna(percentage) else None,
                "industry": row["industry"],
                "country": row["country"],
                "stage": row["stage"],
                "source": row["source"],
            })

        logger.info(f"   📊 Recent layoffs table: {len(result)} records.")
        return result

    @staticmethod
    def _normalize_stage_group(stage: str) -> str:
        """Collapse granular funding stages into chart-friendly groups."""
        normalized = (stage or "Unknown").strip()
        if normalized == "Post-IPO":
            return "Post-IPO"
        if normalized in {"Series D", "Series E", "Series F", "Series G", "Series H", "Series I", "Series J"}:
            return "Series D+"
        if normalized in {"Series A", "Series B", "Series C"}:
            return "Series A-C"
        if normalized in {"Seed", "Pre-Seed", "Angel"}:
            return "Seed / Early"
        if normalized in {"Acquired", "Private Equity"}:
            return "Acquired / PE"
        if normalized == "Unknown":
            return "Unknown"
        return "Other"

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
