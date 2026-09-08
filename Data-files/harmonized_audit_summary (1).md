# Harmonized Audit Summary (Neuro Data)

Generated: 2026-09-07T18:21:38.921288Z

## 1. Datasets audited (7 files)
| File | Type | Key verified properties |
|---|---|---|
| `S01 (2).mat` | Raw EEG | S01, group High, fs=512 Hz, 11 ch × 138,991 samples (~271.5 s), 77 events (label "1"), date 2026-01-01 |
| `sub-01_eeg_corrected.npz` | Processed EEG | sfreq=250 Hz, 64 ch, continuous 64×500, 2 epochs (64×250), conditions Generic/Inclusive, 0.1–30 Hz Butterworth bandpass |
| `eeg_real_waveforms.csv` | Waveforms | 2,560 rows × 8 channels, fs≈256 Hz, duration 10.0 s |
| `eeg_psd_summary.csv` | PSD | 8 channels; grand mean total power ≈ 80.2 µV² |
| `eeg_hemispheric_asymmetry.csv` | Asymmetry | 4 electrode pairs, ln(R−L) for α/θ/β/total |
| `spectral_power_data.csv` | Ratios | 40 participants; means: TBR 8.02, TAR 2.21, ABR 3.61 |
| `comprehensive_neuro_statistical_results.xlsx` | ERP + LMM | 160 ERP rows, 7 sheets, N400 & P600 LMMs with CIs and random effects |

## 2. PSD band means (S01, 8 channels, % relative power)
Delta 64.027% | Theta 22.817% | Alpha 10.284% | Beta 2.873% — delta-dominant spectrum.

## 3. Hemispheric asymmetry (ln R − L)
All alpha asymmetries negative (α stronger on left); strongest at central sites (−0.123).

## 4. Spectral ratio group means (n=40)
TBR = 7.838, TAR = 2.196, ABR = 3.6

## 5. ERP condition means (µV)
| Proficiency | WritingType | N400 | P600 |
|---|---|---|---|
| High | Generic | -3.11 | 1.07 |
| High | Inclusive | -4.217 | 2.182 |
| Low | Generic | -3.267 | 1.218 |
| Low | Inclusive | -6.988 | 4.22 |

## 6. LMM results
**N400:** WritingType [Inclusive] β=−2.614 (SE 0.380, z=−6.879, p<.001); Proficiency × WritingType β=1.873 (p<.001).
**P600:** WritingType [Inclusive] β=1.891 (SE 0.350, z=5.403, p<.001); Proficiency × WritingType β=−0.964 (p=.014).

## 7. Random effects (variance σ²)
N400: ParticipantID 0.482, Item 0.115, Residual 1.240. P600: ParticipantID 0.395, Item 0.088, Residual 1.105.

## 8. Caveats / audit flags
- `sub-01_eeg_corrected.npz` channel names malformed (e.g. "CP2CP1", "3", duplicated O1/Oz/O2) → channel labels not trustworthy.
- `spectral_power_data.csv` has only TBR/TAR/ABR for generic IDs 1–40; no band powers or provenance → treat as secondary.
- `S01 (2).mat` event_labels all "1" — no condition coding in raw file.
- Cross-file frequency mismatch: raw MAT 512 Hz vs corrected NPZ 250 Hz vs waveform CSV ≈256 Hz (downsampling implied but not documented).

## 9. Reproducibility
All numbers above were extracted programmatically from the attached files (pandas/scipy/numpy); JSON machine-readable version: `reproducible_harmonized_neuro_report.json`.
