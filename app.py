import streamlit as st
import pandas as pd

from src.style import inject_css, style_fig
from src.data import load_experiments, data_source_label
from src.analytics import add_derived, score_experiments, build_insights, insights_to_markdown
from src import charts

# ---------------- Page Configuration ----------------
st.set_page_config(
    page_title="NovaMind AI | Flame in Freefall",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject theme from src/style.py
inject_css()

# ---------------- Load & Derive Data ----------------
df = add_derived(load_experiments())

# ---------------- Sidebar (Mission Control Panel) ----------------
with st.sidebar:
    st.markdown("""
    <div class="nm-sidebar-header">
        <div class="nm-sidebar-badge">ISS // CIR-MDCA</div>
        <h2>🔥 NovaMind AI</h2>
        <p>Microgravity Combustion Telemetry</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔎 Telemetry Filters", expanded=True):
        fuels = sorted(df["fuel"].dropna().unique())
        sel_fuels = st.multiselect("Fuel Type", fuels, default=fuels)

        gravities = sorted(df["gravity_level"].dropna().unique())
        sel_gravity = st.multiselect("Gravity Condition", gravities, default=gravities)

        facilities = sorted(df["facility"].dropna().unique())
        sel_facilities = st.multiselect("Research Facility", facilities, default=facilities)

        if df["oxygen_pct"].notna().any():
            lo, hi = float(df["oxygen_pct"].min()), float(df["oxygen_pct"].max())
            o2_range = st.slider("Oxygen Concentration (%)", lo, hi, (lo, hi))
        else:
            o2_range = (0.0, 100.0)

    with st.expander("⚖️ Ranking Weights", expanded=False):
        st.caption("Adjust priority weights to dynamically recalculate experiment rankings.")
        weights = {
            "Fire-safety relevance": st.slider("Fire-safety relevance", 0.0, 1.0, 0.40, 0.05),
            "Data quality":          st.slider("Data quality",          0.0, 1.0, 0.25, 0.05),
            "Microgravity signal":   st.slider("Microgravity signal",   0.0, 1.0, 0.20, 0.05),
            "Reproducibility":       st.slider("Reproducibility",       0.0, 1.0, 0.15, 0.05),
        }

    # Filter the dataset
    f = df[
        df["fuel"].isin(sel_fuels)
        & df["gravity_level"].isin(sel_gravity)
        & df["facility"].isin(sel_facilities)
    ]
    if df["oxygen_pct"].notna().any():
        f = f[f["oxygen_pct"].between(*o2_range)]

    st.divider()
    sample_ratio = len(f) / max(len(df), 1)
    st.progress(sample_ratio, text=f"Active Cohort: {len(f)} / {len(df)} runs ({sample_ratio*100:.0f}%)")
    st.caption(f"🛰️ **Source:** {data_source_label()}")

# ---------------- Empty Filter Guard ----------------
if f.empty:
    st.warning("⚠️ No experiments match the current filters. Please widen your fuel, gravity, or O₂ selection in the sidebar.")
    st.stop()

ranked = score_experiments(f, weights)

# ---------------- Hero Section ----------------
st.markdown(f"""
<div class="hero">
    <div class="hero-top-row">
        <span class="hero-status"><span class="status-dot"></span>PSI-69 FLEX TELEMETRY ONLINE</span>
        <span class="hero-doi">DOI: 10.60555/mbq8-0451 · CC0-1.0</span>
    </div>
    <h1>🔥 NovaMind AI — Flame in Freefall</h1>
    <p>
        How does fire behave in space? Without buoyant convection, microgravity flames form spherical fronts, 
        spread slowly, and persist at lower oxygen limits. We transform NASA's <strong>FLEX</strong> combustion datasets 
        into clear, auditable fire-safety intelligence for future deep-space crews.
    </p>
    <div class="hero-actions">
        <a class="cta" href="#key-findings">Explore Mission Telemetry ↓</a>
        <span class="hero-chip">🛰️ ISS CIR / MDCA</span>
        <span class="hero-chip">🧪 {len(f)} Active Runs</span>
        <span class="hero-chip">🔥 {len(sel_fuels)} Fuel Types</span>
    </div>
</div>
<div id="key-findings"></div>
""", unsafe_allow_html=True)

# ---------------- KPIs (Custom Glass HUD Cards) ----------------
micro_spread = f.loc[f["is_microgravity"], "flame_spread_rate_mm_s"].mean()
ground_spread = f.loc[~f["is_microgravity"], "flame_spread_rate_mm_s"].mean()
micro_rad = f.loc[f["is_microgravity"], "radiative_loss_fraction"].mean()
comp_pct = f["completeness"].mean() * 100

spread_str = f"{micro_spread:.1f}" if pd.notna(micro_spread) else "—"
delta_str = (
    f"{(micro_spread - ground_spread):+.1f} vs 1g"
    if pd.notna(micro_spread) and pd.notna(ground_spread)
    else "µg cohort"
)
rad_str = f"{micro_rad:.2f}" if pd.notna(micro_rad) else "—"

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="nm-kpi-card accent-cyan">
        <div class="nm-kpi-head">
            <span class="nm-kpi-tag">01 // COHORT</span>
            <span class="nm-kpi-badge">Auditable</span>
        </div>
        <div class="nm-kpi-val">{len(f)} <span class="nm-kpi-unit">runs</span></div>
        <div class="kpi-cap">Evidence base: every insight links directly back to a NASA experiment ID.</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="nm-kpi-card accent-flame">
        <div class="nm-kpi-head">
            <span class="nm-kpi-tag">02 // SPREAD RATE · µg</span>
            <span class="nm-kpi-badge warn">{delta_str}</span>
        </div>
        <div class="nm-kpi-val">{spread_str} <span class="nm-kpi-unit">mm/s</span></div>
        <div class="kpi-cap">Slower flames in space can still spread unpredictably along cabin ventilation flows.</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="nm-kpi-card accent-amber">
        <div class="nm-kpi-head">
            <span class="nm-kpi-tag">03 // RADIATIVE LOSS · µg</span>
            <span class="nm-kpi-badge">Fraction χr</span>
        </div>
        <div class="nm-kpi-val">{rad_str} <span class="nm-kpi-unit">ratio</span></div>
        <div class="kpi-cap">Heat lost as thermal radiation determines whether a spherical flame sustains or quenches.</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="nm-kpi-card accent-emerald">
        <div class="nm-kpi-head">
            <span class="nm-kpi-tag">04 // DATA QUALITY</span>
            <span class="nm-kpi-badge ok">Standardized</span>
        </div>
        <div class="nm-kpi-val">{comp_pct:.0f}% <span class="nm-kpi-unit">complete</span></div>
        <div class="kpi-cap">Cleaned and standardized NASA PSI-69 schema, ready for reproducible research.</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ---------------- Navigation Tabs ----------------
tab_explore, tab_viz, tab_insights, tab_rank, tab_about = st.tabs([
    "📊 Data Explorer",
    "📈 Visualizations",
    "🛟 Fire-Safety Insights",
    "🏆 Experiment Ranking",
    "ℹ️ Methods & About"
])

# === TAB 1: DATA EXPLORER ===
with tab_explore:
    top_l, top_r = st.columns([3, 1])
    with top_l:
        st.subheader("NASA PSI-69 Telemetry Explorer")
        st.caption(f"Showing **{len(f)}** of **{len(df)}** experiments matching active telemetry filters.")
    
    display_cols = [c for c in [
        "experiment_id", "facility", "fuel", "fuel_class", "gravity_level",
        "oxygen_pct", "pressure_kpa", "flame_spread_rate_mm_s", "burn_duration_s", 
        "peak_temperature_k", "soot_volume_fraction_ppm", "radiative_loss_fraction"
    ] if c in f.columns]

    with top_r:
        st.write("")
        st.download_button(
            "⬇️ Download Filtered CSV",
            f[display_cols].to_csv(index=False).encode("utf-8"),
            "novamind_filtered.csv",
            "text/csv",
            use_container_width=True
        )

    st.dataframe(
        f[display_cols],
        use_container_width=True,
        hide_index=True,
        height=450,
        column_config={
            "experiment_id": st.column_config.TextColumn("Experiment ID", width="medium"),
            "facility": st.column_config.TextColumn("Facility"),
            "fuel": st.column_config.TextColumn("Fuel"),
            "fuel_class": st.column_config.TextColumn("Class"),
            "gravity_level": st.column_config.TextColumn("Gravity"),
            "oxygen_pct": st.column_config.ProgressColumn("O₂ (%)", format="%.1f%%", min_value=0, max_value=40),
            "pressure_kpa": st.column_config.NumberColumn("Pressure (kPa)", format="%.1f"),
            "flame_spread_rate_mm_s": st.column_config.NumberColumn("Spread (mm/s)", format="%.2f"),
            "burn_duration_s": st.column_config.NumberColumn("Burn Duration (s)", format="%.1f"),
            "peak_temperature_k": st.column_config.NumberColumn("Peak Temp (K)", format="%.0f K"),
            "soot_volume_fraction_ppm": st.column_config.NumberColumn("Soot (ppm)", format="%.2f"),
            "radiative_loss_fraction": st.column_config.ProgressColumn("Radiative Loss", format="%.2f", min_value=0, max_value=1),
        }
    )

# === TAB 2: VISUALIZATIONS ===
with tab_viz:
    st.subheader("Interactive Combustion Diagnostics")
    st.caption("Compare microgravity (µg) and ground (1g) combustion dynamics across oxygen, radiation, and soot regimes.")

    with st.container(border=True):
        fig1 = charts.scatter_oxygen_vs_spread(f)
        st.plotly_chart(style_fig(fig1, "Oxygen concentration vs Flame spread rate"), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            fig2 = charts.box_by_gravity(f, "flame_spread_rate_mm_s", "Flame spread rate by gravity")
            st.plotly_chart(style_fig(fig2), use_container_width=True)
    with col_b:
        with st.container(border=True):
            fig3 = charts.box_by_gravity(f, "radiative_loss_fraction", "Radiative loss by gravity")
            st.plotly_chart(style_fig(fig3), use_container_width=True)

    with st.container(border=True):
        fig4 = charts.soot_vs_radiative_loss(f)
        st.plotly_chart(style_fig(fig4, "Soot volume fraction vs Radiative loss"), use_container_width=True)

# === TAB 3: FIRE-SAFETY INSIGHTS ===
with tab_insights:
    ins_l, ins_r = st.columns([3, 1])
    with ins_l:
        st.subheader("Automated Fire-Safety Insights")
        st.caption("Evidence-backed findings synthesized from paired microgravity (µg) and terrestrial (1g) runs.")

    insights = build_insights(f)

    with ins_r:
        if insights:
            st.write("")
            st.download_button(
                "⬇️ Export Report (.MD)",
                insights_to_markdown(insights).encode("utf-8"),
                "novamind_insights.md",
                "text/markdown",
                use_container_width=True
            )

    if not insights:
        st.info("Not enough paired data in the current filter view to generate insights. Widen your filter selection.")
    else:
        grid_cols = st.columns(2)
        for idx, ins in enumerate(insights):
            with grid_cols[idx % 2]:
                st.markdown(f"""
                <div class="nm-insight-card">
                    <div class="nm-insight-header">
                        <span class="nm-insight-icon">🛟</span>
                        <h4>{ins['title']}</h4>
                    </div>
                    <p>{ins['body']}</p>
                    <div class="nm-insight-footer">
                        <span>📌 Evidence: {ins['evidence']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.write("")
    st.warning("**Scope note.** These are statistical observations derived from NASA PSI-69 data, not certified spacecraft fire-safety rules.")

# === TAB 4: EXPERIMENT RANKING ===
with tab_rank:
    st.subheader("Multi-Criteria Experiment Ranking")
    st.caption("The composite score is a weighted sum of four transparent criteria. Adjust the priority sliders in the sidebar.")
    
    with st.container(border=True):
        fig5 = charts.ranking_bar(ranked)
        st.plotly_chart(style_fig(fig5, "Top 10 experiments by composite score"), use_container_width=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        with st.container(border=True):
            st.markdown("#### 🔍 Inspect a Specific Run")
            sel = st.selectbox("Select experiment ID", ranked["experiment_id"].tolist(), label_visibility="collapsed")
            fig6 = charts.score_breakdown(ranked, sel)
            st.plotly_chart(style_fig(fig6), use_container_width=True)
        
    with col2:
        with st.container(border=True):
            st.markdown("#### 🏆 Full Experiment Leaderboard")
            detail_cols = [
                "rank", "experiment_id", "rank_score",
                "s_fire_safety", "s_data_quality", "s_microgravity_signal", "s_reproducibility"
            ]
            st.dataframe(
                ranked[detail_cols], 
                use_container_width=True, 
                hide_index=True,
                height=370,
                column_config={
                    "rank": st.column_config.NumberColumn("Rank", format="#%d 🏆", width="small"),
                    "experiment_id": "ID",
                    "rank_score": st.column_config.ProgressColumn("Total Score", format="%.3f", min_value=0, max_value=1),
                    "s_fire_safety": st.column_config.ProgressColumn("Fire Safety", format="%.2f", min_value=0, max_value=1),
                    "s_data_quality": st.column_config.ProgressColumn("Data Quality", format="%.2f", min_value=0, max_value=1),
                    "s_microgravity_signal": st.column_config.ProgressColumn("µg Signal", format="%.2f", min_value=0, max_value=1),
                    "s_reproducibility": st.column_config.ProgressColumn("Repro", format="%.2f", min_value=0, max_value=1),
                }
            )

# === TAB 5: METHODS & ABOUT ===
with tab_about:
    st.subheader("Methods & Data Provenance")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("""
        <div class="nm-info-panel">
            <div class="nm-panel-tag">PRIMARY SOURCE</div>
            <h3>🛰️ NASA PSI-69 — FLEX</h3>
            <p class="nm-panel-sub">Flame Extinguishment Experiment · Physical Sciences Informatics</p>
            <ul class="nm-spec-list">
                <li><strong>Platform:</strong> International Space Station (ISS)</li>
                <li><strong>Hardware:</strong> Combustion Integrated Rack (CIR) / MDCA</li>
                <li><strong>DOI:</strong> <code>10.60555/mbq8-0451</code></li>
                <li><strong>Principal Investigator:</strong> Forman A. Williams (UC San Diego)</li>
                <li><strong>License:</strong> CC0-1.0 (Public Domain)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="nm-info-panel">
            <div class="nm-panel-tag">HYBRID COHORT</div>
            <h3>🧪 Dataset Composition</h3>
            <ul class="nm-spec-list">
                <li><strong>5 Verified Rows:</strong> Authentic NASA test runs (Methanol, 1 atm).</li>
                <li><strong>270 Calibrated Rows:</strong> Generated using published FLEX scaling laws to support interactive multi-dimensional analytics.</li>
                <li><strong>Gravity Split:</strong> 79% Microgravity (µg) vs. 21% Ground Baseline (1g).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div class="nm-info-panel">
            <div class="nm-panel-tag">ARCHITECTURE</div>
            <h3>🔬 NovaMind Data Pipeline</h3>
            <div class="nm-step"><span>01</span><div><strong>Ingest & Normalise:</strong> Flat schema extraction from NASA PSI tables.</div></div>
            <div class="nm-step"><span>02</span><div><strong>Standardise:</strong> Numeric coercion, unit harmonization, and gravity tagging.</div></div>
            <div class="nm-step"><span>03</span><div><strong>Derive:</strong> Flammability margin and soot-yield index computation.</div></div>
            <div class="nm-step"><span>04</span><div><strong>Rank:</strong> Min-max normalisation + dynamic user-defined criteria weights.</div></div>
            <div class="nm-step"><span>05</span><div><strong>Explain:</strong> Auto-generated paired µg-vs-1g fire-safety insights.</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="nm-info-panel">
            <div class="nm-panel-tag">SCORING ENGINE</div>
            <h3>⚖️ Default Ranking Criteria</h3>
            <ul class="nm-spec-list">
                <li><strong>Fire-safety relevance (40%):</strong> Limiting-O₂ proximity + radiative heat loss.</li>
                <li><strong>Data quality (25%):</strong> Sensor completeness + replicate trial count.</li>
                <li><strong>µg signal (20%):</strong> Magnitude of deviation from 1g ground baseline.</li>
                <li><strong>Reproducibility (15%):</strong> Experimental repeatability score.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.caption("⚠️ **Scope:** This dashboard presents statistical observations, not certified fire-safety recommendations. Synthetic rows are explicitly tagged in the dataset.")