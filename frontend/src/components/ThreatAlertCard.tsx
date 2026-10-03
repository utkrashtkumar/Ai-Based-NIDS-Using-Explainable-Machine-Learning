"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, ShieldAlert, X, Eye, Lock } from "lucide-react";
import { FlowData } from "../lib/types";

interface ThreatAlertCardProps {
  alert: FlowData | null;
  onDismiss: () => void;
  onInspect: (flow: FlowData) => void;
  onBlockIp: (ip: string) => void;
}

export const ThreatAlertCard: React.FC<ThreatAlertCardProps> = ({
  alert,
  onDismiss,
  onInspect,
  onBlockIp
}) => {
  const [isBlocking, setIsBlocking] = useState(false);

  useEffect(() => {
    if (!alert) return;
    // Auto-dismiss after 15 seconds if not interacted
    const timer = setTimeout(() => {
      onDismiss();
    }, 15000);
    return () => clearTimeout(timer);
  }, [alert, onDismiss]);

  if (!alert) return null;

  const handleBlock = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsBlocking(true);
    try {
      await fetch("/api/mitigate/block", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip_address: alert.src_ip })
      });
      onBlockIp(alert.src_ip);
      onDismiss();
    } catch (err) {
      console.error(err);
    } finally {
      setIsBlocking(false);
    }
  };

  return (
    <div className="fixed top-16 right-4 sm:right-6 z-50 max-w-sm w-full bg-slate-950/95 border-2 border-red-500/80 rounded-xl p-4 shadow-[0_0_30px_rgba(239,68,68,0.4)] backdrop-blur-lg animate-in slide-in-from-top-4 duration-300">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-red-400 uppercase tracking-wider">
                Intrusion Intercepted
              </span>
              <span className="text-[10px] px-1.5 py-0.2 bg-red-500 text-white rounded-full font-bold">
                {Math.round((alert.confidence || 0.9) * 100)}%
              </span>
            </div>
            <h4 className="text-sm font-bold text-slate-100 mt-0.5">
              {alert.prediction} Threat
            </h4>
          </div>
        </div>

        <button
          onClick={onDismiss}
          className="text-slate-500 hover:text-slate-300 p-1 rounded transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="mt-3 text-xs text-slate-300 font-mono bg-slate-900/80 rounded-lg p-2.5 border border-slate-800">
        <div>Attacker: <span className="text-red-400 font-bold">{alert.src_ip}</span></div>
        <div className="text-slate-400 text-[11px] mt-0.5">Target Port: {alert.dst_port} ({alert.protocol})</div>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => {
            onInspect(alert);
            onDismiss();
          }}
          className="flex-1 py-1.5 px-3 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 flex items-center justify-center gap-1.5 transition-colors"
        >
          <Eye className="w-3.5 h-3.5" />
          Explain (XAI)
        </button>

        <button
          onClick={handleBlock}
          disabled={isBlocking}
          className="flex-1 py-1.5 px-3 rounded-lg text-xs font-bold bg-red-600 hover:bg-red-500 text-white flex items-center justify-center gap-1.5 transition-colors shadow-[0_0_10px_rgba(239,68,68,0.3)] disabled:opacity-50"
        >
          <Lock className="w-3.5 h-3.5" />
          {isBlocking ? "Blocking..." : "Block IP"}
        </button>
      </div>
    </div>
  );
};
