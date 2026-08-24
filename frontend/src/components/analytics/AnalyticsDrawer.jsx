import React from 'react';
import { X, Layers, CheckCircle2, Clock, ShieldAlert, TrendingUp } from 'lucide-react';

export function AnalyticsDrawer({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white border-l border-pastel-border shadow-pastel-lg p-6 flex flex-col justify-between text-pastel-text animate-slide-left">
      <div>
        <div className="flex items-center justify-between border-b border-pastel-border pb-4 mb-6">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-pastel-lavender rounded-xl text-pastel-action">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold font-display text-pastel-text">Cadastral Analytics</h3>
              <p className="text-xs text-pastel-muted">Sector 4 Pilot Metrics</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-pastel-subtle hover:text-pastel-text p-1.5 rounded-xl hover:bg-pastel-surface-soft"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-4 bg-pastel-surface-soft border border-pastel-border rounded-2xl">
            <span className="text-xs text-pastel-muted block">Total Parcels</span>
            <span className="text-2xl font-bold font-mono text-pastel-text mt-1 block">10,284</span>
            <span className="text-[10px] text-emerald-600 font-semibold mt-1 block">↑ 98.4% Coverage</span>
          </div>

          <div className="p-4 bg-pastel-amber/30 border border-amber-200 rounded-2xl">
            <span className="text-xs text-pastel-amber-text block font-medium">Pending Review</span>
            <span className="text-2xl font-bold font-mono text-pastel-amber-text mt-1 block">128</span>
            <span className="text-[10px] text-amber-700 font-medium mt-1 block">&lt; 1.5% of total</span>
          </div>

          <div className="p-4 bg-pastel-mint/30 border border-emerald-200 rounded-2xl">
            <span className="text-xs text-pastel-mint-text block font-medium">Approved Parcels</span>
            <span className="text-2xl font-bold font-mono text-pastel-mint-text mt-1 block">8,920</span>
            <span className="text-[10px] text-emerald-700 font-semibold mt-1 block">Export Eligible</span>
          </div>

          <div className="p-4 bg-pastel-rose/30 border border-rose-200 rounded-2xl">
            <span className="text-xs text-pastel-rose-text block font-medium">Topology Flags</span>
            <span className="text-2xl font-bold font-mono text-pastel-rose-text mt-1 block">42</span>
            <span className="text-[10px] text-rose-700 font-medium mt-1 block">Overlaps & Gaps</span>
          </div>
        </div>

        {/* Confidence Distribution */}
        <div className="p-4 bg-pastel-surface-soft border border-pastel-border rounded-2xl space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-pastel-muted">
            Confidence Score Distribution
          </h4>

          <div className="space-y-2 text-xs font-medium">
            <div>
              <div className="flex justify-between text-pastel-text mb-1">
                <span>High (&ge;80%)</span>
                <span className="font-mono text-emerald-700 font-bold">86.7%</span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full rounded-full" style={{ width: '86.7%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-pastel-text mb-1">
                <span>Medium (50-79%)</span>
                <span className="font-mono text-amber-700 font-bold">10.5%</span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: '10.5%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-pastel-text mb-1">
                <span>Low (&lt;50%)</span>
                <span className="font-mono text-rose-700 font-bold">2.8%</span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div className="bg-rose-500 h-full rounded-full" style={{ width: '2.8%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-pastel-border text-center text-xs text-pastel-muted">
        <span>Updated real-time from district PostGIS engine</span>
      </div>
    </div>
  );
}
