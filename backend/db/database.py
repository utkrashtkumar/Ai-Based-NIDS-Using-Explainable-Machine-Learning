"""
Database Controller for AI-NIDS
Manages SQLite engine connection and provides clean CRUD operations for incidents and defense rules.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, create_engine, Session, select

from backend.config import DATABASE_URL
from backend.db.models import Incident, BlockedIP

logger = logging.getLogger(__name__)

# Connect_args for SQLite multi-threaded access
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def init_db():
    """Initializes tables on startup."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("[SUCCESS] Database tables verified/initialized.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

def get_session():
    return Session(engine)

def save_incident(incident_data: Dict[str, Any]) -> Incident:
    with Session(engine) as session:
        incident = Incident(
            timestamp=incident_data.get("timestamp", 0.0),
            src_ip=incident_data.get("src_ip", "0.0.0.0"),
            dst_ip=incident_data.get("dst_ip", "0.0.0.0"),
            src_port=incident_data.get("src_port", 0),
            dst_port=incident_data.get("dst_port", 0),
            protocol=incident_data.get("protocol", "TCP"),
            attack_type=incident_data.get("attack_type", "ANOMALY"),
            confidence=incident_data.get("confidence", 0.0),
            threat_level=incident_data.get("threat_level", "HIGH"),
            narrative=incident_data.get("narrative", ""),
            shap_json=json.dumps(incident_data.get("shap_top5", []))
        )
        session.add(incident)
        session.commit()
        session.refresh(incident)
        return incident

def get_all_incidents(limit: int = 100, offset: int = 0) -> List[Incident]:
    with Session(engine) as session:
        statement = select(Incident).order_by(Incident.timestamp.desc()).offset(offset).limit(limit)
        return list(session.exec(statement).all())

def dismiss_incident(incident_id: int) -> bool:
    with Session(engine) as session:
        incident = session.get(Incident, incident_id)
        if incident:
            incident.is_dismissed = True
            session.add(incident)
            session.commit()
            return True
        return False

def add_blocked_ip(ip_address: str, rule_name: str, timestamp: float) -> BlockedIP:
    with Session(engine) as session:
        existing = session.exec(select(BlockedIP).where(BlockedIP.ip_address == ip_address)).first()
        if existing:
            existing.is_active = True
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
        else:
            blocked = BlockedIP(ip_address=ip_address, rule_name=rule_name, blocked_at=timestamp, is_active=True)
            session.add(blocked)
            session.commit()
            session.refresh(blocked)
            return blocked

def remove_blocked_ip(ip_address: str) -> bool:
    with Session(engine) as session:
        blocked = session.exec(select(BlockedIP).where(BlockedIP.ip_address == ip_address)).first()
        if blocked:
            blocked.is_active = False
            session.add(blocked)
            session.commit()
            return True
        return False

def get_active_blocked_ips() -> List[str]:
    with Session(engine) as session:
        statement = select(BlockedIP).where(BlockedIP.is_active == True)
        return [b.ip_address for b in session.exec(statement).all()]
