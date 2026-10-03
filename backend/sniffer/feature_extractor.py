"""
Feature Extractor for AI-NIDS
Extracts the standardized 20 statistical bi-directional features from a network flow.
"""

from typing import List, Dict, Any
import numpy as np

class FlowFeatureExtractor:
    @staticmethod
    def extract_features(flow_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Computes the standard 20 features from accumulated packets in a flow.
        flow_data is expected to have:
            - 'fwd_packets': list of {'len': int, 'time': float, 'flags': int}
            - 'bwd_packets': list of {'len': int, 'time': float, 'flags': int}
            - 'start_time': float
            - 'end_time': float
        """
        fwd_pkts = flow_data.get("fwd_packets", [])
        bwd_pkts = flow_data.get("bwd_packets", [])

        total_fwd = len(fwd_pkts)
        total_bwd = len(bwd_pkts)
        total_pkts = total_fwd + total_bwd

        start_time = flow_data.get("start_time", 0.0)
        end_time = flow_data.get("end_time", start_time)
        duration_sec = max(end_time - start_time, 0.0001)
        duration_micro = duration_sec * 1.0e6

        # Packet Length Statistics
        fwd_lens = [p["len"] for p in fwd_pkts] if fwd_pkts else [0]
        bwd_lens = [p["len"] for p in bwd_pkts] if bwd_pkts else [0]
        all_lens = fwd_lens + (bwd_lens if total_bwd > 0 else [])

        total_len_fwd = sum(fwd_lens) if fwd_pkts else 0.0
        total_len_bwd = sum(bwd_lens) if bwd_pkts else 0.0
        total_len_all = total_len_fwd + total_len_bwd

        fwd_len_mean = float(np.mean(fwd_lens)) if fwd_pkts else 0.0
        fwd_len_std = float(np.std(fwd_lens)) if fwd_pkts else 0.0
        bwd_len_mean = float(np.mean(bwd_lens)) if bwd_pkts else 0.0
        bwd_len_std = float(np.std(bwd_lens)) if bwd_pkts else 0.0

        # Throughput Rates
        flow_bytes_s = total_len_all / duration_sec
        flow_pkts_s = total_pkts / duration_sec

        # Inter-Arrival Times (IAT)
        all_times = sorted([p["time"] for p in fwd_pkts] + [p["time"] for p in bwd_pkts])
        if len(all_times) > 1:
            iats = np.diff(all_times) * 1.0e6 # convert to microseconds
            iat_mean = float(np.mean(iats))
            iat_std = float(np.std(iats))
            iat_max = float(np.max(iats))
        else:
            iat_mean = duration_micro
            iat_std = 0.0
            iat_max = duration_micro

        # TCP Flag Counts (SYN=0x02, FIN=0x01, RST=0x04, ACK=0x10)
        syn_count = 0
        fin_count = 0
        rst_count = 0
        ack_count = 0

        for p in (fwd_pkts + bwd_pkts):
            flags = p.get("flags", 0)
            if flags & 0x02:
                syn_count += 1
            if flags & 0x01:
                fin_count += 1
            if flags & 0x04:
                rst_count += 1
            if flags & 0x10:
                ack_count += 1

        down_up_ratio = float(total_bwd / max(total_fwd, 1))
        avg_pkt_size = float(total_len_all / max(total_pkts, 1))

        return {
            "Flow_Duration": round(duration_micro, 2),
            "Total_Fwd_Packets": total_fwd,
            "Total_Bwd_Packets": total_bwd,
            "Total_Length_Fwd_Packets": round(total_len_fwd, 2),
            "Total_Length_Bwd_Packets": round(total_len_bwd, 2),
            "Fwd_Packet_Length_Mean": round(fwd_len_mean, 2),
            "Fwd_Packet_Length_Std": round(fwd_len_std, 2),
            "Bwd_Packet_Length_Mean": round(bwd_len_mean, 2),
            "Bwd_Packet_Length_Std": round(bwd_len_std, 2),
            "Flow_Bytes_s": round(flow_bytes_s, 2),
            "Flow_Packets_s": round(flow_pkts_s, 2),
            "Flow_IAT_Mean": round(iat_mean, 2),
            "Flow_IAT_Std": round(iat_std, 2),
            "Flow_IAT_Max": round(iat_max, 2),
            "SYN_Flag_Count": syn_count,
            "FIN_Flag_Count": fin_count,
            "RST_Flag_Count": rst_count,
            "ACK_Flag_Count": ack_count,
            "Down_Up_Ratio": round(down_up_ratio, 4),
            "Average_Packet_Size": round(avg_pkt_size, 2)
        }
