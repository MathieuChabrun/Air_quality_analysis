"""Small Streamlit helpers shared by all sections."""
from __future__ import annotations

import inspect

import streamlit as st

_PARAMS = inspect.signature(st.plotly_chart).parameters


def show_chart(fig, description: str, key: str | None = None) -> None:
    """Draw a Plotly chart + a visible text alternative (accessibility)."""
    kwargs = {}
    if "width" in _PARAMS:  # recent Streamlit
        kwargs["width"] = "stretch"
    else:  # Streamlit < 1.50
        kwargs["use_container_width"] = True
    if "alt" in _PARAMS:
        kwargs["alt"] = description
    if key:
        kwargs["key"] = key
    st.plotly_chart(fig, **kwargs)
    st.caption(f"Chart description: {description}")


def headline(text: str) -> None:
    """One-sentence headline insight at the top of each section."""
    st.markdown(f"#### {text}")


def small_sample_warning(n: int, minimum: int = 20) -> None:
    if n < minimum:
        st.warning(f"Only {n} stations match your filters. Read the results with care.", icon="⚠️")
