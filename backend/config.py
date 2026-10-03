import os
from pathlib import Path
from typing import List

# Paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
ML_ENGINE_DIR = BACKEND_DIR / "ml_engine"
ML_ARTIFACTS_DIR = ML_ENGINE_DIR / "artifacts"
DB_DIR = BACKEND_DIR / "db"
STATIC_DIR = BACKEND_DIR / "static"
DATA_DIR = PROJECT_ROOT / "data"

# Create required directories if they don't exist
for d in [ML_ARTIFACTS_DIR, DB_DIR, STATIC_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = f"sqlite:///{DB_DIR / 'incidents.db'}"

# Server Configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
API_VERSION = "2.0.0"

# Sniffer & Flow Aggregator Settings
FLOW_ACTIVE_TIMEOUT = 2.0  # seconds before flushing active ongoing flow
FLOW_IDLE_TIMEOUT = 1.0    # seconds of silence before flushing completed flow
FLOW_CLEANUP_INTERVAL = 0.5 # interval to check and flush flows

# WebSocket Telemetry Settings
WS_BATCH_INTERVAL_MS = 500  # batch normal flows every 500ms to prevent browser lag
WS_MAX_QUEUE_SIZE = 1000

# Classification & Threat Thresholds
# Flows with confidence below this threshold for attack classes are treated with caution
CONFIDENCE_THRESHOLD = 0.75

# Standardized 20-Feature Schema Aligned with CICFlowMeter / CIC-IDS2017
FEATURES_20: List[str] = [
    "Flow_Duration",
    "Total_Fwd_Packets",
    "Total_Bwd_Packets",
    "Total_Length_Fwd_Packets",
    "Total_Length_Bwd_Packets",
    "Fwd_Packet_Length_Mean",
    "Fwd_Packet_Length_Std",
    "Bwd_Packet_Length_Mean",
    "Bwd_Packet_Length_Std",
    "Flow_Bytes_s",
    "Flow_Packets_s",
    "Flow_IAT_Mean",
    "Flow_IAT_Std",
    "Flow_IAT_Max",
    "SYN_Flag_Count",
    "FIN_Flag_Count",
    "RST_Flag_Count",
    "ACK_Flag_Count",
    "Down_Up_Ratio",
    "Average_Packet_Size"
]

# Attack Class Mapping
ATTACK_CLASSES = [
    "BENIGN",
    "DoS/DDoS",
    "PortScan",
    "BruteForce",
    "Botnet"
]

# Noise Filtering: IPs and Multicast Ranges to ignore for benign local health
IGNORE_MULTICAST_IPS = {
    "224.0.0.251",  # mDNS
    "239.255.255.250",  # SSDP / UPnP
    "224.0.0.252",  # LLMNR
    "255.255.255.255"   # Local Broadcast
}
