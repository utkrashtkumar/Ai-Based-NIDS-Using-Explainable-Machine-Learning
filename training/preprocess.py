"""
Preprocessing Pipeline for AI-NIDS
Handles missing/infinite values, standard feature scaling, and label encoding.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
TRAINING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TRAINING_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "backend" / "ml_engine" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# 20 Standard features
from dataset_downloader import FEATURES_20

class NIDSPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = FEATURES_20
        self.is_fitted = False

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans infinite and NaN values from the dataframe."""
        df = df.copy()
        
        # Ensure all expected feature columns exist
        for col in self.feature_names:
            if col not in df.columns:
                logger.warning(f"Missing expected feature {col}, filling with 0.0")
                df[col] = 0.0

        # Replace infinite values with NaN and impute with column median
        for col in self.feature_names:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val if not np.isnan(median_val) else 0.0)

        return df

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Fits scaler and label encoder on training data, returns X_scaled and y_encoded."""
        df_clean = self.clean_dataframe(df)

        X = df_clean[self.feature_names].values
        X_scaled = self.scaler.fit_transform(X)

        if "Label" in df_clean.columns:
            y = df_clean["Label"].astype(str).values
            y_encoded = self.label_encoder.fit_transform(y)
        else:
            raise ValueError("Dataframe must contain 'Label' column for supervised training.")

        self.is_fitted = True
        return X_scaled, y_encoded

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transforms features using previously fitted scaler."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted or loaded before transform.")
        df_clean = self.clean_dataframe(df)
        X = df_clean[self.feature_names].values
        return self.scaler.transform(X)

    def save_artifacts(self, output_dir: Path = None):
        """Saves fitted scaler, label encoder, and feature names to disk."""
        if output_dir is None:
            output_dir = ARTIFACTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.scaler, output_dir / "scaler.joblib")
        joblib.dump(self.label_encoder, output_dir / "label_encoder.joblib")

        # Save class mapping
        class_mapping = {
            int(idx): str(cls_name)
            for idx, cls_name in enumerate(self.label_encoder.classes_)
        }
        with open(output_dir / "class_mapping.json", "w") as f:
            json.dump(class_mapping, f, indent=2)

        logger.info(f"[SUCCESS] Scaler and LabelEncoder saved to {output_dir}")

    def load_artifacts(self, input_dir: Path = None):
        """Loads fitted scaler and label encoder from disk."""
        if input_dir is None:
            input_dir = ARTIFACTS_DIR

        self.scaler = joblib.load(input_dir / "scaler.joblib")
        self.label_encoder = joblib.load(input_dir / "label_encoder.joblib")
        self.is_fitted = True
        logger.info(f"[SUCCESS] Preprocessing artifacts loaded from {input_dir}")

if __name__ == "__main__":
    data_path = DATA_DIR / "cic_ids2017_curated.csv"
    if not data_path.exists():
        logger.info("Dataset not found, generating now...")
        from dataset_downloader import generate_curated_benchmark_dataset
        generate_curated_benchmark_dataset()

    df = pd.read_csv(data_path)
    preprocessor = NIDSPreprocessor()
    X, y = preprocessor.fit_transform(df)
    preprocessor.save_artifacts()
    logger.info(f"Processed X shape: {X.shape}, y shape: {y.shape}")
