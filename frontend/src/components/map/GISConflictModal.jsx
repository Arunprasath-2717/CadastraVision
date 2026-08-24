import React from 'react';
import { AlertTriangle, X, Check, ShieldAlert, ArrowUpRight } from 'lucide-react';

/**
 * Existing GIS Conflict Resolution Dialog (PRD-CM-04 Section 24 & Rule R4)
 * Surfaced when AI boundary disagrees with recorded official GIS layer.
 */
export function GISConflictModal({ conflict, onClose, onResolve }) {
  if (!conflict) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg glass-panel rounded-xl border border-amber-800/80 shadow-2xl p-6 bg-gov-surface/95 text-white">
        
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4 mb-4">
          <div className="flex items-center space-x-3 text-amber-400">
            <div className="p-2 bg-amber-500/10 rounded-lg">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Existing GIS Boundary Discrepancy</h3>
              <p className="text-xs text-amber-300">Conflict ID: {conflict.conflict_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Details */}
        <div className="space-y-4 text-xs text-slate-300">
          <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-lg text-amber-200 leading-relaxed">
            Existing recorded GIS boundary differs from AI-generated segmentation boundary.
            <strong className="block text-white mt-1">{conflict.description}</strong>
          </div>

          <div className="grid grid-cols-2 gap-3 p-3 bg-slate-900/90 rounded-lg border border-slate-800">
            <div>
              <span className="text-slate-400 block">Recorded GIS Area:</span>
              <span className="font-mono text-sm font-semibold text-white">{conflict.existing_gis_area_sqm} m²</span>
            </div>
            <div>
              <span className="text-slate-400 block">Area Discrepancy:</span>
              <span className="font-mono text-sm font-semibold text-amber-400">+{conflict.discrepancy_sqm} m²</span>
            </div>
          </div>

          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
            <h4 className="font-medium text-slate-200 mb-2">Mandatory Administrator Action (Rule R4):</h4>
            <p className="text-[11px] text-slate-400">
              Per government land-record security guidelines, AI output cannot automatically overwrite recorded survey records.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-2">
          <button
            onClick={() => onResolve('accept_ai')}
            className="px-3 py-2 bg-blue-700 hover:bg-blue-600 text-white rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-1"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Accept AI Version</span>
          </button>

          <button
            onClick={() => onResolve('retain_existing')}
            className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-1"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Retain Existing</span>
          </button>

          <button
            onClick={() => onResolve('escalate')}
            className="px-3 py-2 bg-amber-900/80 hover:bg-amber-800 text-amber-200 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-1"
          >
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>Escalate Field</span>
          </button>
        </div>

      </div>
    </div>
  );
}
