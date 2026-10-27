# Is the air in France getting cleaner? (2015 vs 2025)

Individual student project — Data Storytelling Dashboard with Streamlit (EFREI, group BIA).
Author: Mathieu CHABRUN · mathieu.chabrun@efrei.net

A Streamlit app that tells one story: **between 2015 and 2025, air pollution (NO₂, PM₁₀, PM₂.₅) fell
almost everywhere in France, but traffic stations are still the highest, and many stations are
above the WHO guidelines.**

## Story (hook → context → insights → implications)

| Step | Section in the app | Question answered |
|---|---|---|
| Hook + context | Intro | Why does air quality matter? Who is this for? |
| Before / after | 1. The big picture (KPIs, box plot, scatter, maps) | How much did the air change on the same stations? |
| Comparison | 2. Where did the air improve? (regions, station types) | Where did it change most? |
| Ranking | 3. Who is still above the limits? (top/bottom N, regions, histogram) | Which stations and regions are the worst? |
| Trust | 4. Can we trust the data? | What was cleaned? What are the limits? |
| Implications | 5. What does it mean? (share above limits, what-if scenario) | What happens by 2030 if progress continues? |

**Audience:** citizens and local decision-makers.

## Liens du projet

- Application déployée : https://airqualityanalysis-dgxqobcxzqtrqxgp5la8bb.streamlit.app/
- Repository GitHub : https://github.com/MathieuChabrun/Air_quality_analysis

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

or `make install && make run`. Tests: `make test` (smoke test of the app for every pollutant × reference level).

Python 3.11+ is needed (pandas 3). The app was tested with Python 3.12 and Streamlit 1.66 (the project needs Streamlit ≥ 1.33).

## Data

- **Source:** Geod'air (LCSQA / Ineris) — national air-quality database fed by the 18 AASQA.
  Dataset page: <https://www.data.gouv.fr/datasets/5b98b648634f415309d52a50> (portal: data.gouv.fr).
- **License:** Licence Ouverte / Open Licence 2.0 (Etalab) — reuse is free, source must be cited.
- **Files (in `data/raw/`):** annual means per station, one CSV per pollutant and year, exported from Geod'air
  (statistic “Moy. annuelle”, all stations). Names: `NO2_2015.csv`, `PM10_2015.csv`, `PM25_2015.csv`, same for 2025.
  The `*_2026.csv` files are **only** used in the data-quality section to show why an incomplete year is excluded.
- The files are small (< 130 KB each), so they are included in the repository. To refresh or extend them, export the
  same statistic again from <https://www.geodair.fr/> and keep the file naming and the `;` separator.
- **Main columns:** station id/name, region (AASQA), station type (background / traffic / industrial),
  area type (urban, suburban, rural), pollutant, annual mean (`valeur brute`, µg/m³), time coverage, validity
  (1 = validated), latitude, longitude.

## Method (short)

1. **Clean** (`utils/prep.py`): rename columns, unify units (`µg-m3` / `µg/m3` → µg/m³), translate labels to English,
   map each AASQA to its region, flag mainland stations for the maps.
2. **Validate**: keep one row per station-pollutant-year; keep only `validity = 1`; remove values above 500 µg/m³
   (sensor errors, e.g. one PM₂.₅ value of ~3,600 µg/m³ in 2015, already rejected by the validity flag).
3. **Pair stations**: the **before/after** comparison uses stations validated in **both** years
   (NO₂ 243, PM₁₀ 208, PM₂.₅ 87). **Rankings and “share above limit”** use all validated stations of the year.
4. **Reference levels** (annual mean, µg/m³): WHO 2021 (NO₂ 10, PM₁₀ 15, PM₂.₅ 5); EU limit from 2030, Directive (EU) 2024/2881
   (NO₂ 20, PM₁₀ 20, PM₂.₅ 10); EU limit until 2029, Directive 2008/50/EC (NO₂ 40, PM₁₀ 40, PM₂.₅ 25).
5. **What-if scenario**: for each station, continuous yearly rate `r = ln(after / before) / 10`; projection
   `value(t) = after × exp(r × pace × (t − 2025))`. A scenario with two data points, **not a forecast**.
6. **Why 2015 vs 2025 (not 2026)?** The 2026 files are incomplete (~67 % of the year) and not validated.

## Project structure

```
app.py                 # entry point: layout, sidebar, section order
sections/              # one file per story section (+ sidebar)
  intro.py  overview.py  deep_dives.py  data_quality.py  conclusions.py  sidebar.py
utils/
  constants.py         # years, thresholds, labels, palette (single source of truth)
  io.py                # file reading, source and license text
  prep.py              # cleaning, validation, pairing, KPIs, projection
  viz.py               # all charts (shared style, labelled axes and units)
  ui.py                # helpers: chart + text description, headline
data/raw/              # input CSV files
tests/test_app.py      # smoke tests
.streamlit/config.toml # theme
```

## Requirements checklist (from the project brief)

| Requirement | Where |
|---|---|
| Sidebar controls (pollutant, reference level, station type, area, region) | `sections/sidebar.py` |
| ≥ 3 interactive visuals with hover | box plot, scatter, 3 maps, dumbbell, small multiples, rankings, histogram, what-if chart |
| Map | `viz.change_map`, `viz.level_map` (tabs in section 1) |
| KPIs tied to filters | `overview.render_kpis` |
| Data-quality section | `sections/data_quality.py` (missingness, duplicates, checks, coverage, outlier) |
| Caching / performance | `@st.cache_data` in `app.py`; small pre-cleaned tables, filters are cheap pandas masks |
| Accessibility | colour-blind-safe palette (Okabe-Ito), labelled axes with units, a visible text description under every chart (also passed as `alt` text when Streamlit supports it), help tooltips |
| Reproducibility | pinned `requirements.txt`, data in repo, tests, no random sampling (so no seed needed) |

> Note: there is no date-range control on purpose. The story compares two fixed years, and a date slider would not change the story.

## Limitations and ethics

- Different station networks in 2015 and 2025: before/after uses only common stations.
- A station is a place, not the exposure of residents; traffic stations are sited near roads on purpose.
- Two years only: weather can move a single year up or down. No causal claim.
- PM₂.₅ has fewer common stations (87).
- No personal data is used; all values are measured at fixed stations.

## Deploy (Streamlit Community Cloud)

Push the folder to a public GitHub repository, then create an app on <https://share.streamlit.io> with `app.py`
as the main file. The `requirements.txt` is read automatically.

## Credits

Data: LCSQA / Ineris (Geod'air), AASQA network, via data.gouv.fr — Open Licence 2.0.
Reference levels: WHO Air Quality Guidelines 2021; Directive 2008/50/EC; Directive (EU) 2024/2881.
