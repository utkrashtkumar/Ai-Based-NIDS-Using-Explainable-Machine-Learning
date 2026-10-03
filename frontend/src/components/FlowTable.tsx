"use client";

import React, { useState } from "react";
import {
  Search,
  SlidersHorizontal,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  ExternalLink
} from "lucide-react";
import { FlowData } from "../lib/types";

interface FlowTableProps {
  flows: FlowData[];
  onSelectFlow: (flow: FlowData) => void;
}

export const FlowTable: React.FC<FlowTableProps> = ({ flows, onSelectFlow }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<"ALL" | "THREATS" | "BENIGN">("ALL");

  const filteredFlows = flows.filter((f) => {
    const matchesSearch =
      f.src_ip.includes(searchTerm) ||
      f.dst_ip.includes(searchTerm) ||
      (f.prediction && f.prediction.toLowerCase().includes(searchTerm.toLowerCase())) ||
      f.protocol.toLowerCase().includes(searchTerm.toLowerCase());

    if (!matchesSearch) return false;

    if (filterType === "THREATS") return f.is_threat;
    if (filterType === "BENIGN") return !f.is_threat;
    return true;
  });

  return (
    <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl overflow-hidden backdrop-blur-sm">
      {/* Controls Bar */}
      <div className="p-3.5 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-200">
            Live Intercepted Flows
          </span>
          <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/50">
            {filteredFlows.length} Active
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search IP, Port, Attack..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md pl-8 pr-3 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 w-44 sm:w-56"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex rounded-md border border-slate-800 p-0.5 text-xs bg-slate-950">
            <button
              onClick={() => setFilterType("ALL")}
              className={`px-2.5 py-0.5 rounded text-[11px] font-medium transition-colors ${
                filterType === "ALL" ? "bg-slate-800 text-cyan-400" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterType("THREATS")}
              className={`px-2.5 py-0.5 rounded text-[11px] font-medium transition-colors ${
                filterType === "THREATS" ? "bg-red-500/20 text-red-400 font-bold" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Threats Only
            </button>
            <button
              onClick={() => setFilterType("BENIGN")}
              className={`px-2.5 py-0.5 rounded text-[11px] font-medium transition-colors ${
                filterType === "BENIGN" ? "bg-emerald-500/20 text-emerald-400" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Benign
            </button>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto max-h-[380px] overflow-y-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 font-medium sticky top-0 z-10 border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Timestamp</th>
              <th className="py-2.5 px-3">Source IP</th>
              <th className="py-2.5 px-3">Destination</th>
              <th className="py-2.5 px-3">Proto</th>
              <th className="py-2.5 px-3">Packets</th>
              <th className="py-2.5 px-3">Classification</th>
              <th className="py-2.5 px-3 text-right">Explain (XAI)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {filteredFlows.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-500 font-sans text-xs">
                  Listening for packets... No matching flows intercepted yet.
                </td>
              </tr>
            ) : (
              filteredFlows.map((flow, idx) => {
                const isThreat = flow.is_threat;
                const timeStr = new Date(flow.end_time * 1000).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit"
                });

                return (
                  <tr
                    key={idx}
                    onClick={() => onSelectFlow(flow)}
                    className={`cursor-pointer transition-colors hover:bg-slate-800/40 ${
                      isThreat ? "bg-red-950/15" : ""
                    }`}
                  >
                    <td className="py-2.5 px-3 text-slate-400 text-[11px] whitespace-nowrap">
                      {timeStr}
                    </td>

                    <td className="py-2.5 px-3 font-semibold text-slate-200">
                      {flow.src_ip}
                    </td>

                    <td className="py-2.5 px-3 text-slate-400">
                      {flow.dst_ip}:{flow.dst_port}
                    </td>

                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 border border-slate-700 text-slate-300">
                        {flow.protocol}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 text-slate-400 text-xs">
                      {flow.total_packets} pkts
                    </td>

                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-sans font-medium ${
                          isThreat
                            ? "bg-red-500/20 text-red-400 border border-red-500/40 font-semibold"
                            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        }`}
                      >
                        {isThreat ? (
                          <ShieldAlert className="w-3 h-3 text-red-400" />
                        ) : (
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                        )}
                        {flow.prediction || "BENIGN"}
                        {flow.confidence && (
                          <span className="opacity-70 text-[10px]">
                            ({Math.round(flow.confidence * 100)}%)
                          </span>
                        )}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectFlow(flow);
                        }}
                        className={`px-2 py-1 rounded text-[11px] font-sans flex items-center gap-1 ml-auto transition-all ${
                          isThreat
                            ? "bg-red-600/30 hover:bg-red-600/50 text-red-300 border border-red-500/50 shadow-[0_0_8px_rgba(239,68,68,0.2)]"
                            : "bg-slate-800/80 hover:bg-slate-700 text-cyan-400 border border-slate-700"
                        }`}
                      >
                        <HelpCircle className="w-3 h-3" />
                        Why?
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
