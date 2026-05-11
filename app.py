"""
Spotify Trends Analytics Dashboard — v6
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Changes vs v5:
  ✦ Top-N slider removed entirely — all genre charts hardcoded to TOP_N=10
  ✦ _INPUTS reduced: topn removed from shared input list
  ✦ Reset callback updated: no longer resets a top-N control
  ✦ Chart A  — top 10 genres by avg popularity
  ✦ Chart B  — top 10 artists by song count (was 12, now 10)
  ✦ Chart C  — top 10 genres by track count (stacked column)
  ✦ Chart D  — top 10 genres by track count (content explicitness)
  ✦ Chart E  — top 10 genres by track count (energy & danceability)
  ✦ Chart H  — top 10 genres (bubble) — larger bubbles [18-50px],
               all labels "top center" for clean uniform look
  ✦ Chart M  — engagement area: true auto-scale (no floor), pure data range
  ✦ Filter panel: 4 filters + reset redistributed evenly (no slider gap)
"""

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os, sys

# ══════════════════════════════════════════════════════════════
# 1.  LOAD & VALIDATE
# ══════════════════════════════════════════════════════════════
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "data_preprocessed.csv")

try:
    df = pd.read_csv(CSV_PATH)
    print(f"✅  Loaded {len(df):,} rows")
except FileNotFoundError:
    sys.exit(f"\n❌  Not found: {CSV_PATH}\n    Put data_preprocessed.csv in ./data/\n")

REQUIRED = [
    "artists", "track_name", "popularity", "danceability", "energy",
    "loudness", "valence", "tempo", "track_genre", "duration_min",
    "popularity_level", "duration_category", "tempo_category",
    "engagement_score", "loudness_level", "explicit_label",
    "mood_score", "artist_song_count", "genre_rank",
]
missing = [c for c in REQUIRED if c not in df.columns]
if missing:
    sys.exit(f"\n❌  Missing columns: {missing}\n")

df["popularity"] = df["popularity"].clip(0, 100)

# ── Static filter option lists ─────────────────────────────────
ALL_TEMPO_CATS  = sorted(df["tempo_category"].dropna().unique().tolist())
ALL_DUR_CATS    = sorted(df["duration_category"].dropna().unique().tolist())
ALL_LOUD_LEVELS = sorted(df["loudness_level"].dropna().unique().tolist())

# Hardcoded top-N — slider removed
TOP_N = 10

POP_ORDER   = ["Low", "Medium", "High", "Very High"]
# ── Redesigned palette — softer, Spotify-premium, dark-bg safe ─
POP_PALETTE = {
    "Low": "#4C78A8",      # muted blue
    "Medium": "#1DB954",   # Spotify green
    "High": "#9B5DE5",     # soft purple
}
EXPLICIT_PALETTE = {
    "Explicit": "#9B5DE5",      # soft purple
    "Non-Explicit": "#52B788",  # green
}
# Instrumentalness / Liveness chart colours
CLR_INSTR = "#2EC4B6"    # electric cyan
CLR_LIVE = "#80ED99"   # warm amber


# ══════════════════════════════════════════════════════════════
# 2.  COLOUR SYSTEM
# ══════════════════════════════════════════════════════════════
S_GREEN   = "#1DB954"
S_GREEN2  = "#1ED760"
S_DARK    = "#191414"
S_GRAY    = "#535353"
PRIMARY_GREEN = "#1DB954"
GREEN_MED = "#52B788"
GREEN_LIGHT = "#95D5B2"
TEAL = "#2EC4B6"
MINT = "#80ED99"
PURPLE_ACCENT = "#9B5DE5"
YELLOW_ACCENT = "#FACC15"
WHITE     = "#FFFFFF"
WHITE_DIM = "#A7A7A7"
GRID_CLR  = "#282828"

CHART_PAL = [
    "#1DB954",
    "#52B788",
    "#95D5B2",
    "#2EC4B6",
    "#80ED99",
    "#9B5DE5",
]

# ── Reusable layout pieces ─────────────────────────────────────
# Larger margins give titles room to breathe — fixes overlap
_MARGIN_WIDE  = dict(l=70, r=30, t=72, b=65)
_MARGIN_SHORT = dict(l=70, r=30, t=72, b=50)

_HOVER = dict(bgcolor="#1A1A1A", font_color=WHITE,
              bordercolor=S_GREEN, font_size=12, namelength=24)

# Legend: bottom-right, compact
_LEG_BR = dict(
    orientation="v", bgcolor="rgba(0,0,0,0)",
    font=dict(size=10, color=WHITE_DIM),
    itemsizing="constant",
    x=1.0, y=0.0, xanchor="right", yanchor="bottom",
)
# Legend: horizontal, anchored ABOVE the plot area (y=1.08)
# Used for stacked charts — sits above bars, never overlaps
_LEG_TOP = dict(
    orientation="h",
    bgcolor="rgba(0,0,0,0)",
    font=dict(size=11, color=WHITE_DIM),
    itemsizing="constant",
    x=0.0, y=1.08,
    xanchor="left", yanchor="bottom",
    traceorder="normal",
)
# Legacy alias kept so any code referencing _LEG_BH still compiles
_LEG_BH = _LEG_TOP

_BASE_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'Outfit', sans-serif", color=WHITE),
    margin=_MARGIN_WIDE,
    hoverlabel=_HOVER,
    legend=_LEG_BR,
    xaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR,
               tickfont=dict(color=WHITE_DIM, size=11),
               title_font=dict(size=12, color=WHITE_DIM),
               automargin=True),
    yaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR,
               tickfont=dict(color=WHITE_DIM, size=11),
               title_font=dict(size=12, color=WHITE_DIM),
               automargin=True),
)

_BASE_LIGHT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#F8FAFC",
    font=dict(family="'Outfit', sans-serif", color="#111"),
    margin=_MARGIN_WIDE,
    hoverlabel=dict(bgcolor="#FFF", font_color="#111",
                    bordercolor=S_GREEN, font_size=12, namelength=24),
    legend=dict(**{k: v for k, v in _LEG_BR.items() if k not in ("font", "bgcolor")},
                font=dict(size=10, color="#555"),
                bgcolor="rgba(255,255,255,0.85)"),
    xaxis=dict(gridcolor="#E5E7EB", zerolinecolor="#E5E7EB",
               tickfont=dict(color="#666", size=11),
               title_font=dict(size=12, color="#444"),
               automargin=True),
    yaxis=dict(gridcolor="#E5E7EB", zerolinecolor="#E5E7EB",
               tickfont=dict(color="#666", size=11),
               title_font=dict(size=12, color="#444"),
               automargin=True),
)

def T(theme):
    return _BASE_DARK if theme == "dark" else _BASE_LIGHT


# ══════════════════════════════════════════════════════════════
# 3.  HELPERS
# ══════════════════════════════════════════════════════════════
def compact_num(n: int) -> str:
    """Format large numbers as 12.3K / 1.4M for KPI cards."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def stamp(fig, title: str, t: dict, xt="", yt="", leg_h=False):
    """Apply theme + title + axis labels to a figure."""
    leg_override = {"legend": _LEG_BH} if leg_h else {}
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=14, color=S_GREEN, family="'Outfit', sans-serif"),
            x=0.01, xanchor="left", pad=dict(b=10, t=4),
        ),
        **t,
        **leg_override,
    )
    if xt: fig.update_xaxes(title_text=xt)
    if yt: fig.update_yaxes(title_text=yt)
    return fig


def fdf(tc, dc, lc, content="All"):
    """Filter dataframe by three checklists + content-type radio."""
    tc = tc or ALL_TEMPO_CATS
    dc = dc or ALL_DUR_CATS
    lc = lc or ALL_LOUD_LEVELS
    mask = (
        df["tempo_category"].isin(tc)
        & df["duration_category"].isin(dc)
        & df["loudness_level"].isin(lc)
    )
    if content == "Explicit":
        mask &= df["explicit_label"] == "Explicit"
    elif content == "Non-Explicit":
        mask &= df["explicit_label"] == "Non-Explicit"
    return df[mask].copy()


def top_genres(d, n):
    """Restrict dataframe to the top-n genres by track count."""
    top = d["track_genre"].value_counts().nlargest(int(n)).index
    return d[d["track_genre"].isin(top)]


def safe_sample(d, n=1500, seed=42):
    return d.sample(n, random_state=seed) if len(d) > n else d


def rolling_avg(series: pd.Series, window=5) -> pd.Series:
    """Centred rolling mean, NaN edges filled with original values."""
    rolled = series.rolling(window, center=True, min_periods=1).mean()
    return rolled


# ══════════════════════════════════════════════════════════════
# 4.  APP INIT & LAYOUT
# ══════════════════════════════════════════════════════════════
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Spotify Trends Analytics Dashboard"


def kpi_card(icon, label, vid, color_cls=""):
    return html.Div(className=f"kpi-card {color_cls}", children=[
        html.Div(className="kpi-icon-wrap",
                 children=[html.Span(icon, className="kpi-icon")]),
        html.Div(className="kpi-body", children=[
            html.Div(id=vid,  className="kpi-value", children="—"),
            html.Div(label,   className="kpi-label"),
        ]),
    ])


def gc(gid, h="390px"):
    return html.Div(className="chart-card", children=[
        dcc.Graph(id=gid,
                  config={"displayModeBar": False, "responsive": True},
                  style={"height": h}),
    ])


def sec(num, title, subtitle=""):
    return html.Div(className="section-header", children=[
        html.Div(className="section-left", children=[
            html.Span(num, className="section-num"),
            html.Div(children=[
                html.H2(title,   className="section-title"),
                html.P(subtitle, className="section-sub") if subtitle else None,
            ]),
        ]),
    ])


def pill_checklist(cid, options, value):
    return dcc.Checklist(
        id=cid,
        options=[{"label": f"  {o}", "value": o} for o in options],
        value=value,
        className="pill-checklist",
        inline=True,
    )


# ── LAYOUT ────────────────────────────────────────────────────
app.layout = html.Div(id="root-wrapper", className="dark-mode", children=[

    # ── TOP BAR ───────────────────────────────────────────────
    html.Header(className="top-bar", children=[
        html.Div(className="logo-area", children=[
            html.Span("♫", className="logo-icon"),
            html.Span("Spotify Analytics", className="logo-text"),
        ]),
        html.Div(className="header-right", children=[
            html.Span("Mode:", className="theme-label"),
            dcc.RadioItems(
                id="theme-toggle",
                options=[{"label": "🌙 Dark",  "value": "dark"},
                         {"label": "☀️ Light", "value": "light"}],
                value="dark", className="theme-radio", inline=True,
            ),
        ]),
    ]),

    # ── FILTER PANEL — 4 filters evenly distributed ───────────
    html.Div(className="filter-panel", children=[

        # Tempo
        html.Div(className="filter-group", children=[
            html.Div(className="filter-icon-label", children=[
                html.Span("🥁", className="filter-icon"),
                html.Label("Tempo", className="filter-label"),
            ]),
            pill_checklist("tempo-filter", ALL_TEMPO_CATS, ALL_TEMPO_CATS),
        ]),

        html.Div(className="filter-divider"),

        # Duration
        html.Div(className="filter-group", children=[
            html.Div(className="filter-icon-label", children=[
                html.Span("⏱️", className="filter-icon"),
                html.Label("Duration", className="filter-label"),
            ]),
            pill_checklist("duration-filter", ALL_DUR_CATS, ALL_DUR_CATS),
        ]),

        html.Div(className="filter-divider"),

        # Loudness
        html.Div(className="filter-group", children=[
            html.Div(className="filter-icon-label", children=[
                html.Span("🔊", className="filter-icon"),
                html.Label("Loudness", className="filter-label"),
            ]),
            pill_checklist("loudness-filter", ALL_LOUD_LEVELS, ALL_LOUD_LEVELS),
        ]),

        html.Div(className="filter-divider"),

        # Content Type
        html.Div(className="filter-group filter-group--content", children=[
            html.Div(className="filter-icon-label", children=[
                html.Span("🎵", className="filter-icon"),
                html.Label("Content Type", className="filter-label"),
            ]),
            dcc.RadioItems(
                id="content-radio",
                options=[
                    {"label": "  All",          "value": "All"},
                    {"label": "  Explicit",     "value": "Explicit"},
                    {"label": "  Non-Explicit", "value": "Non-Explicit"},
                ],
                value="All",
                className="content-radio",
                inline=True,
            ),
        ]),

        html.Div(className="filter-divider"),

        # Reset button
        html.Div(className="filter-group filter-group--reset", children=[
            html.Button(
                "↺  Reset",
                id="reset-btn",
                className="reset-btn",
                n_clicks=0,
            ),
        ]),
    ]),

    # ── TITLE BLOCK ───────────────────────────────────────────
    html.Div(className="title-block", children=[
        html.H1("Spotify Trends Analytics Dashboard", className="main-title"),
        html.P(
            "Interactive insights across genres, audio features, and listener "
            "engagement  •  Data: data_preprocessed.csv",
            className="main-subtitle",
        ),
    ]),

    # ── KPI ROW ───────────────────────────────────────────────
    html.Div(className="kpi-row", children=[
        kpi_card("🎧", "Total Tracks",         "kpi-tracks",     "kpi--green"),
        kpi_card("🎼", "Genres Covered",       "kpi-genres",     "kpi--blue"),
        kpi_card("⭐", "Avg Popularity",       "kpi-popularity", "kpi--orange"),
        kpi_card("🔥", "Avg Engagement Score", "kpi-engagement", "kpi--purple"),
    ]),

    # ── 01 GENRE PERFORMANCE ──────────────────────────────────
    sec("01", "Genre Performance Overview",
        "Column Chart: Avg Popularity by Genre  •  Bar Chart: Top Artists by Song Count"),
    html.Div(className="chart-grid two-col", children=[
        gc("chart-col-popularity"),
        gc("chart-bar-artists"),
    ]),

    # ── 02 CONTENT & POPULARITY DISTRIBUTION ──────────────────
    sec("02", "Content & Popularity Distribution",
        "Stacked Column Chart: Popularity Tiers  •  Stacked Bar Chart: Explicit Content"),
    html.Div(className="chart-grid two-col", children=[
        gc("chart-stacked-col"),
        gc("chart-stacked-bar"),
    ]),

    # ── 03 AUDIO FEATURE BENCHMARKS ───────────────────────────
    sec("03", "Audio Feature Benchmarks",
        "Clustered Column Chart: Energy & Danceability  •  Clustered Bar Chart: Instrumentalness vs Liveness"),
    html.Div(className="chart-grid two-col", children=[
        gc("chart-clustered-col"),           # vertical Clustered Column Chart
        gc("chart-clustered-bar"),
    ]),

    # ── 04 RELATIONSHIP ANALYSIS ──────────────────────────────
    sec("04", "Relationship Analysis",
        "Scatter Chart: Energy vs Danceability  •  Bubble Chart: Genre Positioning"),
    html.Div(className="chart-grid two-col", children=[
        gc("chart-scatter"),
        gc("chart-bubble", h="430px"),
    ]),

    # ── 05 STATISTICAL DISTRIBUTIONS ─────────────────────────
    sec("05", "Statistical Distributions",
        "Histogram: Duration  •  Box Plot: Loudness  •  Violin Plot: Valence"),
    html.Div(className="chart-grid three-col", children=[
        gc("chart-histogram"),
        gc("chart-box"),
        gc("chart-violin"),
    ]),

    # ── 06 TREND & ENGAGEMENT ANALYSIS ───────────────────────
    sec("06", "Trend & Engagement Analysis",
        "Line Chart: Tempo Trend by Genre Rank  •  Area Chart: Engagement by Popularity Tier"),
    html.Div(className="chart-grid two-col", children=[
        gc("chart-line"),
        gc("chart-area"),
    ]),

    # ── FOOTER ───────────────────────────────────────────────
    html.Footer(className="footer", children=[
        html.Div(className="footer-inner", children=[
            html.Span("♫  Spotify Trends Analytics Dashboard",
                      className="footer-brand"),
            html.Span("Built with Dash & Plotly  •  Portfolio Project",
                      className="footer-note"),
            html.Span("Source: data_preprocessed.csv",
                      className="footer-source"),
        ]),
    ]),

    dcc.Store(id="theme-store", data="dark"),
])


# ══════════════════════════════════════════════════════════════
# 5.  CALLBACKS
# ══════════════════════════════════════════════════════════════
# TOP_N=10 is hardcoded in every genre chart — no slider input needed
_INPUTS = [
    Input("tempo-filter",    "value"),
    Input("duration-filter", "value"),
    Input("loudness-filter", "value"),
    Input("content-radio",   "value"),
    Input("theme-store",     "data"),
]

# ── Theme ──────────────────────────────────────────────────────
@app.callback(Output("theme-store",  "data"),
              Input("theme-toggle",  "value"))
def store_theme(v): return v

@app.callback(Output("root-wrapper", "className"),
              Input("theme-store",   "data"))
def toggle_class(t): return "dark-mode" if t == "dark" else "light-mode"


# ── Reset — only 4 filter controls remain (no slider)
@app.callback(
    Output("tempo-filter",    "value"),
    Output("duration-filter", "value"),
    Output("loudness-filter", "value"),
    Output("content-radio",   "value"),
    Input("reset-btn",        "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    return ALL_TEMPO_CATS, ALL_DUR_CATS, ALL_LOUD_LEVELS, "All"


# ── KPIs — compact number formatting ──────────────────────────
@app.callback(
    Output("kpi-tracks",     "children"),
    Output("kpi-genres",     "children"),
    Output("kpi-popularity", "children"),
    Output("kpi-engagement", "children"),
    Input("tempo-filter",    "value"),
    Input("duration-filter", "value"),
    Input("loudness-filter", "value"),
    Input("content-radio",   "value"),
)
def update_kpis(tc, dc, lc, content):
    d = fdf(tc, dc, lc, content)
    if d.empty:
        return "0", "0", "—", "—"
    return (
        compact_num(len(d)),                          # e.g. 114.3K
        str(d["track_genre"].nunique()),
        f"{d['popularity'].mean():.1f}",
        f"{d['engagement_score'].mean():.1f}",
    )


# ── A — Column Chart: Avg Popularity by Genre ────────────────
#        Simple vertical columns, single metric, no grouping/stacking
@app.callback(Output("chart-col-popularity", "figure"), *_INPUTS)
def chart_a(tc, dc, lc, content, theme):
    d = fdf(tc, dc, lc, content)
    if d.empty: return go.Figure()
    # Top 10 genres by average popularity, sorted descending left→right
    agg = (d.groupby("track_genre")["popularity"].mean()
             .reset_index()
             .sort_values("popularity", ascending=False)
             .head(TOP_N))
    n = len(agg)
    # Gradient: darkest green at rank 1, lighter at rank 10
    colours = [
        f"rgba(29, {int(185 * (n - i) / max(n - 1, 1))}, "
        f"{int(84  * (n - i) / max(n - 1, 1))}, 0.90)"
        for i in range(n)
    ]
    fig = go.Figure(go.Bar(
        x=agg["track_genre"],
        y=agg["popularity"].round(1),
        orientation="v",                          # vertical columns
        marker=dict(color=colours, line=dict(width=0)),
        text=agg["popularity"].round(1),
        textposition="outside",
        textfont=dict(size=10, color=WHITE_DIM),
        hovertemplate="<b>%{x}</b><br>Avg Popularity: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(
        showlegend=False,
        yaxis_range=[0, 115],          # headroom for outside labels
        xaxis=dict(tickangle=-35, automargin=True),
        margin=dict(l=60, r=24, t=72, b=80),
    )
    return stamp(fig,
                 "Avg Popularity by Genre",
                 T(theme), "Genre", "Avg Popularity Score")


# ── B — Bar Chart: Top Artists by Song Count ─────────────────
#        Horizontal bar chart — single metric, no grouping/stacking
@app.callback(Output("chart-bar-artists", "figure"), *_INPUTS)
def chart_b(tc, dc, lc, content, theme):
    d = fdf(tc, dc, lc, content)
    if d.empty: return go.Figure()
    agg = (d.groupby("artists")["artist_song_count"].max()
             .reset_index()
             .sort_values("artist_song_count", ascending=True)
             .tail(TOP_N))
    fig = go.Figure(go.Bar(
        y=agg["artists"], x=agg["artist_song_count"],
        orientation="h",
        marker=dict(
            color=agg["artist_song_count"],
            colorscale=[[0, "#2D6A4F"], [0.55, "#52B788"], [1, "#1DB954"]],
            line=dict(width=0),
        ),
        text=agg["artist_song_count"],
        textposition="outside",
        textfont=dict(size=10, color=WHITE_DIM),
        hovertemplate="<b>%{y}</b><br>Songs: %{x}<extra></extra>",
    ))
    fig.update_layout(coloraxis_showscale=False, showlegend=False)
    return stamp(fig, f"Top {TOP_N} Artists by Song Count",
                 T(theme), "Number of Tracks", "")


# ── C — Stacked Column: Popularity Tier Mix by Genre ─────────
@app.callback(Output("chart-stacked-col", "figure"), *_INPUTS)
def chart_c(tc, dc, lc, content, theme):
    d = top_genres(fdf(tc, dc, lc, content), TOP_N)
    if d.empty: return go.Figure()

    genre_order = (d["track_genre"].value_counts()
                     .sort_values(ascending=False).index.tolist())
    tiers_present = [p for p in POP_ORDER if p in d["popularity_level"].unique()]

    # Softer border colour — dark separator between stacked segments
    seg_border = dict(width=1, color="rgba(0,0,0,0.35)")

    fig = go.Figure()
    for tier in tiers_present:
        sub = (d[d["popularity_level"] == tier]
               .groupby("track_genre").size()
               .reindex(genre_order, fill_value=0)
               .reset_index(name="count"))
        fig.add_trace(go.Bar(
            x=sub["track_genre"],
            y=sub["count"],
            name=tier,
            marker=dict(
                color=POP_PALETTE[tier],
                opacity=0.88,              # slightly softer than full saturation
                line=seg_border,           # subtle segment separator
            ),
            hovertemplate=f"<b>%{{x}}</b><br>{tier}: %{{y:,}}<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        legend=dict(**_LEG_TOP),           # legend ABOVE the chart
        xaxis=dict(tickangle=-40, automargin=True),
        margin=dict(l=60, r=24, t=92, b=72),   # t=92 gives room for top legend
    )
    return stamp(fig, "Popularity Tier Mix by Genre",
                 T(theme), "", "Track Count")


# ── D — Stacked Bar: Content Explicitness by Genre ───────────
@app.callback(Output("chart-stacked-bar", "figure"), *_INPUTS)
def chart_d(tc, dc, lc, content, theme):
    d = top_genres(fdf(tc, dc, lc, content), TOP_N)
    if d.empty:
        return go.Figure()

    genre_order = (
        d["track_genre"]
        .value_counts()
        .sort_values(ascending=False)
        .index.tolist()
    )

    label_order = ["Non-Explicit", "Explicit"]
    labels_present = [
        label for label in label_order
        if label in d["explicit_label"].unique()
    ]

    colors = {
        "Non-Explicit": "#1DB954",
        "Explicit": "#9B5DE5",
    }

    fig = go.Figure()

    for label in labels_present:
        sub = (
            d[d["explicit_label"] == label]
            .groupby("track_genre")
            .size()
            .reindex(genre_order, fill_value=0)
            .reset_index(name="count")
        )

        fig.add_trace(go.Bar(
            y=sub["track_genre"],
            x=sub["count"],
            name=label,
            orientation="h",
            marker=dict(
                color=colors[label],
                opacity=0.90,
                line=dict(
                    width=0.8,
                    color="rgba(255,255,255,0.16)"
                ),
            ),
            hovertemplate=f"<b>%{{y}}</b><br>{label}: %{{x:,}} tracks<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        legend=dict(**_LEG_TOP),
        margin=dict(l=60, r=24, t=92, b=50),
    )

    return stamp(
        fig,
        "Content Explicitness by Genre",
        T(theme),
        "Track Count",
        ""
    )

# ── E — Clustered Column Chart: Energy & Danceability by Genre ─
#        Grouped VERTICAL columns, barmode="group" — proper clustered column
@app.callback(Output("chart-clustered-col", "figure"), *_INPUTS)
def chart_e(tc, dc, lc, content, theme):
    d = top_genres(fdf(tc, dc, lc, content), TOP_N)
    if d.empty: return go.Figure()
    agg = (d.groupby("track_genre")[["energy", "danceability"]]
             .mean().reset_index()
             .sort_values("energy", ascending=False))   # highest energy left→right

    ENERGY_CLR = S_GREEN    # Spotify green
    DANCE_CLR  = "#2EC4B6"  # vivid purple — max contrast against green

    fig = go.Figure([
        go.Bar(
            x=agg["track_genre"],
            y=agg["energy"].round(3),
            name="⚡ Energy",
            orientation="v",                           # VERTICAL columns
            marker=dict(color=ENERGY_CLR, opacity=0.92, line=dict(width=0)),
            text=agg["energy"].round(2),
            textposition="outside",
            textfont=dict(size=9, color=WHITE_DIM if theme == "dark" else "#444"),
        ),
        go.Bar(
            x=agg["track_genre"],
            y=agg["danceability"].round(3),
            name="💃 Danceability",
            orientation="v",                           # VERTICAL columns
            marker=dict(color=DANCE_CLR, opacity=0.92, line=dict(width=0)),
            text=agg["danceability"].round(2),
            textposition="outside",
            textfont=dict(size=9, color=WHITE_DIM if theme == "dark" else "#444"),
        ),
    ])
    fig.update_layout(
        barmode="group",                               # side-by-side grouped
        yaxis_range=[0, 1.22],                         # headroom for outside labels
        xaxis=dict(tickangle=-35, automargin=True),
        legend=dict(
            orientation="v",
            bgcolor="rgba(20,20,20,0.70)" if theme == "dark"
                    else "rgba(255,255,255,0.85)",
            font=dict(size=11, color=WHITE if theme == "dark" else "#111"),
            itemsizing="constant",
            x=0.99, y=0.99,
            xanchor="right", yanchor="top",
            bordercolor=GRID_CLR, borderwidth=1,
        ),
        margin=dict(l=60, r=24, t=72, b=85),
    )
    return stamp(fig,
                 "Energy vs Danceability by Genre",
                 T(theme), "Genre", "Score (0 – 1)")


# ── F — Clustered Bar: Instrumentalness vs Liveness by Tier ──
#        Replaces Mood & Engagement — more differentiated values,
#        stronger visual contrast, cleaner professional look.
@app.callback(Output("chart-clustered-bar", "figure"), *_INPUTS)
def chart_f(tc, dc, lc, content, theme):
    d = fdf(tc, dc, lc, content)
    if d.empty: return go.Figure()
    order = [x for x in POP_ORDER if x in d["popularity_level"].unique()]
    agg = (d.groupby("popularity_level")[["instrumentalness", "liveness"]]
             .mean()
             .reindex(order)
             .reset_index())

    txt_clr = WHITE_DIM if theme == "dark" else "#444"

    fig = go.Figure([
        go.Bar(
            y=agg["popularity_level"],
            x=agg["instrumentalness"].round(4),
            name="🎸 Instrumentalness",
            orientation="h",
            marker=dict(
                color=CLR_INSTR,
                opacity=0.90,
                line=dict(width=1, color="rgba(0,0,0,0.25)"),
            ),
            text=agg["instrumentalness"].apply(lambda v: f"{v:.3f}"),
            textposition="outside",
            textfont=dict(size=10, color=txt_clr),
            hovertemplate="<b>%{y}</b><br>Instrumentalness: %{x:.4f}<extra></extra>",
        ),
        go.Bar(
            y=agg["popularity_level"],
            x=agg["liveness"].round(4),
            name="🎤 Liveness",
            orientation="h",
            marker=dict(
                color=CLR_LIVE,
                opacity=0.90,
                line=dict(width=1, color="rgba(0,0,0,0.25)"),
            ),
            text=agg["liveness"].apply(lambda v: f"{v:.3f}"),
            textposition="outside",
            textfont=dict(size=10, color=txt_clr),
            hovertemplate="<b>%{y}</b><br>Liveness: %{x:.4f}<extra></extra>",
        ),
    ])

    # Compute right x-axis bound with headroom for outside text labels
    max_val = max(agg["instrumentalness"].max(), agg["liveness"].max())
    fig.update_layout(
        barmode="group",
        xaxis_range=[0, min(max_val * 1.45, 1.0)],   # cap at 1.0 (normalised)
        legend=dict(**_LEG_TOP),                       # legend ABOVE chart
        margin=dict(l=60, r=24, t=92, b=50),
    )
    return stamp(fig,
                 "Instrumentalness vs Liveness by Popularity Tier",
                 T(theme), "Score (0 – 1)", "")


# ── G — Scatter: Energy vs Danceability (by Popularity Tier) ─
@app.callback(Output("chart-scatter", "figure"), *_INPUTS)
def chart_g(tc, dc, lc, content, theme):
    d = safe_sample(fdf(tc, dc, lc, content), 3000, 42)
    if d.empty:
        return go.Figure()

    scatter_palette = {
        "Low": "#4C78A8",      # muted blue
        "Medium": "#1DB954",   # Spotify green
        "High": "#9B5DE5",     # soft purple
        "Very High": "#FACC15"
    }

    fig = px.scatter(
        d,
        x="energy",
        y="danceability",
        color="popularity_level",
        color_discrete_map=scatter_palette,
        category_orders={"popularity_level": POP_ORDER},
        opacity=0.48,
        hover_data={
            "track_name": True,
            "artists": True,
            "energy": ":.2f",
            "danceability": ":.2f",
            "popularity_level": True
        },
        labels={
            "energy": "Energy",
            "danceability": "Danceability",
            "popularity_level": "Popularity Tier"
        },
    )

    fig.update_traces(
        marker=dict(
            size=5.5,
            line=dict(
                width=0.4,
                color="rgba(255,255,255,0.25)" if theme == "dark" else "rgba(0,0,0,0.20)"
            )
        )
    )

    ref = "rgba(255,255,255,0.13)" if theme == "dark" else "rgba(0,0,0,0.13)"

    fig.add_hline(
        y=0.5,
        line=dict(color=ref, dash="dot", width=1)
    )

    fig.add_vline(
        x=0.5,
        line=dict(color=ref, dash="dot", width=1)
    )

    fig.update_layout(
        legend=dict(**_LEG_BR)
    )

    return stamp(
        fig,
        "Energy vs Danceability by Popularity Tier",
        T(theme),
        "Energy",
        "Danceability"
    )


# ── H — Bubble: Genre Positioning ────────────────────────────
@app.callback(Output("chart-bubble", "figure"), *_INPUTS)
def chart_h(tc, dc, lc, content, theme):
    raw = fdf(tc, dc, lc, content)
    if raw.empty: return go.Figure()
    agg = (raw.groupby("track_genre")
               .agg(avg_tempo=("tempo", "mean"),
                    avg_popularity=("popularity", "mean"),
                    avg_engagement=("engagement_score", "mean"),
                    track_count=("track_name", "count"))
               .reset_index()
               .nlargest(TOP_N, "track_count")
               .reset_index(drop=True))

    # Larger bubbles now that we're capped at exactly TOP_N=10: [18, 50]
    eng = agg["avg_engagement"]
    agg["bubble_size"] = 18 + 32 * (eng - eng.min()) / (eng.max() - eng.min() + 1e-9)

    fig = go.Figure()
    for i, row in agg.iterrows():
        colour = CHART_PAL[i % len(CHART_PAL)]
        fig.add_trace(go.Scatter(
            x=[row["avg_tempo"]],
            y=[row["avg_popularity"]],
            mode="markers+text",
            name=row["track_genre"],
            text=[f"<b>{row['track_genre']}</b>"],
            textposition="top center",          # uniform — all above the bubble
            textfont=dict(size=10, color=WHITE if theme == "dark" else "#111"),
            marker=dict(
                size=row["bubble_size"],
                color=colour,
                opacity=0.82,
                line=dict(width=1.5, color="rgba(0,0,0,0.28)"),
            ),
            hovertemplate=(
                f"<b>{row['track_genre']}</b><br>"
                f"Avg Tempo: {row['avg_tempo']:.1f} BPM<br>"
                f"Avg Popularity: {row['avg_popularity']:.1f}<br>"
                f"Avg Engagement: {row['avg_engagement']:.1f}<br>"
                f"Tracks: {row['track_count']:,}"
                "<extra></extra>"
            ),
        ))

    # Wide axis padding so "top center" labels at the top edge aren't clipped
    x_pad = (agg["avg_tempo"].max() - agg["avg_tempo"].min()) * 0.16 + 8
    y_pad = (agg["avg_popularity"].max() - agg["avg_popularity"].min()) * 0.28 + 8
    fig.update_layout(
        showlegend=False,
        xaxis=dict(range=[agg["avg_tempo"].min() - x_pad,
                          agg["avg_tempo"].max() + x_pad]),
        yaxis=dict(range=[agg["avg_popularity"].min() - y_pad,
                          agg["avg_popularity"].max() + y_pad]),
    )
    return stamp(fig,
                 f"Top {TOP_N} Genres: Tempo × Popularity  (size = Engagement)",
                 T(theme), "Average Tempo (BPM)", "Average Popularity")

# ── I — Histogram: Track Duration Distribution ───────────────
@app.callback(Output("chart-histogram", "figure"), *_INPUTS)
def chart_i(tc, dc, lc, content, theme):

    d = fdf(tc, dc, lc, content)

    if d.empty:
        return go.Figure()

    fig = px.histogram(
        d,
        x="duration_min",
        nbins=40,
        color_discrete_sequence=[PRIMARY_GREEN],
        labels={
            "duration_min": "Duration (min)"
        },
    )

    fig.update_traces(
        marker_line_color="rgba(0,0,0,0.30)",
        marker_line_width=0.5,
        opacity=0.88,
    )

    med = d["duration_min"].median()
    mean = d["duration_min"].mean()

    # ── Median Line ─────────────────────────────
    fig.add_shape(
        type="line",
        x0=med,
        x1=med,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(
            color=YELLOW_ACCENT,
            dash="dash",
            width=2.2
        )
    )

    # ── Mean Line ───────────────────────────────
    fig.add_shape(
        type="line",
        x0=mean,
        x1=mean,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(
            color=PURPLE_ACCENT,
            dash="dot",
            width=2.2
        )
    )

    # ── Median Annotation ──────────────────────
    fig.add_annotation(
        x=med,
        xref="x",
        y=1.0,
        yref="paper",
        text=f"<b>Median<br>{med:.2f} min</b>",
        showarrow=True,
        arrowhead=2,
        arrowwidth=1.5,
        arrowcolor=YELLOW_ACCENT,
        ax=30,
        ay=0,
        font=dict(
            color=YELLOW_ACCENT,
            size=10,
            family="'Outfit', sans-serif"
        ),
        bgcolor="rgba(26,26,26,0.78)"
            if theme == "dark"
            else "rgba(255,255,255,0.88)",
        bordercolor=YELLOW_ACCENT,
        borderwidth=1,
        borderpad=4,
        align="left",
    )

    # ── Mean Annotation ────────────────────────
    fig.add_annotation(
        x=mean,
        xref="x",
        y=0.78,
        yref="paper",
        text=f"<b>Mean<br>{mean:.2f} min</b>",
        showarrow=True,
        arrowhead=2,
        arrowwidth=1.5,
        arrowcolor=PURPLE_ACCENT,
        ax=-30,
        ay=0,
        font=dict(
            color=PURPLE_ACCENT,
            size=10,
            family="'Outfit', sans-serif"
        ),
        bgcolor="rgba(26,26,26,0.78)"
            if theme == "dark"
            else "rgba(255,255,255,0.88)",
        bordercolor=PURPLE_ACCENT,
        borderwidth=1,
        borderpad=4,
        align="right",
    )

    return stamp(
        fig,
        "Track Duration Distribution",
        T(theme),
        "Duration (min)",
        "Track Count"
    )


# ── J — Box: Loudness Profile by Popularity Tier ─────────────
@app.callback(Output("chart-box", "figure"), *_INPUTS)
def chart_j(tc, dc, lc, content, theme):
    d = fdf(tc, dc, lc, content)
    if d.empty: return go.Figure()
    order = [x for x in POP_ORDER if x in d["popularity_level"].unique()]
    fig = px.box(
        d, x="popularity_level", y="loudness",
        color="popularity_level",
        category_orders={"popularity_level": order},
        color_discrete_map=POP_PALETTE,
        notched=True,
        labels={"popularity_level": "", "loudness": "Loudness (dB)"},
    )
    fig.update_traces(marker_size=2, line_width=1.8, showlegend=False)
    return stamp(fig, "Loudness Distribution by Popularity Tier",
                 T(theme), "", "Loudness (dB)")


# ── K — Violin: Emotional Tone (Valence) by Popularity Tier ──
@app.callback(Output("chart-violin", "figure"), *_INPUTS)
def chart_k(tc, dc, lc, content, theme):
    d = fdf(tc, dc, lc, content)
    if d.empty: return go.Figure()
    order = [x for x in POP_ORDER if x in d["popularity_level"].unique()]
    fig = px.violin(
        d, x="popularity_level", y="valence",
        color="popularity_level", box=True, points=False,
        category_orders={"popularity_level": order},
        color_discrete_map=POP_PALETTE,
        labels={"popularity_level": "", "valence": "Valence (0–1)"},
    )
    fig.update_traces(showlegend=False, line_width=1.8)
    return stamp(fig, "Valence (Emotional Tone) by Popularity Tier",
                 T(theme), "", "Valence")


# ── L — Line Chart: Tempo Trend with Moving Average ──────────
@app.callback(Output("chart-line", "figure"), *_INPUTS)
def chart_l(tc, dc, lc, content, theme):
    d = fdf(tc, dc, lc, content)
    if d.empty: return go.Figure()
    agg = (d.groupby("genre_rank")["tempo"].mean()
             .reset_index().sort_values("genre_rank"))
    if agg.empty: return go.Figure()

    ma = rolling_avg(agg["tempo"], window=7)

    fig = go.Figure()

    # Raw line — subtle, thin, low opacity
    fig.add_trace(go.Scatter(
        x=agg["genre_rank"], y=agg["tempo"].round(1),
        mode="lines",
        name="Avg Tempo (raw)",
        line=dict(color="rgba(29,185,84,0.28)", width=1.2),
        hovertemplate="Rank %{x}<br>Tempo: %{y:.1f} BPM<extra></extra>",
    ))

    # Moving-average — bold, thick, filled area — clearly dominant line
    fig.add_trace(go.Scatter(
        x=agg["genre_rank"], y=ma.round(1),
        mode="lines",
        name="7-pt Moving Avg",
        line=dict(color=S_GREEN, width=3.5),   # thicker than raw (1.2)
        fill="tozeroy",
        fillcolor="rgba(29,185,84,0.08)",
        hovertemplate="Rank %{x}<br>MA: %{y:.1f} BPM<extra></extra>",
    ))

    # ── Peak annotation: find the REAL maximum of raw avg tempo ──
    # Use the raw series (agg) — not the smoothed MA — for the true peak
    peak_pos  = agg["tempo"].idxmax()                  # integer index in agg
    peak_rank = agg.loc[peak_pos, "genre_rank"]        # x-value (rank)
    peak_val  = agg.loc[peak_pos, "tempo"]             # y-value (real tempo)

    fig.add_trace(go.Scatter(
    x=[peak_rank], y=[peak_val],
    mode="markers",
    name="Peak",
    marker=dict(
        color=YELLOW_ACCENT,
        size=10,
        symbol="star",
        line=dict(color=WHITE, width=1.5)
    ),
    hovertemplate=f"Peak: {peak_val:.1f} BPM @ Rank {peak_rank}<extra></extra>",
    showlegend=True,
))

    fig.add_annotation(
    x=peak_rank,
    y=peak_val,
    text=f"<b>▲ Peak<br>{peak_val:.0f} BPM</b>",
    showarrow=True,
    arrowhead=2,
    arrowwidth=1.8,
    arrowcolor=YELLOW_ACCENT,
    ax=40,
    ay=-38,
    font=dict(
        color=MINT,
        size=11,
        family="'Outfit', sans-serif"
    ),
    bgcolor="rgba(26,26,26,0.80)" if theme == "dark"
             else "rgba(255,255,255,0.85)",
    bordercolor=YELLOW_ACCENT,
    borderwidth=1,
    borderpad=4,
)

    fig.update_layout(legend=dict(**_LEG_BR))
    return stamp(fig,
                 "Avg Tempo by Genre Rank  (7-pt Moving Avg)",
                 T(theme), "Genre Rank →", "Avg Tempo (BPM)")


# ── M — Area: Engagement Performance by Popularity Tier ──────
@app.callback(Output("chart-area", "figure"), *_INPUTS)
def chart_m(tc, dc, lc, content, theme):
    d = fdf(tc, dc, lc, content)
    if d.empty: return go.Figure()
    order = [x for x in POP_ORDER if x in d["popularity_level"].unique()]
    agg = (d.groupby("popularity_level")["engagement_score"]
             .mean().reindex(order).dropna().reset_index())
    if agg.empty: return go.Figure()

    y_min = agg["engagement_score"].min()
    y_max = agg["engagement_score"].max()
    spread = y_max - y_min

    # True auto-scale: if data is very flat (spread < 0.05),
    # force a ±0.05 window; otherwise pad 35% each side
    if spread < 0.05:
        y_lo = y_min - 0.05
        y_hi = y_max + 0.08   # extra room for annotations
    else:
        y_lo = y_min - spread * 0.35
        y_hi = y_max + spread * 0.50

    fig = px.area(
        agg, x="popularity_level", y="engagement_score",
        color_discrete_sequence=[TEAL],
        markers=True,
        labels={"popularity_level": "Popularity Tier",
                "engagement_score": "Avg Engagement Score"},
    )
    fig.update_traces(
        line=dict(width=2.5),
        marker=dict(size=9, color=MINT, line=dict(width=2, color=WHITE)),
        fillcolor="rgba(82,183,136,0.18)",
    )
    for _, row in agg.iterrows():
        fig.add_annotation(
            x=row["popularity_level"], y=row["engagement_score"],
            text=f"<b>{row['engagement_score']:.3f}</b>",
            showarrow=False, yshift=18,
            font=dict(color=MINT, size=12, family="'Outfit', sans-serif"),
        )
    fig.update_yaxes(range=[y_lo, y_hi], autorange=False)
    return stamp(fig, "Engagement Score by Popularity Tier",
                 T(theme), "Popularity Tier", "Avg Engagement Score")


# ══════════════════════════════════════════════════════════════
# 6.  RUN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=8050)