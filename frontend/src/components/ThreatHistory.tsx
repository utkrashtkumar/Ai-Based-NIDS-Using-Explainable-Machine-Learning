"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Trash2,
  Lock,
  Unlock,
  CheckCircle2,
  Calendar,
  ExternalLink,
  Search,
  RefreshCw
} from "lucide-react";
import { IncidentRecord, FlowData } from "../lib/types";

interface ThreatHistoryProps {
  onInspectFlow: (flow: FlowData) => void;
}

export const ThreatHistory: React.FC<ThreatHistoryProps> = ({ onInspectFlow }) => {
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [blockedIps, setBlockedIps] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [incRes, blockRes] = await Promise.all([
        fetch("/api/incidents"),
        fetch("/api/incidents/blocked-ips")
      ]);
      const incData = await incRes.json();
      const blockData = await blockRes.json();

      if (Array.isArray(incData)) setIncidents(incData);
      if (Array.isArray(blockData)) setBlockedIps(blockData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDismiss = async (id: number) => {
    try {
      await fetch(`/api/incidents/${id}/dismiss`, { method: "POST" });
      setIncidents((prev) => prev.filter((i) => i.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleUnblock = async (ip: string) => {
    try {
      await fetch("/api/mitigate/unblock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip_address: ip })
      });
      setBlockedIps((prev) => prev.filter((b) => b !== ip));
    } catch (e) {
      console.error(e);
    }
  };

  const filteredIncidents = incidents.filter(
    (i) =>
      i.src_ip.includes(searchTerm) ||
      i.attack_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Section: Active Firewall Blocked IPs */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-red-400" />
            <h2 className="text-sm font-bold text-slate-100">
              Active Windows Firewall Rules ({blockedIps.length})
            </h2>
          </div>
          <button
            onClick={fetchData}
            className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>

        {blockedIps.length === 0 ? (
          <p className="text-xs text-slate-500">
            No IPs are currently blocked. When an attack is flagged, click &ldquo;Block IP&rdquo; to isolate the attacker in Windows Firewall.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {blockedIps.map((ip) => (
              <div
                key={ip}
                className="bg-red-950/40 border border-red-500/50 rounded-lg px-3 py-1.5 flex items-center gap-2 text-xs font-mono"
              >
                <span className="text-red-300 font-semibold">{ip}</span>
                <button
                  onClick={() => handleUnblock(ip)}
                  title="Remove firewall block rule"
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  <Unlock className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Incident Log Table */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-sm">
        <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-slate-200">
              Persistent Threat Audit Log (SQLite)
            </h2>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter threat records..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md pl-8 pr-3 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 w-56"
            />
          </div>
        </div>

        <div className="overflow-x-auto max-h-[450px] overflow-y-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 sticky top-0 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4">Detected At</th>
                <th className="py-2.5 px-4">Attacker IP</th>
                <th className="py-2.5 px-4">Attack Vector</th>
                <th className="py-2.5 px-4">Confidence</th>
                <th className="py-2.5 px-4">Reasoning Summary</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredIncidents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500 font-sans text-xs">
                    {loading ? "Loading incident history..." : "No recorded threat incidents in database."}
                  </td>
                </tr>
              ) : (
                filteredIncidents.map((inc) => {
                  const dateStr = new Date(inc.timestamp * 1000).toLocaleString([], {
                    dateStyle: "short",
                    timeStyle: "medium"
                  });

                  return (
                    <tr key={inc.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-4 text-slate-400 text-[11px] whitespace-nowrap">
                        {dateStr}
                      </td>
                      <td className="py-2.5 px-4 font-semibold text-red-400">
                        {inc.src_ip}
                      </td>
                      <td className="py-2.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[11px] bg-red-500/20 text-red-300 border border-red-500/40">
                          {inc.attack_type}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-slate-200">
                        {Math.round(inc.confidence * 100)}%
                      </td>
                      <td className="py-2.5 px-4 max-w-xs truncate font-sans text-slate-400 text-[11px]">
                        {inc.narrative}
                      </td>
                      <td className="py-2.5 px-4 text-right flex items-center justify-end gap-2">
                        <button
                          onClick={() => {
                            let shapTop5 = [];
                            try {
                              shapTop5 = JSON.parse(inc.shap_json);
                            } catch {}

                            onInspectFlow({
                              src_ip: inc.src_ip,
                              dst_ip: inc.dst_ip,
                              src_port: inc.src_port,
                              dst_port: inc.dst_port,
                              protocol: inc.protocol,
                              start_time: inc.timestamp,
                              end_time: inc.timestamp,
                              duration: 0.1,
                              total_packets: 10,
                              prediction: inc.attack_type,
                              confidence: inc.confidence,
                              is_threat: true,
                              narrative: inc.narrative,
                              shap_top5: shapTop5
                            });
                          }}
                          className="p-1 text-cyan-400 hover:text-cyan-300 rounded hover:bg-slate-800"
                          title="Inspect XAI explanation"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </button>

                        <button
                          onClick={() => handleDismiss(inc.id)}
                          className="p-1 text-slate-500 hover:text-red-400 rounded hover:bg-slate-800"
                          title="Dismiss incident"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
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
    </div>
  );
};
