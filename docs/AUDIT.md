# Audit

## Teammate

Repository: https://github.com/roynguyenn/bikeshare-open

`/leakage-auditor` was run from a clone of that repo, with `bikeshare-coder`, against `src/config.py`, `src/features.py`, `src/train.py`, and `tests/`. It reported no finding. Verbatim:

```
Based on my careful reading of all files in this repository, here is my audit against the five checks:

## Summary: All Five Checks Pass

1. **Target leakage** ✓ - `casual + registered == cnt` is exactly enforced; forbidden columns excluded via `feature_columns()`; all lags use `.shift(1)` before aggregation.

2. **Temporal ordering** ✓ - `temporal_split()` uses date thresholds (not random); models fitted only on training data; baselines are not transformer pipelines that could see future data.

3. **Calendar gaps** ✓ - `reindex_to_calendar()` fills calendar gaps before lagging; `.shift(1)` operates on gap-free index; dropped rows accounted for in test at lines 40-44 of test_contract.py.

4. **Silent row loss** ✓ - Row loss bounded by warmup + missing days assertion; weather encoder raises on unknown labels rather than silently dropping (verified by pytest.raises).

5. **Unreported baseline** ✓ - Both `baseline_mean` and `baseline_persistence` are in MODELS dictionary; both scored with R²/MAE in valid/test splits.

The code adheres to all requirements in CLAUDE.md: no leakage, temporal splits only, calendar-gap-aware lags, row-loss assertions, and both baselines reported alongside each model.
```

### Verdict

I agree: nothing here changes a score by leakage, a random split, a same-day window, a silent row drop, or a missing baseline. `casual`, `registered`, and `cnt` stay out of `feature_columns`. `cnt_roll_7` and `cnt_roll_28` are `.shift(1).rolling(...)` after `reindex_to_calendar`, and `cnt_lag_7` is `.shift(7)`. `temporal_split` cuts on `2011-12-31` and `2012-06-30`. The scaler sits inside the pipeline and is fit on the training rows only. `reports/metrics.json` is the untransformed run and includes both baselines. The 28-day warmup changes the training mean (306 training rows, test mean-baseline R² −1.7717), and that number is the feature's warmup, not a leak.

## Own repo

Command, from the repo root, against the local `bikeshare-coder` model:

```
python agent/audit.py . --out reports/audit.jsonl --concurrency 1
```

`reports/audit.jsonl` is one line. The script printed `audited 1 repos; 0 flagged`.

```json
{"repo": "bikeshare-open", "leakage": "none", "temporal_ok": true, "baseline_reported": true, "reproducible": true, "findings": [{"file": "N/A", "issue": "No leakage detected", "line": 0, "why_it_matters": "Model does not have access to target or its components"}, {"file": "N/A", "issue": "Temporal validity maintained", "line": 0, "why_it_matters": "Data splits respect time ordering, preventing future data leakage"}, {"file": "N/A", "issue": "Baselines reported", "line": 0, "why_it_matters": "Mean and persistence baselines provide context for model performance"}, {"file": "N/A", "issue": "Pipeline is reproducible", "line": 0, "why_it_matters": "Documented commands and pinned dependencies ensure consistent results"}], "confidence": "high"}
```

## Verdict

None of these findings change a number. `leakage` is `none`, and the three booleans are true, which matches the pipeline: forbidden columns stay out of `feature_columns`, lags are shifted on a calendar index, the split is by date, and `reports/metrics.json` includes the mean and persistence baselines. The four `findings` entries are those same checks restated, each with file `N/A` and line 0, so they do not name a defect. I agree with the pass, and there is nothing in this run to fix.
