"use client";

import React, { useState } from "react";
import {
  X,
  ShieldAlert,
  ShieldCheck,
  Brain,
  Sliders,
  Flame,
  CheckCircle2,
  Lock,
  Layers,
  ArrowRight,
  TrendingUp,
  TrendingDown
} from "lucide-react";
import { FlowData } from "../lib/types";

interface XaiModalProps {
  flow: FlowData | null;
  onClose: () => void;
  onBlockIp: (ip: string) => void;
}

export const XaiModal: React.FC<XaiModalProps> = ({ flow, onClose, onBlockIp }) => {
  const [activeTab, setActiveTab] = useState<"shap" | "features">("shap");
  const [isBlocking, setIsBlocking] = useState(false);
  const [blockStatus, setBlockStatus] = useState<string | null>(null);

  if (!flow) return null;

  const isThreat = flow.is_threat;
  const attackName = flow.prediction || "BENIGN";
  const confidencePct = Math.round((flow.confidence || 0.5) * 100);

  const handleBlock = async () => {
    setIsBlocking(true);
    setBlockStatus("Deploying Windows Firewall rule...");
    try {
      const res = await fetch("/api/mitigate/block", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip_address: flow.src_ip })
      });
      const data = await res.json();
      if (data.success) {
        setBlockStatus(`IP ${flow.src_ip} successfully blocked!`);
        onBlockIp(flow.src_ip);
      } else {
        setBlockStatus(`Error: ${data.message}`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setBlockStatus(`Failed: ${message}`);
    } finally {
      setIsBlocking(false);
    }
  };

  const topShap = flow.shap_top5 || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-950 border border-cyan-900/60 rounded-2xl w-full max-w-3xl overflow-hidden shadow-[0_0_50px_rgba(6,182,212,0.15)] flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`p-2.5 rounded-xl border ${
                isThreat
                  ? "bg-red-500/10 border-red-500/40 text-red-400"
                  : "bg-emerald-500/10 border-emerald-500/40 text-emerald-400"
              }`}
            >
              {isThreat ? <ShieldAlert className="w-6 h-6" /> : <ShieldCheck className="w-6 h-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base sm:text-lg font-bold text-slate-100 flex items-center gap-2">
                  Explainable AI (XAI) Inspector
                </h3>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    isThreat
                      ? "bg-red-500/20 text-red-400 border border-red-500/40"
                      : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                  }`}
                >
                  {attackName} ({confidencePct}%)
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                {flow.src_ip}:{flow.src_port} ➔ {flow.dst_ip}:{flow.dst_port} ({flow.protocol})
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Area */}
        <div className="p-4 sm:p-6 overflow-y-auto space-y-5">
          {/* Plain English Narrative Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 relative overflow-hidden">
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <Brain className="w-4 h-4" />
              Plain-English Decision Reasoning
            </div>
            <p className="text-sm text-slate-200 leading-relaxed font-sans">
              {flow.narrative ||
                `Traffic from ${flow.src_ip} exhibits anomalous statistical deviation matching ${attackName} patterns. The XGBoost classifier identified this session based on high Shapley feature attributions.`}
            </p>
            <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none" />
          </div>

          {/* Sub Navigation */}
          <div className="flex border-b border-slate-800 text-xs font-medium gap-4">
            <button
              onClick={() => setActiveTab("shap")}
              className={`pb-2.5 transition-colors border-b-2 flex items-center gap-1.5 ${
                activeTab === "shap"
                  ? "border-cyan-400 text-cyan-400 font-bold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              TreeSHAP Feature Impact
            </button>
            <button
              onClick={() => setActiveTab("features")}
              className={`pb-2.5 transition-colors border-b-2 flex items-center gap-1.5 ${
                activeTab === "features"
                  ? "border-cyan-400 text-cyan-400 font-bold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              All 20 Flow Features
            </button>
          </div>

          {/* Tab 1: SHAP Waterfall / Feature Impact */}
          {activeTab === "shap" && (
            <div className="space-y-3">
              <p className="text-xs text-slate-400">
                The chart below shows which statistical network characteristics pushed the AI model toward flagging this threat.
              </p>

              {topShap.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500 bg-slate-900/40 rounded-lg">
                  Benign traffic baseline: Feature weights are evenly distributed within normal parameters.
                </div>
              ) : (
                <div className="space-y-2.5 font-mono">
                  {topShap.map((item, i) => {
                    const isPositive = item.shap_value > 0;
                    const maxShap = Math.max(...topShap.map((s) => Math.abs(s.shap_value)), 1);
                    const barWidth = Math.min(100, Math.round((Math.abs(item.shap_value) / maxShap) * 100));

                    return (
                      <div key={i} className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-3 text-xs">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-semibold text-slate-200">{item.feature}</span>
                          <span className="text-slate-400">
                            Raw: <span className="text-cyan-400">{item.raw_value}</span>
                          </span>
                        </div>

                        {/* Bar */}
                        <div className="flex items-center gap-2">
                          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden flex">
                            <div
                              className={`h-full rounded-full transition-all ${
                                isPositive ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" : "bg-emerald-500"
                              }`}
                              style={{ width: `${barWidth}%` }}
                            />
                          </div>
                          <span
                            className={`text-[11px] font-bold min-w-[50px] text-right ${
                              isPositive ? "text-red-400" : "text-emerald-400"
                            }`}
                          >
                            {isPositive ? `+${item.shap_value}` : item.shap_value}
                          </span>
                        </div>

                        <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1 font-sans">
                          {isPositive ? (
                            <span className="text-red-400 flex items-center gap-1">
                              <TrendingUp className="w-3 h-3" /> Pushed prediction toward {attackName}
                            </span>
                          ) : (
                            <span className="text-emerald-400 flex items-center gap-1">
                              <TrendingDown className="w-3 h-3" /> Supported normal benign behavior
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Tab 2: All 20 Features Table */}
          {activeTab === "features" && (
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 font-sans">
                  <tr>
                    <th className="py-2 px-3">Feature Name</th>
                    <th className="py-2 px-3">Measured Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {Object.entries(flow.features || {}).map(([key, val], idx) => (
                    <tr key={idx} className="hover:bg-slate-900/50">
                      <td className="py-2 px-3 font-semibold text-slate-400">{key}</td>
                      <td className="py-2 px-3 text-cyan-400">{val}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal Footer / Mitigation Action */}
        <div className="p-4 sm:p-5 border-t border-slate-800 bg-slate-900/80 flex flex-wrap items-center justify-between gap-3">
          <div className="text-xs text-slate-400 font-mono">
            {blockStatus ? (
              <span className="text-cyan-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                {blockStatus}
              </span>
            ) : (
              <span>Target: {flow.src_ip}</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors"
            >
              Close
            </button>

            {isThreat && (
              <button
                onClick={handleBlock}
                disabled={isBlocking}
                className="px-4 py-2 rounded-lg text-xs font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50 transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(239,68,68,0.3)]"
              >
                <Lock className="w-3.5 h-3.5" />
                {isBlocking ? "Blocking..." : "🛡️ Block IP in Firewall"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
