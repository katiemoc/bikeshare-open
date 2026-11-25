# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-25: Added `cnt_roll_3`, the mean of `cnt` on the three calendar days before the forecast date (known at prediction time; built after `reindex_to_calendar` with `.shift(1)` before `.rolling(3)`). Validation R² ridge 0.6475 → 0.6439 (Δ −0.0036), hgb 0.2185 → 0.1983 (Δ −0.0202). Both changes are under 0.01 and negative, so I recommend dropping the feature. It stays in this pipeline so the exercise test and the before/after table match `reports/metrics.json`.
- 2026-11-25: Left `CLAUDE.md` unchanged. `cnt_roll_3` is a shifted rolling mean of past `cnt`, which the existing lag rule already requires.
- 2026-11-25: Pin `RAW_SHA256` and check it in `load_raw`. A `cp` into `data/raw/` from Bash is invisible to the PostToolUse hook, whose matcher is `Edit|Write` and whose script only runs leakage tests for `src/*.py`. The hash check makes `make data` fail when those bytes change. Left out of `CLAUDE.md` because the check is code, not a reminder.
- 2026-11-25: Exercise 4 models `cnt - cnt_lag_1` and adds `cnt_lag_1` back, behind `python -m src.train --target residual`, which does not write `reports/metrics.json`. Chosen on validation: hgb R² 0.1983 → 0.6251, ridge stays 0.6445; `log(cnt)` left hgb at 0.1617 and was dropped before the test split. The change is a defensible forecast of the day-to-day innovation and a different question from the raw-level comparison, so the committed metrics stay untransformed. Test was scored once after the choice: hgb R² 0.567, ridge 0.5831, persistence 0.5099.
