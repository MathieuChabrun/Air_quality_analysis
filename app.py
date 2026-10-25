"""Data storytelling dashboard — air quality in France, 2015 vs 2025.

Run with:  streamlit run app.py
"""
import streamlit as st

from sections import conclusions, data_quality, deep_dives, intro, overview
from sections.sidebar import render_sidebar
from utils.io import LICENSE_TEXT, load_data
from utils.prep import make_tables

st.set_page_config(page_title="Air quality in France: 2015 vs 2025", page_icon="🌫️", layout="wide")


@st.cache_data(show_spinner="Loading and cleaning data…")
def get_data():
    return make_tables(load_data())


tables = get_data()
ctx = render_sidebar(tables)

intro.render()

if ctx["paired"].empty or ctx["st_after"].empty or ctx["st_before"].empty:
    st.warning("No station matches your filters for this pollutant. Please widen the filters in the sidebar.", icon="⚠️")
    st.stop()

kpis = overview.render_kpis(ctx)
overview.render(ctx, kpis)
deep_dives.render(ctx)
data_quality.render(tables)
conclusions.render(ctx)

st.divider()
st.caption(LICENSE_TEXT)
