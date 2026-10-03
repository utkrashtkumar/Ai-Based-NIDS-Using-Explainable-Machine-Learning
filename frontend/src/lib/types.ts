export interface FlowData {
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: string;
  start_time: number;
  end_time: number;
  duration: number;
  total_packets: number;
  prediction?: string;
  confidence?: number;
  is_threat?: boolean;
  threat_level?: "NORMAL" | "HIGH" | "CRITICAL";
  probabilities?: Record<string, number>;
  features?: Record<string, number>;
  shap_top5?: Array<{
    feature: string;
    raw_value: number;
    shap_value: number;
    impact: "INCREASES_RISK" | "DECREASES_RISK";
  }>;
  narrative?: string;
  is_simulated?: boolean;
}

export interface TelemetryData {
  type: string;
  kb_s: number;
  pkts_s: number;
  total_flows: number;
  total_threats: number;
  clients: number;
  timestamp: number;
}

export interface IncidentRecord {
  id: number;
  timestamp: number;
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: string;
  attack_type: string;
  confidence: number;
  threat_level: string;
  narrative: string;
  shap_json: string;
  is_blocked: boolean;
  is_dismissed: boolean;
}

export interface InterfaceInfo {
  name: string;
  ip: string;
  type: string;
  is_up: boolean;
}

export interface RuntimeConfig {
  version: string;
  default_host: string;
  default_port: number;
  confidence_threshold: number;
  features: string[];
  attack_classes: string[];
}
