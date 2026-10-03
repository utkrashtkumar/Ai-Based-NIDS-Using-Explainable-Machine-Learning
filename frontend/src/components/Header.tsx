"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  Radio,
  History,
  FileSpreadsheet,
  Volume2,
  VolumeX,
  Server,
  Activity,
  Flame
} from "lucide-react";
import { InterfaceInfo } from "../lib/types";
import { soundEffects } from "./AudioAlert";

interface HeaderProps {
  activeTab: "monitor" | "history" | "csv";
  setActiveTab: (tab: "monitor" | "history" | "csv") => void;
  isConnected: boolean;
  threatCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  isConnected,
  threatCount
}) => {
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [interfaces, setInterfaces] = useState<InterfaceInfo[]>([]);
  const [selectedIface, setSelectedIface] = useState<string>("All Active");

  useEffect(() => {
    fetch("/api/interfaces")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setInterfaces(data);
      })
      .catch(() => {});
  }, []);

  const toggleSound = () => {
    soundEffects.enabled = !soundEnabled;
    setSoundEnabled(!soundEnabled);
  };

  return (
    <header className="border-b border-cyan-900/40 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-4 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Status */}
      <div className="flex items-center gap-3">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)]">
          <Shield className="w-5 h-5" />
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isConnected ? "bg-emerald-400" : "bg-red-500"
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-3 w-3 ${
                isConnected ? "bg-emerald-500" : "bg-red-500"
              }`}
            />
          </span>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-slate-100 flex items-center gap-2">
              AI-NIDS <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-700/50 font-mono">XAI v2.0</span>
            </h1>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium flex items-center gap-1 ${
                isConnected
                  ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30"
                  : "bg-red-950/60 text-red-400 border border-red-500/30"
              }`}
            >
              <Radio className="w-3 h-3 animate-pulse" />
              {isConnected ? "PROTECTION ACTIVE" : "DISCONNECTED"}
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            Explainable Machine Learning • Host-Level Threat Defense
          </p>
        </div>
      </div>

      {/* Nav Tabs */}
      <nav className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
        <button
          onClick={() => setActiveTab("monitor")}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            activeTab === "monitor"
              ? "bg-cyan-600/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Live Sentinel
        </button>

        <button
          onClick={() => setActiveTab("history")}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all relative ${
            activeTab === "history"
              ? "bg-cyan-600/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <History className="w-3.5 h-3.5" />
          Threat History
          {threatCount > 0 && (
            <span className="bg-red-500 text-white text-[10px] px-1.5 py-0.2 rounded-full font-bold">
              {threatCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("csv")}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            activeTab === "csv"
              ? "bg-cyan-600/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileSpreadsheet className="w-3.5 h-3.5" />
          CSV Studio
        </button>
      </nav>

      {/* Interface Selector & Sound Controls */}
      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 text-xs bg-slate-900/60 border border-slate-800 rounded-md px-2.5 py-1">
          <Server className="w-3.5 h-3.5 text-cyan-400" />
          <select
            value={selectedIface}
            onChange={(e) => setSelectedIface(e.target.value)}
            className="bg-transparent text-slate-300 border-none outline-none cursor-pointer text-xs"
          >
            <option value="All Active" className="bg-slate-900 text-slate-200">
              Auto Adapter (Wi-Fi / Ethernet)
            </option>
            {interfaces.map((iface) => (
              <option key={iface.name} value={iface.name} className="bg-slate-900 text-slate-200">
                {iface.type}: {iface.name} ({iface.ip})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={toggleSound}
          title={soundEnabled ? "Mute audio alerts" : "Enable audio alerts"}
          className={`p-2 rounded-md border text-xs transition-colors ${
            soundEnabled
              ? "bg-slate-800/60 border-slate-700 text-cyan-400 hover:bg-slate-800"
              : "bg-slate-900/60 border-slate-800 text-slate-500"
          }`}
        >
          {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
};
