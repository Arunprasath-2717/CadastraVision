import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react';

export function MapLegend() {
  return (
    <div className="bg-white/95 backdrop-blur-md p-4 rounded-2xl border border-pastel-border shadow-pastel-md text-pastel-text space-y-3">
      <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-pastel-muted border-b border-pastel-border pb-2">
        <Info className="w-4 h-4 text-pastel-action" />
        <span>Confidence Legend (WCAG AA)</span>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex items-center justify-between p-2 rounded-xl bg-pastel-mint/30 border border-emerald-200">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-emerald-400 border border-emerald-600" />
            <span className="text-pastel-mint-text font-semibold">High Confidence (&ge;80%)</span>
          </div>
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
        </div>

        <div className="flex items-center justify-between p-2 rounded-xl bg-pastel-amber/30 border border-amber-200">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-amber-400 border border-amber-600" />
            <span className="text-pastel-amber-text font-semibold">Medium (50-79%)</span>
          </div>
          <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
        </div>

        <div className="flex items-center justify-between p-2 rounded-xl bg-pastel-rose/30 border border-rose-200">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-rose-400 border border-rose-600" />
            <span className="text-pastel-rose-text font-semibold">Low Confidence (&lt;50%)</span>
          </div>
          <XCircle className="w-3.5 h-3.5 text-rose-700" />
        </div>
      </div>
    </div>
  );
}
