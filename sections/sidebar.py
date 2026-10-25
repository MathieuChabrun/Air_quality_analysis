"""Sidebar controls. Returns a context dict used by every section."""
from __future__ import annotations

import streamlit as st

from utils.constants import POLLUTANTS, REFERENCES, YEAR_AFTER, YEAR_BEFORE
from utils.prep import apply_filters


def render_sidebar(tables: dict) -> dict:
    stations, paired = tables["stations"], tables["paired"]
    with st.sidebar:
        st.header("Filters")
        pol = st.selectbox(
            "Pollutant", list(POLLUTANTS), format_func=lambda k: POLLUTANTS[k]["label"],
            help="Pollutant shown in the main charts. Some charts compare all three.",
        )
        ref_label = st.radio(
            "Reference level", list(REFERENCES), index=1,
            help="Dashed line in the charts and threshold used for the KPIs. "
                 "WHO = health guideline. EU = legal limit.",
        )
        influence = st.multiselect(
            "Station type", sorted(stations["influence"].unique()), default=sorted(stations["influence"].unique()),
            help="Background = away from direct sources. Traffic = near busy roads. Industrial = near factories.",
        )
        areas = sorted(stations["area_type"].unique())
        area_type = st.multiselect("Area type", areas, default=areas)
        regions = sorted(stations["region"].unique())
        region = st.multiselect("Region", regions, default=regions,
                                help="Region of the air-quality association that runs the station.")
        st.caption(f"Compared years: {YEAR_BEFORE} → {YEAR_AFTER}. "
                   "Only validated yearly means are used.")

    ref_key = REFERENCES[ref_label]
    st_f = apply_filters(stations, influence, area_type, region)
    pa_f = apply_filters(paired, influence, area_type, region)
    ctx = dict(
        pol=pol, ref_label=ref_label, ref_key=ref_key, ref=POLLUTANTS[pol][ref_key],
        stations_all=st_f, paired_all=pa_f,
        paired=pa_f[pa_f["pollutant"] == pol],
        st_before=st_f[(st_f["pollutant"] == pol) & (st_f["year"] == YEAR_BEFORE)],
        st_after=st_f[(st_f["pollutant"] == pol) & (st_f["year"] == YEAR_AFTER)],
        filters=dict(influence=influence, area_type=area_type, region=region),
    )
    return ctx
