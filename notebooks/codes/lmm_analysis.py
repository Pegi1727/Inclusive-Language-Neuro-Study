import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from scipy import stats

df = pd.read_csv("/mnt/data/erp_data_clean.csv")

def analyze_dv(dv_name):
    out = []
    out.append("="*73)
    out.append(f"                         ANALYSIS FOR: {dv_name}")
    out.append("="*73 + "\n")

    desc = df.groupby(["Proficiency", "WritingType"])[dv_name].agg(
        Mean='mean', SD='std', N='count').reset_index()
    desc['SE'] = desc['SD'] / np.sqrt(desc['N'])
    out.append("--- Cell Descriptives ---")
    out.append(desc.to_string(index=False))
    out.append("\n")

    model = smf.mixedlm(
        f"{dv_name} ~ C(WritingType, Treatment(reference='Generic')) * C(Proficiency, Treatment(reference='High'))",
        data=df, groups=df["ParticipantID"])
    res = model.fit(reml=True, method=["lbfgs", "cg", "powell"])
    out.append("--- MixedLM (REML) Fixed Effects Summary ---")
    out.append(str(res.summary().tables[1]))
    out.append(f"\nRandom Effects Variance (Group Var): {res.cov_re.iloc[0,0]:.6f}")
    out.append(f"Scale (Residual Var): {res.scale:.6f}")

    m_null = smf.mixedlm(f"{dv_name} ~ 1", data=df, groups=df["ParticipantID"]).fit(reml=False)
    m_main = smf.mixedlm(f"{dv_name} ~ C(WritingType) + C(Proficiency)", data=df, groups=df["ParticipantID"]).fit(reml=False)
    m_full = smf.mixedlm(f"{dv_name} ~ C(WritingType) * C(Proficiency)", data=df, groups=df["ParticipantID"]).fit(reml=False)

    lr_stat = 2 * (m_full.llf - m_main.llf)
    lr_p = stats.chi2.sf(lr_stat, df=1)

    out.append("\n--- Model Comparison (ML) ---")
    out.append(f"Null Model AIC:    {m_null.aic:.2f}, BIC: {m_null.bic:.2f}, LogLik: {m_null.llf:.2f}")
    out.append(f"Additive Model AIC:{m_main.aic:.2f}, BIC: {m_main.bic:.2f}, LogLik: {m_main.llf:.2f}")
    out.append(f"Full Model AIC:    {m_full.aic:.2f}, BIC: {m_full.bic:.2f}, LogLik: {m_full.llf:.2f}")
    out.append(f"Interaction Test:  LR chi2(1) = {lr_stat:.3f}, p = {lr_p:.3e}")

    p_agg = df.groupby(["ParticipantID", "Proficiency", "WritingType"])[dv_name].mean().unstack("WritingType").reset_index()
    p_high = p_agg[p_agg["Proficiency"] == "High"]
    p_low = p_agg[p_agg["Proficiency"] == "Low"]

    diff_high = p_high["Inclusive"] - p_high["Generic"]
    t_high, p_high_t = stats.ttest_1samp(diff_high, 0)
    dz_high = diff_high.mean() / diff_high.std()

    diff_low = p_low["Inclusive"] - p_low["Generic"]
    t_low, p_low_t = stats.ttest_1samp(diff_low, 0)
    dz_low = diff_low.mean() / diff_low.std()

    t_gen, p_gen_t = stats.ttest_ind(p_low["Generic"], p_high["Generic"])
    d_gen = (p_low["Generic"].mean() - p_high["Generic"].mean()) / np.sqrt((p_low["Generic"].var() + p_high["Generic"].var())/2)

    t_inc, p_inc_t = stats.ttest_ind(p_low["Inclusive"], p_high["Inclusive"])
    d_inc = (p_low["Inclusive"].mean() - p_high["Inclusive"].mean()) / np.sqrt((p_low["Inclusive"].var() + p_high["Inclusive"].var())/2)

    out.append("\n--- Simple Effects / Pairwise Contrasts (with Bonferroni-adj(),) ---")
    comparisons = [
        ("High: Inclusive - Generic", diff_high.mean(), t_high, 19, p_high_t, min(1.0, p_high_t*4), dz_high),
        ("Low: Inclusive - Generic", diff_low.mean(), t_low, 19, p_low_t, min(1.0, p_low_t*4), dz_low),
        ("Generic: Low - High", p_low["Generic"].mean() - p_high["Generic"].mean(), t_gen, 38, p_gen_t, min(1.0, p_gen_t*4), d_gen),
        ("Inclusive: Low - High", p_low["Inclusive"].mean() - p_high["Inclusive"].mean(), t_inc, 38, p_inc_t, min(1.0, p_inc_t*4), d_inc),
    ]
    comp_df = pd.DataFrame(comparisons, columns=["Contrast", "Estimate", "t_stat", "df", "p_raw", "p_bonf", "Effect_Size"])
    out.append(comp_df.to_string(index=False))

    resids = res.resid
    shapiro_stat, shapiro_p = stats.shapiro(resids)
    out.append("\n--- Residual Diagnostics ---")
    out.append(f"Residual Normality (Shapiro-Wilk): W = {shapiro_stat:.4f}, p = {shapiro_p:.4f}")

    out.append("\n" + "="*73 + "\n")
    return "\n".join(out)

report_n400 = analyze_dv("N400_Amp")
report_p600 = analyze_dv("P600_Amp")
full_report = report_n400 + "\n\n" + report_p600

with open("/mnt/data/lmm_report.txt", "w") as f:
    f.write(full_report)
print(full_report)
