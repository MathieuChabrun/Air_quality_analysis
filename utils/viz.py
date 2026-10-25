"""Chart functions. Every chart goes through the same style helper so that
colours, fonts, units and axis labels stay consistent (accessibility)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .constants import (
    C_AFTER, C_BEFORE, C_GOOD, C_NEUTRAL, C_WARN, INFLUENCE_COLORS, LEVEL_COLORS,
    MAP_CENTER, MIN_STATIONS_PER_GROUP, POLLUTANTS, UNIT, YEAR_AFTER, YEAR_BEFORE,
)
from .prep import level_class

YEAR_COLORS = {str(YEAR_BEFORE): C_BEFORE, str(YEAR_AFTER): C_AFTER}


def style(fig: go.Figure, title: str | None = None, x: str | None = None,
          y: str | None = None, height: int = 430) -> go.Figure:
    """Common layout: white background, readable fonts, labelled axes."""
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, x=0, font=dict(size=16)) if title else None,
        font=dict(size=14, color="#1f1f1f"),
        height=height,
        margin=dict(l=10, r=10, t=100 if title else 50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0, title_text=""),
        hoverlabel=dict(font_size=13),
    )
    if x is not None:
        fig.update_xaxes(title_text=x)
    if y is not None:
        fig.update_yaxes(title_text=y)
    return fig


def _ref_line(fig, ref, ref_label, axis="y"):
    kw = dict(line_dash="dash", line_color=C_NEUTRAL, line_width=2,
              annotation_text=f"{ref_label}: {ref:g} {UNIT}",
              annotation_font=dict(size=12, color=C_NEUTRAL))
    if axis == "y":
        fig.add_hline(y=ref, annotation_position="top left", **kw)
    else:
        fig.add_vline(x=ref, line_dash="dash", line_color=C_NEUTRAL, line_width=2)
        fig.add_annotation(x=ref, y=1.0, xref="x", yref="paper", yanchor="bottom", xanchor="left",
                           text=f"{ref_label}: {ref:g} {UNIT}", showarrow=False,
                           font=dict(size=12, color=C_NEUTRAL))


def _scatter_map(df, **kwargs):
    """plotly >= 5.24 has scatter_map; older versions have scatter_mapbox."""
    if hasattr(px, "scatter_map"):
        return px.scatter_map(df, map_style="carto-positron", **kwargs)
    return px.scatter_mapbox(df, mapbox_style="carto-positron", **kwargs)


def _label(df: pd.DataFrame) -> pd.Series:
    lab = df["site_name"] + " (" + df["region"] + ")"
    dup = lab.duplicated(keep=False)
    return lab.where(~dup, lab + " [" + df["site_id"] + "]")


# --------------------------------------------------------------------------
# Before / after
# --------------------------------------------------------------------------
def box_before_after(paired: pd.DataFrame, pol: str, ref: float, ref_label: str) -> go.Figure:
    long = pd.concat([
        paired.assign(year=str(YEAR_BEFORE), value=paired["before"]),
        paired.assign(year=str(YEAR_AFTER), value=paired["after"]),
    ])
    fig = px.box(
        long, x="year", y="value", color="year", color_discrete_map=YEAR_COLORS,
        points="all", hover_name="site_name",
        hover_data={"region": True, "influence": True, "year": False, "value": ":.1f"},
        category_orders={"year": [str(YEAR_BEFORE), str(YEAR_AFTER)]},
    )
    fig.update_traces(marker=dict(size=4, opacity=0.5), jitter=0.4, pointpos=0)
    _ref_line(fig, ref, ref_label)
    fig.update_layout(showlegend=False)
    return style(fig, f"Station values, same stations in both years — {POLLUTANTS[pol]['short']}",
                 "Year", f"Annual mean ({UNIT})")


def paired_scatter(paired: pd.DataFrame, pol: str, ref: float, ref_label: str) -> go.Figure:
    top = float(max(paired["before"].max(), paired["after"].max())) * 1.05
    fig = px.scatter(
        paired, x="before", y="after", color="influence",
        color_discrete_map=INFLUENCE_COLORS, hover_name="site_name",
        hover_data={"region": True, "before": ":.1f", "after": ":.1f", "change": ":.1f", "influence": False},
        labels={"influence": "Station type"},
    )
    fig.update_traces(marker=dict(size=8, opacity=0.75))
    fig.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", name="No change",
                             line=dict(color=C_NEUTRAL, dash="dot"), hoverinfo="skip"))
    _ref_line(fig, ref, ref_label)
    fig.update_xaxes(range=[0, top])
    fig.update_yaxes(range=[0, top], scaleanchor="x", scaleratio=1)
    fig.add_annotation(x=top * 0.97, y=top * 0.06, text="Below the line = cleaner in 2025",
                       showarrow=False, xanchor="right", font=dict(size=12, color=C_NEUTRAL))
    return style(fig, f"Each dot is a station — {POLLUTANTS[pol]['short']}",
                 f"{YEAR_BEFORE} annual mean ({UNIT})", f"{YEAR_AFTER} annual mean ({UNIT})", height=480)


def change_map(paired: pd.DataFrame, pol: str) -> go.Figure:
    d = paired[paired["is_mainland"]]
    m = float(np.nanpercentile(np.abs(d["change"]), 95)) if len(d) else 1.0  # cap so one outlier does not wash out the colours
    m = max(m, 1.0)
    fig = _scatter_map(
        d, lat="lat", lon="lon", color="change", hover_name="site_name",
        hover_data={"lat": False, "lon": False, "region": True, "influence": True,
                    "before": ":.1f", "after": ":.1f", "change": ":.1f"},
        color_continuous_scale=[[0, C_AFTER], [0.5, "#F2F2F2"], [1, C_WARN]],
        range_color=(-m, m), zoom=4.7, center=MAP_CENTER, opacity=0.85,
        labels={"change": f"Change ({UNIT})"},
    )
    fig.update_traces(marker=dict(size=11))
    fig.update_coloraxes(colorbar=dict(title=f"Change<br>{YEAR_BEFORE}→{YEAR_AFTER}<br>({UNIT})"))
    return style(fig, f"Change in {POLLUTANTS[pol]['short']} (blue = cleaner)", height=520)


def level_map(stations: pd.DataFrame, pol: str, year: int) -> go.Figure:
    d = stations[(stations["year"] == year) & stations["is_mainland"]].copy()
    d["Level"] = level_class(d["value"], pol)
    d["Level"] = d["Level"].astype(str)
    order = list(level_class(pd.Series([0.0]), pol).cat.categories)
    fig = _scatter_map(
        d, lat="lat", lon="lon", color="Level", hover_name="site_name",
        hover_data={"lat": False, "lon": False, "region": True, "influence": True, "value": ":.1f", "Level": False},
        color_discrete_sequence=LEVEL_COLORS, category_orders={"Level": order},
        zoom=4.7, center=MAP_CENTER, opacity=0.85, labels={"value": f"Annual mean ({UNIT})"},
    )
    fig.update_traces(marker=dict(size=9))
    return style(fig, f"{POLLUTANTS[pol]['short']} levels in {year}", height=520)


def dumbbell_by_region(paired: pd.DataFrame, pol: str, ref: float, ref_label: str):
    g = (paired.groupby("region")
         .agg(before=("before", "mean"), after=("after", "mean"), n=("before", "size"))
         .reset_index())
    kept = g[g["n"] >= MIN_STATIONS_PER_GROUP].sort_values("after")
    hidden = len(g) - len(kept)
    fig = go.Figure()
    xs, ys = [], []
    for _, r in kept.iterrows():
        xs += [r["before"], r["after"], None]
        ys += [r["region"], r["region"], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#BBBBBB", width=3),
                             hoverinfo="skip", showlegend=False))
    for col, name, color in (("before", str(YEAR_BEFORE), C_BEFORE), ("after", str(YEAR_AFTER), C_AFTER)):
        fig.add_trace(go.Scatter(
            x=kept[col], y=kept["region"], mode="markers", name=name,
            marker=dict(size=12, color=color, symbol="circle" if col == "after" else "diamond"),
            customdata=kept[["n"]].to_numpy(),
            hovertemplate="%{y}<br>" + name + ": %{x:.1f} " + UNIT + "<br>%{customdata[0]} stations<extra></extra>",
        ))
    _ref_line(fig, ref, ref_label, axis="x")
    fig.update_yaxes(categoryorder="array", categoryarray=list(kept["region"]))
    style(fig, f"Average by region — {POLLUTANTS[pol]['short']}", f"Annual mean ({UNIT})", None,
          height=max(380, 34 * len(kept) + 140))
    return fig, hidden


def influence_small_multiples(paired_all: pd.DataFrame) -> go.Figure:
    long = pd.concat([
        paired_all.assign(year=str(YEAR_BEFORE), value=paired_all["before"]),
        paired_all.assign(year=str(YEAR_AFTER), value=paired_all["after"]),
    ])
    agg = (long.groupby(["pollutant", "influence", "year"])["value"].agg(["mean", "size"]).reset_index())
    agg["pollutant"] = agg["pollutant"].map(lambda p: POLLUTANTS[p]["short"])
    fig = px.bar(
        agg, x="influence", y="mean", color="year", barmode="group", facet_col="pollutant",
        color_discrete_map=YEAR_COLORS, text=agg["mean"].round(1),
        hover_data={"size": True, "mean": ":.1f"},
        category_orders={"year": [str(YEAR_BEFORE), str(YEAR_AFTER)],
                         "influence": ["Background", "Traffic", "Industrial"]},
        labels={"mean": f"Average ({UNIT})", "influence": "Station type", "size": "Stations"},
    )
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    return style(fig, "Small multiples: traffic stations stay the highest", None, f"Annual mean ({UNIT})", height=420)


# --------------------------------------------------------------------------
# Ranking
# --------------------------------------------------------------------------
def ranking_bar(stations_after: pd.DataFrame, pol: str, n: int, top: bool,
                ref: float, ref_label: str) -> go.Figure:
    d = stations_after.sort_values("value", ascending=not top).head(n).copy()
    d["label"] = _label(d)
    fig = px.bar(
        d, x="value", y="label", color="influence", orientation="h",
        color_discrete_map=INFLUENCE_COLORS, hover_name="site_name",
        hover_data={"region": True, "area_type": True, "value": ":.1f", "label": False, "influence": False},
        labels={"influence": "Station type", "area_type": "Area"},
        text=d["value"].round(1),
    )
    fig.update_yaxes(categoryorder="array", categoryarray=list(d["label"]), autorange="reversed", title_text="")
    fig.update_traces(textposition="outside", cliponaxis=False)
    _ref_line(fig, ref, ref_label, axis="x")
    name = "Most polluted" if top else "Cleanest"
    return style(fig, f"{name} {len(d)} stations in {YEAR_AFTER} — {POLLUTANTS[pol]['short']}",
                 f"Annual mean ({UNIT})", None, height=max(360, 30 * len(d) + 140))


def region_ranking_bar(stations_after: pd.DataFrame, pol: str, ref: float, ref_label: str):
    g = (stations_after.groupby("region")["value"].agg(["mean", "size"]).reset_index()
         .rename(columns={"mean": "avg", "size": "n"}))
    kept = g[g["n"] >= MIN_STATIONS_PER_GROUP].sort_values("avg", ascending=False)
    hidden = len(g) - len(kept)
    kept["status"] = np.where(kept["avg"] > ref, "Above reference", "At or below reference")
    fig = px.bar(
        kept, x="avg", y="region", orientation="h", color="status",
        color_discrete_map={"Above reference": C_WARN, "At or below reference": C_GOOD},
        hover_data={"n": True, "avg": ":.1f", "status": False}, text=kept["avg"].round(1),
        labels={"n": "Stations", "avg": f"Average ({UNIT})"},
    )
    fig.update_yaxes(categoryorder="array", categoryarray=list(kept["region"]), autorange="reversed", title_text="")
    fig.update_traces(textposition="outside", cliponaxis=False)
    _ref_line(fig, ref, ref_label, axis="x")
    style(fig, f"Regions ranked by average level in {YEAR_AFTER} — {POLLUTANTS[pol]['short']}",
          f"Annual mean ({UNIT})", None, height=max(380, 32 * len(kept) + 140))
    return fig, hidden


def distribution_hist(stations_after: pd.DataFrame, pol: str, ref: float, ref_label: str) -> go.Figure:
    fig = px.histogram(
        stations_after, x="value", color="influence", nbins=30, barmode="stack",
        color_discrete_map=INFLUENCE_COLORS, labels={"influence": "Station type"},
    )
    fig.update_traces(hovertemplate="%{x} " + UNIT + "<br>%{y} stations<extra></extra>")
    _ref_line(fig, ref, ref_label, axis="x")
    return style(fig, f"How {YEAR_AFTER} values are spread — {POLLUTANTS[pol]['short']}",
                 f"Annual mean ({UNIT})", "Number of stations", height=380)


# --------------------------------------------------------------------------
# Implications
# --------------------------------------------------------------------------
def share_above_bar(df: pd.DataFrame, ref_label: str) -> go.Figure:
    """df columns: pollutant, year (str), share."""
    fig = px.bar(
        df, x="pollutant", y="share", color="year", barmode="group",
        color_discrete_map=YEAR_COLORS, text=df["share"].round(0).astype(int).astype(str) + "%",
        category_orders={"year": [str(YEAR_BEFORE), str(YEAR_AFTER)]},
        hover_data={"n": True, "share": ":.1f"}, labels={"n": "Stations", "share": "Share (%)"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(range=[0, 105])
    return style(fig, f"Stations above: {ref_label}", "Pollutant", "Share of stations (%)", height=380)


def projection_chart(proj_ref: pd.DataFrame, proj_who: pd.DataFrame, target_year: int,
                     pol: str, pace: int) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=proj_ref["year"], y=proj_ref["share_above"], mode="lines+markers",
                             name="Above EU limit from 2030", line=dict(color=C_AFTER, width=3),
                             hovertemplate="%{x}: %{y:.0f}% of stations<extra></extra>"))
    fig.add_trace(go.Scatter(x=proj_who["year"], y=proj_who["share_above"], mode="lines+markers",
                             name="Above WHO 2021 guideline", line=dict(color=C_WARN, width=3, dash="dot"),
                             hovertemplate="%{x}: %{y:.0f}% of stations<extra></extra>"))
    fig.add_vline(x=target_year, line_dash="dash", line_color=C_NEUTRAL,
                  annotation_text=f"Target year {target_year}", annotation_position="top left")
    fig.update_yaxes(range=[0, 105])
    return style(fig, f"What if the pace is {pace}% of the last 10 years? — {POLLUTANTS[pol]['short']}",
                 "Year", "Share of stations above the level (%)", height=400)


# --------------------------------------------------------------------------
# Data quality
# --------------------------------------------------------------------------
def qc_bar(qc: pd.DataFrame) -> go.Figure:
    d = qc[qc["year"].isin([YEAR_BEFORE, YEAR_AFTER])].copy()
    d["Removed (not validated, duplicate or implausible)"] = d["rows"] - d["usable_stations"]
    d["Kept for analysis"] = d["usable_stations"]
    d["file"] = d["pollutant"].map(lambda p: POLLUTANTS[p]["short"]) + " " + d["year"].astype(str)
    long = d.melt(id_vars="file", value_vars=["Kept for analysis", "Removed (not validated, duplicate or implausible)"],
                  var_name="Status", value_name="Rows")
    fig = px.bar(long, x="file", y="Rows", color="Status", barmode="stack",
                 color_discrete_map={"Kept for analysis": C_AFTER,
                                     "Removed (not validated, duplicate or implausible)": C_WARN},
                 text="Rows")
    fig.update_traces(textposition="inside")
    return style(fig, "Rows kept and removed per file", "File (pollutant and year)", "Number of station rows", height=380)


def coverage_bar(qc: pd.DataFrame) -> go.Figure:
    d = qc.copy()
    d["pollutant"] = d["pollutant"].map(lambda p: POLLUTANTS[p]["short"])
    d["year"] = d["year"].astype(str)
    fig = px.bar(d, x="pollutant", y="mean_time_coverage", color="year", barmode="group",
                 text=d["mean_time_coverage"].round(0).astype(int).astype(str) + "%",
                 color_discrete_sequence=[C_BEFORE, C_AFTER, C_NEUTRAL],
                 labels={"mean_time_coverage": "Time coverage (%)"})
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.add_hline(y=75, line_dash="dash", line_color=C_NEUTRAL, annotation_text="75% (usual minimum)",
                  annotation_position="top left")
    fig.update_yaxes(range=[0, 110])
    return style(fig, "Average time coverage of the yearly mean", "Pollutant", "Share of the year measured (%)", height=380)
