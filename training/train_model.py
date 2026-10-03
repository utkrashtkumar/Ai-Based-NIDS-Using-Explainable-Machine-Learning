"""
Model Training Pipeline for AI-NIDS using XGBoost
Trains an optimized Multi-Class XGBoost Classifier with cross-validation
on the curated CIC-IDS2017 benchmark dataset for instant TreeSHAP attribution.
"""

import sys
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score, f1_score
import xgboost as xgb
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
TRAINING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TRAINING_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "backend" / "ml_engine" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

from preprocess import NIDSPreprocessor

def train_nids_model(data_path: Path = None):
    if data_path is None:
        data_path = DATA_DIR / "cic_ids2017_curated.csv"

    if not data_path.exists():
        logger.info("Dataset not found. Generating curated benchmark dataset...")
        from dataset_downloader import generate_curated_benchmark_dataset
        generate_curated_benchmark_dataset(output_file=data_path)

    logger.info(f"Loading dataset from {data_path}...")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records. Class distribution:\n{df['Label'].value_counts()}")

    # Preprocess
    preprocessor = NIDSPreprocessor()
    X, y = preprocessor.fit_transform(df)
    preprocessor.save_artifacts(ARTIFACTS_DIR)

    # Train / Test split (80% train, 20% test, stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    num_classes = len(preprocessor.label_encoder.classes_)
    logger.info(f"Configuring XGBoost for {num_classes} classes: {list(preprocessor.label_encoder.classes_)}")

    # XGBoost Classifier Configuration
    model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=num_classes,
        n_estimators=150,
        learning_rate=0.08,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric="mlogloss",
        tree_method="hist"
    )

    # 5-Fold Stratified Cross Validation
    logger.info("Performing 5-Fold Stratified Cross Validation with XGBoost...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = []

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train), 1):
        fold_X_tr, fold_y_tr = X_train[train_idx], y_train[train_idx]
        fold_X_va, fold_y_va = X_train[val_idx], y_train[val_idx]

        model.fit(fold_X_tr, fold_y_tr)
        preds = model.predict(fold_X_va)
        f1 = f1_score(fold_y_va, preds, average="weighted")
        cv_scores.append(f1)
        logger.info(f"  Fold {fold} Weighted F1-Score: {f1:.4f}")

    logger.info(f"Mean CV Weighted F1-Score: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")

    # Final Fit on full training set
    logger.info("Fitting final XGBoost model on full training set...")
    model.fit(X_train, y_train)

    # Final Test Set Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1_weighted = f1_score(y_test, y_pred, average="weighted")

    logger.info(f"Test Accuracy: {acc * 100:.2f}%")
    logger.info(f"Test Weighted F1-Score: {f1_weighted:.4f}")

    report = classification_report(
        y_test, y_pred, target_names=preprocessor.label_encoder.classes_, digits=4
    )
    logger.info(f"Classification Report:\n{report}")

    # Save trained XGBoost model
    xgb_output_path = ARTIFACTS_DIR / "nids_xgboost.joblib"
    joblib.dump(model, xgb_output_path)
    logger.info(f"[SUCCESS] Trained XGBoost model saved to {xgb_output_path}")

    # Save training metadata
    metrics_summary = {
        "model_type": "XGBoost",
        "accuracy": float(acc),
        "weighted_f1": float(f1_weighted),
        "cv_mean_f1": float(np.mean(cv_scores)),
        "cv_std_f1": float(np.std(cv_scores)),
        "num_samples_total": len(df),
        "num_train_samples": len(X_train),
        "num_test_samples": len(X_test),
        "classes": list(preprocessor.label_encoder.classes_)
    }
    with open(ARTIFACTS_DIR / "training_metrics.json", "w") as f:
        json.dump(metrics_summary, f, indent=2)

    return model, preprocessor, metrics_summary

if __name__ == "__main__":
    train_nids_model()
