"""Data loading. Raw CSV files come from Geod'air (LCSQA / Ineris)."""
from __future__ import annotations

import pandas as pd

from .constants import DATA_DIR, POLLUTANTS, YEAR_BEFORE, YEAR_AFTER, YEAR_PARTIAL

SOURCE_TEXT = (
    "Source: Geod'air annual means per station (LCSQA / Ineris), data.gouv.fr "
    "dataset “Données temps réel de mesure des concentrations de polluants "
    "atmosphériques réglementés” — Licence Ouverte / Open Licence 2.0 (Etalab)."
)
LICENSE_TEXT = (
    "Data: Open Licence 2.0 (Etalab). Reuse is free if the source is cited. "
    "Code of this app: MIT-style, for academic use."
)

COLUMN_MAP = {
    "Date de début": "start",
    "Organisme": "aasqa",
    "code zas": "zone_code",
    "Zas": "zone",
    "code site": "site_id",
    "nom site": "site_name",
    "type d'implantation": "area_type",
    "Polluant": "pollutant",
    "type d'influence": "influence",
    "type d'évaluation": "method",
    "valeur": "value_rounded",
    "valeur brute": "value",
    "unité de mesure": "unit_raw",
    "taux de saisie": "capture_rate",
    "couverture temporelle": "time_coverage",
    "code qualité": "quality_code",
    "validité": "validity",
    "Latitude": "lat",
    "Longitude": "lon",
}


def csv_path(pollutant: str, year: int):
    return DATA_DIR / f"{POLLUTANTS[pollutant]['file_key']}_{year}.csv"


def read_one(pollutant: str, year: int) -> pd.DataFrame | None:
    """Read one Geod'air export. Returns None if the file does not exist."""
    path = csv_path(pollutant, year)
    if not path.exists():
        return None
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    df = df.rename(columns=COLUMN_MAP)
    keep = [c for c in COLUMN_MAP.values() if c in df.columns]
    df = df[keep].copy()
    df["year"] = df["start"].str[:4].astype(int)
    return df


def load_data() -> pd.DataFrame:
    """Load every available file (main years + the incomplete year)."""
    frames, missing = [], []
    for pol in POLLUTANTS:
        for year in (YEAR_BEFORE, YEAR_AFTER, YEAR_PARTIAL):
            df = read_one(pol, year)
            if df is None:
                if year != YEAR_PARTIAL:
                    missing.append(str(csv_path(pol, year)))
                continue
            frames.append(df)
    if missing:
        raise FileNotFoundError(
            "Missing data files. Export them from Geod'air (see README):\n"
            + "\n".join(missing)
        )
    return pd.concat(frames, ignore_index=True)
