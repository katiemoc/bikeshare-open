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
