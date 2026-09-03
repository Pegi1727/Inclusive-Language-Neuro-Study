# =====================================================================
# Reproducible EEG / ERP Analysis in R
# ---------------------------------------------------------------------
# Data files expected in the working directory:
#   - erp_data_clean.csv        : ERP amplitudes (N400, P600) per participant
#   - eeg_real_waveforms.csv    : continuous EEG waveforms (8 channels)
#   - eeg_psd_summary.csv       : pre-computed PSD band-power summary
#
# Design of ERP data:
#   ParticipantID (Ss) x Proficiency (High/Low) x WritingType
#   (Generic vs Inclusive) x Item, repeated measures on WritingType & Item.
#
# Author : <your name>
# Date   : `r Sys.Date()`  (auto-updated)
# =====================================================================

# ---------------------------------------------------------------------
# 0. Reproducibility setup
# ---------------------------------------------------------------------
options(stringsAsFactors = FALSE, scipen = 999, digits = 3)
set.seed(42)                                   # reproducible RNG
Sys.setenv(LANG = "en")

required_pkgs <- c("tidyverse", "lme4", "lmerTest",
                   "emmeans", "effsize", "ggplot2", "knitr")
missing_pkgs  <- required_pkgs[!required_pkgs %in% installed.packages()[, "Package"]]
if (length(missing_pkgs) > 0) {
  install.packages(missing_pkgs, dependencies = TRUE)
}
invisible(lapply(required_pkgs, library, character.only = TRUE))
theme_set(theme_minimal(base_size = 12))

# ---------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------
erp  <- read_csv("erp_data_clean.csv",
                 col_types = cols(ParticipantID = col_character(),
                                  Proficiency   = col_factor(),
                                  WritingType   = col_factor(),
                                  Item          = col_character(),
                                  Electrode     = col_character()))
eeg  <- read_csv("eeg_real_waveforms.csv")     # 2560 samples @ 256 Hz
psd  <- read_csv("eeg_psd_summary.csv")

cat("ERP:", nrow(erp), "rows |", n_distinct(erp$ParticipantID), "participants\n")
cat("EEG:", nrow(eeg), "samples,", ncol(eeg) - 1, "channels\n")

# ---------------------------------------------------------------------
# 2. Descriptive statistics (APA style)
# ---------------------------------------------------------------------
desc_erp <- erp %>%
  group_by(Proficiency, WritingType) %>%
  summarise(
    N          = n(),
    N400_mean  = mean(N400_Amp, na.rm = TRUE),
    N400_sd    = sd(N400_Amp, na.rm = TRUE),
    P600_mean  = mean(P600_Amp, na.rm = TRUE),
    P600_sd    = sd(P600_Amp, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    N400_M_SD = sprintf("%.2f (%.2f)", N400_mean, N400_sd),
    P600_M_SD = sprintf("%.2f (%.2f)", P600_mean, P600_sd)
  )
knitr::kable(desc_erp %>% select(Proficiency, WritingType, N,
                                 N400_M_SD, P600_M_SD),
             caption = "Table 1. Descriptive statistics (M and SD) for N400 and P600 amplitudes (\u00B5V).")

# Grand-average waveform plot per condition (mean over participants/items)
erp_means <- erp %>%
  group_by(Proficiency, WritingType) %>%
  summarise(across(c(N400_Amp, P600_Amp), mean, na.rm = TRUE), .groups = "drop")

p_bars <- erp_means %>%
  pivot_longer(cols = c(N400_Amp, P600_Amp),
               names_to = "Component", values_to = "Amplitude") %>%
  ggplot(aes(WritingType, Amplitude, fill = Proficiency)) +
  geom_col(position = position_dodge()) +
  facet_wrap(~ Component) +
  labs(title = "Mean ERP amplitude by condition",
       x = "Writing type", y = "Amplitude (\u00B5V)", fill = "Proficiency")
print(p_bars)
ggsave("plot_erp_means.png", p_bars, width = 8, height = 4.5, dpi = 300)

# ---------------------------------------------------------------------
# 3. Linear Mixed-Effects Models
# ---------------------------------------------------------------------
# N400: maximal random-effects structure that converges
m_n400 <- lmer(N400_Amp ~ Proficiency * WritingType +
                 (1 + WritingType | ParticipantID) +
                 (1 | Item),
               data = erp,
               control = lmerControl(optimizer = "bobyqa"))
summary(m_n400)

# P600
m_p600 <- lmer(P600_Amp ~ Proficiency * WritingType +
                 (1 + WritingType | ParticipantID) +
                 (1 | Item),
               data = erp,
               control = lmerControl(optimizer = "bobyqa"))
summary(m_p600)

# Fixed-effects tables -> APA format
apa_fixef <- function(m, modname) {
  s <- as.data.frame(coef(summary(m)))
  s$term <- rownames(s)
  s$`t value` <- if (!"t value" %in% names(s)) s$statistic else s$`t value`
  s %>%
    transmute(Predictor   = term,
              b           = Estimate,
              SE          = `Std. Error`,
              t           = `t value`,
              p           = `Pr(>|t|)`,
              Effect_size = sprintf("d = %.2f", abs(Estimate) / sd(erp[[modname]], na.rm = TRUE)))
}
tab_n400 <- apa_fixef(m_n400, "N400_Amp")
tab_p600 <- apa_fixef(m_p600, "P600_Amp")
knitr::kable(tab_n400, digits = 2,
             caption = "Table 2. Fixed effects of the N400 model (b, SE, t, p).")
knitr::kable(tab_p600, digits = 2,
             caption = "Table 3. Fixed effects of the P600 model (b, SE, t, p).")

# Model comparison: does the interaction help? ( likelihood-ratio test )
m_n400_null <- lmer(N400_Amp ~ Proficiency + WritingType +
                      (1 + WritingType | ParticipantID) + (1 | Item),
                    data = erp, control = lmerControl(optimizer = "bobyqa"))
anova(m_n400_null, m_n400)

# ---------------------------------------------------------------------
# 4. Estimated marginal means & pairwise contrasts
# ---------------------------------------------------------------------
emm_n400 <- emmeans(m_n400, ~ WritingType | Proficiency)
pairs_n400 <- pairs(emm_n400, adjust = "bonferroni")
confint(pairs_n400)
knitr::kable(as.data.frame(pairs_n400), digits = 3,
             caption = "Table 4. Pairwise contrasts (WritingType) within each Proficiency level, Bonferroni-adjusted.")

# ---------------------------------------------------------------------
# 5. Paired-samples t-tests + Cohen's d (effsize)
# ---------------------------------------------------------------------
# Mean per participant per condition, then paired t-test (within subjects)
subj_means <- erp %>%
  group_by(ParticipantID, Proficiency, WritingType) %>%
  summarise(N400 = mean(N400_Amp, na.rm = TRUE),
            P600 = mean(P600_Amp, na.rm = TRUE), .groups = "drop")

paired_tests <- subj_means %>%
  group_by(Proficiency) %>%
  group_modify(~ {
    wide  <- pivot_wider(.x, id_cols = ParticipantID,
                         names_from = WritingType,
                         values_from = c(N400, P600))
    t_n <- t.test(wide$N400_Inclusive, wide$N400_Generic, paired = TRUE)
    t_p <- t.test(wide$P600_Inclusive, wide$P600_Generic, paired = TRUE)
    d_n <- cohen.d(wide$N400_Inclusive, wide$N400_Generic, paired = TRUE)
    d_p <- cohen.d(wide$P600_Inclusive, wide$P600_Generic, paired = TRUE)
    tibble(Comparison   = c("N400: Inclusive - Generic", "P600: Inclusive - Generic"),
           t            = c(t_n$statistic, t_p$statistic),
           df           = c(t_n$parameter,  t_p$parameter),
           p            = c(t_n$p.value,    t_p$p.value),
           cohen_d      = c(d_n$estimate,   d_p$estimate))
  })
knitr::kable(paired_tests, digits = 3,
             caption = "Table 5. Paired-samples t-tests with Cohen's d for ERP amplitudes (Inclusive vs Generic).")

# APA-formatted t-test lines
paired_tests %>%
  mutate(apa = sprintf("t(%d) = %.2f, p = %.3f, d = %.2f",
                       df, t, p, cohen_d)) %>%
  select(Proficiency, Comparison, apa) %>%
  print(n = Inf)

# Individual differences plot
p_subj <- subj_means %>%
  ggplot(aes(WritingType, N400, group = ParticipantID)) +
  geom_line(alpha = .3) +
  stat_summary(fun = mean, geom = "point", size = 4, color = "red") +
  facet_wrap(~ Proficiency) +
  labs(title = "N400 amplitude: individual trajectories",
       x = "Writing type", y = "N400 amplitude (\u00B5V)")
print(p_subj)
ggsave("plot_individual_n400.png", p_subj, width = 8, height = 4.5, dpi = 300)

# ---------------------------------------------------------------------
# 6. Spectral analysis of continuous EEG
# ---------------------------------------------------------------------
fs   <- 1 / (eeg$time_s[2] - eeg$time_s[1])   # sampling rate (Hz) ~256
nfft <- nrow(eeg)

# Welch-like average PSD across channels
spec <- map_dfr(setdiff(names(eeg), "time_s"), function(ch) {
  s <- spectrum(eeg[[ch]], plot = FALSE, span = 51)   # smoothing
  tibble(Channel = ch,
         freq_Hz = s$freq * fs,
         power   = s$spec)
})
p_psd <- ggplot(spec, aes(freq_Hz, log10(power), color = Channel)) +
  geom_line() +
  coord_cartesian(xlim = c(0, 40)) +
  labs(title = "Power spectral density (Welch-smoothed)",
       x = "Frequency (Hz)", y = expression(log[10]*" power"))
print(p_psd)
ggsave("plot_psd.png", p_psd, width = 8, height = 4.5, dpi = 300)

# Band-power summary (from precomputed file)
psd_long <- psd %>%
  select(Channel, matches("_rel$")) %>%
  pivot_longer(-Channel, names_to = "Band", values_to = "RelativePower") %>%
  mutate(Band = str_remove(Band, "_rel") %>% str_replace("\\(.*\\)", "") %>% str_trim())

p_band <- ggplot(psd_long, aes(Channel, RelativePower, fill = Band)) +
  geom_col(position = position_dodge()) +
  labs(title = "Relative band power per channel",
       x = "Channel", y = "Relative power (%)", fill = "Band")
print(p_band)
ggsave("plot_band_power.png", p_band, width = 8, height = 4.5, dpi = 300)

# ---------------------------------------------------------------------
# 7. Session info (full reproducibility record)
# ---------------------------------------------------------------------
sessionInfo()
writeLines(capture.output(sessionInfo()), "sessionInfo.txt")
# =====================================================================
# END OF SCRIPT
# =====================================================================
