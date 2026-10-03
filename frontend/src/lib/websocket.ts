import { FlowData, TelemetryData } from "./types";

export type FlowBatchCallback = (flows: FlowData[]) => void;
export type CriticalAlertCallback = (flow: FlowData) => void;
export type TelemetryCallback = (telemetry: TelemetryData) => void;
export type StatusCallback = (connected: boolean) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private flowBatchListeners: FlowBatchCallback[] = [];
  private criticalAlertListeners: CriticalAlertCallback[] = [];
  private telemetryListeners: TelemetryCallback[] = [];
  private statusListeners: StatusCallback[] = [];
  private isConnecting: boolean = false;
  private reconnectTimer: NodeJS.Timeout | null = null;

  public connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isConnecting = true;

    // Dynamically calculate WebSocket URL
    let wsHost = "127.0.0.1:8000";
    if (typeof window !== "undefined") {
      if (window.location.port === "8000") {
        wsHost = window.location.host;
      }
    }

    const wsUrl = `ws://${wsHost}/ws/live-traffic`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.isConnecting = false;
        this.notifyStatus(true);
        console.log("[AI-NIDS] WebSocket connected to", wsUrl);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "FLOW_BATCH" && data.flows) {
            this.flowBatchListeners.forEach((listener) => listener(data.flows));
          } else if (data.type === "CRITICAL_ALERT" && data.flow) {
            this.criticalAlertListeners.forEach((listener) => listener(data.flow));
          } else if (data.type === "TELEMETRY") {
            this.telemetryListeners.forEach((listener) => listener(data as TelemetryData));
          }
        } catch (err) {
          console.debug("Non-JSON WS message:", event.data);
        }
      };

      this.socket.onclose = () => {
        this.isConnecting = false;
        this.notifyStatus(false);
        this.scheduleReconnect();
      };

      this.socket.onerror = (err) => {
        this.isConnecting = false;
        this.notifyStatus(false);
        this.socket?.close();
      };
    } catch (err) {
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2500);
  }

  private notifyStatus(connected: boolean): void {
    this.statusListeners.forEach((l) => l(connected));
  }

  public onFlowBatch(cb: FlowBatchCallback): () => void {
    this.flowBatchListeners.push(cb);
    return () => {
      this.flowBatchListeners = this.flowBatchListeners.filter((l) => l !== cb);
    };
  }

  public onCriticalAlert(cb: CriticalAlertCallback): () => void {
    this.criticalAlertListeners.push(cb);
    return () => {
      this.criticalAlertListeners = this.criticalAlertListeners.filter((l) => l !== cb);
    };
  }

  public onTelemetry(cb: TelemetryCallback): () => void {
    this.telemetryListeners.push(cb);
    return () => {
      this.telemetryListeners = this.telemetryListeners.filter((l) => l !== cb);
    };
  }

  public onStatus(cb: StatusCallback): () => void {
    this.statusListeners.push(cb);
    return () => {
      this.statusListeners = this.statusListeners.filter((l) => l !== cb);
    };
  }
}

export const wsService = new WebSocketService();
