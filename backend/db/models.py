"""
Database Models for AI-NIDS Incident & Defense Persistence
Uses SQLModel (Pydantic + SQLAlchemy) with SQLite.
"""

from typing import Optional
from sqlmodel import SQLModel, Field

class Incident(SQLModel, table=True):
    __tablename__ = "incidents"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: float = Field(index=True)
    src_ip: str = Field(index=True)
    dst_ip: str
    src_port: int = 0
    dst_port: int = 0
    protocol: str = "TCP"
    attack_type: str = Field(index=True)
    confidence: float
    threat_level: str = "HIGH"
    narrative: str
    shap_json: str = "{}"
    is_blocked: bool = False
    is_dismissed: bool = False

class BlockedIP(SQLModel, table=True):
    __tablename__ = "blocked_ips"

    id: Optional[int] = Field(default=None, primary_key=True)
    ip_address: str = Field(unique=True, index=True)
    blocked_at: float
    rule_name: str
    is_active: bool = True
