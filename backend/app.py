"""
AI-Based Network Intrusion Detection System (AI-NIDS)
FastAPI Main Application Entrypoint
Orchestrates ML inference, TreeSHAP explainability, Scapy packet capture,
WebSocket streaming, SQLite incident persistence, and Next.js frontend serving.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import (
    STATIC_DIR,
    API_VERSION,
    DEFAULT_HOST,
    DEFAULT_PORT
)
from backend.db.database import init_db
from backend.ml_engine.classifier import NIDSClassifier
from backend.ml_engine.explainer import NIDSExplainer
from backend.sniffer.simulator import TrafficSimulator
from backend.api import (
    routes_network,
    routes_csv,
    routes_incidents,
    routes_mitigation,
    websocket_stream
)
from backend.db.database import save_incident
from backend.ml_engine.nlp_reasoner import NLPReasoner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("AI-NIDS")

# Shared Global Engines
classifier = NIDSClassifier()
explainer = NIDSExplainer()
simulator: TrafficSimulator = None

def handle_flow_analyzed(flow_data: dict):
    """
    Callback invoked whenever a flow (live or simulated) is completed.
    Runs ML classification, TreeSHAP explanation if threat, and enqueues to WebSocket.
    """
    features = flow_data.get("features", {})
    pred_result = classifier.predict_single(features)

    # Attach prediction to flow
    flow_data["prediction"] = pred_result["prediction"]
    flow_data["confidence"] = pred_result["confidence"]
    flow_data["is_threat"] = pred_result["is_threat"]
    flow_data["threat_level"] = pred_result["threat_level"]
    flow_data["probabilities"] = pred_result["probabilities"]

    # Compute SHAP explanation if threat or periodically
    shap_top5 = []
    narrative = ""

    if pred_result["is_threat"]:
        explanation = explainer.explain_flow(
            features,
            pred_result["prediction"],
            scaled_vector=pred_result.get("scaled_vector")
        )
        shap_top5 = explanation.get("top_features", [])
        narrative = NLPReasoner.generate_explanation(
            pred_result["prediction"],
            pred_result["confidence"],
            shap_top5,
            src_ip=flow_data.get("src_ip", "Unknown"),
            dst_port=flow_data.get("dst_port", 0)
        )

        flow_data["shap_top5"] = shap_top5
        flow_data["narrative"] = narrative

        # Persist to SQLite incident database
        try:
            save_incident({
                "timestamp": flow_data.get("end_time", flow_data.get("start_time")),
                "src_ip": flow_data.get("src_ip"),
                "dst_ip": flow_data.get("dst_ip"),
                "src_port": flow_data.get("src_port", 0),
                "dst_port": flow_data.get("dst_port", 0),
                "protocol": flow_data.get("protocol", "TCP"),
                "attack_type": pred_result["prediction"],
                "confidence": pred_result["confidence"],
                "threat_level": pred_result["threat_level"],
                "narrative": narrative,
                "shap_top5": shap_top5
            })
        except Exception as e:
            logger.error(f"Failed to persist incident: {e}")

    # Track bandwidth telemetry
    pkt_len = int(features.get("Total_Length_Fwd_Packets", 0) + features.get("Total_Length_Bwd_Packets", 0))
    pkt_cnt = int(features.get("Total_Fwd_Packets", 0) + features.get("Total_Bwd_Packets", 0))
    websocket_stream.manager.bytes_last_sec += pkt_len
    websocket_stream.manager.pkts_last_sec += pkt_cnt

    # Push to WebSocket batch queue
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                websocket_stream.manager.enqueue_flow(flow_data), loop
            )
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Lifespan
    logger.info("=" * 60)
    logger.info(f" Starting AI-NIDS Engine v{API_VERSION}")
    logger.info("=" * 60)

    # 1. Initialize SQLite
    init_db()

    # 2. Start WebSocket background batch loop
    batch_task = asyncio.create_task(websocket_stream.manager.start_batch_loop())

    # 3. Setup and start default simulator instance (runs in simulation mode until physical capture is triggered)
    global simulator
    simulator = TrafficSimulator(on_flow_callback=handle_flow_analyzed)
    simulator.start()
    routes_network.SNIFFER_STATE["is_running"] = True
    routes_network.SNIFFER_STATE["mode"] = "SIMULATION"

    yield

    # Shutdown Lifespan
    logger.info("Shutting down AI-NIDS...")
    if simulator and simulator.is_running:
        simulator.stop()
    batch_task.cancel()

# FastAPI App Creation
app = FastAPI(
    title="AI-Based Network Intrusion Detection System",
    description="Real-Time Host Intrusion Detection with TreeSHAP Explainable Machine Learning",
    version=API_VERSION,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(routes_network.router)
app.include_router(routes_csv.router)
app.include_router(routes_incidents.router)
app.include_router(routes_mitigation.router)
app.include_router(websocket_stream.router)

# Mount Next.js Pre-Compiled Static Assets
if STATIC_DIR.exists():
    next_assets_dir = STATIC_DIR / "_next"
    if next_assets_dir.exists():
        app.mount("/_next", StaticFiles(directory=str(next_assets_dir)), name="next_assets")

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {
            "status": "AI-NIDS API is Running",
            "version": API_VERSION,
            "docs": "/docs",
            "message": "Frontend static bundle not yet built. Visit /docs to test endpoints."
        }

