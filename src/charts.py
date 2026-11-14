"""Interactive Plotly telemetry visualisations for NovaMind AI — Flame in Freefall."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------- Orbital Telemetry Color Palette ----------------
GRAVITY_COLORS: dict[str, str] = {
    "microgravity": "#00E5FF",   # Neon Cyan (Spherical µg diffusion flame)
    "ground (1g)":  "#FF6B2B",   # Plasma Flame Orange (Buoyant 1g flame)
}

FUEL_CLASS_SYMBOLS: dict[str, str] = {
    "liquid": "circle",
    "gas":    "diamond",
    "solid":  "square",
}

PRETTY_LABELS: dict[str, str] = {
    "oxygen_pct": "Oxygen Concentration (%)",
    "flame_spread_rate_mm_s": "Flame Spread Rate (mm/s)",
    "radiative_loss_fraction": "Radiative Loss Fraction (χr)",
    "soot_volume_fraction_ppm": "Soot Volume Fraction (ppm)",
    "burn_duration_s": "Burn Duration (s)",
    "peak_temperature_k": "Peak Temperature (K)",
    "pressure_kpa": "Cabin Pressure (kPa)",
    "gravity_level": "Gravity Regime",
    "fuel_class": "Fuel Class",
    "experiment_id": "Experiment ID",
    "rank_score": "Composite Score (0–1)",
}


def _color_map_for(df: pd.DataFrame) -> dict[str, str]:
    """Builds a dynamic color map that guarantees microgravity is cyan and 1g is flame orange."""
    cmap = dict(GRAVITY_COLORS)
    if "gravity_level" in df.columns:
        for val in df["gravity_level"].dropna().unique():
            s = str(val)
            if s not in cmap:
                if any(k in s.lower() for k in ("micro", "µg", "ug", "0g", "free")):
                    cmap[s] = "#00E5FF"
                else:
                    cmap[s] = "#FF6B2B"
    return cmap


def scatter_oxygen_vs_spread(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of Oxygen % vs. Flame Spread Rate with ISS 21% O2 cabin reference."""
    d = df.dropna(subset=["oxygen_pct", "flame_spread_rate_mm_s"]).copy()

    hover_cols = [
        c for c in ["experiment_id", "fuel", "pressure_kpa", "peak_temperature_k", "facility"]
        if c in d.columns
    ]

    fig = px.scatter(
        d,
        x="oxygen_pct",
        y="flame_spread_rate_mm_s",
        color="gravity_level",
        symbol="fuel_class" if "fuel_class" in d.columns else None,
        color_discrete_map=_color_map_for(d),
        symbol_map=FUEL_CLASS_SYMBOLS,
        hover_data=hover_cols,
        labels=PRETTY_LABELS,
    )

    fig.update_traces(
        marker=dict(
            size=11,
            opacity=0.88,
            line=dict(width=1.2, color="rgba(255, 255, 255, 0.85)"),
        )
    )

    # Add ISS Nominal Cabin Oxygen (21% O2) reference line
    if not d.empty and d["oxygen_pct"].min() <= 21.0 <= d["oxygen_pct"].max():
        fig.add_vline(
            x=21.0,
            line_width=1.5,
            line_dash="dash",
            line_color="rgba(255, 184, 0, 0.65)",
            annotation_text="ISS Nominal O₂ (21%)",
            annotation_position="top right",
            annotation_font=dict(size=11, color="#FFB800", family="JetBrains Mono, monospace"),
        )

    fig.update_layout(height=420)
    return fig


def box_by_gravity(df: pd.DataFrame, y: str, title: str) -> go.Figure:
    """Box + jittered telemetry distribution plot with notched medians and mean lines."""
    d = df.dropna(subset=[y]).copy()

    hover_cols = [c for c in ["experiment_id", "fuel", "oxygen_pct"] if c in d.columns]

    fig = px.box(
        d,
        x="gravity_level",
        y=y,
        color="gravity_level",
        color_discrete_map=_color_map_for(d),
        points="all",
        notched=True,
        hover_data=hover_cols,
        title=title,
        labels={**PRETTY_LABELS, y: PRETTY_LABELS.get(y, y)},
    )

    fig.update_traces(
        boxmean=True,
        jitter=0.35,
        pointpos=-1.6,
        marker=dict(
            opacity=0.65,
            size=6,
            line=dict(width=0.6, color="rgba(255, 255, 255, 0.6)"),
        ),
        line=dict(width=2),
    )

    fig.update_layout(showlegend=False, height=370)
    return fig


def grouped_bar_by_fuel(df: pd.DataFrame, y: str, title: str) -> go.Figure:
    """Grouped bar chart comparing mean combustion metrics across fuel classes and gravity."""
    d = df.dropna(subset=[y]).copy()
    agg = d.groupby(["fuel_class", "gravity_level"], as_index=False)[y].mean()

    fig = px.bar(
        agg,
        x="fuel_class",
        y=y,
        color="gravity_level",
        color_discrete_map=_color_map_for(d),
        barmode="group",
        text_auto=".2f",
        title=title,
        labels={**PRETTY_LABELS, y: PRETTY_LABELS.get(y, y)},
    )

    fig.update_traces(
        textposition="outside",
        marker_line_color="rgba(255, 255, 255, 0.25)",
        marker_line_width=1,
    )
    fig.update_layout(height=380)
    return fig


def soot_vs_radiative_loss(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of Soot Volume Fraction vs. Radiative Loss with quenching threshold."""
    d = df.dropna(subset=["soot_volume_fraction_ppm", "radiative_loss_fraction"]).copy()

    hover_cols = [
        c for c in ["experiment_id", "fuel", "oxygen_pct", "pressure_kpa"]
        if c in d.columns
    ]

    fig = px.scatter(
        d,
        x="soot_volume_fraction_ppm",
        y="radiative_loss_fraction",
        color="gravity_level",
        symbol="fuel_class" if "fuel_class" in d.columns else None,
        color_discrete_map=_color_map_for(d),
        symbol_map=FUEL_CLASS_SYMBOLS,
        hover_data=hover_cols,
        labels=PRETTY_LABELS,
    )

    fig.update_traces(
        marker=dict(
            size=10,
            opacity=0.85,
            line=dict(width=1.1, color="rgba(255, 255, 255, 0.8)"),
        )
    )

    # Add Radiative Quenching Threshold zone (chi_r >= 0.45)
    if not d.empty and d["radiative_loss_fraction"].max() >= 0.42:
        fig.add_hline(
            y=0.45,
            line_width=1.5,
            line_dash="dot",
            line_color="rgba(255, 107, 43, 0.75)",
            annotation_text="Radiative Quenching Regime (χr ≈ 0.45)",
            annotation_position="top left",
            annotation_font=dict(size=11, color="#FF8E3C", family="JetBrains Mono, monospace"),
        )

    fig.update_layout(height=400)
    return fig


def ranking_bar(ranked: pd.DataFrame, n: int = 10) -> go.Figure:
    """Horizontal leaderboard bar chart for the top-N highest scoring experiments."""
    d = ranked.head(n).sort_values("rank_score", ascending=True).copy()

    hover_cols = [
        c for c in [
            "fuel", "gravity_level", "facility",
            "s_fire_safety", "s_data_quality", "s_microgravity_signal", "s_reproducibility"
        ]
        if c in d.columns
    ]

    fig = px.bar(
        d,
        x="rank_score",
        y="experiment_id",
        orientation="h",
        color="rank_score",
        text="rank_score",
        hover_data=hover_cols,
        color_continuous_scale=[
            [0.0, "#1E293B"],
            [0.45, "#FF6B2B"],
            [0.75, "#FFB800"],
            [1.0, "#00E5FF"],
        ],
        labels={"rank_score": "Composite Priority Score (0–1)", "experiment_id": ""},
    )

    fig.update_traces(
        texttemplate="%{text:.3f}",
        textposition="outside",
        textfont=dict(family="JetBrains Mono, monospace", size=11, color="#F8FAFC"),
        marker_line_color="rgba(255, 255, 255, 0.2)",
        marker_line_width=1,
        cliponaxis=False,
    )

    max_score = float(d["rank_score"].max()) if not d.empty else 1.0
    fig.update_layout(
        coloraxis_showscale=False,
         yaxis=dict(tickmode="linear", tickfont=dict(family="JetBrains Mono, monospace", size=12)),
        xaxis=dict(range=[0, min(max_score * 1.14, 1.12)]),
        height=390,
    )
    return fig


def score_breakdown(ranked: pd.DataFrame, experiment_id: str) -> go.Figure:
    """Dark-mode telemetry radar chart comparing a single experiment against the cohort mean."""
    matches = ranked.loc[ranked["experiment_id"] == experiment_id]
    row = matches.iloc[0] if not matches.empty else ranked.iloc[0]

    categories = ["Fire-Safety", "Data Quality", "µg Signal", "Reproducibility"]
    metric_cols = ["s_fire_safety", "s_data_quality", "s_microgravity_signal", "s_reproducibility"]

    values = [float(row.get(c, 0.0)) for c in metric_cols]
    cohort_avg = [float(ranked[c].mean()) if c in ranked.columns else 0.0 for c in metric_cols]

    fig = go.Figure()

    # 1. Cohort Average Baseline Polygon
    fig.add_trace(
        go.Scatterpolar(
            r=cohort_avg + [cohort_avg[0]],
            theta=categories + [categories[0]],
            name="Cohort Mean",
            fill="toself",
            fillcolor="rgba(255, 184, 0, 0.08)",
            line=dict(color="rgba(255, 184, 0, 0.65)", width=1.5, dash="dot"),
            marker=dict(color="#FFB800", size=5),
            hovertemplate="%{theta}: %{r:.2f} (Cohort Mean)<extra></extra>",
        )
    )

    # 2. Selected Experiment Polygon
    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            name=str(row["experiment_id"]),
            fill="toself",
            fillcolor="rgba(0, 229, 255, 0.22)",
            line=dict(color="#00E5FF", width=2.5),
            marker=dict(
                color="#00E5FF",
                size=9,
                line=dict(width=1.5, color="#FFFFFF"),
            ),
            hovertemplate="%{theta}: %{r:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(11, 16, 30, 0.65)",
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0.25, 0.50, 0.75, 1.0],
                gridcolor="rgba(255, 255, 255, 0.10)",
                linecolor="rgba(255, 255, 255, 0.15)",
                tickfont=dict(size=9, color="#94A3B8", family="JetBrains Mono, monospace"),
            ),
            angularaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.10)",
                linecolor="rgba(255, 255, 255, 0.20)",
                tickfont=dict(size=11, color="#F8FAFC", family="Space Grotesk, sans-serif"),
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color="#CBD5E1"),
        ),
        title=f"Telemetry Profile — {row['experiment_id']}",
        height=370,
        margin=dict(t=48, b=45, l=35, r=35),
    )
    return fig