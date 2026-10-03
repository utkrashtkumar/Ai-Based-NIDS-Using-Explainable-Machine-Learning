"""
Network & Sniffer Controller Endpoints
Provides runtime configuration discovery, network interface listing,
and controls starting/stopping packet capture.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import psutil

from backend.config import (
    API_VERSION,
    CONFIDENCE_THRESHOLD,
    FEATURES_20,
    ATTACK_CLASSES,
    DEFAULT_HOST,
    DEFAULT_PORT
)

router = APIRouter(prefix="/api", tags=["Network & Sniffer"])

# Shared global state references
SNIFFER_STATE: Dict[str, Any] = {
    "is_running": False,
    "mode": "IDLE", # "LIVE", "SIMULATION", or "IDLE"
    "active_interface": "None",
    "total_flows": 0,
    "threats_count": 0
}

@router.get("/config")
async def get_runtime_config() -> Dict[str, Any]:
    """
    Returns dynamic runtime configuration to frontend.
    Allows frontend to dynamically connect to the correct WebSocket URL
    without hardcoding host or port.
    """
    return {
        "version": API_VERSION,
        "default_host": DEFAULT_HOST,
        "default_port": DEFAULT_PORT,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "features": FEATURES_20,
        "attack_classes": ATTACK_CLASSES,
        "state": SNIFFER_STATE
    }

@router.get("/interfaces")
async def list_network_interfaces() -> List[Dict[str, Any]]:
    """
    Lists physical and wireless network adapters with their IP addresses.
    """
    interfaces = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for iface_name, addr_list in addrs.items():
        stat = stats.get(iface_name)
        is_up = stat.isup if stat else False

        ipv4 = None
        for addr in addr_list:
            if addr.family.name == "AF_INET":
                ipv4 = addr.address
                break

        # Classify interface type
        name_lower = iface_name.lower()
        if "wi-fi" in name_lower or "wireless" in name_lower or "wlan" in name_lower:
            iface_type = "Wi-Fi"
        elif "ethernet" in name_lower or "eth" in name_lower:
            iface_type = "Ethernet"
        elif "loopback" in name_lower:
            iface_type = "Loopback"
        else:
            iface_type = "Virtual / Other"

        interfaces.append({
            "name": iface_name,
            "ip": ipv4 or "No IPv4",
            "type": iface_type,
            "is_up": is_up
        })

    return interfaces

@router.get("/sniffer/status")
async def get_sniffer_status() -> Dict[str, Any]:
    return SNIFFER_STATE
