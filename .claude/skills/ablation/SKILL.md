---
name: ablation
description: Evaluate the validation delta from dropping a feature from the modelling set. Use when evaluating feature importance or deciding whether to keep a predictor.
allowed-tools: Read, Edit, Bash(make*), Bash(python -m src.*)
---

# Feature Ablation: $ARGUMENTS

Follow this procedure to measure the effect of removing `$ARGUMENTS` from the feature set:

1. **Verify feature existence:**
   Confirm that `$ARGUMENTS` is present in the current feature set returned by `src.features.feature_columns`.

2. **Record baseline metrics:**
   Read `reports/metrics.json` to note current validation R^2 and MAE for `ridge` and `hgb`.

3. **Ablate the feature:**
   Temporarily exclude `$ARGUMENTS` from `feature_columns` in `src/features.py` (e.g. by filtering it out from `feature_columns` or commenting out its definition in `build_features`).

4. **Retrain and evaluate:**
   Run `make features && python -m src.train` to evaluate the pipeline without `$ARGUMENTS`.

5. **Report validation delta:**
   Compute:
   - $\Delta R^2_{\text{valid}} = R^2_{\text{ablated}} - R^2_{\text{baseline}}$ for ridge and hgb.
   - If $|\Delta R^2| < 0.01$, report that the feature has negligible impact.
   - If $\Delta R^2 > 0$ when dropped, report that the feature was harming performance.

6. **Restore or record:**
   Revert the edit to `src/features.py` unless the decision is to permanently drop the feature, in which case record the decision in `docs/DECISIONS.md`.
