"""KPI header and the big-picture before/after comparison."""
import streamlit as st

from utils import viz
from utils.constants import POLLUTANTS, UNIT, YEAR_AFTER, YEAR_BEFORE
from utils.prep import compute_kpis
from utils.ui import headline, show_chart, small_sample_warning


def render_kpis(ctx: dict) -> dict:
    """KPI row tied to the filters. Returns the KPI dict for reuse."""
    k = compute_kpis(ctx["paired"], ctx["st_before"], ctx["st_after"], ctx["ref"])
    short = POLLUTANTS[ctx["pol"]]["short"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Average {short}, {YEAR_AFTER}", f"{k['mean_after']:.1f} {UNIT}",
              f"{k['pct_change']:+.0f}% vs {YEAR_BEFORE}", delta_color="inverse",
              help=f"Mean of the same {k['n_pairs']} stations in both years. {YEAR_BEFORE}: {k['mean_before']:.1f} {UNIT}.")
    c2.metric("Stations that improved", f"{k['share_improved']:.0f}%",
              help="Share of stations with a lower annual mean in 2025 than in 2015.")
    c3.metric(f"Above {ctx['ref_label']}, {YEAR_AFTER}", f"{k['above_after']:.0f}% of stations",
              f"{k['above_after'] - k['above_before']:+.0f} pts vs {YEAR_BEFORE}", delta_color="inverse",
              help=f"Reference: {ctx['ref']:g} {UNIT}. Uses all validated stations of each year "
                   f"({k['n_before']} in {YEAR_BEFORE}, {k['n_after']} in {YEAR_AFTER}).")
    c4.metric("Stations compared", f"{k['n_pairs']}",
              help="Stations validated in both years and matching your filters.")
    small_sample_warning(k["n_pairs"])
    return k


def render(ctx: dict, k: dict) -> None:
    pol, short = ctx["pol"], POLLUTANTS[ctx["pol"]]["short"]
    st.header("1. The big picture")
    headline(
        f"On the same {k['n_pairs']} stations, average {short} went from {k['mean_before']:.1f} to "
        f"{k['mean_after']:.1f} {UNIT} ({k['pct_change']:+.0f}%) — and {k['share_improved']:.0f}% of stations improved."
    )
    paired, ref, ref_label = ctx["paired"], ctx["ref"], ctx["ref_label"]

    left, right = st.columns(2)
    with left:
        show_chart(
            viz.box_before_after(paired, pol, ref, ref_label),
            f"Box plot of {short} annual means for {len(paired)} stations in {YEAR_BEFORE} and {YEAR_AFTER}. "
            f"The median moves from {paired['before'].median():.1f} to {paired['after'].median():.1f} {UNIT}. "
            f"A dashed line shows the reference level ({ref:g} {UNIT}).",
        )
    with right:
        below = int((paired["change"] < 0).sum())
        show_chart(
            viz.paired_scatter(paired, pol, ref, ref_label),
            f"Scatter plot, one dot per station, {YEAR_BEFORE} on the x-axis and {YEAR_AFTER} on the y-axis. "
            f"{below} of {len(paired)} dots are below the diagonal line, which means cleaner air in {YEAR_AFTER}.",
        )

    st.subheader("Where are the stations?")
    n_over = int((~paired["is_mainland"]).sum())
    tab1, tab2, tab3 = st.tabs([f"Change {YEAR_BEFORE}→{YEAR_AFTER}", f"Levels {YEAR_BEFORE}", f"Levels {YEAR_AFTER}"])
    with tab1:
        show_chart(viz.change_map(paired, pol),
                   f"Map of mainland France. Each point is a station coloured by the change in {short}. "
                   "Blue points became cleaner; orange points became more polluted. Colours are capped at the 95th percentile of changes, so a few extreme stations do not hide the others.")
    with tab2:
        show_chart(viz.level_map(ctx["stations_all"][ctx["stations_all"]["pollutant"] == pol], pol, YEAR_BEFORE),
                   f"Map of {short} levels in {YEAR_BEFORE}, coloured by WHO and EU reference levels.")
    with tab3:
        show_chart(viz.level_map(ctx["stations_all"][ctx["stations_all"]["pollutant"] == pol], pol, YEAR_AFTER),
                   f"Map of {short} levels in {YEAR_AFTER}, coloured by WHO and EU reference levels.")
    if n_over:
        st.caption(f"Overseas stations not drawn on the maps: {n_over} (they are included in all numbers).")
