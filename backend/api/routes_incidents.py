"""
Incident Management & Threat History Endpoints
Provides paginated query access to persistent intrusion incidents and blocked IPs.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from backend.db.database import get_all_incidents, dismiss_incident, get_active_blocked_ips

router = APIRouter(prefix="/api/incidents", tags=["Threat History"])

@router.get("/")
async def list_incidents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
) -> List[Dict[str, Any]]:
    """Retrieves paginated incident records from SQLite."""
    incidents = get_all_incidents(limit=limit, offset=offset)
    return [inc.dict() for inc in incidents]

@router.post("/{incident_id}/dismiss")
async def dismiss_incident_record(incident_id: int) -> Dict[str, Any]:
    """Dismisses an incident from the active view."""
    success = dismiss_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return {"success": True, "message": f"Incident {incident_id} dismissed."}

@router.get("/blocked-ips")
async def list_blocked_ips() -> List[str]:
    """Returns all currently active blocked IPs."""
    return get_active_blocked_ips()
