"""Comparisons by region and station type, then rankings."""
import streamlit as st

from utils import viz
from utils.constants import MIN_STATIONS_PER_GROUP, POLLUTANTS, UNIT, YEAR_AFTER, YEAR_BEFORE
from utils.ui import headline, show_chart


def render(ctx: dict) -> None:
    pol, short = ctx["pol"], POLLUTANTS[ctx["pol"]]["short"]
    ref, ref_label = ctx["ref"], ctx["ref_label"]
    paired, after = ctx["paired"], ctx["st_after"]

    # ---------------- 2. Where did it change? ----------------
    st.header("2. Where did the air improve?")
    reg = paired.groupby("region")["pct_change"].mean()
    reg = reg[paired.groupby("region").size() >= MIN_STATIONS_PER_GROUP]
    if len(reg):
        headline(f"The biggest drop is in {reg.idxmin()} ({reg.min():+.0f}%); "
                 f"the smallest is in {reg.idxmax()} ({reg.max():+.0f}%).")
    fig, hidden = viz.dumbbell_by_region(paired, pol, ref, ref_label)
    show_chart(fig, f"Dumbbell chart: for each region, an orange diamond shows the average {short} in {YEAR_BEFORE} "
                    f"and a blue circle shows {YEAR_AFTER}. The line between them is the change.")
    if hidden:
        st.caption(f"{hidden} region(s) with fewer than {MIN_STATIONS_PER_GROUP} stations are hidden.")

    paired_all = ctx["paired_all"]
    if len(paired_all):
        show_chart(viz.influence_small_multiples(paired_all),
                   "Three small bar charts, one per pollutant. Each compares Background, Traffic and Industrial stations "
                   f"in {YEAR_BEFORE} and {YEAR_AFTER}. Traffic stations have the highest levels in both years.")

    # ---------------- 3. Ranking ----------------
    st.header("3. Who is still above the limits?")
    if after.empty:
        st.info("No station matches the filters.")
        return
    n_above = int((after["value"] > ref).sum())
    worst = after.loc[after["value"].idxmax()]
    headline(f"In {YEAR_AFTER}, {n_above} of {len(after)} stations are above {ref_label} ({ref:g} {UNIT}). "
             f"The highest is {worst['site_name']} ({worst['value']:.1f} {UNIT}, {worst['influence'].lower()} station).")

    n = st.slider("Number of stations to show", 5, 25, 10, help="Applies to the two station rankings below.")
    t1, t2 = st.tabs(["Most polluted", "Cleanest"])
    with t1:
        top = after.nlargest(n, "value")
        share_traffic = (top["influence"] == "Traffic").mean() * 100
        show_chart(viz.ranking_bar(after, pol, n, True, ref, ref_label),
                   f"Horizontal bars ranking the {n} stations with the highest {short} in {YEAR_AFTER}. "
                   f"{share_traffic:.0f}% of them are traffic stations.")
    with t2:
        show_chart(viz.ranking_bar(after, pol, n, False, ref, ref_label),
                   f"Horizontal bars ranking the {n} stations with the lowest {short} in {YEAR_AFTER}.")

    col_a, col_b = st.columns(2)
    with col_a:
        fig, hidden = viz.region_ranking_bar(after, pol, ref, ref_label)
        show_chart(fig, f"Regions ranked by their average {short} in {YEAR_AFTER}. Orange bars are above the reference level.")
        if hidden:
            st.caption(f"{hidden} region(s) with fewer than {MIN_STATIONS_PER_GROUP} stations are hidden.")
    with col_b:
        show_chart(viz.distribution_hist(after, pol, ref, ref_label),
                   f"Histogram of {short} annual means in {YEAR_AFTER}, stacked by station type. "
                   "Most stations are below the reference level, with a long tail of higher values.")
