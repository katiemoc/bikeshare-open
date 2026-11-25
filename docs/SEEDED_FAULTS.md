# Seeded faults

## Exercise 1: `cnt_roll_3` test written before the feature

`tests/test_leakage.py::test_cnt_roll_3_on_named_date` was added while `src/features.py` still had no `cnt_roll_3` column. `make test` failed on that column and on nothing else. The hand-check asserts above the lookup had already passed: on 2011-07-04 the three prior counts are 4649, 5119, and 5362.

```
python -m pytest tests/ -q
.........F.....                                                          [100%]
=================================== FAILURES ===================================
________________________ test_cnt_roll_3_on_named_date _________________________
        assert expected == pytest.approx((4649 + 5119 + 5362) / 3)
        assert float(by_date.loc[date, TARGET]) == 6043
>       assert by_date.loc[date, "cnt_roll_3"] == pytest.approx(expected)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_leakage.py:74:
E           KeyError: 'cnt_roll_3'
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_cnt_roll_3_on_named_date - KeyError: 'cnt_...
1 failed, 14 passed in 1.16s
make: *** [test] Error 1
```

The feature was then implemented as `out[TARGET].shift(1).rolling(3).mean()` after `reindex_to_calendar`. `make test` then reported `15 passed`.

## Exercise 2

Each seed was applied to `src/features.py`, then reverted. The hook is the starter script, run with the PostToolUse JSON on stdin (`CLAUDE_PROJECT_DIR` set to the repo). It reruns only `tests/test_leakage.py`. Full-suite output is from `python -m pytest tests/ -q --tb=line`. After all four faults, `data/raw/bike_daily.csv` was back to sha256 `a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc` and `make test` reported `15 passed`.

The repair for each source fault was one edit that put the original lines back after the failure text was on screen. That is the turn count below.

### Fault 1: forbidden column added to `feature_columns`

`return [c for c in numeric if c not in FORBIDDEN]` was replaced with:

```python
cols = [c for c in numeric if c not in FORBIDDEN]
cols.append("casual")
return cols
```

`casual` is in `LEAKAGE_COLS`. One test failed.

```
.....F.........                                                          [100%]
=================================== FAILURES ===================================
E   AssertionError: forbidden columns in feature set: {'casual'}
    assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})
/Users/wwidjaja0/Downloads/bikeshare-open/tests/test_leakage.py:31: AssertionError: forbidden columns in feature set: {'casual'}
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 14 passed in 0.72s
```

Hook stderr (exit 2). The hook's own pytest run is `tests/test_leakage.py` only, so the count is 7 passed rather than 14:

```
Leakage tests failed after editing /Users/wwidjaja0/Downloads/bikeshare-open/src/features.py:
feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_3   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...     134....333333  1530.142857
713 2012-12-31    731.0  WINTER  ...      920.0  2077.333333  1531.428571

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 7 passed in 0.23s
```

Turns to fix: 1. Deleted `cols.append("casual")` and restored the original `return`.

### Fault 2: `.shift(1)` deleted from `cnt_roll_7`

```python
out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
```

The rolling window then includes the current day. `cnt_roll_3` was left shifted.

```
........F......                                                          [100%]
=================================== FAILURES ===================================
E   assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486

      comparison failed
      Obtained: 4389.0
      Expected: 4414.857142857143 ± 0.00441486
/Users/wwidjaja0/Downloads/bikeshare-open/tests/test_leakage.py:57: assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 14 passed in 0.72s
```

Hook stderr (exit 2):

```
Leakage tests failed after editing /Users/wwidjaja0/Downloads/bikeshare-open/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.23s
```

Turns to fix: 1. Put `.shift(1)` back on `cnt_roll_7`.

### Fault 3: weather encoder's `raise` removed

Deleted the unknown-label check and left the map untouched:

```python
return series.map(WEATHER_ORDER).astype(float)
```

`GOOD`, `MISTY`, and `BAD` are all in `WEATHER_ORDER`, so no new NaNs appear. The suite stayed green and the hook wrote nothing.

```
...............                                                          [100%]
15 passed in 0.71s
```

Hook exit code: 0. Stderr was empty.

That seed does not make a test red. The silent deletion in the lesson also drops `BAD` out of the map, which is what lets `dropna` remove those days. Replaced the same block with:

```python
order = {"GOOD": 0, "MISTY": 1}
return series.map(order).astype(float)
```

`test_only_expected_rows_are_dropped` then failed. 34 lost rows is the usual 14 plus the 20 `BAD` days.

```
.F.............                                                          [100%]
=================================== FAILURES ===================================
E   AssertionError: lost 34 rows; expected at most 14
    assert 34 <= 14
/Users/wwidjaja0/Downloads/bikeshare-open/tests/test_contract.py:43: AssertionError: lost 34 rows; expected at most 14
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_only_expected_rows_are_dropped - Assertio...
1 failed, 14 passed in 0.71s
```

Hook exit code: 0. Stderr was empty. `test_only_expected_rows_are_dropped` lives in `tests/test_contract.py`, and `check_leakage.sh` runs `tests/test_leakage.py` only.

Turns to fix: 1. Restored the `WEATHER_ORDER` map and the `raise`. The hook did not ask for that edit; the contract-test output did.

### Fault 4: `cp` into `data/raw/` from Bash

The PostToolUse matcher is `Edit|Write`. A shell copy never starts `check_leakage.sh`. Feeding the hook a Bash payload also exits 0, because the script only continues when `tool_input.file_path` matches `src/*.py`.

A mutated copy was written over the raw csv. `cp` succeeded. The hook did not run the tests.

```
cp /tmp/bikeshare-faults/mut.csv data/raw/bike_daily.csv
CP_EXIT:0
799a5fc8f1007f21182bff55bc065ee8130cadb27eb7a755ccc44b7eb933d5c1  data/raw/bike_daily.csv
```

```
echo '{"tool_name":"Bash","tool_input":{"command":"cp /tmp/bikeshare-faults/mut.csv data/raw/bike_daily.csv"}}' | .claude/hooks/check_leakage.sh
HOOK_EXIT:0
```

Stdout and stderr were both empty.

What catches it:

- A PreToolUse hook whose matcher is `Bash`, rejecting any command that writes under `data/raw/`.
- `chmod -w data/raw`, so `cp` fails in the filesystem. Permission rules in `settings.json` only bind the Edit and Write tools.
- A hash check in `make data`. Implemented below. A Stop hook that runs `make test` catches this only when the new bytes fail a test. A still-valid csv with one changed count can leave the tests green. The hash check fails on any byte change.

`src/config.py` and `src/ingest.py`:

```diff
diff --git a/src/config.py b/src/config.py
index 405de6f..2b2c2c9 100644
--- a/src/config.py
+++ b/src/config.py
@@ -3,6 +3,10 @@ from pathlib import Path

 ROOT = Path(__file__).resolve().parents[1]
 RAW = ROOT / "data" / "raw" / "bike_daily.csv"
+# Full sha256 of the checked-in mirror (prefix a6bed1577f6e4de5). load_raw()
+# refuses a Bash overwrite of this file. The Edit deny rules and the
+# PostToolUse hook do not see that write.
+RAW_SHA256 = "a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc"
 PROCESSED = ROOT / "data" / "processed" / "features.parquet"
 METRICS = ROOT / "reports" / "metrics.json"

diff --git a/src/ingest.py b/src/ingest.py
index 6654075..79dd7d1 100644
--- a/src/ingest.py
+++ b/src/ingest.py
@@ -2,12 +2,13 @@
 
 Run: python -m src.ingest
 """
+import hashlib
 import sys
 import urllib.request
 
 import pandas as pd
 
-from src.config import DATA_URL, RAW
+from src.config import DATA_URL, RAW, RAW_SHA256
 
 EXPECTED_MIN_ROWS = 700
 REQUIRED_COLS = {"dteday", "cnt", "casual", "registered", "temp", "hum", "windspeed"}
@@ -21,6 +22,12 @@ def download(force: bool = False) -> None:
 
 
 def load_raw() -> pd.DataFrame:
+    digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
+    if digest != RAW_SHA256:
+        raise ValueError(
+            f"raw file sha256 is {digest}, expected {RAW_SHA256}. "
+            "data/raw is immutable; change features downstream."
+        )
     df = pd.read_csv(RAW, parse_dates=["dteday"])
```

On the tampered file, `load_raw()` raised:

```
ValueError: raw file sha256 is 799a5fc8f1007f21182bff55bc065ee8130cadb27eb7a755ccc44b7eb933d5c1, expected a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc. data/raw is immutable; change features downstream.
```

The original file was copied back. `shasum` matched `RAW_SHA256`, `load_raw()` returned 728 rows, and `make test` reported `15 passed`.
