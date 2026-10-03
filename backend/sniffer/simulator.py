"""
Traffic Simulator Fallback Engine for AI-NIDS
Generates realistic streaming flows to emulate live network traffic
when running in non-admin mode or when Npcap is unavailable.
"""

import time
import random
import logging
import threading
from typing import Callable, Optional, Dict, Any

from backend.sniffer.feature_extractor import FlowFeatureExtractor

logger = logging.getLogger(__name__)

class TrafficSimulator:
    def __init__(self, on_flow_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.on_flow_callback = on_flow_callback
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        # Sample pool of realistic IPs
        self.local_ips = ["192.168.1.15", "192.168.1.45"]
        self.remote_benign_ips = [
            "142.250.190.46",  # Google
            "151.101.65.140",  # Reddit
            "104.244.42.1",    # Twitter/X
            "13.107.42.14",    # Microsoft
            "185.199.108.153"  # GitHub
        ]
        self.attacker_ips = [
            "185.220.101.5",   # Tor Exit Node
            "45.146.164.110",  # Scanner
            "194.26.29.112",   # Botnet C2
            "192.168.1.108"    # Local Rogue Host
        ]

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("[SUCCESS] TrafficSimulator started (Simulation Mode).")

    def stop(self):
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("TrafficSimulator stopped.")

    def _run_loop(self):
        step = 0
        while self.is_running:
            time.sleep(random.uniform(0.3, 0.8)) # Emit 1-3 flows per second
            step += 1

            # Decide traffic type: 85% Benign, 15% Attacks
            is_attack = (step % 7 == 0)

            if not is_attack:
                flow = self._generate_benign_flow()
            else:
                attack_choice = random.choice(["PortScan", "DoS/DDoS", "BruteForce"])
                flow = self._generate_attack_flow(attack_choice)

            if self.on_flow_callback and self.is_running:
                try:
                    self.on_flow_callback(flow)
                except Exception as e:
                    logger.error(f"Simulator callback error: {e}")

    def _generate_benign_flow(self) -> Dict[str, Any]:
        src = random.choice(self.local_ips)
        dst = random.choice(self.remote_benign_ips)
        sport = random.randint(49152, 65535)
        dport = random.choice([443, 80, 53, 8080])
        proto = "TCP" if dport != 53 else "UDP"

        now = time.time()
        duration = random.uniform(0.05, 1.8)
        fwd_count = random.randint(4, 25)
        bwd_count = random.randint(5, 30)

        fwd_pkts = [
            {"len": random.randint(60, 400), "time": now - duration + (i * duration / fwd_count), "flags": 0x10 | (0x02 if i == 0 else 0)}
            for i in range(fwd_count)
        ]
        bwd_pkts = [
            {"len": random.randint(100, 1460), "time": now - duration + (i * duration / bwd_count), "flags": 0x10 | (0x01 if i == bwd_count - 1 else 0)}
            for i in range(bwd_count)
        ]

        features = FlowFeatureExtractor.extract_features({
            "fwd_packets": fwd_pkts,
            "bwd_packets": bwd_pkts,
            "start_time": now - duration,
            "end_time": now
        })

        return {
            "src_ip": src,
            "dst_ip": dst,
            "src_port": sport,
            "dst_port": dport,
            "protocol": proto,
            "start_time": now - duration,
            "end_time": now,
            "duration": duration,
            "total_packets": fwd_count + bwd_count,
            "features": features,
            "is_simulated": True
        }

    def _generate_attack_flow(self, attack_type: str) -> Dict[str, Any]:
        src = random.choice(self.attacker_ips)
        dst = random.choice(self.local_ips)
        now = time.time()

        if attack_type == "PortScan":
            sport = random.randint(40000, 60000)
            dport = random.randint(20, 1024)
            proto = "TCP"
            duration = random.uniform(0.001, 0.02)
            fwd_pkts = [{"len": 44, "time": now - duration, "flags": 0x02}] # SYN only
            bwd_pkts = [{"len": 40, "time": now, "flags": 0x04}] if random.random() > 0.5 else [] # RST

        elif attack_type == "DoS/DDoS":
            sport = random.randint(1024, 65535)
            dport = 80
            proto = "TCP"
            duration = random.uniform(0.01, 0.1)
            burst = random.randint(30, 80)
            fwd_pkts = [{"len": 60, "time": now - duration + (i * duration / burst), "flags": 0x02} for i in range(burst)]
            bwd_pkts = []

        else: # BruteForce
            sport = random.randint(30000, 50000)
            dport = 22 # SSH
            proto = "TCP"
            duration = random.uniform(0.4, 0.9)
            burst = 16
            fwd_pkts = [{"len": 120, "time": now - duration + (i * duration / burst), "flags": 0x18} for i in range(burst)]
            bwd_pkts = [{"len": 160, "time": now - duration + (i * duration / burst), "flags": 0x10} for i in range(burst)]

        features = FlowFeatureExtractor.extract_features({
            "fwd_packets": fwd_pkts,
            "bwd_packets": bwd_pkts,
            "start_time": now - duration,
            "end_time": now
        })

        return {
            "src_ip": src,
            "dst_ip": dst,
            "src_port": sport,
            "dst_port": dport,
            "protocol": proto,
            "start_time": now - duration,
            "end_time": now,
            "duration": duration,
            "total_packets": len(fwd_pkts) + len(bwd_pkts),
            "features": features,
            "is_simulated": True
        }
