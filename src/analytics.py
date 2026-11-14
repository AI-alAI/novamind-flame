"""Derived combustion metrics, multi-criteria experiment ranking, and automated
NASA fire-safety insight synthesis for NovaMind AI — Flame in Freefall.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from .data import KEY_COLS

DEFAULT_WEIGHTS: dict[str, float] = {
    "Fire-safety relevance": 0.40,
    "Data quality": 0.25,
    "Microgravity signal": 0.20,
    "Reproducibility": 0.15,
}

# Physical 1g reference spread rates (mm/s) used if the user filters out all 1g rows
CANONICAL_1G_SPREAD_MM_S: dict[str, float] = {
    "liquid": 12.0,
    "gas": 24.0,
    "solid": 6.2,
}


def _minmax(s: pd.Series) -> pd.Series:
    """Normalises a numeric Series to [0, 1] while safely handling NaNs and constant values."""
    s_num = pd.to_numeric(s, errors="coerce").astype(float)
    lo, hi = s_num.min(), s_num.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or (hi - lo) < 1e-9:
        return pd.Series(0.5, index=s.index, dtype=float)
    return ((s_num - lo) / (hi - lo)).fillna(0.5)


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Computes derived combustion indices and telemetry completeness per experiment."""
    out = df.copy()

    # 1. Oxygen margin above limiting extinction threshold (% O2)
    out["flammability_margin_pct"] = (
        out["oxygen_pct"] - out["extinction_oxygen_pct"]
    ).round(2)

    # 2. Thermal-normalised soot yield index (ppm per 1000 K)
    temp_safe = out["peak_temperature_k"].replace(0, np.nan)
    out["soot_yield_index"] = (
        (out["soot_volume_fraction_ppm"] / temp_safe) * 1000.0
    ).round(4)

    # 3. Radiative quenching regime indicator (chi_r >= 0.42 in microgravity)
    out["radiative_quenching_risk"] = (
        (out["radiative_loss_fraction"] >= 0.42) & out["is_microgravity"]
    )

    # 4. Telemetry completeness across core physical columns (0.0 to 1.0)
    present_key_cols = [c for c in KEY_COLS if c in out.columns]
    out["completeness"] = (
        out[present_key_cols].notna().mean(axis=1)
        if present_key_cols
        else 1.0
    )

    return out


def score_experiments(
    df: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Computes transparent sub-scores and a weighted composite priority rank."""
    w = weights or DEFAULT_WEIGHTS
    out = df.copy()

    if out.empty:
        return out

    # 1. Fire-Safety Relevance (Limiting-O2 margin proximity + radiative loss + µg context)
    has_extinction = out["extinction_oxygen_pct"].notna().astype(float)
    # Flames that sustain at low O2 extinction thresholds pose higher spacecraft risk
    low_lo2_hazard = 1.0 - _minmax(out["extinction_oxygen_pct"])
    rad_norm = _minmax(out["radiative_loss_fraction"])
    out["s_fire_safety"] = (
        0.35 * has_extinction
        + 0.25 * low_lo2_hazard
        + 0.25 * rad_norm
        + 0.15 * out["is_microgravity"].astype(float)
    ).clip(0.0, 1.0)

    # 2. Data Quality (Sensor completeness + replicate trial count + verified bonus)
    is_verified = (
        ~out.get("is_synthetic", pd.Series(True, index=out.index)).astype(bool)
    ).astype(float)
    out["s_data_quality"] = (
        0.60 * out["completeness"].fillna(0.5)
        + 0.30 * _minmax(out["trials"])
        + 0.10 * is_verified
    ).clip(0.0, 1.0)

    # 3. Microgravity Signal (Magnitude of spread-rate shift vs 1g fuel-class baseline)
    ground_rows = out.loc[~out["is_microgravity"]]
    if not ground_rows.empty:
        baseline_map = (
            ground_rows.groupby("fuel_class")["flame_spread_rate_mm_s"]
            .mean()
            .to_dict()
        )
    else:
        baseline_map = {}

    # Fallback to canonical 1g values if a fuel class has no 1g rows in the current filter
    full_baseline = {
        fc: baseline_map.get(fc, CANONICAL_1G_SPREAD_MM_S.get(fc, 12.0))
        for fc in out["fuel_class"].dropna().unique()
    }
    expected_1g = out["fuel_class"].map(full_baseline).fillna(12.0)
    rel_deviation = ((out["flame_spread_rate_mm_s"] - expected_1g).abs() / expected_1g.clip(lower=0.5))
    out["s_microgravity_signal"] = (
        _minmax(rel_deviation) * out["is_microgravity"].astype(float)
    ).clip(0.0, 1.0)

    # 4. Reproducibility (Replicate trials + verified archival provenance)
    out["s_reproducibility"] = (
        0.85 * _minmax(out["trials"]) + 0.15 * is_verified
    ).clip(0.0, 1.0)

    # Weighted Composite Score (safe against all-zero slider weights)
    total_w = float(sum(w.values()))
    if total_w <= 1e-9:
        total_w = 1.0
        w = DEFAULT_WEIGHTS

    out["rank_score"] = (
        w.get("Fire-safety relevance", 0.0) * out["s_fire_safety"]
        + w.get("Data quality", 0.0) * out["s_data_quality"]
        + w.get("Microgravity signal", 0.0) * out["s_microgravity_signal"]
        + w.get("Reproducibility", 0.0) * out["s_reproducibility"]
    ) / total_w

    out["rank_score"] = out["rank_score"].round(4)

    # Sort descending by score, breaking ties deterministically by experiment_id
    out = out.sort_values(
        by=["rank_score", "s_fire_safety", "experiment_id"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1, dtype=int)
    return out


def _paired_stats(df: pd.DataFrame, col: str) -> dict[str, float | int] | None:
    """Computes paired microgravity (µg) and ground (1g) summary statistics for a column."""
    if col not in df.columns:
        return None
    m = pd.to_numeric(df.loc[df["is_microgravity"], col], errors="coerce").dropna()
    g = pd.to_numeric(df.loc[~df["is_microgravity"], col], errors="coerce").dropna()
    if len(m) < 2 or len(g) < 2:
        return None
    m_mean, g_mean = float(m.mean()), float(g.mean())
    if abs(g_mean) < 1e-9:
        return None
    pct_delta = ((m_mean - g_mean) / abs(g_mean)) * 100.0
    return {
        "m_mean": m_mean,
        "g_mean": g_mean,
        "m_count": int(len(m)),
        "g_count": int(len(g)),
        "pct_delta": pct_delta,
    }


def _top_evidence_ids(df: pd.DataFrame, col: str, k: int = 4) -> str:
    """Returns a concise list of representative experiment IDs prioritizing verified NASA runs."""
    valid = df.loc[df[col].notna()].copy()
    if valid.empty:
        return "N/A"
    # Prioritise verified PSI-69 runs first, then microgravity runs
    if "is_synthetic" in valid.columns:
        valid = valid.sort_values(by=["is_synthetic", "is_microgravity"], ascending=[True, False])
    ids = valid["experiment_id"].head(k).tolist()
    suffix = f" (+{len(valid) - k} more)" if len(valid) > k else ""
    return ", ".join(ids) + suffix


def build_insights(df: pd.DataFrame) -> list[dict[str, str]]:
    """Synthesises paired microgravity vs. 1g fire-safety insights with physical mechanisms."""
    insights: list[dict[str, str]] = []
    if df.empty:
        return insights

    # 1. Flame Spread Rate
    st_spread = _paired_stats(df, "flame_spread_rate_mm_s")
    if st_spread:
        direction = "slower" if st_spread["pct_delta"] < 0 else "faster"
        insights.append({
            "title": "Flame Propagation Slows in Freefall",
            "body": (
                f"Mean flame spread rate is {st_spread['m_mean']:.2f} mm/s in microgravity "
                f"(n={st_spread['m_count']}) vs. {st_spread['g_mean']:.2f} mm/s at 1g "
                f"(n={st_spread['g_count']}) — {abs(st_spread['pct_delta']):.0f}% {direction}. "
                f"Without buoyant natural convection, oxygen reaches the reaction zone primarily "
                f"via molecular diffusion and gentle HVAC ventilation drafts."
            ),
            "evidence": _top_evidence_ids(df, "flame_spread_rate_mm_s"),
            "metric": "flame_spread_rate_mm_s",
        })

    # 2. Radiative Heat Loss Fraction
    st_rad = _paired_stats(df, "radiative_loss_fraction")
    if st_rad:
        direction = "higher" if st_rad["pct_delta"] > 0 else "lower"
        insights.append({
            "title": "Radiative Heat Loss Governs Extinction",
            "body": (
                f"Radiative loss fraction (χr) averages {st_rad['m_mean']:.3f} in microgravity "
                f"compared to {st_rad['g_mean']:.3f} on Earth ({abs(st_rad['pct_delta']):.0f}% {direction}). "
                f"Spherical microgravity flames trap hot combustion products near the burner, "
                f"making radiative heat loss the primary trigger for radiative quenching."
            ),
            "evidence": _top_evidence_ids(df, "radiative_loss_fraction"),
            "metric": "radiative_loss_fraction",
        })

    # 3. Soot Volume Fraction
    st_soot = _paired_stats(df, "soot_volume_fraction_ppm")
    if st_soot:
        direction = "increases" if st_soot["pct_delta"] > 0 else "decreases"
        insights.append({
            "title": "Extended Residence Time Amplifies Soot",
            "body": (
                f"Soot volume fraction {direction} by {abs(st_soot['pct_delta']):.0f}% in orbit, "
                f"averaging {st_soot['m_mean']:.1f} ppm (µg) vs. {st_soot['g_mean']:.1f} ppm (1g). "
                f"Longer gas-phase residence times inside spherical diffusion shells promote "
                f"polycyclic aromatic hydrocarbon (PAH) growth and optical smoke obscuration."
            ),
            "evidence": _top_evidence_ids(df, "soot_volume_fraction_ppm"),
            "metric": "soot_volume_fraction_ppm",
        })

    # 4. Limiting Oxygen Extinction Threshold
    st_lo2 = _paired_stats(df, "extinction_oxygen_pct")
    if st_lo2:
        delta_pts = abs(st_lo2["m_mean"] - st_lo2["g_mean"])
        insights.append({
            "title": "Flammability Window Widens at Low O₂",
            "body": (
                f"Limiting oxygen concentration drops to {st_lo2['m_mean']:.1f}% O₂ in microgravity "
                f"vs. {st_lo2['g_mean']:.1f}% O₂ at 1g (a {delta_pts:.1f} percentage-point wider "
                f"hazard window). Spacecraft flames can sustain at lower oxygen concentrations "
                f"because convective heat losses are absent."
            ),
            "evidence": _top_evidence_ids(df, "extinction_oxygen_pct"),
            "metric": "extinction_oxygen_pct",
        })

    # 5. Burn Duration
    st_dur = _paired_stats(df, "burn_duration_s")
    if st_dur:
        direction = "longer" if st_dur["pct_delta"] > 0 else "shorter"
        insights.append({
            "title": "Sustained Burn Duration in Quiescent Cabins",
            "body": (
                f"Active burn duration averages {st_dur['m_mean']:.1f} s in microgravity vs. "
                f"{st_dur['g_mean']:.1f} s at 1g ({abs(st_dur['pct_delta']):.0f}% {direction}). "
                f"Slower fuel consumption prolongs the window during which smoldering or "
                f"spherical cool flames can re-ignite adjacent materials."
            ),
            "evidence": _top_evidence_ids(df, "burn_duration_s"),
            "metric": "burn_duration_s",
        })

    # 6. Peak Flame Temperature
    st_temp = _paired_stats(df, "peak_temperature_k")
    if st_temp:
        temp_drop = abs(st_temp["g_mean"] - st_temp["m_mean"])
        insights.append({
            "title": "Cooler Reaction Zones from Soot Radiation",
            "body": (
                f"Peak flame temperature averages {st_temp['m_mean']:.0f} K in microgravity vs. "
                f"{st_temp['g_mean']:.0f} K at 1g (a {temp_drop:.0f} K reduction). "
                f"Broadened diffusion zones and soot radiation cool the flame front, shifting "
                f"optimal fire-detector wavelength signatures toward the infrared."
            ),
            "evidence": _top_evidence_ids(df, "peak_temperature_k"),
            "metric": "peak_temperature_k",
        })

    return insights


def insights_to_markdown(insights: list[dict[str, str]]) -> str:
    """Exports synthesised insights as a structured NASA PSI-69 Markdown technical brief."""
    lines = [
        "# 🔥 NovaMind AI — Spacecraft Fire-Safety Telemetry Brief",
        "**Dataset Provenance:** NASA Physical Sciences Informatics · PSI-69 (FLEX) · DOI: `10.60555/mbq8-0451`",
        "",
        "---",
        "",
    ]
    for i, ins in enumerate(insights, 1):
        lines += [
            f"## {i}. {ins['title']}",
            f"**Tracked Telemetry Metric:** `{ins.get('metric', 'composite')}`",
            "",
            ins["body"],
            "",
            f"> **Auditable NASA Run Evidence:** `{ins['evidence']}`",
            "",
        ]
    lines += [
        "---",
        "*Scope Note: Generated by NovaMind AI for the NASA Space Apps Challenge ('Flame in Freefall'). "
        "Values represent statistical observations across filtered cohorts, not certified flight-safety rules.*",
    ]
    return "\n".join(lines)