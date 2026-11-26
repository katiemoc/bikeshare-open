# Audit

## Teammate Audit

For Exercise 3, I audited Roy Nguyen's repository at https://github.com/roynguyenn/bikeshare-open using the `/leakage-auditor` subagent driven by `bikeshare-coder`. I reviewed their implementation across `src/config.py`, `src/features.py`, `src/train.py`, and the test suite. The auditor returned no methodology violations. Here is the verbatim output from the run:

```text
Based on my careful reading of all files in this repository, here is my audit against the five checks:

## Summary: All Five Checks Pass

1. **Target leakage** ✓ - `casual + registered == cnt` is exactly enforced; forbidden columns excluded via `feature_columns()`; all lags use `.shift(1)` before aggregation.

2. **Temporal ordering** ✓ - `temporal_split()` uses date thresholds (not random); models fitted only on training data; baselines are not transformer pipelines that could see future data.

3. **Calendar gaps** ✓ - `reindex_to_calendar()` fills calendar gaps before lagging; `.shift(1)` operates on gap-free index; dropped rows accounted for in test at lines 40-44 of test_contract.py.

4. **Silent row loss** ✓ - Row loss bounded by warmup + missing days assertion; weather encoder raises on unknown labels rather than silently dropping (verified by pytest.raises).

5. **Unreported baseline** ✓ - Both `baseline_mean` and `baseline_persistence` are in MODELS dictionary; both scored with R²/MAE in valid/test splits.

The code adheres to all requirements in CLAUDE.md: no leakage, temporal splits only, calendar-gap-aware lags, row-loss assertions, and both baselines reported alongside each model.
```

I agree with the auditor's verdict that none of the code changes any metrics through invalid methodology. Their pipeline excludes `casual`, `registered`, and `cnt` from model features, preventing the identity leak. Their engineered features (`cnt_roll_7` and `cnt_roll_28`) properly apply `.shift(1)` after reindexing to a full daily calendar, while `cnt_lag_7` uses `.shift(7)`. The data split is strictly chronological, separating train (2011), validation (first half of 2012), and test (second half of 2012), and the feature scaler is fitted exclusively on the training partition. Their reported metrics file includes both the historical mean and persistence baselines. While their 28-day lag warmup reduces the training set to 306 rows and shifts the training mean, this is an expected mathematical consequence of the window length rather than a data leak or silent row drop.

## Repository Batch Audit

To audit my own repository, I executed the Agent SDK script against the finished project:

```bash
python agent/audit.py . --out reports/audit.jsonl --concurrency 1
```

The run completed with zero flagged issues, generating the following record in `reports/audit.jsonl`:

```json
{"repo": "bikeshare-open", "leakage": "none", "temporal_ok": true, "baseline_reported": true, "reproducible": true, "findings": [{"file": "N/A", "issue": "No leakage detected", "line": 0, "why_it_matters": "Model does not have access to target or its components"}, {"file": "N/A", "issue": "Temporal validity maintained", "line": 0, "why_it_matters": "Data splits respect time ordering, preventing future data leakage"}, {"file": "N/A", "issue": "Baselines reported", "line": 0, "why_it_matters": "Mean and persistence baselines provide context for model performance"}, {"file": "N/A", "issue": "Pipeline is reproducible", "line": 0, "why_it_matters": "Documented commands and pinned dependencies ensure consistent results"}], "confidence": "high"}
```

I reviewed the generated audit results and confirmed that none of the findings alter any reported numbers. The auditor classified leakage as none and marked temporal ordering, baseline reporting, and reproducibility as true with high confidence. The four items in the findings array simply restate the core verification checks rather than naming specific code faults or file locations. This matches the actual state of the repository, where forbidden columns are barred from feature sets, lags are strictly shifted on a complete calendar, and both baselines are tracked alongside model scores in `reports/metrics.json`.
