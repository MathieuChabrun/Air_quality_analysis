"""Project-wide constants: one place to change years, thresholds and labels."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"

# --- Years -----------------------------------------------------------------
YEAR_BEFORE = 2015
YEAR_AFTER = 2025
YEAR_PARTIAL = 2026  # only used in the data-quality section (incomplete year)
YEARS_USED = (YEAR_BEFORE, YEAR_AFTER)

UNIT = "µg/m³"
PLAUSIBLE_MAX = 500.0  # values above this are treated as sensor errors
MIN_STATIONS_PER_GROUP = 3  # smaller groups are not shown in region charts

# --- Pollutants and reference levels (annual mean, µg/m³) -------------------
# WHO 2021 guidelines; EU limit until 2029 (Directive 2008/50/EC);
# EU limit from 1 Jan 2030 (Directive (EU) 2024/2881).
POLLUTANTS = {
    "NO2": dict(
        label="Nitrogen dioxide (NO₂)", short="NO₂", file_key="NO2",
        who=10, eu_2030=20, eu_current=40,
        source="Mostly road traffic and combustion engines.",
        health="Irritates the airways and can worsen asthma.",
    ),
    "PM10": dict(
        label="Particles under 10 µm (PM₁₀)", short="PM₁₀", file_key="PM10",
        who=15, eu_2030=20, eu_current=40,
        source="Road traffic, heating, industry, agriculture, dust.",
        health="Enters the lungs and affects breathing.",
    ),
    "PM2.5": dict(
        label="Fine particles under 2.5 µm (PM₂.₅)", short="PM₂.₅", file_key="PM25",
        who=5, eu_2030=10, eu_current=25,
        source="Wood heating, road traffic, industry.",
        health="Reaches the blood stream; linked to heart and lung disease.",
    ),
}

# Reference level the user can choose in the sidebar -> key in POLLUTANTS
REFERENCES = {
    "WHO 2021 guideline": "who",
    "EU limit from 2030": "eu_2030",
    "EU limit until 2029": "eu_current",
}

# --- Label translations (French source -> English UI) ----------------------
INFLUENCE_EN = {"Fond": "Background", "Trafic": "Traffic", "Industrielle": "Industrial"}
AREA_EN = {
    "Urbaine": "Urban",
    "Périurbaine": "Suburban",
    "Rurale près des villes": "Rural (near city)",
    "Rurale régionale": "Rural (regional)",
    "Rurale nationale": "Rural (remote)",
}
# AASQA (air quality association) -> region name
REGION_MAP = {
    "AIR BREIZH": "Brittany",
    "AIR PAYS DE LA LOIRE": "Pays de la Loire",
    "AIRPARIF": "Île-de-France",
    "ATMO AUVERGNE-RHÔNE-ALPES": "Auvergne-Rhône-Alpes",
    "ATMO BOURGOGNE-FRANCHE-COMTE": "Bourgogne-Franche-Comté",
    "ATMO GRAND EST": "Grand Est",
    "ATMO GUYANE": "French Guiana",
    "ATMO HAUTS DE FRANCE": "Hauts-de-France",
    "ATMO NORMANDIE": "Normandy",
    "ATMO NOUVELLE-AQUITAINE": "Nouvelle-Aquitaine",
    "ATMO OCCITANIE": "Occitanie",
    "ATMO REUNION": "Réunion",
    "ATMO SUD": "Provence-Alpes-Côte d'Azur",
    "GWAD'AIR": "Guadeloupe",
    "HAWA MAYOTTE": "Mayotte",
    "LIG'AIR": "Centre-Val de Loire",
    "MADININAIR": "Martinique",
    "QUALITAIR CORSE": "Corsica",
}

# Mainland France bounding box (used for the maps)
MAINLAND = dict(lat_min=41.0, lat_max=51.5, lon_min=-5.5, lon_max=10.0)
MAP_CENTER = dict(lat=46.6, lon=2.4)

# --- Colour-blind safe palette (Okabe-Ito) ----------------------------------
C_BEFORE = "#E69F00"   # orange
C_AFTER = "#0072B2"    # blue
C_GOOD = "#009E73"     # green
C_WARN = "#D55E00"     # vermillion
C_NEUTRAL = "#595959"
INFLUENCE_COLORS = {"Background": "#0072B2", "Traffic": "#D55E00", "Industrial": "#009E73"}
LEVEL_COLORS = ["#009E73", "#56B4E9", "#E69F00", "#D55E00"]
