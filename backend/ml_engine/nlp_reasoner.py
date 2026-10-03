"""
Natural Language Reasoning Generator for AI-NIDS
Translates mathematical TreeSHAP feature attributions into intuitive,
plain-English explanations for everyday users and security evaluators.
"""

from typing import Dict, Any, List

class NLPReasoner:
    @staticmethod
    def generate_explanation(
        attack_type: str,
        confidence: float,
        top_features: List[Dict[str, Any]],
        src_ip: str = "Unknown",
        dst_port: int = 0
    ) -> str:
        """
        Produces a crisp, plain-English summary explaining why a flow was classified as an attack.
        """
        conf_pct = int(confidence * 100)

        if attack_type == "BENIGN":
            return (
                f"Traffic from {src_ip} exhibits normal behavioral characteristics. "
                "Packet sizes, handshake ACK responses, and inter-arrival intervals are consistent with standard legitimate communications."
            )

        # Extract top positive contributors
        positive_features = [f for f in top_features if f.get("shap_value", 0) > 0]
        feat_names = [f["feature"] for f in positive_features[:3]]

        reasons = []

        if attack_type == "PortScan":
            has_syn = any("SYN" in f for f in feat_names)
            has_dur = any("Duration" in f for f in feat_names)
            if has_syn and has_dur:
                reasons.append("rapid sequence of short-lived connection probes containing only SYN flags without completing handshakes")
            else:
                reasons.append("unusually low packet counts and brief connection duration typical of port reconnaissance sweeps")

        elif attack_type == "DoS/DDoS":
            has_pkts_s = any("Packets_s" in f or "Bytes_s" in f for f in feat_names)
            if has_pkts_s:
                reasons.append("extreme incoming packet rate and abnormal volume of half-open TCP connections")
            else:
                reasons.append("asymmetric traffic with near-zero response acknowledgments, attempting to exhaust network socket buffers")

        elif attack_type == "BruteForce":
            reasons.append("repetitive authentication session bursts with fixed payload sizes and identical flow durations")

        elif attack_type == "Botnet":
            reasons.append("regular periodic heartbeat beacons with low jitter and small uniform packet sizes")

        else:
            reasons.append(f"anomalous statistical divergence in {', '.join(feat_names)}")

        primary_reason = reasons[0] if reasons else "anomalous flow attributes"

        narrative = (
            f"Detected {attack_type} ({conf_pct}% confidence) from remote host {src_ip}. "
            f"Primary trigger: {primary_reason}. "
            "Recommendation: Consider isolating or blocking this IP address via the firewall."
        )

        return narrative
