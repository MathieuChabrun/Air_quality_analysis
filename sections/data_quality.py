"""Data-quality section: missingness, duplicates, validation checks, limits."""
import pandas as pd
import streamlit as st

from utils import viz
from utils.constants import PLAUSIBLE_MAX, POLLUTANTS, UNIT, YEAR_AFTER, YEAR_BEFORE, YEAR_PARTIAL
from utils.ui import headline, show_chart


def _only_validated(tables: dict) -> bool:
    cl = tables["clean"]
    ok = set(zip(cl.loc[cl["is_valid"], "pollutant"], cl.loc[cl["is_valid"], "year"], cl.loc[cl["is_valid"], "site_id"]))
    s = tables["stations"]
    return all(k in ok for k in zip(s["pollutant"], s["year"], s["site_id"]))


def _checks(tables: dict) -> pd.DataFrame:
    s, qc = tables["stations"], tables["qc"]
    rows = [
        ("One row per station, pollutant and year", int(s.duplicated(["pollutant", "year", "site_id"]).sum()) == 0),
        (f"All values between 0 and {PLAUSIBLE_MAX:g} {UNIT}", bool(s["value"].between(0, PLAUSIBLE_MAX).all())),
        ("No missing value in the analysis table", bool(s[["value", "lat", "lon", "region", "influence"]].notna().all().all())),
        ("Latitude and longitude inside the expected world range",
         bool(s["lat"].between(-90, 90).all() and s["lon"].between(-180, 180).all())),
        ("Only validated yearly means are kept (validity = 1)", _only_validated(tables)),
        ("A single unit (µg/m³) after cleaning", bool(tables["clean"]["unit"].nunique() == 1)),
        (f"Both years present for the 3 pollutants", bool(set(s["year"]) == {YEAR_BEFORE, YEAR_AFTER}
                                                         and s["pollutant"].nunique() == 3)),
    ]
    return pd.DataFrame(rows, columns=["Check", "Result"]).assign(Result=lambda d: d["Result"].map({True: "Pass", False: "To review"}))


def render(tables: dict) -> None:
    qc, partial, outliers = tables["qc"], tables["partial"], tables["outliers"]
    st.header("4. Can we trust the data?")
    main = qc[qc["year"].isin([YEAR_BEFORE, YEAR_AFTER])]
    kept = main["usable_stations"].sum() / main["rows"].sum() * 100
    headline(f"We keep {kept:.0f}% of the station rows: only validated yearly means are used, "
             "and the incomplete year 2026 is left out.")

    c1, c2 = st.columns(2)
    with c1:
        show_chart(viz.qc_bar(qc), "Stacked bars showing, for each pollutant and year, how many station rows are kept (blue) "
                                   "and how many are removed (orange).")
    with c2:
        show_chart(viz.coverage_bar(qc), "Grouped bars of the average share of the year measured, by pollutant. "
                                          f"{YEAR_BEFORE} and {YEAR_AFTER} are above 90%; {YEAR_PARTIAL} is only about 67%.")

    st.subheader("Validation checks")
    st.dataframe(_checks(tables), hide_index=True)

    st.subheader("Missing values, duplicates and rejected rows")
    t = qc.copy()
    t["Pollutant"] = t["pollutant"].map(lambda p: POLLUTANTS[p]["short"])
    t = t.rename(columns={
        "year": "Year", "rows": "Rows", "stations": "Stations", "missing_value": "Missing values",
        "duplicate_rows": "Duplicate rows", "implausible": f"Values > {PLAUSIBLE_MAX:g}",
        "not_validated": "Not validated", "usable_stations": "Usable", "mean_time_coverage": "Mean coverage (%)",
    })
    t["Mean coverage (%)"] = t["Mean coverage (%)"].round(0).astype(int)
    st.dataframe(t[["Pollutant", "Year", "Rows", "Missing values", "Duplicate rows", f"Values > {PLAUSIBLE_MAX:g}",
                    "Not validated", "Usable", "Mean coverage (%)"]], hide_index=True)

    with st.expander("Why not use 2026? And what was the extreme value?"):
        share_nv = (partial["is_valid"] == False).mean() * 100  # noqa: E712
        st.markdown(
            f"- **{YEAR_PARTIAL} is incomplete.** The files cover about {qc[qc.year == YEAR_PARTIAL]['mean_time_coverage'].mean():.0f}% of the year "
            f"and {share_nv:.0f}% of the rows are not validated yet. Winter months are missing, so a comparison with a full year "
            "would be unfair. This is why we compare 2015 with 2025.\n"
            "- **Sensor error.** In the 2015 PM₂.₅ file, one station reports a yearly mean of more than 3,000 µg/m³. "
            "It is not validated, and it is removed by the validity filter."
        )
        if len(outliers):
            show = outliers.rename(columns={"pollutant": "Pollutant", "year": "Year", "site_name": "Station", "region": "Region",
                                            "value": f"Value ({UNIT})", "time_coverage": "Coverage (%)", "validity": "Validity"})
            st.dataframe(show.round(1), hide_index=True)

    st.subheader("Limits of this analysis")
    st.markdown(
        f"""
- **Different stations.** The network changed between {YEAR_BEFORE} and {YEAR_AFTER}. We compare *the same stations* for changes, and *all validated stations* for rankings and shares.
- **Stations are not people.** A station measures one place, not the exposure of residents. Traffic stations are placed near roads on purpose.
- **Two years only.** We do not see year-to-year changes, and weather (wind, rain, heat) can move a single year up or down.
- **No cause and effect.** We do not prove *why* the air improved (cleaner vehicles, rules, industry changes, weather).
- **Few PM₂.₅ stations in {YEAR_BEFORE}.** The network was smaller, so PM₂.₅ comparisons rely on fewer stations.
- **Privacy.** The data are about places, not about people. No personal data is used.
"""
    )
