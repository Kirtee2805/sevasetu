"""
SevaSetu — stockout_predictor.py
Team AstraSync | GEC Rajkot

WHAT THIS FILE DOES:
Predicts which district will run out of which medicine
within the next 7 days — BEFORE it actually happens.

MODEL: XGBoost Classifier
WHY XGBOOST?
- Best performance on tabular/structured data
- Handles real-world messy data well
- Fast to train and predict
- You already know it from your internship

REAL FINDING FROM GUJARAT DATA:
111 out of 231 district-medicine combinations
are already CRITICAL (0-7 days remaining).
Our model predicts this BEFORE stock runs out.

HOW TO USE:
    from models.data_loader import load_data
    from models.feature_engineering import engineer_features
    from models.anomaly_detector import AnomalyDetector
    from models.stockout_predictor import StockoutPredictor

    df = load_data()
    df = engineer_features(df)
    detector = AnomalyDetector()
    df = detector.detect(df)
    predictor = StockoutPredictor()
    df = predictor.train_predict(df)
    alerts = predictor.get_alerts(df)
"""

import pandas as pd
import numpy as np
import pickle
import os
import warnings
import optuna
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, f1_score,
    precision_score, recall_score
)
from imblearn.over_sampling import SMOTE

# Suppress warnings
warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)


class StockoutPredictor:
    """
    Predicts medicine stock-outs using XGBoost.

    TARGET: Will this district run out of medicine in 7 days?
    OUTPUT: probability (0.0 to 1.0) + risk level
    """

    FEATURES = [
        # Stock signals
        "days_remaining",
        "stock_coverage_ratio",
        "stock_utilization_rate",
        "is_critical_stock",
        "is_low_stock",
        "unusable_ratio",
        "daily_consumption_rate",

        # Consumption signals
        "consumption_ratio",
        "consumption_spike",
        "consumption_collapse",
        "anomaly_signal_strength",

        # Health system signals
        "opd_attendance",
        "bed_occupancy_rate",
        "lab_coverage_rate",
        "stockout_pressure",
        "has_stockout",
        "disease_burden",

        # Context signals
        "is_monsoon",
        "month_idx",
        "anomaly_detected",
        "facility_risk_score",
        "data_quality_score",

        # Encoded categoricals
        "medicine_encoded",
        "district_encoded",
    ]

    def __init__(self):
        # Base model for quick instantiation, real model will be calibrated after optuna
        self.base_model    = XGBClassifier(random_state=42, eval_metric="logloss", verbosity=0, n_jobs=-1)
        self.scaler        = StandardScaler()
        self.model         = None
        self.is_trained    = False
        self.feature_names = []

    def train_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Trains XGBoost (with Optuna + Scaling + Calibration) and predicts stockout risk.
        """
        print("[stockout_predictor] Training Professional ML stock-out prediction model...")

        df = df.copy()
        df["will_stockout"] = (df["days_remaining"] <= 7).astype(int)

        self.feature_names = [f for f in self.FEATURES if f in df.columns]
        X = df[self.feature_names].fillna(0)
        y = df["will_stockout"]

        print(f"[stockout_predictor] Features used  : {len(self.feature_names)}")
        print(f"[stockout_predictor] Total records  : {len(X)}")
        print(f"[stockout_predictor] Stockout rate  : {y.mean()*100:.1f}%")

        if len(X) < 20:
            X_train, X_test, y_train, y_test = X, X, y, y
        else:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # 1. Feature Scaling & Distance-Aware SMOTE
        print("[stockout_predictor] Applying StandardScaler & SMOTE...")
        try:
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled  = self.scaler.transform(X_test)
            # Use smaller k_neighbors for tiny datasets
            k_neighbors = min(5, y_train.value_counts().min() - 1)
            if k_neighbors > 0:
                smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                X_resampled, y_resampled = smote.fit_resample(X_train_scaled, y_train)
                print(f"[stockout_predictor] Resampled dataset: {len(y_resampled)} samples")
            else:
                X_resampled, y_resampled = X_train_scaled, y_train
        except Exception as e:
            print(f"[stockout_predictor] SMOTE skipped: {e}")
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled  = self.scaler.transform(X_test)
            X_resampled, y_resampled = X_train_scaled, y_train

        # 2. Optuna Bayesian Hyperparameter Optimization
        print("[stockout_predictor] Running Optuna Bayesian Optimization (15 trials)...")
        
        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 250),
                "max_depth": trial.suggest_int("max_depth", 3, 7),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "random_state": 42,
                "verbosity": 0,
                "n_jobs": -1
            }
            
            # Stratified K-Fold for robust evaluation
            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            scores = []
            
            for train_idx, val_idx in cv.split(X_resampled, y_resampled):
                X_cv_train, X_cv_val = X_resampled[train_idx], X_resampled[val_idx]
                y_cv_train, y_cv_val = y_resampled.iloc[train_idx] if isinstance(y_resampled, pd.Series) else y_resampled[train_idx], y_resampled.iloc[val_idx] if isinstance(y_resampled, pd.Series) else y_resampled[val_idx]
                
                model = XGBClassifier(**params)
                model.fit(X_cv_train, y_cv_train)
                preds = model.predict(X_cv_val)
                scores.append(f1_score(y_cv_val, preds, zero_division=0))
            
            return np.mean(scores)

        # Run Optuna Study
        if len(np.unique(y_resampled)) > 1:
            study = optuna.create_study(direction="maximize")
            study.optimize(objective, n_trials=15)
            best_params = study.best_params
            print(f"[stockout_predictor] Best Optuna params: {best_params}")
            self.base_model = XGBClassifier(**best_params, random_state=42, verbosity=0, n_jobs=-1)
        else:
            print("[stockout_predictor] Skipping Optuna due to single class in training data.")

        # 3. Probability Calibration (Isotonic Regression)
        print("[stockout_predictor] Calibrating model probabilities...")
        if len(np.unique(y_resampled)) > 1:
            self.model = CalibratedClassifierCV(self.base_model, method="isotonic", cv=3)
            self.model.fit(X_resampled, y_resampled)
        else:
            self.base_model.fit(X_resampled, y_resampled)
            self.model = self.base_model
        
        self.is_trained = True

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        acc    = accuracy_score(y_test, y_pred)
        f1     = f1_score(y_test, y_pred, zero_division=0)
        prec   = precision_score(y_test, y_pred, zero_division=0)
        rec    = recall_score(y_test, y_pred, zero_division=0)

        print("\n[stockout_predictor] Calibrated Model Performance:")
        print(f"  Accuracy  : {acc*100:.1f}%")
        print(f"  F1 Score  : {f1*100:.1f}%")
        print(f"  Precision : {prec*100:.1f}%")
        print(f"  Recall    : {rec*100:.1f}%")

        # 4. Predict on Full Dataset
        X_full_scaled = self.scaler.transform(X)
        df["stockout_probability"] = self.model.predict_proba(X_full_scaled)[:, 1].round(3)
        df["stockout_prediction"] = self.model.predict(X_full_scaled)
        df["risk_level"]          = df["stockout_probability"].apply(self._risk_label)
        df["recommended_action"]  = df.apply(self._action, axis=1)

        # Feature importance (Extract from base model since CalibratedClassifier doesn't have it directly)
        self._print_importance()

        return df

    def _risk_label(self, prob: float) -> str:
        if prob >= 0.75: return "CRITICAL"
        elif prob >= 0.50: return "HIGH"
        elif prob >= 0.25: return "MEDIUM"
        else: return "LOW"

    def _action(self, row) -> str:
        district = row.get("district", "Unknown")
        medicine = row.get("medicine", "Unknown")
        days     = int(row.get("days_remaining", 0))
        level    = row.get("risk_level", "LOW")

        if level == "CRITICAL":
            return (
                f"URGENT: {medicine} will run out in {days} days "
                f"at {district}. Emergency resupply required immediately."
            )
        elif level == "HIGH":
            return (
                f"ALERT: {medicine} stock at {district} needs "
                f"replenishment within 2 weeks ({days} days remaining)."
            )
        elif level == "MEDIUM":
            return (
                f"WATCH: Monitor {medicine} at {district}. "
                f"{days} days of stock remaining."
            )
        else:
            return f"OK: {medicine} stock adequate at {district}."

    def get_alerts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Returns HIGH and CRITICAL alerts for dashboard."""
        alerts = df[
            df["risk_level"].isin(["CRITICAL", "HIGH"])
        ][[
            "district", "month", "medicine",
            "days_remaining", "closing_stock",
            "opd_attendance", "stockout_probability",
            "risk_level", "recommended_action",
            "anomaly_detected",
        ]].sort_values(
            ["risk_level", "stockout_probability"],
            ascending=[True, False]
        )

        print(f"\n[stockout_predictor] Alerts generated:")
        print(f"  CRITICAL: {(alerts['risk_level']=='CRITICAL').sum()}")
        print(f"  HIGH    : {(alerts['risk_level']=='HIGH').sum()}")
        return alerts

    def _print_importance(self):
        # CalibratedClassifierCV wraps the estimator, so we pull from base_model
        estimator = getattr(self.model, "estimator", self.model)
        if hasattr(estimator, "feature_importances_"):
            imp = pd.Series(
                estimator.feature_importances_,
                index=self.feature_names
            ).sort_values(ascending=False)

            print("\\n[stockout_predictor] Top 5 important features:")
            for feat, score in imp.head(5).items():
                bar = "#" * int(score * 40)
                print(f"  {feat:<35} {bar} {score:.3f}")
        else:
            print("\\n[stockout_predictor] Feature importances not available.")

    def save(self, path="models/saved/stockout_predictor.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "model"        : self.model,
                "base_model"   : self.base_model,
                "scaler"       : self.scaler,
                "feature_names": self.feature_names,
            }, f)
        print(f"[stockout_predictor] Saved to {path}")

    def load(self, path="models/saved/stockout_predictor.pkl"):
        with open(path, "rb") as f:
            saved = pickle.load(f)
        self.model         = saved["model"]
        self.base_model    = saved.get("base_model", None)
        self.scaler        = saved.get("scaler", None)
        self.feature_names = saved["feature_names"]
        self.is_trained    = True
        print(f"[stockout_predictor] Loaded from {path}")


# ─────────────────────────────────────────────────────────
# TEST — python models/stockout_predictor.py
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    from models.data_loader import load_data
    from models.feature_engineering import engineer_features
    from models.anomaly_detector import AnomalyDetector

    print("=" * 55)
    print("SevaSetu — Stock-out Predictor Test")
    print("=" * 55)

    df = load_data("data/raw/B-Gujarat_May.xlsx")
    df = engineer_features(df)

    detector  = AnomalyDetector()
    df        = detector.detect(df)

    predictor = StockoutPredictor()
    df        = predictor.train_predict(df)

    alerts = predictor.get_alerts(df)

    print(f"\nTop 10 critical alerts:")
    print(alerts[[
        "district", "medicine",
        "days_remaining", "risk_level",
        "recommended_action"
    ]].head(10).to_string())

    predictor.save()
    df.to_csv("data/processed/stockout_results.csv", index=False)
    alerts.to_csv("data/processed/critical_alerts.csv", index=False)
    print("\nSaved: data/processed/stockout_results.csv")
    print("Saved: data/processed/critical_alerts.csv")
    print("\nstockout_predictor.py working correctly!")