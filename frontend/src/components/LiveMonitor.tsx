"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  ShieldAlert,
  HardDrive,
  Zap,
  TrendingUp,
  Cpu
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";
import { TelemetryData } from "../lib/types";

interface LiveMonitorProps {
  telemetry: TelemetryData | null;
  totalThreats: number;
  activeRulesCount: number;
}

interface ChartPoint {
  time: string;
  kb_s: number;
  pkts_s: number;
}

export const LiveMonitor: React.FC<LiveMonitorProps> = ({
  telemetry,
  totalThreats,
  activeRulesCount
}) => {
  const [chartData, setChartData] = useState<ChartPoint[]>([]);

  useEffect(() => {
    if (!telemetry) return;

    const timeLabel = new Date(telemetry.timestamp * 1000).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });

    setChartData((prev) => {
      const next = [...prev, { time: timeLabel, kb_s: telemetry.kb_s, pkts_s: telemetry.pkts_s }];
      return next.slice(-25); // keep last 25 seconds of telemetry
    });
  }, [telemetry]);

  // Calculate dynamic risk level (0-100)
  const currentRiskScore = Math.min(
    100,
    Math.round((totalThreats * 15) + (telemetry?.pkts_s && telemetry.pkts_s > 500 ? 30 : 0))
  );

  return (
    <div className="space-y-4">
      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 lg:gap-4">
        {/* KPI 1: Live Bandwidth */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/40 transition-all">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-medium">Throughput</span>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {telemetry?.kb_s ?? 0} <span className="text-xs text-cyan-400 font-sans font-normal">KB/s</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-emerald-400" /> {telemetry?.pkts_s ?? 0} packets/sec
          </div>
          <div className="absolute -bottom-6 -right-6 w-16 h-16 bg-cyan-500/5 rounded-full blur-xl group-hover:bg-cyan-500/10 transition-all" />
        </div>

        {/* KPI 2: Total Flows Analyzed */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-medium">Flows Inspected</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {(telemetry?.total_flows ?? 0).toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Sub-millisecond XGBoost classification
          </div>
        </div>

        {/* KPI 3: Flagged Threats */}
        <div className={`border rounded-xl p-3.5 backdrop-blur-sm relative overflow-hidden transition-all ${
          totalThreats > 0
            ? "bg-red-950/20 border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.15)]"
            : "bg-slate-900/60 border-slate-800/80"
        }`}>
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-medium">Threats Detected</span>
            <AlertTriangle className={`w-4 h-4 ${totalThreats > 0 ? "text-red-400 animate-bounce" : "text-slate-500"}`} />
          </div>
          <div className={`text-2xl font-bold font-mono ${totalThreats > 0 ? "text-red-400" : "text-slate-100"}`}>
            {totalThreats}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {totalThreats === 0 ? "All traffic secure" : "Active alerts logged"}
          </div>
          {totalThreats > 0 && (
            <div className="absolute top-0 right-0 h-1.5 w-full bg-gradient-to-r from-transparent via-red-500 to-transparent" />
          )}
        </div>

        {/* KPI 4: Threat Severity Gauge */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 backdrop-blur-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-medium">Host Risk Index</span>
            <ShieldAlert className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-slate-100">
              {currentRiskScore}%
            </span>
            <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
              currentRiskScore > 60
                ? "bg-red-500/20 text-red-400"
                : currentRiskScore > 25
                ? "bg-amber-500/20 text-amber-400"
                : "bg-emerald-500/20 text-emerald-400"
            }`}>
              {currentRiskScore > 60 ? "Severe" : currentRiskScore > 25 ? "Elevated" : "Low Risk"}
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2.5 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                currentRiskScore > 60
                  ? "bg-red-500"
                  : currentRiskScore > 25
                  ? "bg-amber-400"
                  : "bg-emerald-400"
              }`}
              style={{ width: `${Math.max(5, currentRiskScore)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Real-time Streaming Throughput Chart */}
      <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-slate-200">
              Real-Time Network Telemetry
            </h2>
          </div>
          <span className="text-xs font-mono text-slate-400 flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Streaming Live
          </span>
        </div>

        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="kbGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                axisLine={{ stroke: "#334155" }}
              />
              <YAxis
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                axisLine={{ stroke: "#334155" }}
                tickFormatter={(v) => `${v} KB`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#090d16",
                  borderColor: "#1e293b",
                  borderRadius: "8px",
                  fontSize: "11px",
                  color: "#e2e8f0"
                }}
              />
              <Area
                type="monotone"
                dataKey="kb_s"
                stroke="#06b6d4"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#kbGradient)"
                name="Throughput (KB/s)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
