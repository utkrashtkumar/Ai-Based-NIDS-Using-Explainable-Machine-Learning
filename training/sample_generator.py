"""
Sample Test Dataset Generator for AI-NIDS CSV Studio
Generates small, realistic CSV test files (with mixed attacks and pure benign traffic)
for users and evaluators to test drag-and-drop offline classification.
"""

import sys
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
SAMPLE_DIR = PROJECT_ROOT / "sample_data"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

from dataset_downloader import generate_curated_benchmark_dataset

def generate_sample_csvs():
    logger.info("Generating test CSV datasets for CSV Studio...")

    # Generate 500-row mixed dataset
    mixed_df = generate_curated_benchmark_dataset(
        num_samples=500,
        output_file=SAMPLE_DIR / "sample_attacks.csv"
    )

    # Generate 100-row purely benign dataset
    benign_df = mixed_df[mixed_df["Label"] == "BENIGN"].head(100).copy()
    benign_path = SAMPLE_DIR / "normal_traffic.csv"
    benign_df.to_csv(benign_path, index=False)

    # Generate 100-row unlabeled test dataset (simulating raw unlabelled flow capture)
    unlabeled_df = mixed_df.drop(columns=["Label"]).head(100).copy()
    unlabeled_path = SAMPLE_DIR / "unlabeled_live_flows.csv"
    unlabeled_df.to_csv(unlabeled_path, index=False)

    logger.info(f"[SUCCESS] Created:")
    logger.info(f"  1. {SAMPLE_DIR / 'sample_attacks.csv'} (500 mixed flows)")
    logger.info(f"  2. {benign_path} (100 benign flows)")
    logger.info(f"  3. {unlabeled_path} (100 unlabelled flows)")

if __name__ == "__main__":
    generate_sample_csvs()
