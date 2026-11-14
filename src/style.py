import streamlit as st
import plotly.graph_objects as go


def inject_css() -> None:
    """Injects the NASA Mission Control & Orbital Telemetry CSS theme."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --bg-deep: #070A12;
        --bg-panel: rgba(15, 22, 38, 0.78);
        --flame: #FF6B2B;
        --amber: #FFB800;
        --cyan: #00E5FF;
        --emerald: #10B981;
        --text-bright: #F8FAFC;
        --text-muted: #94A3B8;
        --border-glass: rgba(255, 255, 255, 0.09);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em;
    }

    /* Sidebar Header */
    .nm-sidebar-header {
        background: linear-gradient(135deg, rgba(255, 107, 43, 0.16), rgba(0, 229, 255, 0.08));
        border: 1px solid rgba(255, 107, 43, 0.35);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .nm-sidebar-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        color: var(--cyan);
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }
    .nm-sidebar-header h2 {
        margin: 0;
        font-size: 1.3rem;
        color: #FFFFFF;
    }
    .nm-sidebar-header p {
        margin: 2px 0 0 0;
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    /* Hero Banner */
    .hero {
        background:
            radial-gradient(circle at 88% 15%, rgba(255, 107, 43, 0.22) 0%, transparent 42%),
            radial-gradient(circle at 12% 88%, rgba(0, 229, 255, 0.14) 0%, transparent 45%),
            linear-gradient(135deg, #0B101E 0%, #121B30 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45);
    }
    .hero-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 0.85rem;
    }
    .hero-status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 229, 255, 0.1);
        border: 1px solid rgba(0, 229, 255, 0.35);
        color: var(--cyan);
        padding: 4px 12px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.06em;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        background: var(--cyan);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--cyan);
    }
    .hero-doi {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: var(--text-muted);
    }
    .hero h1 {
        font-size: 2.45rem;
        font-weight: 700;
        margin: 0 0 0.6rem 0;
        background: linear-gradient(90deg, #FFFFFF 0%, #FFD6BA 55%, #FF6B2B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero p {
        color: #CBD5E1;
        font-size: 1.02rem;
        max-width: 820px;
        line-height: 1.6;
        margin: 0 0 1.35rem 0;
    }
    .hero-actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px;
    }
    .hero .cta {
        display: inline-block;
        background: linear-gradient(90deg, #FF6B2B 0%, #FF8E3C 100%);
        color: #FFFFFF !important;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 8px 18px;
        border-radius: 9px;
        box-shadow: 0 4px 15px rgba(255, 107, 43, 0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .hero .cta:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(255, 107, 43, 0.55);
    }
    .hero-chip {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #E2E8F0;
        padding: 6px 12px;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    }

    /* Custom KPI Cards */
    .nm-kpi-card {
        background: var(--bg-panel);
        border: 1px solid var(--border-glass);
        border-top: 3px solid var(--flame);
        border-radius: 14px;
        padding: 1.15rem 1.25rem;
        height: 100%;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .nm-kpi-card:hover {
        transform: translateY(-3px);
        border-color: rgba(255, 255, 255, 0.22);
    }
    .nm-kpi-card.accent-cyan { border-top-color: var(--cyan); }
    .nm-kpi-card.accent-flame { border-top-color: var(--flame); }
    .nm-kpi-card.accent-amber { border-top-color: var(--amber); }
    .nm-kpi-card.accent-emerald { border-top-color: var(--emerald); }

    .nm-kpi-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.45rem;
    }
    .nm-kpi-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: var(--text-muted);
        letter-spacing: 0.05em;
    }
    .nm-kpi-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        padding: 2px 8px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.06);
        color: #E2E8F0;
    }
    .nm-kpi-badge.warn {
        background: rgba(255, 107, 43, 0.16);
        color: #FFA07A;
        border: 1px solid rgba(255, 107, 43, 0.35);
    }
    .nm-kpi-badge.ok {
        background: rgba(16, 185, 129, 0.15);
        color: #6EE7B7;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .nm-kpi-val {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1.15;
        margin-bottom: 0.4rem;
    }
    .nm-kpi-unit {
        font-size: 0.9rem;
        font-weight: 400;
        color: var(--text-muted);
    }
    .kpi-cap {
        font-size: 0.79rem;
        color: var(--text-muted);
        line-height: 1.45;
    }

    /* Insight Cards */
    .nm-insight-card {
        background: linear-gradient(145deg, rgba(16, 23, 40, 0.9), rgba(10, 14, 26, 0.95));
        border: 1px solid var(--border-glass);
        border-left: 4px solid var(--flame);
        border-radius: 12px;
        padding: 1.2rem 1.35rem;
        margin-bottom: 1rem;
    }
    .nm-insight-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 0.45rem;
    }
    .nm-insight-header h4 {
        margin: 0;
        font-size: 1.05rem;
        color: #FFFFFF;
    }
    .nm-insight-card p {
        color: #CBD5E1;
        font-size: 0.9rem;
        line-height: 1.55;
        margin: 0 0 0.75rem 0;
    }
    .nm-insight-footer span {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.73rem;
        color: var(--cyan);
        background: rgba(0, 229, 255, 0.08);
        border: 1px solid rgba(0, 229, 255, 0.25);
        padding: 3px 10px;
        border-radius: 6px;
    }

    /* Info Panels (About Tab) */
    .nm-info-panel {
        background: var(--bg-panel);
        border: 1px solid var(--border-glass);
        border-radius: 14px;
        padding: 1.3rem 1.45rem;
        margin-bottom: 1rem;
    }
    .nm-panel-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        color: var(--cyan);
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }
    .nm-info-panel h3 {
        margin: 0 0 4px 0;
        font-size: 1.2rem;
        color: #FFFFFF;
    }
    .nm-panel-sub {
        color: var(--text-muted);
        font-size: 0.83rem;
        margin-bottom: 0.8rem;
    }
    .nm-spec-list {
        margin: 0;
        padding-left: 1.1rem;
        color: #CBD5E1;
        font-size: 0.9rem;
        line-height: 1.65;
    }
    .nm-step {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        font-size: 0.88rem;
        color: #CBD5E1;
    }
    .nm-step:last-child { border-bottom: none; }
    .nm-step span {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: var(--flame);
        background: rgba(255, 107, 43, 0.14);
        border: 1px solid rgba(255, 107, 43, 0.35);
        padding: 2px 7px;
        border-radius: 5px;
        margin-top: 2px;
    }

    /* Modernized Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 23, 42, 0.65);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid var(--border-glass);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 9px 16px;
        font-weight: 600;
        font-size: 0.88rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, rgba(255, 107, 43, 0.25), rgba(0, 229, 255, 0.14)) !important;
        border: 1px solid rgba(255, 107, 43, 0.45) !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)


def style_fig(fig: go.Figure, title: str | None = None) -> go.Figure:
    """Applies a dark NASA telemetry theme to any Plotly figure."""
    if title:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(family="Space Grotesk, sans-serif", size=17, color="#F8FAFC"),
                x=0.01,
                y=0.96
            )
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(11, 16, 30, 0.55)",
        font=dict(family="Inter, sans-serif", color="#CBD5E1", size=12),
        margin=dict(l=20, r=20, t=52 if title else 28, b=20),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.75)",
            bordercolor="rgba(255, 255, 255, 0.1)",
            borderwidth=1,
            font=dict(size=11, color="#E2E8F0")
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="#00E5FF",
            font=dict(family="JetBrains Mono, monospace", size=12, color="#F8FAFC")
        )
    )

    fig.update_xaxes(
        gridcolor="rgba(255, 255, 255, 0.06)",
        zerolinecolor="rgba(255, 255, 255, 0.12)",
        linecolor="rgba(255, 255, 255, 0.15)"
    )
    fig.update_yaxes(
        gridcolor="rgba(255, 255, 255, 0.06)",
        zerolinecolor="rgba(255, 255, 255, 0.12)",
        linecolor="rgba(255, 255, 255, 0.15)"
    )
    return fig