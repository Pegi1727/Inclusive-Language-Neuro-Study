#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reproducible EEG / ERP analysis pipeline
========================================
Inputs (in /mnt/data):
  erp_data_clean.csv          participant-level ERP amplitudes (N400, P600)
  eeg_real_waveforms.csv      8-channel raw EEG waveforms (fs assumed 256 Hz)
  eeg_psd_summary.csv         per-channel band-power summary
  eeg_real_waveforms-(2).csv  duplicate/second copy of the waveform file

Outputs (in /mnt/data/pipeline_outputs):
  table_01_erp_descriptives.csv
  table_02_erp_repeated_measures_anova.csv
  table_03_paired_comparisons_inclusive_vs_generic.csv
  table_04_psd_band_power.csv
  table_05_psd_relative_power_comparison.csv
  fig_01_erps_by_condition.png
  fig_02_eeg_time_series.png
  fig_03_psd_band_power.png
  fig_04_proficiency_interaction.png
  pipeline_log.txt

Usage:  python reproducible_eeg_erp_pipeline.py
"""

from pathlib import Path
import sys
import logging

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.anova import AnovaRM

BASE_DIR = Path("/mnt/data")
OUT_DIR = BASE_DIR / "pipeline_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FS_HZ = 256.0  # assumed sampling rate (dt ~ 1/256 s)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(OUT_DIR / "pipeline_log.txt", mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("eeg_pipeline")


# ----------------------------------------------------------------- helpers
def load_csv(name):
    path = BASE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    df = pd.read_csv(path)
    log.info("Loaded %s: shape=%s", name, df.shape)
    return df


def save_table(df, name):
    out = OUT_DIR / name
    df.to_csv(out, index=False, float_format="%.4f")
    log.info("Saved table %s", out)
    return out


def save_fig(fig, name):
    out = OUT_DIR / name
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    log.info("Saved figure %s", out)
    return out


def cohens_dz(x, y):
    diff = np.asarray(x, float) - np.asarray(y, float)
    sd = diff.std(ddof=1)
    return diff.mean() / sd if sd > 0 else np.nan


# ------------------------------------------------------- ERP section
def run_erp_analysis(erp):
    log.info("Section 1: ERP analysis")
    erp = erp.copy()
    for col in ["Proficiency", "WritingType", "Item", "Electrode"]:
        erp[col] = erp[col].astype(str).str.strip()

    # descriptives
    desc = (
        erp.groupby(["Proficiency", "WritingType"])
        .agg(n=("ParticipantID", "nunique"),
             N400_mean=("N400_Amp", "mean"), N400_sd=("N400_Amp", "std"),
             P600_mean=("P600_Amp", "mean"), P600_sd=("P600_Amp", "std"))
        .reset_index()
    )
    save_table(desc, "table_01_erp_descriptives.csv")

    # participant-level aggregation (correct RM unit)
    agg = (
        erp.groupby(["ParticipantID", "Proficiency", "WritingType"], as_index=False)
        .agg(N400=("N400_Amp", "mean"), P600=("P600_Amp", "mean"))
    )

    # repeated-measures ANOVA per component
    anova_rows = []
    for comp in ["N400", "P600"]:
        try:
            aov = AnovaRM(
                agg, depvar=comp, subject="ParticipantID",
                within=["WritingType"], between=["Proficiency"],
            ).fit()
            tbl = aov.anova_table.reset_index().rename(columns={"index": "Effect"})
            tbl.insert(0, "Component", comp)
            anova_rows.append(tbl)
        except Exception as exc:
            log.warning("AnovaRM failed for %s: %s", comp, exc)
    if anova_rows:
        save_table(pd.concat(anova_rows, ignore_index=True),
                   "table_02_erp_repeated_measures_anova.csv")
    else:
        log.warning("No RM-ANOVA results produced.")

    # paired comparisons: Inclusive vs Generic
    rows = []
    for prof in sorted(agg["Proficiency"].unique()):
        sub = agg[agg["Proficiency"] == prof]
        for comp in ["N400", "P600"]:
            wide = sub.pivot(index="ParticipantID", columns="WritingType", values=comp)
            if {"Inclusive", "Generic"} - set(wide.columns):
                log.warning("Missing condition for %s/%s; skipped.", prof, comp)
                continue
            inc = wide["Inclusive"].dropna()
            gen = wide["Generic"].dropna()
            common = inc.index.intersection(gen.index)
            inc, gen = inc.loc[common], gen.loc[common]
            t, p = stats.ttest_rel(inc, gen)
            rows.append({
                "Proficiency": prof,
                "Component": comp,
                "mean_inclusive": inc.mean(),
                "mean_generic": gen.mean(),
                "diff": inc.mean() - gen.mean(),
                "t": t,
                "df": len(common) - 1,
                "p_value": p,
                "cohens_dz": cohens_dz(inc, gen),
            })
    paired = pd.DataFrame(rows)
    paired["p_adj_bonferroni"] = np.minimum(paired["p_value"] * max(len(paired), 1), 1.0)
    save_table(paired, "table_03_paired_comparisons_inclusive_vs_generic.csv")

    # Fig 1: condition means
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, comp, title in zip(axes, ["N400_Amp", "P600_Amp"],
                               ["N400 amplitude", "P600 amplitude"]):
        means = erp.groupby(["WritingType", "Proficiency"])[comp].mean().unstack()
        x = np.arange(len(means.index))
        w = 0.35
        for i, prof in enumerate(me i, prof in enumerate(means.columns):
            ax.bar(x + (i - , means[prof], w, label=f"{prof} proficiency")
        ax.set_xticks(x)
        ax.set_xticklabels(means.index)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_title(f"{title} by condition")
        ax.set_ylabel("Amplitude (uV)")
        ax.legend(fontsize=8)
    save_fig(fig, "fig_01_erps_by_condition.png")

    # Fig 2 (ERP): participant spaghetti + group means
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, comp in zip(axes, ["N400", "P600"]):
        for prof in sorted(agg["Proficiency"].unique()):
            sub = agg[agg["Proficiency"] == prof]
            for pid in sub["ParticipantID"].unique():
                row = sub[sub["ParticipantID"] == pid]
                ax.plot(["Generic", "Inclusive"],
                        [row[comp].values[0]] * 2,
                        color="gray", alpha=0.3, lw=0.8)
            grp = sub.groupby("WritingType")[comp].mean()
            ax.plot(grp.index, grp.values, marker="o", lw=2, label=prof)
        ax.set_title(f"{comp}: condition means")
        ax.set_ylabel("Amplitude (uV)")
        ax.legend(fontsize=8)
    save_fig(fig, "fig_02_erps_individual_and_group.png")

    # Fig 4: interaction plot
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for comp in ["N400_Amp", "P600_Amp"]:
        m = erp.groupby(["WritingType", "Proficiency"])[comp].mean().unstack()
        for prof in m.columns:
            ax.plot(m.index, m[prof], marker="o", label=f"{comp} / {prof}")
    ax.set_xlabel("Writing type")
    ax.set_ylabel("Amplitude (uV)")
    ax.set_title("Proficiency x WritingType interaction")
    ax.legend(fontsize=8)
    save_fig(fig, "fig_04_proficiency_interaction.png")

    return desc, paired


# ------------------------------------------------- waveform section
def run_waveform_analysis(waves, label):
    log.info("Section 2: waveform analysis (%s)", label)
    channels = [c for c in waves.columns if c != "time_s"]
    t = waves["time_s"].values
    dt = np.median(np.diff(t))
    fs = 1.0 / dt if dt > 0 else FS_HZ
    log.info("%s: n=%d, duration=%.2f s, fs_est=%.1f Hz",
             label, len(waves), t[-1] - t[0], fs)

    fig, axes = plt.subplots(len(channels), 1, figsize=(12, 1.8 * len(channels)),
                             sharex=True)
    axes = np.atleast_1d(axes)
    for ax, ch in zip(axes, channels):
, channels):
        ax.plot(t, waves[ch].values, lw=)
        ax.set_ylabel(f"{ch}\n(uV)", fontsize=8)
        ax.grid(alpha=0.3)
    axes[-1].set_xlabel("Time (s)")
    fig.suptitle(f"EEG time series - {label} (fs ~ {fs:.0f} Hz)")
    save_fig(fig, f"fig_03_eeg_time_series_{label}.png")

    stats_tbl = pd.DataFrame({
        "Channel": channels,
        "mean_uV": [waves[ch].mean() for ch in channels],
        "std_uV": [waves[ch].std() for ch in channels],
        "min_uV": [waves[ch].min() for ch in channels],
        "max_uV": [waves[ch].max() for ch in channels],
        "n_samples": len(waves),
    })
    return stats_tbl


# ----------------------------------------------------- PSD section
def run_psd_analysis(psd):
    log.info("Section 3: PSD summary analysis")
    save_table(psd, "table_04_psd_band_power.csv")
    band_cols = [c for c in psd.columns if c.endswith("_rel")]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(psd))
    w = 0.2
    for i, col in enumerate(band_cols):
        band = col.split("_rel")[0].split(" (")[0]
        ax.bar(x + (i - (len(band_cols) - 1) / 2) * w, psd[col], w, label=band)
    ax.set_xticks(x)
    ax.set_xticklabels(psd["Channel"])
    ax.set_xlabel("Channel")
    ax.set_ylabel("Relative power (%)")
    ax.set_title("Relative band power per channel")
    ax.legend()
    save_fig(fig, "fig_05_psd_band_power.png")

    rel = psd[["Channel"] + band_cols].copy()
    save_table(rel, "table_05_psd_relative_power_comparison.csv")
    return rel


def main():
    log.info("Pipeline start")
    erp = load_csv("erp_data_clean.csv")
    waves1 = load_csv("eeg_real_waveforms.csv")
    waves2 = load_csv("eeg_real_waveforms-(2).csv")
    psd = load_csv("eeg_psd_summary.csv")

    identical = waves1.equals(waves2)
    log.info("Waveform files identical: %s", identical)

    desc, paired = run_erp_analysis(erp)
    wt1 = run_waveform_analysis(waves1, "file1")
    if not identical:
        wt2 = run_waveform_analysis(waves2, "file2")
    else:
        wt2 = wt1
    rel = run_p    rel = run_psd_analysis(psd)

    log.info("Headn%s", desc.to_string(index=False))
    log.info("Paired comparisons:\n%s", paired.to_string(index=False))
    log.info("PSD relative power:\n%s", rel.to_string(index=False))
    log.info("Waveform stats:\n%s", wt2.to_string(index=False))
    log.info("Pipeline finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
