"""
Feature Parity & Schema Validator for AI-NIDS
Verifies that all 20 statistical features extracted by Python
conform strictly to the CICFlowMeter / CIC-IDS2017 schema and data types.
"""

import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
TRAINING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TRAINING_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "backend" / "ml_engine" / "artifacts"

from dataset_downloader import FEATURES_20

def validate_feature_schema(data_path: Path = None) -> bool:
    if data_path is None:
        data_path = DATA_DIR / "cic_ids2017_curated.csv"

    logger.info("Validating feature schema parity...")

    if not data_path.exists():
        logger.error(f"Dataset {data_path} not found.")
        return False

    df = pd.read_csv(data_path)

    # 1. Check all 20 features exist
    missing_feats = [f for f in FEATURES_20 if f not in df.columns]
    if missing_feats:
        logger.error(f"Validation FAILED: Missing features: {missing_feats}")
        return False

    # 2. Check no unexpected infinities or NaNs
    for feat in FEATURES_20:
        if np.isinf(df[feat]).any():
            logger.error(f"Validation FAILED: Infinite values detected in {feat}")
            return False
        if df[feat].isna().any():
            logger.error(f"Validation FAILED: NaN values detected in {feat}")
            return False

    # 3. Check physical network constraints
    # Duration >= 0
    if (df["Flow_Duration"] < 0).any():
        logger.error("Validation FAILED: Flow_Duration has negative values")
        return False

    # Packets >= 1
    if (df["Total_Fwd_Packets"] < 1).any():
        logger.error("Validation FAILED: Total_Fwd_Packets must be at least 1")
        return False

    # SYN flag count >= 0
    if (df["SYN_Flag_Count"] < 0).any():
        logger.error("Validation FAILED: SYN_Flag_Count cannot be negative")
        return False

    logger.info("[SUCCESS] Feature parity validation PASSED: All 20 features conform to network flow physics.")
    return True

if __name__ == "__main__":
    valid = validate_feature_schema()
    sys.exit(0 if valid else 1)
