"""
Inference Classifier Wrapper for AI-NIDS
Loads trained LightGBM model and preprocessor, runs low-latency inference,
and applies calibrated confidence thresholding.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Union

import numpy as np
import pandas as pd
import joblib

from backend.config import (
    ML_ARTIFACTS_DIR,
    CONFIDENCE_THRESHOLD,
    FEATURES_20,
    ATTACK_CLASSES
)

logger = logging.getLogger(__name__)

class NIDSClassifier:
    def __init__(self, artifacts_dir: Path = None):
        self.artifacts_dir = artifacts_dir or ML_ARTIFACTS_DIR
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.classes = []
        self.is_loaded = False
        self._load_artifacts()

    def _load_artifacts(self):
        try:
            model_path = self.artifacts_dir / "nids_xgboost.joblib"
            if not model_path.exists():
                model_path = self.artifacts_dir / "nids_lightgbm.joblib"
            scaler_path = self.artifacts_dir / "scaler.joblib"
            encoder_path = self.artifacts_dir / "label_encoder.joblib"

            if model_path.exists() and scaler_path.exists() and encoder_path.exists():
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                self.label_encoder = joblib.load(encoder_path)
                self.classes = list(self.label_encoder.classes_)
                self.is_loaded = True
                logger.info(f"[SUCCESS] NIDSClassifier loaded with classes: {self.classes}")
            else:
                logger.warning(f"Model artifacts not found in {self.artifacts_dir}. Run training first.")
        except Exception as e:
            logger.error(f"Error loading model artifacts: {e}")

    def predict_single(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """Runs inference on a single 20-feature dictionary."""
        if not self.is_loaded:
            self._load_artifacts()
            if not self.is_loaded:
                return {
                    "prediction": "BENIGN",
                    "confidence": 0.50,
                    "is_threat": False,
                    "probabilities": {"BENIGN": 1.0}
                }

        # Vectorize features in canonical order
        vector = np.array([[feature_dict.get(feat, 0.0) for feat in FEATURES_20]], dtype=np.float32)
        
        # Scale
        vector_scaled = self.scaler.transform(vector)

        # Predict probabilities
        probs = self.model.predict_proba(vector_scaled)[0]
        max_idx = int(np.argmax(probs))
        predicted_class = self.classes[max_idx]
        confidence = float(probs[max_idx])

        # Attack vs Benign check
        is_threat = (predicted_class != "BENIGN") and (confidence >= CONFIDENCE_THRESHOLD)

        prob_dict = {
            self.classes[i]: round(float(probs[i]), 4)
            for i in range(len(self.classes))
        }

        return {
            "prediction": predicted_class,
            "confidence": round(confidence, 4),
            "is_threat": is_threat,
            "threat_level": "CRITICAL" if (is_threat and confidence > 0.90) else ("HIGH" if is_threat else "NORMAL"),
            "probabilities": prob_dict,
            "raw_vector": vector[0].tolist(),
            "scaled_vector": vector_scaled[0].tolist()
        }

    def predict_batch(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Runs batch inference on a DataFrame."""
        if not self.is_loaded:
            self._load_artifacts()

        # Clean & extract
        X_raw = df[FEATURES_20].fillna(0.0).values
        X_scaled = self.scaler.transform(X_raw)
        probs_matrix = self.model.predict_proba(X_scaled)
        pred_indices = np.argmax(probs_matrix, axis=1)

        results = []
        for i in range(len(df)):
            p_class = self.classes[pred_indices[i]]
            conf = float(probs_matrix[i, pred_indices[i]])
            is_threat = (p_class != "BENIGN") and (conf >= CONFIDENCE_THRESHOLD)

            results.append({
                "row_id": i + 1,
                "prediction": p_class,
                "confidence": round(conf, 4),
                "is_threat": is_threat,
                "threat_level": "CRITICAL" if (is_threat and conf > 0.90) else ("HIGH" if is_threat else "NORMAL"),
                "probabilities": {
                    self.classes[c]: round(float(probs_matrix[i, c]), 4)
                    for c in range(len(self.classes))
                }
            })
        return results
