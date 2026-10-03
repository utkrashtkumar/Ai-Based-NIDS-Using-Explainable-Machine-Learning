"""
Mitigation & Firewall Controller Endpoints
Provides 1-click IP blocking and unblocking via Windows Defender Firewall.
"""

import time
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from backend.defense.firewall import FirewallManager
from backend.db.database import add_blocked_ip, remove_blocked_ip

router = APIRouter(prefix="/api/mitigate", tags=["Host Defense"])

class MitigationRequest(BaseModel):
    ip_address: str

@router.post("/block")
async def block_attacker_ip(req: MitigationRequest) -> Dict[str, Any]:
    """Adds a Windows Firewall inbound block rule and records it in the database."""
    ip = req.ip_address.strip()
    if not ip or len(ip.split(".")) != 4:
        raise HTTPException(status_code=400, detail="Invalid IPv4 address provided.")

    result = FirewallManager.block_ip(ip)
    if result["success"]:
        add_blocked_ip(ip, result.get("rule_name", f"BLOCK_{ip}"), time.time())
    return result

@router.post("/unblock")
async def unblock_attacker_ip(req: MitigationRequest) -> Dict[str, Any]:
    """Removes a Windows Firewall block rule and updates the database."""
    ip = req.ip_address.strip()
    result = FirewallManager.unblock_ip(ip)
    if result["success"]:
        remove_blocked_ip(ip)
    return result

@router.get("/rules")
async def list_active_rules() -> List[str]:
    """Lists all active NIDS firewall rules."""
    return FirewallManager.list_rules()
