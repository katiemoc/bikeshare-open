# Results

The newly engineered feature `cnt_roll_3` represents the rolling average of total daily bike rentals across the three calendar days immediately preceding the forecast date. In the table below, the label "before" refers to the baseline feature set of fourteen columns provided in the starter repository. The label "after" denotes the feature set with `cnt_roll_3` incorporated, matching the evaluation stored in `reports/metrics.json`. Because the baseline models rely strictly on the historical training mean and the immediate prior day count rather than the rolling aggregate, their performance metrics remain identical across both evaluations.

| Model | Set | Valid R² | Valid MAE | Test R² | Test MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| baseline_mean | before | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| baseline_mean | after | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| baseline_persistence | before | 0.4507 | 900.6 | 0.5099 | 840.1 |
| baseline_persistence | after | 0.4507 | 900.6 | 0.5099 | 840.1 |
| ridge | before | 0.6475 | 832.9 | 0.5833 | 947.1 |
| ridge | after | 0.6439 | 836.5 | 0.58 | 946.2 |
| hgb | before | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| hgb | after | 0.1983 | 1311.6 | -0.5338 | 1998.7 |

# Headline finding

When evaluated on the second half of 2012 after training exclusively on 2011 data, the historical mean baseline achieves an R² of -2.1441 and a mean absolute error of 2847.7 rides. This negative score demonstrates that relying on an unadjusted historical average fails once ridership experiences substantial growth. In contrast, the naive persistence baseline, which predicts yesterday's count directly, achieves an R² of 0.5099 and an MAE of 840.1. Ridge regression produces an R² of 0.5800 and an MAE of 946.2, outperforming persistence by 0.07 in R² but yielding higher absolute errors on average. The gradient boosting model (HistGradientBoostingRegressor) posts an R² of -0.5338 and an MAE of 1998.7. While gradient boosting outperforms the naive mean baseline, it fails relative to Ridge regression because decision tree ensembles cannot predict values outside the range of targets observed during training. Because daily ridership in the second half of 2012 exceeds the 2011 training maximum on 56.52 percent of the test dates, the tree model hits an artificial ceiling. Incorporating `cnt_roll_3` shifted validation R² from 0.6475 to 0.6439 for Ridge regression (a decrease of 0.0036) and from 0.2185 to 0.1983 for gradient boosting (a decrease of 0.0202). Because both changes are negative and fall short of the required 0.01 threshold, I recommend discarding the feature; the column remains present in the code so that the verification tests and the table above remain aligned with `reports/metrics.json`.

# Exercise 4: target transformation

The primary structural obstacle facing tree-based models in this time series task is the growth of overall ridership between 2011 and 2012. In the 2011 training dataset, the maximum single-day ridership count was 6,043 rides. Tree ensembles predict by averaging targets in terminal leaves, which makes it mathematically impossible for them to output any value higher than the training maximum. During the validation period covering the first half of 2012, 39.01 percent of days (71 out of 182) exceed 6,043 rides, causing the gradient booster to cap its predictions at a maximum of 5,596 rides.

Before touching the test dataset, two alternative target transformations were evaluated on the validation split and subsequently discarded. Modeling the natural logarithm of the target, `log(cnt)`, failed to address the extrapolation constraint because taking the exponential of the leaf predictions merely mapped back to the 6,043 ceiling, leaving the model with a validation R² of 0.1617 and a prediction maximum of 5,625 rides. Predicting the multiplicative ratio `cnt / cnt_lag_1` raised the booster's validation R² to 0.6167, but it destabilized Ridge regression, driving its validation R² down to -1.2933 due to small denominator values on low-ridership winter days.

The transformation I selected is the additive day-to-day difference, `cnt - cnt_lag_1`, which is converted back into daily counts at prediction time by adding `cnt_lag_1`. Because yesterday's total is fully known prior to making a forecast, this adjustment is operationally feasible. On the validation partition, Ridge regression maintains an R² of 0.6445 and an MAE of 835.5 (compared to 0.6439 and 836.5 on raw counts), while gradient boosting improves dramatically from an R² of 0.1983 and an MAE of 1311.6 to an R² of 0.6251 and an MAE of 805.4. This transformation succeeds because only 2.2 percent of day-to-day differences in the validation set fall outside the range of differences observed in 2011. The tree model is now predicting the local innovation, which is a quantity it has actually encountered during training.

Forecasting the day-to-day change is a defensible methodological choice because the reference level is supplied by an operationally valid lag, and performance is judged on reconstructed daily totals. At the same time, this choice fundamentally reformulates the modeling question: the tree is no longer learning the growth trend from calendar and weather features, but is instead relying on the lag to carry the ridership level into 2012. Because this shifts the nature of the model comparison, I kept the primary metrics in `reports/metrics.json` untransformed.

The held-out test split was evaluated exactly once after finalizing this choice. In the test period, 56.52 percent of daily counts exceed the 2011 training maximum. When evaluating reconstructed daily counts, gradient boosting achieves a test R² of 0.5670 with an MAE of 883.8, Ridge regression achieves an R² of 0.5831 with an MAE of 942.1, and persistence records an R² of 0.5099 with an MAE of 840.1. By forecasting the day-to-day difference, gradient boosting remains competitive with Ridge regression on R², although persistence still records the lowest mean absolute error overall.

# Exercise 5: ridge vs persistence

Based on the empirical test results, the Capital Bikeshare system should deploy the naive persistence baseline rather than the Ridge regression model. In the test partition, Ridge regression achieves an R² of 0.5800 and an MAE of 946.2, whereas persistence scores an R² of 0.5099 and an MAE of 840.1. While Ridge holds a nominal advantage of 0.07 in R², its predictions are off by an additional 106.1 rides per day on average compared to persistence. Furthermore, persistence produces a more accurate forecast on 113 of the 184 test days, and its median absolute error of 506.5 rides is considerably better than Ridge's median absolute error of 890.6 rides.

An inspection of the model errors reveals that Ridge regression suffers from a consistent downward bias during the 2012 expansion. Although Ridge predictions correlate strongly with `cnt_lag_1` at 0.895, they average 551 rides below actual demand, whereas persistence overpredicts actual demand by only 16 rides on average. The standardized coefficients for Ridge are dominated by lagged demand features, specifically `cnt_roll_7` at 375 and `cnt_lag_1` at 285, while `weather_severity` carries a negative weight of -284. In practice, Ridge functions as a noisy version of persistence whose weather adjustments systematically drag predictions downward in a growing system. Although validation MAE initially favored Ridge over persistence (836.5 versus 900.6), that advantage does not hold across the actual forecast horizon. When operational costs depend on absolute error magnitudes rather than squared deviations, persistence represents the superior forecasting strategy.

# Attribution

Model: `bikeshare-coder` (built from `qwen3.5:9b` with a 64k context window running locally via Ollama); no model switch occurred during the project.

### Components Generated by the Agent
- In `src/features.py`, the agent implemented the feature calculation logic for `cnt_roll_3`, computing a three-day rolling average shifted by one day to avoid target leakage.
- In `tests/test_leakage.py`, the agent authored the unit test `test_cnt_roll_3_on_named_date`, verifying that the rolling feature matches hand-calculated historical values strictly prior to the forecast date.
- In `src/train.py`, the agent implemented the `fit_residual()` function and added the `--target residual` command-line option to train models on day-to-day increments and invert them at inference time for Exercise 4.
- In `src/ingest.py`, the agent implemented the SHA256 integrity check within `load_raw()` to verify the raw data file against `RAW_SHA256`.
- In `tests/test_contract.py`, the agent created `test_no_unclassified_raw_columns` to ensure that every column in the raw CSV is accounted for in the configuration.
- In `.claude/skills/ablation/SKILL.md`, the agent defined the ablation workflow skill to automate measuring validation deltas when removing individual features.

### Methodological Decisions Made by Me
Every decision below corresponds directly to an entry recorded in `docs/DECISIONS.md`:
1. Excluded `casual` and `registered` from feature candidates because their sum equals the target count `cnt` exactly, which constitutes trivial data leakage. In addition, excluded `cnt_2d_bfr` because the alignment of that lag in the mirror data cannot be independently verified.
2. Excluded raw time index columns (`instant`, `yr`, and `days_since_2011`) to prevent decision trees from memorizing arbitrary time splits and to stop linear models from extrapolating an unverified secular trend.
3. Structured the dataset split chronologically into 2011 training data, first-half 2012 validation data, and second-half 2012 test data, holding out the test partition until all feature choices were complete.
4. Required reporting both the historical mean baseline and the naive persistence baseline alongside all model evaluations to provide honest benchmarks for time series forecasting.
5. Evaluated `cnt_roll_3` using past information, observed validation R² drops of 0.0036 for Ridge and 0.0202 for gradient boosting, and decided to recommend discarding the feature because it failed to achieve the 0.01 improvement threshold.
6. Selected the additive difference `cnt - cnt_lag_1` for Exercise 4 after validation screening showed it reduced out-of-range targets to 2.2 percent and restored tree performance, while deciding to keep committed metrics untransformed because it addresses a different modeling objective.
7. Decided against deploying Ridge regression in Exercise 5 because the persistence heuristic achieves lower mean absolute error, lower median error, and superior accuracy on 113 of 184 test days.
8. Pinned `RAW_SHA256` and introduced hash validation in `src/ingest.py` to prevent shell commands from quietly altering raw input data.
9. Explicitly defined `RAW_FEATURE_COLS` in `src/config.py` and instituted contract verification in `tests/test_contract.py` so that unclassified raw columns cannot enter the feature pipeline unnoticed.
10. Maintained `CLAUDE.md` as a concise set of non-negotiable operational rules under 60 lines, documenting only essential operational commands and non-negotiable rules.
