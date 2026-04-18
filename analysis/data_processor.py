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
  - industry_pages.json → Topic-page datasets by industry
  - country_pages.json → Topic-page datasets by country/region
  - reports/*/*.json → Daily, weekly, monthly, and quarterly report datasets
"""

import json
import logging
import re
from datetime import datetime
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
            "industry_pages": self._build_topic_pages("industry", min_events=3, min_layoffs=500),
            "country_pages": self._build_topic_pages("country", min_events=3, min_layoffs=500),
            "stats": self._compute_stats(),
        }

        # Save each result to JSON
        for name, data in results.items():
            output_path = self.output_dir / f"{name}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"   💾 Saved: {output_path}")

        self._write_period_reports()

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

        # Keep all date-valid records for the recent table (num_laid_off may be missing)
        self.df_all = df.reset_index(drop=True)

        # Drop rows without layoff counts for aggregation
        df = df.dropna(subset=["num_laid_off"])
        df["num_laid_off"] = df["num_laid_off"].astype(int)

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
        """Return latest layoff records for homepage table.

        Uses df_all (includes entries without layoff counts) so that the most
        recently reported companies appear even before layoffs.fyi fills in the
        exact headcount.
        """
        recent = (
            self.df_all.sort_values("date", ascending=False)
            .head(12)
        )
        result = []
        for _, row in recent.iterrows():
            percentage = row.get("percentage_laid_off")
            num = row.get("num_laid_off")
            result.append({
                "date": str(row["date"].date()),
                "company": row["company"],
                "num_laid_off": int(num) if pd.notna(num) else None,
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

    def _build_topic_pages(
        self,
        dimension: str,
        min_events: int,
        min_layoffs: int,
    ) -> list[dict]:
        """Build SEO topic-page datasets for industries or countries."""
        pages = []
        all_values = sorted(
            value for value in self.df_all[dimension].dropna().unique()
            if str(value).strip() not in {"", "Unknown", "Other"}
        )

        for value in all_values:
            all_subset = self.df_all[self.df_all[dimension] == value].copy()
            count_subset = self.df[self.df[dimension] == value].copy()
            total_laid_off = int(count_subset["num_laid_off"].sum()) if not count_subset.empty else 0
            event_count = int(len(all_subset))
            if event_count < min_events and total_laid_off < min_layoffs:
                continue

            monthly = (
                count_subset.groupby("year_month")["num_laid_off"]
                .sum()
                .sort_index()
            )
            company_top = (
                count_subset.groupby("company")["num_laid_off"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )

            recent_events = []
            for _, row in all_subset.sort_values("date", ascending=False).head(15).iterrows():
                num = row.get("num_laid_off")
                pct = row.get("percentage_laid_off")
                recent_events.append({
                    "date": str(row["date"].date()),
                    "company": row["company"],
                    "num_laid_off": int(num) if pd.notna(num) else None,
                    "percentage_laid_off": float(pct) if pd.notna(pct) else None,
                    "industry": row["industry"],
                    "country": row["country"],
                    "stage": row["stage"],
                    "source": row["source"],
                })

            slug = self._slugify(value)
            path_prefix = "industries" if dimension == "industry" else "countries"
            title_prefix = "Industry" if dimension == "industry" else "Country"
            start_date = str(all_subset["date"].min().date())
            end_date = str(all_subset["date"].max().date())
            pages.append({
                "type": dimension,
                "name": str(value),
                "slug": slug,
                "title": f"Tech Layoffs by {title_prefix}: {value}",
                "canonical_url": f"/{path_prefix}/{slug}.html",
                "date_range": {
                    "start": start_date,
                    "end": end_date,
                },
                "kpis": {
                    "total_laid_off": total_laid_off,
                    "event_count": event_count,
                    "headcount_event_count": int(len(count_subset)),
                    "company_count": int(all_subset["company"].nunique()),
                    "country_count": int(all_subset["country"].nunique()),
                    "industry_count": int(all_subset["industry"].nunique()),
                    "high_intensity_event_count": int(
                        (all_subset["percentage_laid_off"] >= 0.25).fillna(False).sum()
                    ),
                },
                "charts": {
                    "monthly_trend": [
                        {"month": str(month), "total_laid_off": int(count)}
                        for month, count in monthly.items()
                    ],
                    "company_top": [
                        {"company": str(company), "total_laid_off": int(count)}
                        for company, count in company_top.items()
                    ],
                },
                "tables": {
                    "recent_events": recent_events,
                },
                "summary": (
                    f"{value} has {total_laid_off:,} reported tech layoffs across "
                    f"{event_count:,} public events from {start_date} to {end_date}."
                ),
            })

        pages.sort(key=lambda row: row["kpis"]["total_laid_off"], reverse=True)
        logger.info(f"   📄 {dimension.title()} topic pages: {len(pages)} candidates.")
        return pages

    @staticmethod
    def _slugify(value: str) -> str:
        """Convert a category label into a stable URL slug."""
        slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
        return slug or "unknown"

    def _write_period_reports(self) -> None:
        """Generate daily, weekly, monthly, and quarterly report JSON files."""
        reports_root = self.output_dir / "reports"
        manifests = []
        total_reports = 0

        specs = [
            ("daily", "day", "D", "daily"),
            ("weekly", "iso_week", "W-MON", "weekly"),
            ("monthly", "year_month", "M", "monthly"),
            ("quarterly", "year_quarter", "Q", "quarterly"),
            ("yearly", "year", "Y", "yearly"),
        ]

        df_all = self.df_all.copy()
        df_all["day"] = df_all["date"].dt.strftime("%Y-%m-%d")
        iso = df_all["date"].dt.isocalendar()
        df_all["iso_week"] = (
            iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
        )
        df_all["year_quarter"] = (
            df_all["date"].dt.year.astype(str) + "-Q" + df_all["date"].dt.quarter.astype(str)
        )
        df_all["year"] = df_all["year"].astype(str)

        df_counts = self.df.copy()
        df_counts["day"] = df_counts["date"].dt.strftime("%Y-%m-%d")
        iso_counts = df_counts["date"].dt.isocalendar()
        df_counts["iso_week"] = (
            iso_counts["year"].astype(str)
            + "-W"
            + iso_counts["week"].astype(str).str.zfill(2)
        )
        df_counts["year_quarter"] = (
            df_counts["date"].dt.year.astype(str)
            + "-Q"
            + df_counts["date"].dt.quarter.astype(str)
        )
        df_counts["year"] = df_counts["year"].astype(str)
        self._report_df_all = df_all
        self._report_df_counts = df_counts

        latest_data_date = self.df_all["date"].max().date()

        for report_type, period_col, freq, dirname in specs:
            out_dir = reports_root / dirname
            out_dir.mkdir(parents=True, exist_ok=True)
            period_values = sorted(df_all[period_col].dropna().unique())
            reports = []

            for period in period_values:
                period_all = df_all[df_all[period_col] == period].copy()
                period_counts = df_counts[df_counts[period_col] == period].copy()
                if period_all.empty:
                    continue

                report = self._build_period_report(
                    report_type=report_type,
                    period=str(period),
                    period_all=period_all,
                    period_counts=period_counts,
                    latest_data_date=latest_data_date,
                    freq=freq,
                )

                output_path = out_dir / f"{period}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2, default=str)

                reports.append({
                    "report_type": report_type,
                    "period": str(period),
                    "status": report["status"],
                    "date_range": report["date_range"],
                    "path": f"reports/{dirname}/{period}.json",
                    "canonical_url": report["canonical_url"],
                    "total_laid_off": report["kpis"]["total_laid_off"],
                    "event_count": report["kpis"]["event_count"],
                })
                total_reports += 1

            manifests.append({
                "report_type": report_type,
                "count": len(reports),
                "reports": reports,
            })

        index = {
            "updated_at": str(latest_data_date),
            "date_range": {
                "start": str(self.df_all["date"].min().date()),
                "end": str(latest_data_date),
            },
            "report_groups": manifests,
        }
        index_path = reports_root / "index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"   🗂 Period reports: {total_reports} JSON files saved under {reports_root}")

    def _build_period_report(
        self,
        report_type: str,
        period: str,
        period_all: pd.DataFrame,
        period_counts: pd.DataFrame,
        latest_data_date,
        freq: str,
    ) -> dict:
        """Build one normalized period report payload."""
        start_date = period_all["date"].min().date()
        end_date = period_all["date"].max().date()
        period_end = self._period_end_date(period_all["date"].min(), freq)
        status = "rolling" if report_type != "daily" and latest_data_date <= period_end else "final"
        canonical_url = self._period_canonical_url(report_type, period)

        kpis = self._period_kpis(period_all, period_counts)
        charts = {
            "company_top": self._top_dimension(period_counts, "company", "company", 10),
            "industry_top": self._top_dimension(period_counts, "industry", "industry", 10),
            "country_top": self._top_dimension(period_counts, "country", "country", 10),
            "stage_top": self._top_dimension(period_counts, "stage", "stage", 10),
            "layoff_pct_distribution": self._period_layoff_pct_distribution(period_counts),
        }
        tables = {
            "largest_events": self._period_events(period_counts, sort_by="num_laid_off", limit=10),
            "recent_events": self._period_events(period_all, sort_by="date", limit=20),
            "high_intensity_events": self._high_intensity_events(period_all, limit=10),
        }

        return {
            "report_type": report_type,
            "period": period,
            "status": status,
            "date_range": {
                "start": str(start_date),
                "end": str(end_date),
            },
            "updated_at": str(latest_data_date),
            "canonical_url": canonical_url,
            "kpis": kpis,
            "comparisons": {
                "previous_period": self._period_comparison(report_type, period, mode="previous"),
                "same_period_last_year": self._period_comparison(report_type, period, mode="year_ago"),
            },
            "charts": charts,
            "tables": tables,
            "insights": self._period_insights(report_type, period, kpis, charts),
            "methodology_notes": [
                "Rows with invalid dates are excluded from period reports.",
                "Rows without num_laid_off count as events but are excluded from headcount totals.",
                "Layoff percentage, funding stage, and funds raised fields are incomplete in source data.",
            ],
        }

    def _period_kpis(self, period_all: pd.DataFrame, period_counts: pd.DataFrame) -> dict:
        """Compute normalized KPI values for a period."""
        total = int(period_counts["num_laid_off"].sum()) if not period_counts.empty else 0
        count_events = len(period_counts)
        return {
            "total_laid_off": total,
            "event_count": int(len(period_all)),
            "headcount_event_count": int(count_events),
            "company_count": int(period_all["company"].nunique()),
            "country_count": int(period_all["country"].nunique()),
            "industry_count": int(period_all["industry"].nunique()),
            "average_layoffs_per_headcount_event": round(total / count_events, 2) if count_events else None,
            "median_layoffs_per_headcount_event": (
                float(period_counts["num_laid_off"].median()) if count_events else None
            ),
            "high_intensity_event_count": int(
                (period_all["percentage_laid_off"] >= 0.25).fillna(False).sum()
            ),
        }

    def _top_dimension(
        self,
        df: pd.DataFrame,
        source_col: str,
        output_col: str,
        limit: int,
    ) -> list[dict]:
        """Aggregate period headcount by one categorical dimension."""
        if df.empty:
            return []
        grouped = (
            df.groupby(source_col)["num_laid_off"]
            .sum()
            .sort_values(ascending=False)
            .head(limit)
        )
        return [
            {
                output_col: str(name),
                "total_laid_off": int(value),
            }
            for name, value in grouped.items()
        ]

    def _period_layoff_pct_distribution(self, df: pd.DataFrame) -> list[dict]:
        """Build layoff percentage buckets for one period."""
        df = df.dropna(subset=["percentage_laid_off"]).copy()
        order = ["<10%", "10-24%", "25-49%", "50-99%", "100%+"]
        if df.empty:
            return [{"bucket": bucket, "event_count": 0} for bucket in order]

        df["pct_bucket"] = pd.cut(
            df["percentage_laid_off"],
            bins=[0, 0.10, 0.25, 0.50, 1.0, float("inf")],
            labels=order,
            include_lowest=True,
            right=False,
        ).astype(str)
        grouped = df.groupby("pct_bucket").size().reindex(order, fill_value=0)
        return [
            {"bucket": bucket, "event_count": int(grouped.loc[bucket])}
            for bucket in order
        ]

    def _period_events(self, df: pd.DataFrame, sort_by: str, limit: int) -> list[dict]:
        """Serialize period event rows for report tables."""
        if df.empty:
            return []
        sorted_df = df.sort_values(sort_by, ascending=False).head(limit)
        result = []
        for _, row in sorted_df.iterrows():
            num = row.get("num_laid_off")
            pct = row.get("percentage_laid_off")
            result.append({
                "date": str(row["date"].date()),
                "company": row["company"],
                "num_laid_off": int(num) if pd.notna(num) else None,
                "percentage_laid_off": float(pct) if pd.notna(pct) else None,
                "industry": row["industry"],
                "country": row["country"],
                "stage": row["stage"],
                "source": row["source"],
            })
        return result

    def _high_intensity_events(self, df: pd.DataFrame, limit: int) -> list[dict]:
        """Return events where layoff percentage is 25% or higher."""
        high = df[df["percentage_laid_off"] >= 0.25].copy()
        if high.empty:
            return []
        return self._period_events(high, sort_by="percentage_laid_off", limit=limit)

    def _period_insights(
        self,
        report_type: str,
        period: str,
        kpis: dict,
        charts: dict,
    ) -> list[str]:
        """Generate conservative, data-backed period insight strings."""
        insights = []
        if kpis["event_count"] == 0:
            return [f"No public layoff events were found for {period}."]

        insights.append(
            f"{period} includes {kpis['event_count']} public layoff events and "
            f"{format(kpis['total_laid_off'], ',')} reported layoffs."
        )

        top_company = charts["company_top"][0] if charts["company_top"] else None
        if top_company:
            insights.append(
                f"The largest company contributor is {top_company['company']} with "
                f"{format(top_company['total_laid_off'], ',')} reported layoffs."
            )

        top_industry = self._first_named_report_item(charts["industry_top"], "industry")
        if top_industry:
            insights.append(
                f"The leading named industry is {top_industry['industry']} with "
                f"{format(top_industry['total_laid_off'], ',')} reported layoffs."
            )

        if kpis["high_intensity_event_count"]:
            insights.append(
                f"{kpis['high_intensity_event_count']} events report a layoff percentage of 25% or higher."
            )

        return insights

    @staticmethod
    def _first_named_report_item(items: list[dict], key: str) -> dict | None:
        """Pick the first non-generic category from a report ranking."""
        for item in items:
            name = str(item.get(key, "")).strip()
            if name not in {"Other", "Unknown", ""}:
                return item
        return items[0] if items else None

    def _period_comparison(self, report_type: str, period: str, mode: str) -> dict:
        """Compute period-over-period or year-over-year comparison metrics."""
        target_period = self._comparison_period(report_type, period, mode)
        period_col = {
            "daily": "day",
            "weekly": "iso_week",
            "monthly": "year_month",
            "quarterly": "year_quarter",
            "yearly": "year",
        }[report_type]

        target_all = self._report_df_all[self._report_df_all[period_col] == target_period]
        target_counts = self._report_df_counts[self._report_df_counts[period_col] == target_period]
        current_all = self._report_df_all[self._report_df_all[period_col] == period]
        current_counts = self._report_df_counts[self._report_df_counts[period_col] == period]

        if target_all.empty:
            return {
                "period": target_period,
                "total_laid_off": None,
                "event_count": None,
                "total_laid_off_delta": None,
                "total_laid_off_pct_change": None,
                "event_count_delta": None,
                "event_count_pct_change": None,
                "note": "No comparison data is available for this period.",
            }

        current_total = int(current_counts["num_laid_off"].sum()) if not current_counts.empty else 0
        target_total = int(target_counts["num_laid_off"].sum()) if not target_counts.empty else 0
        current_events = int(len(current_all))
        target_events = int(len(target_all))

        return {
            "period": target_period,
            "total_laid_off": target_total,
            "event_count": target_events,
            "total_laid_off_delta": current_total - target_total,
            "total_laid_off_pct_change": self._pct_change(current_total, target_total),
            "event_count_delta": current_events - target_events,
            "event_count_pct_change": self._pct_change(current_events, target_events),
            "note": None,
        }

    @staticmethod
    def _comparison_period(report_type: str, period: str, mode: str) -> str:
        """Return the period key used for previous or year-ago comparison."""
        if report_type == "daily":
            dt = pd.Timestamp(period)
            delta = pd.DateOffset(days=1) if mode == "previous" else pd.DateOffset(years=1)
            return str((dt - delta).date())

        if report_type == "weekly":
            start = pd.Timestamp(datetime.strptime(f"{period}-1", "%G-W%V-%u"))
            delta = pd.DateOffset(weeks=1) if mode == "previous" else pd.DateOffset(weeks=52)
            target = start - delta
            iso = target.isocalendar()
            return f"{iso.year}-W{iso.week:02d}"

        if report_type == "monthly":
            offset = 1 if mode == "previous" else 12
            return str(pd.Period(period, freq="M") - offset)

        if report_type == "quarterly":
            offset = 1 if mode == "previous" else 4
            target = pd.Period(period.replace("-Q", "Q"), freq="Q") - offset
            return f"{target.year}-Q{target.quarter}"

        if report_type == "yearly":
            return str(int(period) - 1)

        return period

    @staticmethod
    def _pct_change(current: int | float, previous: int | float) -> float | None:
        """Return percentage change, with None when the baseline is zero."""
        if not previous:
            return None
        return round((current - previous) / previous, 4)

    @staticmethod
    def _period_end_date(start_ts: pd.Timestamp, freq: str):
        """Return the natural period end date for status classification."""
        if freq == "D":
            return start_ts.date()
        if freq == "W-MON":
            return (start_ts + pd.offsets.Week(weekday=6)).date()
        if freq == "M":
            return (start_ts + pd.offsets.MonthEnd(0)).date()
        if freq == "Q":
            return (start_ts + pd.offsets.QuarterEnd(0)).date()
        if freq == "Y":
            return (start_ts + pd.offsets.YearEnd(0)).date()
        return start_ts.date()

    @staticmethod
    def _period_canonical_url(report_type: str, period: str) -> str:
        """Build the future static HTML URL for a period report."""
        paths = {
            "daily": "daily",
            "weekly": "weekly",
            "monthly": "monthly",
            "quarterly": "quarterly",
            "yearly": "yearly",
        }
        return f"/reports/{paths[report_type]}/{period}.html"
