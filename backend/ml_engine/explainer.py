"""
Explainable AI (XAI) Engine for AI-NIDS using XGBoost & TreeSHAP
Computes local feature attribution for live flows with sub-millisecond latency
using native C++ TreeSHAP (Lundberg et al.) and the SHAP framework.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import shap
import xgboost as xgb
import joblib

from backend.config import ML_ARTIFACTS_DIR, FEATURES_20

logger = logging.getLogger(__name__)

class NIDSExplainer:
    def __init__(self, artifacts_dir: Path = None):
        self.artifacts_dir = artifacts_dir or ML_ARTIFACTS_DIR
        self.model = None
        self.booster = None
        self.scaler = None
        self.label_encoder = None
        self.shap_explainer = None
        self.classes = []
        self.is_ready = False
        self._initialize()

    def _initialize(self):
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

                # Check if model is XGBoost
                if hasattr(self.model, "get_booster"):
                    self.booster = self.model.get_booster()
                    logger.info("[SUCCESS] Initialized native C++ TreeSHAP engine via XGBoost booster.")
                else:
                    # Fallback for LightGBM
                    self.shap_explainer = shap.TreeExplainer(self.model)
                    logger.info("[SUCCESS] Initialized TreeSHAP Explainer via shap.TreeExplainer.")

                self.is_ready = True
            else:
                logger.warning("Model artifacts not found for SHAP explainer.")
        except Exception as e:
            logger.error(f"Failed to initialize TreeSHAP explainer: {e}")

    def explain_flow(
        self,
        feature_dict: Dict[str, float],
        predicted_class: str,
        scaled_vector: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Computes local TreeSHAP attribution for a flow.
        Returns top features pushing toward and against the prediction.
        """
        if not self.is_ready:
            self._initialize()
            if not self.is_ready:
                return {
                    "predicted_class": predicted_class,
                    "top_features": [],
                    "summary": "Explainer not initialized."
                }

        # Prepare vector
        if scaled_vector is not None:
            vec_scaled = np.array([scaled_vector], dtype=np.float32)
        else:
            raw_vec = np.array([[feature_dict.get(feat, 0.0) for feat in FEATURES_20]], dtype=np.float32)
            vec_scaled = self.scaler.transform(raw_vec)

        class_idx = self.classes.index(predicted_class) if predicted_class in self.classes else 0

        # Method 1: Native C++ TreeSHAP via XGBoost Booster
        if self.booster is not None:
            dmat = xgb.DMatrix(vec_scaled, feature_names=FEATURES_20)
            # Shape for multi-class: (1, num_classes, num_features + 1)
            contribs = self.booster.predict(dmat, pred_contribs=True)
            if len(contribs.shape) == 3:
                class_shap = contribs[0, class_idx, :len(FEATURES_20)]
                base_val = float(contribs[0, class_idx, len(FEATURES_20)])
            else:
                class_shap = contribs[0, :len(FEATURES_20)]
                base_val = float(contribs[0, len(FEATURES_20)])

        # Method 2: Fallback to shap.TreeExplainer
        elif self.shap_explainer is not None:
            shap_values = self.shap_explainer.shap_values(vec_scaled)
            if isinstance(shap_values, list):
                class_shap = shap_values[class_idx][0]
            elif len(shap_values.shape) == 3:
                class_shap = shap_values[0, :, class_idx]
            else:
                class_shap = shap_values[0]

            expected_vals = self.shap_explainer.expected_value
            if isinstance(expected_vals, (list, np.ndarray)):
                base_val = float(expected_vals[class_idx])
            else:
                base_val = float(expected_vals or 0.0)
        else:
            return {"predicted_class": predicted_class, "top_features": []}

        # Pair features with their SHAP values and raw values
        feature_contributions = []
        for i, feat in enumerate(FEATURES_20):
            raw_val = float(feature_dict.get(feat, 0.0))
            shap_val = float(class_shap[i])
            feature_contributions.append({
                "feature": feat,
                "raw_value": round(raw_val, 4),
                "shap_value": round(shap_val, 4),
                "impact": "INCREASES_RISK" if shap_val > 0 else "DECREASES_RISK",
                "abs_importance": abs(shap_val)
            })

        # Sort by absolute SHAP impact
        feature_contributions.sort(key=lambda x: x["abs_importance"], reverse=True)

        return {
            "predicted_class": predicted_class,
            "base_value": round(base_val, 4),
            "top_features": feature_contributions[:6],
            "all_features": feature_contributions
        }
