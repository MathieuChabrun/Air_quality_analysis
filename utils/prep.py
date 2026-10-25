"""Cleaning, validation and feature engineering (pure pandas, no Streamlit)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import (
    AREA_EN, INFLUENCE_EN, MAINLAND, PLAUSIBLE_MAX, POLLUTANTS, REGION_MAP,
    UNIT, YEAR_AFTER, YEAR_BEFORE, YEAR_PARTIAL, YEARS_USED,
)

STATION_COLS = [
    "pollutant", "year", "site_id", "site_name", "region", "zone", "influence",
    "area_type", "method", "lat", "lon", "is_mainland", "value", "time_coverage",
]


# --------------------------------------------------------------------------
# 1. Cleaning
# --------------------------------------------------------------------------
def clean(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Standardise types, units and labels. Does not drop any row."""
    df = df_raw.copy()
    for col in ["value_rounded", "value", "capture_rate", "time_coverage", "lat", "lon"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["unit"] = UNIT  # source mixes "µg-m3" and "µg/m3"
    df["is_valid"] = df["validity"].eq("1")  # 1 = validated by the AASQA
    df["region"] = df["aasqa"].map(REGION_MAP).fillna(df["aasqa"].str.title())
    df["influence"] = df["influence"].map(INFLUENCE_EN).fillna(df["influence"])
    df["area_type"] = df["area_type"].map(AREA_EN).fillna(df["area_type"])
    df["is_mainland"] = (
        df["lat"].between(MAINLAND["lat_min"], MAINLAND["lat_max"])
        & df["lon"].between(MAINLAND["lon_min"], MAINLAND["lon_max"])
    )
    return df


def build_qc(df: pd.DataFrame) -> pd.DataFrame:
    """One row per pollutant-year with simple data-quality counters."""
    g = df.groupby(["pollutant", "year"])
    qc = g.agg(
        rows=("site_id", "size"),
        stations=("site_id", "nunique"),
        missing_value=("value", lambda s: int(s.isna().sum())),
        implausible=("value", lambda s: int((s > PLAUSIBLE_MAX).sum())),
        not_validated=("is_valid", lambda s: int((~s).sum())),
        mean_time_coverage=("time_coverage", "mean"),
        unit_variants=("unit_raw", "nunique"),
    ).reset_index()
    qc["duplicate_rows"] = qc["rows"] - qc["stations"]
    qc["usable_stations"] = [
        int(
            df[(df.pollutant == p) & (df.year == y) & df.is_valid & df.value.notna()
               & (df.value <= PLAUSIBLE_MAX)]["site_id"].nunique()
        )
        for p, y in zip(qc["pollutant"], qc["year"])
    ]
    return qc


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Keep one row per station, pollutant and year (best validated first)."""
    ordered = df.sort_values(["is_valid", "time_coverage"], ascending=[False, False])
    return ordered.drop_duplicates(["pollutant", "year", "site_id"], keep="first")


# --------------------------------------------------------------------------
# 2. Feature engineering
# --------------------------------------------------------------------------
def make_paired(stations: pd.DataFrame) -> pd.DataFrame:
    """Stations measured and validated in BOTH years (like-for-like comparison)."""
    idx = ["pollutant", "site_id"]
    b = stations[stations.year == YEAR_BEFORE].set_index(idx)
    a = stations[stations.year == YEAR_AFTER].set_index(idx)
    common = b.index.intersection(a.index)
    p = a.loc[common, ["site_name", "region", "zone", "influence", "area_type",
                       "lat", "lon", "is_mainland"]].copy()
    p["before"] = b.loc[common, "value"]
    p["after"] = a.loc[common, "value"]
    p["change"] = p["after"] - p["before"]
    p["pct_change"] = np.where(p["before"] > 0, p["change"] / p["before"] * 100, np.nan)
    both_pos = (p["before"] > 0) & (p["after"] > 0)
    years = YEAR_AFTER - YEAR_BEFORE
    # continuous yearly rate: after = before * exp(rate * years)
    p["rate"] = np.where(both_pos, np.log(p["after"] / p["before"].where(both_pos)) / years, np.nan)
    return p.reset_index()


def make_tables(df_raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build every table used by the app."""
    df = clean(df_raw)
    qc = build_qc(df)
    dedup = deduplicate(df)
    usable = dedup["is_valid"] & dedup["value"].notna() & (dedup["value"] <= PLAUSIBLE_MAX)
    stations = dedup[dedup["year"].isin(YEARS_USED) & usable][STATION_COLS].reset_index(drop=True)
    paired = make_paired(stations)
    partial = dedup[dedup["year"] == YEAR_PARTIAL][STATION_COLS + ["is_valid"]].reset_index(drop=True)
    # overview of the 5 largest removed values (shown as evidence in the app)
    outliers = (
        df[(df["value"] > PLAUSIBLE_MAX)]
        [["pollutant", "year", "site_name", "region", "value", "time_coverage", "validity"]]
        .sort_values("value", ascending=False)
    )
    return dict(qc=qc, stations=stations, paired=paired, partial=partial, outliers=outliers, clean=df)


# --------------------------------------------------------------------------
# 3. Filters and metrics
# --------------------------------------------------------------------------
def apply_filters(df: pd.DataFrame, influence, area_type, region) -> pd.DataFrame:
    mask = df["influence"].isin(influence) & df["area_type"].isin(area_type) & df["region"].isin(region)
    return df[mask]


def ref_value(pollutant: str, ref_key: str) -> float:
    return POLLUTANTS[pollutant][ref_key]


def share_above(values: pd.Series, ref: float) -> float:
    return float((values > ref).mean() * 100) if len(values) else float("nan")


def compute_kpis(paired: pd.DataFrame, st_before: pd.DataFrame, st_after: pd.DataFrame, ref: float) -> dict:
    """Numbers shown in the KPI header (all tied to the current filters)."""
    k = dict(n_pairs=len(paired), n_before=len(st_before), n_after=len(st_after))
    k["mean_before"] = paired["before"].mean() if len(paired) else np.nan
    k["mean_after"] = paired["after"].mean() if len(paired) else np.nan
    k["pct_change"] = (
        (k["mean_after"] - k["mean_before"]) / k["mean_before"] * 100 if len(paired) and k["mean_before"] > 0 else np.nan
    )
    k["share_improved"] = float((paired["change"] < 0).mean() * 100) if len(paired) else np.nan
    k["above_before"] = share_above(st_before["value"], ref)
    k["above_after"] = share_above(st_after["value"], ref)
    return k


def level_class(values: pd.Series, pollutant: str) -> pd.Series:
    """Classify concentrations against WHO / EU levels (for maps and counts)."""
    p = POLLUTANTS[pollutant]
    bins = [-np.inf, p["who"], p["eu_2030"], p["eu_current"], np.inf]
    labels = [
        f"≤ WHO guideline ({p['who']})",
        f"WHO to EU 2030 limit ({p['eu_2030']})",
        f"EU 2030 limit to today's limit ({p['eu_current']})",
        f"Above today's EU limit (> {p['eu_current']})",
    ]
    return pd.cut(values, bins=bins, labels=labels, right=True, ordered=True)


def project_share_above(paired: pd.DataFrame, ref: float, pace: float, years_ahead: int = 15) -> pd.DataFrame:
    """What-if: keep the 2015-2025 yearly rate (times `pace`) for each station.

    value(t) = after * exp(rate * pace * (t - 2025)). Needs two points per station,
    so this is a scenario, not a forecast. Stations without a valid rate are dropped.
    """
    d = paired.dropna(subset=["rate"])
    if d.empty:
        return pd.DataFrame(columns=["year", "share_above"])
    t = np.arange(0, years_ahead + 1)
    proj = d["after"].to_numpy()[:, None] * np.exp(d["rate"].to_numpy()[:, None] * pace * t[None, :])
    share = (proj > ref).mean(axis=0) * 100
    return pd.DataFrame({"year": YEAR_AFTER + t, "share_above": share, "n": len(d)})
