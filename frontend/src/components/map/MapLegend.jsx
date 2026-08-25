import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react';

export function MapLegend() {
  return (
    <div className="cv-panel-elevated space-y-3 rounded-2xl p-4 text-pastel-text transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_40px_rgba(1,28,64,0.12)]">
      <div className="flex items-center space-x-2 border-b border-[#C9E5EE] pb-2 text-xs font-bold uppercase tracking-[0.18em] text-[#4F7285]">
        <Info className="h-4 w-4 text-[#266580]" />
        <span>Confidence Legend</span>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex items-center justify-between rounded-xl border border-emerald-200 bg-[linear-gradient(135deg,rgba(167,235,242,0.30),rgba(16,185,129,0.08))] p-2">
          <div className="flex items-center space-x-2">
            <span className="h-3 w-3 rounded-full border border-emerald-600 bg-emerald-400" />
            <span className="font-semibold text-[#0B5463]">High Confidence (&ge;80%)</span>
          </div>
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700" />
        </div>

        <div className="flex items-center justify-between rounded-xl border border-amber-200 bg-[linear-gradient(135deg,rgba(246,215,166,0.35),rgba(245,158,11,0.08))] p-2">
          <div className="flex items-center space-x-2">
            <span className="h-3 w-3 rounded-full border border-amber-600 bg-amber-400" />
            <span className="font-semibold text-[#7E560B]">Medium (50-79%)</span>
          </div>
          <AlertTriangle className="h-3.5 w-3.5 text-amber-700" />
        </div>

        <div className="flex items-center justify-between rounded-xl border border-rose-200 bg-[linear-gradient(135deg,rgba(233,186,200,0.3),rgba(239,68,68,0.08))] p-2">
          <div className="flex items-center space-x-2">
            <span className="h-3 w-3 rounded-full border border-rose-600 bg-rose-400" />
            <span className="font-semibold text-[#8A3348]">Low Confidence (&lt;50%)</span>
          </div>
          <XCircle className="h-3.5 w-3.5 text-rose-700" />
        </div>
      </div>
    </div>
  );
}
