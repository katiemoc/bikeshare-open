# Results

`cnt_roll_3` is the mean of daily ridership on the three calendar days before the forecast date. "Before" is the starter feature set (14 columns). "After" adds `cnt_roll_3` and is the run in `reports/metrics.json`. Baselines do not use the new column, so their scores are unchanged.

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

On the second half of 2012, after training on 2011, the mean baseline scores R² = −2.1441 (MAE 2847.7): the 2011 average is a poor forecast once ridership has grown. Persistence, yesterday's count, scores R² = 0.5099 and MAE 840.1. Ridge scores R² = 0.58 and MAE 946.2, ahead of persistence by 0.07 R² and behind it on MAE. Gradient boosting scores R² = −0.5338 (MAE 1998.7). It still beats the mean baseline, and it loses to ridge because a tree cannot predict above the highest training target while ridership in 2012 sits above the 2011 maximum on most test days. Adding `cnt_roll_3` moved validation R² from 0.6475 to 0.6439 for ridge (Δ −0.0036) and from 0.2185 to 0.1983 for gradient boosting (Δ −0.0202). Both changes are under the 0.01 bar and negative, so I recommend dropping the feature; the column remains in this pipeline so the test and the table above stay tied to `reports/metrics.json`.

# Exercise 4: target transformation

The 2011 training maximum is 6,043 rides. On the raw target, gradient boosting’s highest validation prediction is 5,596, and 39.01% of validation days (71 of 182) sit above that training maximum, so a leaf average from 2011 cannot reach them. Two other transforms were scored on validation and dropped before the test set was touched. `log(cnt)` left the booster at validation R² 0.1617 with a prediction maximum of 5,625, because the exponential of a training log is still the training maximum of `cnt`. The ratio `cnt / cnt_lag_1` raised the booster to validation R² 0.6167 and sent ridge to −1.2933.

The transform I kept is the day-to-day change, `cnt - cnt_lag_1`, inverted by adding `cnt_lag_1` back. Yesterday’s count is known at prediction time. On validation, ridge stays at R² 0.6445 (MAE 835.5), against 0.6439 (MAE 836.5) on the raw target, and gradient boosting moves from R² 0.1983 (MAE 1,311.6) to R² 0.6251 (MAE 805.4). Only 2.2% of validation changes fall outside the 2011 range of changes, so the tree is now predicting a quantity it saw. That is a defensible forecast of the innovation: the level is carried by a lag that would be known operationally, and the model is scored on the reconstructed count. It is also a different question from the untransformed comparison. The 2012 level arrives through the lag, which is why the booster can now post a number near ridge. I do not replace `reports/metrics.json` with it.

The test split was scored once, after that choice. 56.52% of test days are above the 2011 maximum. On the reconstructed count, gradient boosting reaches test R² 0.567 (MAE 883.8), ridge 0.5831 (MAE 942.1), and persistence 0.5099 (MAE 840.1). The booster now stays with ridge and ahead of persistence on R², and it still loses to persistence on MAE.

# Exercise 5: ridge vs persistence

Deploy yesterday’s count, not ridge. On the committed test scores ridge reaches R² 0.58 and MAE 946.2, against persistence at R² 0.5099 and MAE 840.1: the R² gain is 0.07, and the absolute error is 106.1 rides worse per day. Persistence is closer on 113 of 184 test days, and the median absolute error is 506.5 rides against ridge’s 890.6. Ridge’s test predictions correlate 0.895 with `cnt_lag_1` and average 551 rides too low, while persistence averages 16 rides too high. The largest standardized coefficients are `cnt_roll_7` (375), `cnt_lag_1` (285), and `weather_severity` (−284), so the fit is recent demand adjusted by weather, and that adjustment pulls the 2012 level down. Validation MAE would have chosen ridge (836.5 versus 900.6). That choice does not survive the half-year being forecast.
