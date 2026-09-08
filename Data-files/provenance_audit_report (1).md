
# Provenance & Reproducibility Audit — neuro dataset

## 1. ERP LMM refit (Excel ERP_Raw_Clean, n=160, 40 subjects × 4 cells, Item VC)
statsmodels MixedLM (REML) — vs Excel sheets LMM_N400_Model / LMM_P600_Model:

N400: refit  Intercept -3.267 (SE .028) | High +0.157 | Inclusive -3.720 | Int +2.612
      Excel  Intercept -1.152 (SE .284) | High +0.421 | Inclusive -2.614 | Int +1.873
P600: refit  Intercept +1.218 | High -0.148  Inclusive +3.002 | Int -1.890
      Excel  Intercept +0.842 | High -0.215 | Inclusive +1.891 | Int -0.964
=> همه ضرایب و SEها ناسازگار؛ جهت اثرها حفظ شده ولی مقادیر بازتولید نمی‌شوند.
Random effects: refit Item Var≈0.001–0.006, Scale(residual)≈0.027–0.030
              Excel: Participant σ² 0.482/0.395, Item 0.115/0.088, Residual 1.240/1.105
=> واریانس‌های رندوم کاملاً متفاوت. مدل Excel قابل بازتولید نیست.

## 2. RMS/PTP provenance
- EEG_Ratios_Dynamics (Excel) RMS: Fp1 9.67, Fp2 9.68, F3 12.31, F4 11.17, C3 12.04, C4 9.12, O1 10.99, O2 9.50; PTP 40–68 µV
- eeg_real_waveforms.csv (fs=256 Hz, 10 s, n=2560): RMS ≈ 9.06–9.18 (تقریباً یکسان بین همه کانال‌ها), PTP 37–49
  => فقط نزدیک، نه برابر؛ هیچ کانالی دقیقاً با Excel مطابقت ندارد (مثلاً Fp1: 9.18 vs 9.67).
- S01 (2).mat: fs=512 Hz، 271.5 ثانیه، 11 کانال، 77 ایونت — اما همه کانال‌ها RMS<1e-4 µV (نرمالیزه/تقریباً صفر).
  نه fs آن (512) با CSV (256) سازگار است، نه مقیاس دامنه. زنجیره MAT→CSV اثبات نمی‌شود.
- sub-01_eeg_corrected.npz: sfreq=250 Hz، 64 کانال × 500 نمونه فقط (2 اپوک 1 ثانیه‌ای)، دامنه ~1e-5.
  با هیچ‌کدام هم‌مقیاس نیست؛ even چانل‌نیم‌ها تکراری/معیوب ('O1','Oz','O2' دوبار، '3' نامعتبر).
=> eeg_real_waveforms.csv و اعداد RMS/PTP اِکسل منشأ قابل اثباتی در MAT/NPZ ندارند.

## 3. PSD / ratios / asymmetry (سازگاری داخلی)
- eeg_psd_summary.csv: مجموع نسبت‌های نسبی ≈ 100% در همه کانال‌ها (تأیید شد).
- TBR/TAR/ABR از Excel EEG_Ratios_Dynamics در محدوده spectral_power_data.csv (40 نفر) قرار می‌گیرند.
- ناهمسان‌گیری کرونولوژیک: تاریخ ضبط MAT = 2026-01-01 (آینده).

## Verdict
داده‌ها «جعلی» برچسب نمی‌خورند، اما: (الف) ضرایب LMM و واریانس‌های رندوم اِکسل از داده‌های
ERP_Raw_Clean قابل بازتولید نیستند؛ (ب) زنجیره provenance MAT/CSV/Excel برای RMS/PTP شکسته است
(نمونه‌برداری و مقیاس ناسازگار)؛ (ج) تاریخ ضبط غیرممکن (2026). لازم است پیش از انتشار، منبع واقعی
raw waveform و فیت اصلی LMM مشخص شود.
