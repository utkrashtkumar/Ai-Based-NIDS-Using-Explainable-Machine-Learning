"""
Bi-directional Flow Manager for AI-NIDS
Aggregates live packets into 5-tuple flows with active/idle timeouts
and passes completed flows to the inference engine.
"""

import time
import logging
from typing import Dict, Tuple, Optional, Callable, List, Any
from collections import defaultdict

from backend.config import (
    FLOW_ACTIVE_TIMEOUT,
    FLOW_IDLE_TIMEOUT,
    IGNORE_MULTICAST_IPS
)
from backend.sniffer.feature_extractor import FlowFeatureExtractor

logger = logging.getLogger(__name__)

FlowKey = Tuple[str, str, int, int, str]

class FlowSession:
    def __init__(self, src_ip: str, dst_ip: str, sport: int, dport: int, proto: str, start_time: float):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.sport = sport
        self.dport = dport
        self.proto = proto
        self.start_time = start_time
        self.last_seen = start_time

        # Store packets
        self.fwd_packets: List[Dict[str, Any]] = []
        self.bwd_packets: List[Dict[str, Any]] = []

    def add_packet(self, s_ip: str, d_ip: str, s_port: int, d_port: int, pkt_len: int, timestamp: float, flags: int):
        self.last_seen = timestamp
        pkt_entry = {"len": pkt_len, "time": timestamp, "flags": flags}

        # Check direction
        if s_ip == self.src_ip and s_port == self.sport:
            self.fwd_packets.append(pkt_entry)
        else:
            self.bwd_packets.append(pkt_entry)

    def is_expired(self, current_time: float) -> bool:
        # Expired if idle for > IDLE_TIMEOUT or active for > ACTIVE_TIMEOUT
        idle_duration = current_time - self.last_seen
        total_duration = current_time - self.start_time
        return (idle_duration >= FLOW_IDLE_TIMEOUT) or (total_duration >= FLOW_ACTIVE_TIMEOUT)

class FlowManager:
    def __init__(self, on_flow_completed: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.active_flows: Dict[FlowKey, FlowSession] = {}
        self.on_flow_completed = on_flow_completed
        self.total_flows_processed = 0

    @staticmethod
    def get_canonical_key(src_ip: str, dst_ip: str, sport: int, dport: int, proto: str) -> FlowKey:
        """Returns a canonical representation so both directions share the same key."""
        if (src_ip, sport) < (dst_ip, dport):
            return (src_ip, dst_ip, sport, dport, proto)
        return (dst_ip, src_ip, dport, sport, proto)

    def process_packet(
        self,
        src_ip: str,
        dst_ip: str,
        sport: int,
        dport: int,
        proto: str,
        pkt_len: int,
        flags: int = 0,
        timestamp: Optional[float] = None
    ):
        """Processes an incoming raw packet and updates or creates its flow session."""
        if dst_ip in IGNORE_MULTICAST_IPS or src_ip in IGNORE_MULTICAST_IPS:
            return

        ts = timestamp or time.time()
        canonical_key = self.get_canonical_key(src_ip, dst_ip, sport, dport, proto)

        if canonical_key not in self.active_flows:
            self.active_flows[canonical_key] = FlowSession(
                src_ip=src_ip,
                dst_ip=dst_ip,
                sport=sport,
                dport=dport,
                proto=proto,
                start_time=ts
            )

        session = self.active_flows[canonical_key]
        session.add_packet(src_ip, dst_ip, sport, dport, pkt_len, ts, flags)

        # Immediate flush if TCP connection terminates (FIN or RST)
        if flags & 0x01 or flags & 0x04: # FIN or RST
            self._flush_flow(canonical_key)

    def flush_expired_flows(self, current_time: Optional[float] = None):
        """Checks and flushes all flows exceeding active or idle timeouts."""
        now = current_time or time.time()
        expired_keys = [
            k for k, session in self.active_flows.items()
            if session.is_expired(now)
        ]

        for k in expired_keys:
            self._flush_flow(k)

    def _flush_flow(self, key: FlowKey):
        session = self.active_flows.pop(key, None)
        if not session:
            return

        total_pkts = len(session.fwd_packets) + len(session.bwd_packets)
        if total_pkts == 0:
            return

        # Extract features
        raw_flow_data = {
            "fwd_packets": session.fwd_packets,
            "bwd_packets": session.bwd_packets,
            "start_time": session.start_time,
            "end_time": session.last_seen
        }

        features = FlowFeatureExtractor.extract_features(raw_flow_data)

        # Flow summary metadata
        flow_summary = {
            "src_ip": session.src_ip,
            "dst_ip": session.dst_ip,
            "src_port": session.sport,
            "dst_port": session.dport,
            "protocol": session.proto,
            "start_time": session.start_time,
            "end_time": session.last_seen,
            "duration": features["Flow_Duration"] / 1.0e6,
            "total_packets": total_pkts,
            "features": features
        }

        self.total_flows_processed += 1

        if self.on_flow_completed:
            try:
                self.on_flow_completed(flow_summary)
            except Exception as e:
                logger.error(f"Error in on_flow_completed callback: {e}")
