"""Stage 3: temporal split, fit, evaluate, write metrics.

Two baselines and two models, on purpose.

  baseline_mean         predict the 2011 average for every day
  baseline_persistence  predict yesterday's count (cnt_lag_1)
  ridge                 standardised linear model on the audited features
  hgb                   gradient-boosted trees on the same features

The mean baseline shows what "the distribution moved" costs. Persistence
is the baseline that actually matters: ridge's features are dominated by
lagged demand, so if it cannot beat "yesterday again" it has learned
nothing worth reporting. The booster is there because it fails, and the
reason it fails is the headline result.

Run: python -m src.train
    writes reports/metrics.json for the untransformed target.

    python -m src.train --target residual
    fits ridge and gradient boosting on cnt - cnt_lag_1, adds the lag
    back, and prints validation scores only. --include-test scores the
    test split as well. That path does not write metrics.json.
"""
import argparse
import json

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import METRICS, PROCESSED, TARGET, TRAIN_END, VALID_END
from src.features import feature_columns


class PersistenceBaseline(BaseEstimator, RegressorMixin):
    """Predict a single lagged column unchanged. Nothing is fit."""

    def __init__(self, column: str = "cnt_lag_1"):
        self.column = column

    def fit(self, X, y=None):
        if self.column not in X.columns:
            raise ValueError(f"persistence baseline needs column {self.column!r}")
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


MODELS = {
    "baseline_mean": DummyRegressor(strategy="mean"),
    "baseline_persistence": PersistenceBaseline("cnt_lag_1"),
    "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "hgb": HistGradientBoostingRegressor(random_state=0, max_iter=300),
}


def temporal_split(df: pd.DataFrame):
    """Split by date, never at random. A random split on a time series
    puts tomorrow in train and today in test."""
    train = df[df.dteday <= TRAIN_END]
    valid = df[(df.dteday > TRAIN_END) & (df.dteday <= VALID_END)]
    test = df[df.dteday > VALID_END]
    return train, valid, test


def fit_and_score() -> dict:
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, test = temporal_split(df)

    results = {
        "n_features": len(cols),
        "features": cols,
        "n_train": len(train),
        "n_valid": len(valid),
        "n_test": len(test),
    }
    for name, model in MODELS.items():
        model.fit(train[cols], train[TARGET])
        results[name] = {
            split: {
                "r2": round(float(r2_score(part[TARGET], model.predict(part[cols]))), 4),
                "mae": round(float(mean_absolute_error(part[TARGET], model.predict(part[cols]))), 1),
            }
            for split, part in [("valid", valid), ("test", test)]
        }
    return results


def _fresh_models() -> dict:
    """New estimators. The module-level MODELS dict is what the tests fit."""
    return {
        "baseline_mean": DummyRegressor(strategy="mean"),
        "baseline_persistence": PersistenceBaseline("cnt_lag_1"),
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "hgb": HistGradientBoostingRegressor(random_state=0, max_iter=300),
    }


def fit_residual(include_test: bool = False) -> dict:
    """Score cnt after training ridge and hgb on the day-to-day change.

    Yesterday's count is known at prediction time, so the reconstructed
    forecast is cnt_lag_1 plus the predicted change. The mean and
    persistence baselines stay forecasts of cnt itself. Nothing is written
    to reports/metrics.json.
    """
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, test = temporal_split(df)
    models = _fresh_models()
    delta = train[TARGET] - train["cnt_lag_1"]
    models["baseline_mean"].fit(train[cols], train[TARGET])
    models["baseline_persistence"].fit(train[cols], train[TARGET])
    models["ridge"].fit(train[cols], delta)
    models["hgb"].fit(train[cols], delta)

    def predict_cnt(name: str, part: pd.DataFrame):
        raw = models[name].predict(part[cols])
        if name in {"ridge", "hgb"}:
            return part["cnt_lag_1"].to_numpy(dtype=float) + raw
        return raw

    scored = [("valid", valid)]
    if include_test:
        scored.append(("test", test))
    results = {"target": "cnt - cnt_lag_1", "include_test": include_test}
    train_max = float(train[TARGET].max())
    for split, part in scored:
        y = part[TARGET].to_numpy(dtype=float)
        results[split] = {}
        results[f"{split}_above_train_max"] = round(float((y > train_max).mean()), 4)
        for name in models:
            pred = predict_cnt(name, part)
            results[split][name] = {
                "r2": round(float(r2_score(y, pred)), 4),
                "mae": round(float(mean_absolute_error(y, pred)), 1),
            }
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("identity", "residual"), default="identity")
    parser.add_argument(
        "--include-test",
        action="store_true",
        help="with --target residual, also score the held-out test split",
    )
    args = parser.parse_args()
    if args.target == "identity":
        res = fit_and_score()
        METRICS.parent.mkdir(parents=True, exist_ok=True)
        METRICS.write_text(json.dumps(res, indent=2))
        print(json.dumps({k: v for k, v in res.items() if k != "features"}, indent=2))
    else:
        print(json.dumps(fit_residual(include_test=args.include_test), indent=2))
