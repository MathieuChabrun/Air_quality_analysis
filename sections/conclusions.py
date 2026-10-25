"""Implications, what-if scenario and next steps."""
import pandas as pd
import streamlit as st

from utils import viz
from utils.constants import POLLUTANTS, REFERENCES, UNIT, YEAR_AFTER, YEAR_BEFORE
from utils.prep import project_share_above, share_above
from utils.ui import headline, show_chart


def _share_table(ctx: dict) -> pd.DataFrame:
    s = ctx["stations_all"]
    rows = []
    for pol, meta in POLLUTANTS.items():
        ref = meta[ctx["ref_key"]]
        for y in (YEAR_BEFORE, YEAR_AFTER):
            v = s[(s["pollutant"] == pol) & (s["year"] == y)]["value"]
            rows.append(dict(pollutant=meta["short"], year=str(y), share=share_above(v, ref), n=len(v)))
    return pd.DataFrame(rows).dropna()


def render(ctx: dict) -> None:
    pol, short = ctx["pol"], POLLUTANTS[ctx["pol"]]["short"]
    paired = ctx["paired"]
    st.header("5. What does it mean?")

    share = _share_table(ctx)
    if len(share):
        after = share[share["year"] == str(YEAR_AFTER)].set_index("pollutant")["share"]
        headline(f"Against the {ctx['ref_label']}, the share of stations above the level in {YEAR_AFTER} is "
                 + ", ".join(f"{v:.0f}% for {k}" for k, v in after.items()) + ".")
        show_chart(viz.share_above_bar(share, f"{ctx['ref_label']} (level depends on the pollutant)"),
                   f"Grouped bars: share of stations above the selected reference level, for NO₂, PM₁₀ and PM₂.₅, "
                   f"in {YEAR_BEFORE} and {YEAR_AFTER}. Change the reference level in the sidebar to see how the picture changes.")

    # ---------------- What-if ----------------
    st.subheader("What if the improvement continues?")
    st.markdown(
        f"Move the sliders to test a simple scenario. For each station, we keep its {YEAR_BEFORE}–{YEAR_AFTER} "
        "yearly rate of change and apply it to the future. **This is a scenario, not a forecast** "
        "(two data points per station, no weather or policy model)."
    )
    c1, c2 = st.columns(2)
    pace = c1.slider("Pace compared with the last 10 years (%)", 0, 150, 100, 25,
                     help="100% = same speed as 2015–2025. 50% = half as fast. 0% = no more progress.")
    target = c2.slider("Target year", YEAR_AFTER + 1, YEAR_AFTER + 15, 2030)
    ref_eu = POLLUTANTS[pol]["eu_2030"]
    ref_who = POLLUTANTS[pol]["who"]
    p_eu = project_share_above(paired, ref_eu, pace / 100)
    p_who = project_share_above(paired, ref_who, pace / 100)
    if p_eu.empty:
        st.info("Not enough stations to run the scenario with these filters.")
    else:
        now_eu, tgt_eu = p_eu.iloc[0]["share_above"], p_eu[p_eu["year"] == target].iloc[0]["share_above"]
        now_who, tgt_who = p_who.iloc[0]["share_above"], p_who[p_who["year"] == target].iloc[0]["share_above"]
        m1, m2 = st.columns(2)
        m1.metric(f"Above EU 2030 limit ({ref_eu} {UNIT}) in {target}", f"{tgt_eu:.0f}% of stations",
                  f"{tgt_eu - now_eu:+.0f} pts vs {YEAR_AFTER}", delta_color="inverse")
        m2.metric(f"Above WHO guideline ({ref_who} {UNIT}) in {target}", f"{tgt_who:.0f}% of stations",
                  f"{tgt_who - now_who:+.0f} pts vs {YEAR_AFTER}", delta_color="inverse")
        show_chart(viz.projection_chart(p_eu, p_who, target, pol, pace),
                   f"Two lines from {YEAR_AFTER} to {YEAR_AFTER + 15}: the share of {len(paired)} stations above the EU 2030 limit "
                   f"and above the WHO guideline for {short}, if the 2015–2025 rate continues at {pace}% of its speed.")
        st.caption(f"Based on {int(p_eu.iloc[0]['n'])} stations with a positive value in both years.")

    # ---------------- Takeaways ----------------
    st.subheader("Key insights")
    pa = ctx["paired_all"]
    if len(pa):
        g = pa.groupby("pollutant")[["before", "after"]].mean()
        g["pct"] = (g["after"] - g["before"]) / g["before"] * 100
        lines = [f"**{POLLUTANTS[p]['short']}** changed by **{r['pct']:+.0f}%** on average "
                 f"({r['before']:.1f} → {r['after']:.1f} {UNIT})." for p, r in g.iterrows()]
        st.markdown("1. " + "\n1. ".join(lines))
    st.markdown(
        """
- **Progress is broad.** Almost every station recorded a lower level in 2025 than in 2015.
- **Traffic stations are still the highest** in every pollutant, so road traffic remains the main hotspot.
- **The WHO guideline is much stricter than the law.** Many stations meet the EU limits but not the WHO levels, especially for fine particles.
"""
    )
    st.subheader("Implications and next steps")
    st.markdown(
        """
- **For local decision-makers:** focus new actions on traffic hotspots and on places that are still above the 2030 EU limit.
- **For citizens:** use the maps to see how your area compares, and keep in mind that levels are annual averages.
- **For future work:** add the years between 2015 and 2025 to see the trend, add weather data, and link stations to population exposure.
"""
    )
    st.info(
        "Method note: yearly means come from Geod'air (LCSQA / Ineris). WHO 2021 guidelines and EU limits "
        "(Directive 2008/50/EC until 2029, Directive (EU) 2024/2881 from 2030) are used as reference levels."
    )
