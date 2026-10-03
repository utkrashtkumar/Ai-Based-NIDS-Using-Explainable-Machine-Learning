"use client";

import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Download,
  Play,
  RotateCcw
} from "lucide-react";
import { FlowData } from "../lib/types";

interface CsvStudioProps {
  onInspectFlow: (flow: FlowData) => void;
}

interface CsvResultPayload {
  filename: string;
  total_flows: number;
  benign_count: number;
  threat_count: number;
  threat_percentage: number;
  attack_distribution: Record<string, number>;
  results: FlowData[];
}

export const CsvStudio: React.FC<CsvStudioProps> = ({ onInspectFlow }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<CsvResultPayload | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setErrorMsg("Please upload a valid .csv file.");
      return;
    }

    setErrorMsg(null);
    setIsUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/csv/upload", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to process CSV");
      }

      const data: CsvResultPayload = await res.json();
      setResult(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMsg(message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Box */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
          isDragging
            ? "border-cyan-400 bg-cyan-950/30 scale-[1.01]"
            : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-cyan-950/60 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.2)]">
            <UploadCloud className="w-7 h-7" />
          </div>

          <div>
            <h3 className="text-base font-bold text-slate-100">
              Drag and drop network flow CSV here
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md">
              Upload pre-recorded PCAP flows or CIC-IDS2017 benchmark files to evaluate detection accuracy and inspect TreeSHAP explanations offline.
            </p>
          </div>

          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 border border-slate-700 font-medium">
              {isUploading ? "Analyzing flows with XGBoost..." : "Browse CSV File"}
            </span>
          </div>

          <p className="text-[11px] text-slate-500">
            Tip: Pre-generated test files are available in <code className="text-cyan-400 font-mono">sample_data/sample_attacks.csv</code>
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-red-950/40 border border-red-500/50 text-red-300 p-3.5 rounded-xl text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Results Dashboard */}
      {result && (
        <div className="space-y-4 animate-in fade-in duration-300">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 font-medium">Total Flows</span>
              <div className="text-xl font-bold font-mono text-slate-100 mt-1">
                {result.total_flows}
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 font-medium">Benign Traffic</span>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                {result.benign_count}
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 font-medium">Flagged Threats</span>
              <div className="text-xl font-bold font-mono text-red-400 mt-1">
                {result.threat_count}
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 font-medium">Threat Percentage</span>
              <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
                {result.threat_percentage}%
              </div>
            </div>
          </div>

          {/* Attack Breakdown Pills */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3.5 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-400 mr-2">Attack Breakdown:</span>
            {Object.entries(result.attack_distribution).map(([cls, cnt]) => (
              <span
                key={cls}
                className={`text-xs px-2.5 py-1 rounded-md font-mono flex items-center gap-1.5 ${
                  cls === "BENIGN"
                    ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30"
                    : "bg-red-950/60 text-red-300 border border-red-500/40 font-bold"
                }`}
              >
                {cls}: {cnt}
              </span>
            ))}
          </div>

          {/* Table Preview */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-3.5 border-b border-slate-800 flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Classified Flow Records ({result.results.length} Previewed)
              </h4>
              <span className="text-xs text-slate-500">
                Click &ldquo;Explain&rdquo; on any row to open the TreeSHAP inspector
              </span>
            </div>

            <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-slate-400 sticky top-0 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">#</th>
                    <th className="py-2.5 px-3">Predicted Class</th>
                    <th className="py-2.5 px-3">Confidence</th>
                    <th className="py-2.5 px-3">Reasoning Preview</th>
                    <th className="py-2.5 px-3 text-right">Explain (XAI)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {result.results.map((row, idx) => (
                    <tr
                      key={idx}
                      onClick={() => onInspectFlow(row)}
                      className={`cursor-pointer hover:bg-slate-800/40 transition-colors ${
                        row.is_threat ? "bg-red-950/15" : ""
                      }`}
                    >
                      <td className="py-2.5 px-3 text-slate-500">{idx + 1}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-sans ${
                            row.is_threat
                              ? "bg-red-500/20 text-red-400 border border-red-500/40 font-bold"
                              : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                          }`}
                        >
                          {row.prediction}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {Math.round((row.confidence || 0) * 100)}%
                      </td>
                      <td className="py-2.5 px-3 max-w-md truncate text-slate-400 text-[11px] font-sans">
                        {row.narrative || "Flow analyzed."}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onInspectFlow(row);
                          }}
                          className="px-2 py-1 rounded text-[11px] font-sans bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
