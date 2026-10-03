"use client";

import React, { useState, useEffect } from "react";
import { Header } from "../components/Header";
import { LiveMonitor } from "../components/LiveMonitor";
import { FlowTable } from "../components/FlowTable";
import { XaiModal } from "../components/XaiModal";
import { ThreatAlertCard } from "../components/ThreatAlertCard";
import { ThreatHistory } from "../components/ThreatHistory";
import { CsvStudio } from "../components/CsvStudio";
import { soundEffects } from "../components/AudioAlert";
import { FlowData, TelemetryData } from "../lib/types";
import { wsService } from "../lib/websocket";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"monitor" | "history" | "csv">("monitor");
  const [flows, setFlows] = useState<FlowData[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [selectedFlowForXai, setSelectedFlowForXai] = useState<FlowData | null>(null);
  const [activeAlert, setActiveAlert] = useState<FlowData | null>(null);
  const [threatCount, setThreatCount] = useState<number>(0);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [activeRulesCount, setActiveRulesCount] = useState<number>(0);

  useEffect(() => {
    // 1. Connect WebSocket
    wsService.connect();

    // 2. Subscribe to status
    const unsubStatus = wsService.onStatus((connected) => {
      setIsConnected(connected);
    });

    // 3. Subscribe to batched flows
    const unsubBatch = wsService.onFlowBatch((newFlows) => {
      setFlows((prev) => {
        const combined = [...newFlows, ...prev];
        return combined.slice(0, 200); // retain last 200 flows
      });
    });

    // 4. Subscribe to critical alerts
    const unsubAlert = wsService.onCriticalAlert((flow) => {
      setActiveAlert(flow);
      setThreatCount((prev) => prev + 1);
      soundEffects.playThreatAlarm();
    });

    // 5. Subscribe to telemetry
    const unsubTelemetry = wsService.onTelemetry((t) => {
      setTelemetry(t);
      if (t.total_threats) setThreatCount(t.total_threats);
    });

    // 6. Fetch initial active rules count
    fetch("/api/mitigate/rules")
      .then((r) => r.json())
      .then((rules) => {
        if (Array.isArray(rules)) setActiveRulesCount(rules.length);
      })
      .catch(() => {});

    return () => {
      unsubStatus();
      unsubBatch();
      unsubAlert();
      unsubTelemetry();
    };
  }, []);

  const handleBlockIp = (ip: string) => {
    setActiveRulesCount((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-300">
      {/* Top Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isConnected={isConnected}
        threatCount={threatCount}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {activeTab === "monitor" && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Real-time Telemetry & KPIs */}
            <LiveMonitor
              telemetry={telemetry}
              totalThreats={threatCount}
              activeRulesCount={activeRulesCount}
            />

            {/* Live Streaming Flow Table */}
            <FlowTable
              flows={flows}
              onSelectFlow={(flow) => setSelectedFlowForXai(flow)}
            />
          </div>
        )}

        {activeTab === "history" && (
          <div className="animate-in fade-in duration-200">
            <ThreatHistory
              onInspectFlow={(flow) => setSelectedFlowForXai(flow)}
            />
          </div>
        )}

        {activeTab === "csv" && (
          <div className="animate-in fade-in duration-200">
            <CsvStudio
              onInspectFlow={(flow) => setSelectedFlowForXai(flow)}
            />
          </div>
        )}
      </main>

      {/* Slide-in Intrusion Notification Card */}
      <ThreatAlertCard
        alert={activeAlert}
        onDismiss={() => setActiveAlert(null)}
        onInspect={(flow) => setSelectedFlowForXai(flow)}
        onBlockIp={handleBlockIp}
      />

      {/* Explainable AI Modal Dialog */}
      <XaiModal
        flow={selectedFlowForXai}
        onClose={() => setSelectedFlowForXai(null)}
        onBlockIp={handleBlockIp}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/60 px-6 py-4 text-center text-xs text-slate-500">
        AI-Based Network Intrusion Detection System with Explainable ML (TreeSHAP) • IET Lucknow MCA 2026-27
      </footer>
    </div>
  );
}
