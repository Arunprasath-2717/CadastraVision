import React, { useState } from 'react';
import { useMapSelection } from '../../context/MapContext';
import { ConfidenceBadge, StatusBadge } from '../common/Badge';
import { GISConflictModal } from './GISConflictModal';
import {
  X, Edit3, CheckCircle, Ban, Building2, Calendar, User,
  AlertTriangle, ShieldCheck, FileCheck, Layers
} from 'lucide-react';

export function ParcelInspector() {
  const {
    selectedParcel,
    selectParcel,
    startEditing,
    approveCurrentParcel,
    rejectCurrentParcel,
    gisConflict,
    setGisConflict
  } = useMapSelection();

  const [showApproveConfirm, setShowApproveConfirm] = useState(false);
  const [showRejectConfirm, setShowRejectConfirm] = useState(false);
  const [rejectReason, setRejectReason] = useState('Boundary discrepancy');

  if (!selectedParcel) {
    return (
      <div className="bg-white/95 backdrop-blur-md p-6 rounded-2xl border border-pastel-border shadow-pastel-md text-center text-pastel-muted text-xs flex flex-col items-center justify-center h-full space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-pastel-lavender flex items-center justify-center text-pastel-action shadow-pastel-sm animate-bounce">
          <Layers className="w-6 h-6" />
        </div>
        <div>
          <p className="font-bold text-sm text-pastel-text font-display uppercase tracking-wider">NO PARCEL SELECTED</p>
          <p className="mt-1 text-xs text-pastel-muted max-w-xs mx-auto leading-relaxed">
            Select a parcel on the map or choose an item from the Review Queue to inspect cadastral details.
          </p>
        </div>
        <button
          onClick={() => selectParcel('P-1024', true)}
          className="mt-2 px-3.5 py-2 bg-pastel-lavender hover:bg-pastel-action hover:text-white text-pastel-action font-semibold text-xs rounded-xl border border-pastel-border shadow-pastel-sm transition-all duration-200 flex items-center space-x-1.5"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Inspect Sample P-1024</span>
        </button>
      </div>
    );
  }

  const handleApprove = async () => {
    await approveCurrentParcel();
    setShowApproveConfirm(false);
  };

  const handleReject = async () => {
    await rejectCurrentParcel(rejectReason);
    setShowRejectConfirm(false);
  };

  return (
    <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-pastel-border shadow-pastel-md text-pastel-text p-5 flex flex-col h-full overflow-y-auto space-y-4">
      
      {/* Header Bar */}
      <div className="flex items-start justify-between border-b border-pastel-border pb-3">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-bold font-mono text-pastel-text">{selectedParcel.id}</h3>
            <StatusBadge status={selectedParcel.validation_status} />
          </div>
          <p className="text-xs text-pastel-muted mt-0.5">{selectedParcel.jurisdiction} • {selectedParcel.zone}</p>
        </div>
        <button
          onClick={() => selectParcel(null)}
          className="text-pastel-subtle hover:text-pastel-text p-1 rounded-xl hover:bg-pastel-surface-soft transition-colors"
          title="Close Inspector"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Existing GIS Conflict Banner (Rule R4) */}
      {gisConflict && (
        <div className="p-3.5 bg-pastel-amber/40 border border-amber-300 rounded-xl text-xs space-y-2">
          <div className="flex items-center justify-between text-pastel-amber-text font-semibold">
            <div className="flex items-center space-x-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-700" />
              <span>Existing GIS Discrepancy</span>
            </div>
            <button
              onClick={() => setGisConflict(gisConflict)}
              className="text-[11px] underline hover:text-amber-900"
            >
              Review Action
            </button>
          </div>
          <p className="text-pastel-text">{gisConflict.description}</p>
        </div>
      )}

      {/* Confidence & Source Metrics */}
      <div className="space-y-2.5 p-3.5 bg-pastel-surface-soft rounded-xl border border-pastel-border text-xs">
        <div className="flex items-center justify-between">
          <span className="text-pastel-muted">AI Confidence:</span>
          <ConfidenceBadge band={selectedParcel.confidence_band} score={selectedParcel.confidence_score} />
        </div>

        <div className="flex items-center justify-between">
          <span className="text-pastel-muted">Feature Source:</span>
          <span className="font-mono text-pastel-text font-medium">{selectedParcel.source}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-pastel-muted">Calculated Area:</span>
          <span className="font-mono text-pastel-text font-semibold">{selectedParcel.area_sqm} m²</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-pastel-muted">Linked Buildings:</span>
          <span className="font-mono text-pastel-text flex items-center space-x-1 font-medium">
            <Building2 className="w-3.5 h-3.5 text-pastel-action" />
            <span>{selectedParcel.linked_buildings?.length || 0} Structures</span>
          </span>
        </div>
      </div>

      {/* Validation Flags List */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-pastel-muted flex items-center space-x-1.5">
          <ShieldCheck className="w-4 h-4 text-pastel-action" />
          <span>Validation Flags ({selectedParcel.flags?.length || 0})</span>
        </h4>

        {(!selectedParcel.flags || selectedParcel.flags.length === 0) ? (
          <div className="p-3 bg-pastel-mint/30 border border-emerald-200 rounded-xl text-pastel-mint-text text-xs flex items-center space-x-2">
            <FileCheck className="w-4 h-4 text-emerald-700 shrink-0" />
            <span>No topology errors or validation flags detected.</span>
          </div>
        ) : (
          <div className="space-y-2">
            {selectedParcel.flags.map(flag => (
              <div key={flag.id} className="p-3 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-700 uppercase tracking-wider text-[10px]">
                    {flag.flag_type}
                  </span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase font-semibold ${
                    flag.severity === 'high' ? 'bg-pastel-rose/50 text-pastel-rose-text border border-rose-300' : 'bg-pastel-amber/50 text-pastel-amber-text border border-amber-300'
                  }`}>
                    {flag.severity}
                  </span>
                </div>
                <p className="text-pastel-text">{flag.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Metadata Audit Info */}
      <div className="text-[11px] text-pastel-muted space-y-1 pt-2 border-t border-pastel-border font-mono">
        <div className="flex items-center space-x-1">
          <Calendar className="w-3 h-3 text-pastel-subtle" />
          <span>Updated: {new Date(selectedParcel.last_updated).toLocaleString()}</span>
        </div>
        <div className="flex items-center space-x-1">
          <User className="w-3 h-3 text-pastel-subtle" />
          <span>Actor: {selectedParcel.updated_by || 'System'}</span>
        </div>
      </div>

      {/* Workflow Action Buttons */}
      <div className="pt-2 border-t border-pastel-border space-y-2">
        <button
          onClick={startEditing}
          className="w-full py-2.5 bg-pastel-lavender hover:bg-slate-200/60 text-pastel-action rounded-xl text-xs font-semibold transition-all flex items-center justify-center space-x-2 border border-pastel-border shadow-pastel-sm"
        >
          <Edit3 className="w-4 h-4 text-pastel-action" />
          <span>Edit Boundary Vertices</span>
        </button>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => setShowApproveConfirm(true)}
            disabled={selectedParcel.validation_status === 'approved'}
            className="py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 shadow-pastel-sm"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Approve</span>
          </button>

          <button
            onClick={() => setShowRejectConfirm(true)}
            disabled={selectedParcel.validation_status === 'rejected'}
            className="py-2.5 bg-rose-600 hover:bg-rose-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 shadow-pastel-sm"
          >
            <Ban className="w-4 h-4" />
            <span>Reject</span>
          </button>
        </div>
      </div>

      {/* Confirmation Modals */}
      {showApproveConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white p-6 rounded-2xl border border-pastel-border shadow-pastel-lg text-pastel-text">
            <h4 className="text-base font-bold text-pastel-text mb-2">Approve Parcel {selectedParcel.id}?</h4>
            <p className="text-xs text-pastel-muted leading-relaxed">
              Once approved by staff, this parcel feature becomes official GIS export-eligible.
            </p>
            <div className="mt-6 flex justify-end space-x-3 text-xs font-medium">
              <button
                onClick={() => setShowApproveConfirm(false)}
                className="px-4 py-2 bg-pastel-surface-soft hover:bg-slate-200 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-xl text-white font-semibold shadow-pastel-sm"
              >
                Confirm Approval
              </button>
            </div>
          </div>
        </div>
      )}

      {showRejectConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white p-6 rounded-2xl border border-pastel-border shadow-pastel-lg text-pastel-text">
            <h4 className="text-base font-bold text-pastel-text mb-2">Reject Parcel {selectedParcel.id}?</h4>
            <p className="text-xs text-pastel-muted leading-relaxed mb-3">
              Rejected features remain available for audit and field re-survey.
            </p>
            <label className="block text-xs font-medium text-pastel-muted mb-1">Rejection Reason:</label>
            <input
              type="text"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full px-3 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text mb-4"
            />
            <div className="flex justify-end space-x-3 text-xs font-medium">
              <button
                onClick={() => setShowRejectConfirm(false)}
                className="px-4 py-2 bg-pastel-surface-soft hover:bg-slate-200 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 rounded-xl text-white font-semibold shadow-pastel-sm"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      <GISConflictModal
        conflict={gisConflict}
        onClose={() => setGisConflict(null)}
        onResolve={() => setGisConflict(null)}
      />

    </div>
  );
}
