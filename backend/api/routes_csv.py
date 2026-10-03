"""
CSV Studio Endpoints for AI-NIDS
Handles CSV upload, feature schema validation, batch classification,
and offline Explainable AI (XAI) feature attribution.
"""

import io
import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import numpy as np

from backend.config import FEATURES_20, CONFIDENCE_THRESHOLD
from backend.ml_engine.classifier import NIDSClassifier
from backend.ml_engine.explainer import NIDSExplainer
from backend.ml_engine.nlp_reasoner import NLPReasoner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/csv", tags=["CSV Studio"])

classifier = NIDSClassifier()
explainer = NIDSExplainer()

@router.post("/upload")
async def upload_csv_and_analyze(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Parses an uploaded CSV file, validates feature columns, runs batch classification,
    and computes SHAP explanations for detected threats.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV files are supported.")

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

    if len(df) == 0:
        raise HTTPException(status_code=400, detail="Uploaded CSV file contains no data rows.")

    # Validate feature presence
    missing_cols = [col for col in FEATURES_20 if col not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=422,
            detail=f"Schema validation failed. Missing {len(missing_cols)} required features: {missing_cols[:5]}..."
        )

    # Impute missing/infinite values
    for col in FEATURES_20:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        df[col] = df[col].replace([np.inf, -np.inf], 0.0)

    # Batch Predict
    predictions = classifier.predict_batch(df)

    # Summary Statistics
    total_flows = len(predictions)
    threats = [p for p in predictions if p["is_threat"]]
    benign_count = total_flows - len(threats)

    attack_distribution: Dict[str, int] = {}
    for p in predictions:
        pred = p["prediction"]
        attack_distribution[pred] = attack_distribution.get(pred, 0) + 1

    # Augment results with SHAP explanations for top rows or first few threats
    sample_explanations = []
    max_to_explain = min(len(predictions), 50)

    for i in range(max_to_explain):
        item = predictions[i]
        feature_dict = {col: float(df.iloc[i][col]) for col in FEATURES_20}

        explanation = explainer.explain_flow(feature_dict, item["prediction"])
        narrative = NLPReasoner.generate_explanation(
            item["prediction"],
            item["confidence"],
            explanation["top_features"],
            src_ip=str(df.iloc[i].get("src_ip", f"Host_{i+1}")),
            dst_port=int(df.iloc[i].get("dst_port", 0))
        )

        sample_explanations.append({
            **item,
            "features": feature_dict,
            "shap_top5": explanation["top_features"],
            "narrative": narrative
        })

    return {
        "filename": file.filename,
        "total_flows": total_flows,
        "benign_count": benign_count,
        "threat_count": len(threats),
        "threat_percentage": round((len(threats) / total_flows) * 100, 2),
        "attack_distribution": attack_distribution,
        "results": sample_explanations
    }
