# Inclusive Language Neuro-Study: EEG Analysis Pipeline

This repository provides a standardized, reproducible pipeline for analyzing EEG data stored in MATLAB `.mat` format. The focus is on quantifying frequency-band power and spectral characteristics.

---

## 📊 Quick Look: Results & Visualizations

### 1. Signal & Spectral Analysis
Below are the representative outputs generated from the `S14_EEG.mat` dataset.

| Raw EEG Signals | Power Spectral Density (PSD) |
|:---:|:---:|
| ![Raw EEG](results/S14_raw_eeg.png) | ![PSD](results/S14_psd.png) |

*Note: Images are automatically saved to the `results/` folder after running the analysis.*

### 2. Quantitative Summary Table
The following table summarizes the spectral features, including dominant frequency and band powers (Delta, Theta, Alpha, Beta, Gamma) for each channel.

| Channel | Dominant Freq (Hz) | Alpha Power ($\mu V^2$) | Beta Power ($\mu V^2$) | ... |
|:---|:---:|:---:|:---:|:---:|
| *Example_Ch* | *10.2* | *0.45* | *0.12* | ... |

> **Tip:** For the full high-resolution dataset, please refer to [results/S14_channel_summary.csv](./results/S14_channel_summary.csv).

---

## ⚠️ Data Provenance & Ethical Warning

**IMPORTANT:** The EEG data used in this repository (`S14_EEG.mat`) is **SYNTHETIC/SIMULATED**. 
- It is NOT collected from human participants.
- It must NOT be presented or used as clinical, biological, or human neuroscientific data in any publication without explicit documentation of its synthetic nature.
- This pipeline is intended for **methodological benchmarking and software testing** only.

---

## 🚀 Getting Started

### 1. Installation
Ensure you have Python 3.8+ installed. Install the required dependencies:
```bash
pip install -r requirements.txt
