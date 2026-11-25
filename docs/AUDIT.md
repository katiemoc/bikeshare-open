# Audit

The teammate `/leakage-auditor` run is not in this file. It was skipped on request.

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
