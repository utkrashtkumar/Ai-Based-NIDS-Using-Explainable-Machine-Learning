"""
Live Network Packet Sniffer for AI-NIDS
Captures live L3/L4 packets using Scapy and Npcap driver,
with graceful handling for both physical Ethernet and Wi-Fi adapters.
"""

import time
import logging
import threading
from typing import Optional, Callable, Dict, Any

from scapy.all import AsyncSniffer, IP, IPv6, TCP, UDP, conf
import psutil

from backend.config import IGNORE_MULTICAST_IPS
from backend.sniffer.flow_manager import FlowManager

logger = logging.getLogger(__name__)

class LivePacketSniffer:
    def __init__(self, flow_manager: FlowManager, interface_name: Optional[str] = None):
        self.flow_manager = flow_manager
        self.interface_name = interface_name
        self.sniffer: Optional[AsyncSniffer] = None
        self.is_running = False
        self._cleanup_timer: Optional[threading.Thread] = None

    def start(self):
        if self.is_running:
            return

        logger.info(f"Starting LivePacketSniffer on interface: {self.interface_name or 'Default'}...")

        # Configure Scapy interface
        if self.interface_name:
            conf.iface = self.interface_name

        try:
            # Initialize Scapy AsyncSniffer
            self.sniffer = AsyncSniffer(
                iface=self.interface_name,
                prn=self._packet_callback,
                store=False,
                filter="ip or ip6" # capture IPv4 and IPv6 packets
            )
            self.sniffer.start()
            self.is_running = True
            logger.info("[SUCCESS] Scapy packet capture active.")

            # Start background flow timeout cleaner thread
            self._cleanup_timer = threading.Thread(target=self._timeout_loop, daemon=True)
            self._cleanup_timer.start()

        except Exception as e:
            logger.error(f"Failed to start Scapy live sniffer: {e}")
            self.is_running = False
            raise

    def stop(self):
        if not self.is_running:
            return
        logger.info("Stopping LivePacketSniffer...")
        self.is_running = False
        if self.sniffer:
            try:
                self.sniffer.stop()
            except Exception as e:
                logger.warning(f"Notice while stopping sniffer: {e}")
            self.sniffer = None

    def _timeout_loop(self):
        """Periodically flushes flows that exceeded active or idle timeout thresholds."""
        while self.is_running:
            time.sleep(0.5)
            self.flow_manager.flush_expired_flows()

    def _packet_callback(self, pkt):
        """Callback invoked by Scapy for every captured packet."""
        try:
            if not (IP in pkt or IPv6 in pkt):
                return

            timestamp = float(pkt.time)
            pkt_len = len(pkt)

            # Extract IP layer
            if IP in pkt:
                src_ip = pkt[IP].src
                dst_ip = pkt[IP].dst
            else:
                src_ip = pkt[IPv6].src
                dst_ip = pkt[IPv6].dst

            # Ignore multicast/broadcast noise
            if dst_ip in IGNORE_MULTICAST_IPS or src_ip in IGNORE_MULTICAST_IPS:
                return

            sport = 0
            dport = 0
            proto = "OTHER"
            flags = 0

            # Extract Transport Layer
            if TCP in pkt:
                proto = "TCP"
                sport = int(pkt[TCP].sport)
                dport = int(pkt[TCP].dport)
                flags = int(pkt[TCP].flags)
            elif UDP in pkt:
                proto = "UDP"
                sport = int(pkt[UDP].sport)
                dport = int(pkt[UDP].dport)

            # Pass to flow aggregator
            self.flow_manager.process_packet(
                src_ip=src_ip,
                dst_ip=dst_ip,
                sport=sport,
                dport=dport,
                proto=proto,
                pkt_len=pkt_len,
                flags=flags,
                timestamp=timestamp
            )

        except Exception as e:
            logger.debug(f"Packet processing error: {e}")
