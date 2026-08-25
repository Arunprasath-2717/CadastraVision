import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMapSelection } from '../context/MapContext';
import { ConfidenceBadge, StatusBadge } from '../components/common/Badge';
import { GlowingButton } from '../components/common/GlowingButton';
import { 
  CheckSquare, 
  Filter, 
  ShieldCheck, 
  CheckCircle, 
  Ban, 
  Edit3, 
  MapPin, 
  AlertTriangle, 
  Building2, 
  Calendar, 
  User, 
  Layers, 
  FileCheck,
  Search,
  RefreshCw,
  Clock
} from 'lucide-react';

import reviewQueueData from '../mocks/reviewQueue.json';

export function ReviewValidationPage() {
  const navigate = useNavigate();
  const { selectParcel, startEditing } = useMapSelection();

  const [queueItems, setQueueItems] = useState(reviewQueueData.items || []);
  const [selectedQueueItem, setSelectedQueueItem] = useState(reviewQueueData.items?.[0] || null);
  const [filterRisk, setFilterRisk] = useState('ALL'); // ALL | HIGH | MEDIUM | LOW
  const [searchQuery, setSearchQuery] = useState('');
  const [reviewActionSuccess, setReviewActionSuccess] = useState(null);

  const filteredItems = queueItems.filter(item => {
    if (filterRisk === 'HIGH' && item.confidence_band !== 'LOW') return false; // low confidence = high risk
    if (filterRisk === 'MEDIUM' && item.confidence_band !== 'MEDIUM') return false;
    if (filterRisk === 'LOW' && item.confidence_band !== 'HIGH') return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        item.parcel_id.toLowerCase().includes(q) ||
        item.flag_type.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleApprove = (parcelId) => {
    setQueueItems(prev => prev.filter(i => i.parcel_id !== parcelId));
    setReviewActionSuccess(`Parcel ${parcelId} approved successfully.`);
    setTimeout(() => setReviewActionSuccess(null), 3000);
    if (selectedQueueItem?.parcel_id === parcelId) {
      setSelectedQueueItem(queueItems.find(i => i.parcel_id !== parcelId) || null);
    }
  };

  const handleReject = (parcelId) => {
    setQueueItems(prev => prev.filter(i => i.parcel_id !== parcelId));
    setReviewActionSuccess(`Parcel ${parcelId} rejected.`);
    setTimeout(() => setReviewActionSuccess(null), 3000);
    if (selectedQueueItem?.parcel_id === parcelId) {
      setSelectedQueueItem(queueItems.find(i => i.parcel_id !== parcelId) || null);
    }
  };

  const handleInspectOnMap = (parcelId) => {
    selectParcel(parcelId, true);
    navigate('/dashboard');
  };

  return (
    <div className="h-full w-full p-4 lg:p-6 overflow-hidden bg-pastel-bg flex flex-col space-y-4">
      
      {/* Header Bar */}
      <div className="bg-white p-4 lg:p-5 rounded-2xl border border-pastel-border shadow-pastel-sm flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-emerald-100 text-emerald-800">
              <CheckSquare className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base lg:text-lg font-bold font-display text-pastel-text">
                SURVEYOR REVIEW & VALIDATION QUEUE
              </h1>
              <p className="text-xs text-pastel-muted font-mono">
                Cadastral verification workflow • Dual human-in-the-loop validation
              </p>
            </div>
          </div>
        </div>

        {/* Stats Pills */}
        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-xl bg-pastel-surface-soft border border-pastel-border text-pastel-text">
            <span className="text-pastel-muted">Total Pending:</span>{' '}
            <span className="font-bold text-pastel-action">{queueItems.length}</span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800">
            <span className="text-rose-700">High Risk:</span>{' '}
            <span className="font-bold">
              {queueItems.filter(i => i.confidence_band === 'LOW').length}
            </span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800">
            <span className="text-emerald-700">Reviewed Today:</span>{' '}
            <span className="font-bold">18</span>
          </div>
        </div>
      </div>

      {/* Success Notification Alert */}
      {reviewActionSuccess && (
        <div className="p-3 bg-emerald-100 border border-emerald-300 text-emerald-900 text-xs rounded-xl flex items-center justify-between font-medium shadow-pastel-sm animate-fade-in shrink-0">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-emerald-700" />
            <span>{reviewActionSuccess}</span>
          </div>
        </div>
      )}

      {/* Main Split View: Left Queue List (5 cols) & Right Parcel Inspection Detail (7 cols) */}
      <div className="flex-1 grid grid-cols-12 gap-4 overflow-hidden">
        
        {/* Left Review Queue Column (5 cols) */}
        <div className="col-span-12 lg:col-span-5 bg-white rounded-2xl border border-pastel-border shadow-pastel-sm p-4 flex flex-col space-y-3 overflow-hidden">
          
          {/* Controls: Filter & Search */}
          <div className="space-y-2 shrink-0">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter by Parcel ID, discrepancy..."
                className="w-full pl-8 pr-3 py-1.5 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text placeholder-pastel-subtle"
              />
              <Search className="w-3.5 h-3.5 text-pastel-subtle absolute left-2.5 top-2.5" />
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="text-pastel-muted flex items-center space-x-1 font-mono text-[11px]">
                <Filter className="w-3 h-3 text-pastel-action" />
                <span>RISK LEVEL:</span>
              </span>
              <div className="flex space-x-1 font-mono text-[11px]">
                {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((risk) => (
                  <button
                    key={risk}
                    onClick={() => setFilterRisk(risk)}
                    className={`px-2.5 py-0.5 rounded-lg font-semibold transition-colors ${
                      filterRisk === risk
                        ? 'bg-pastel-action text-white'
                        : 'bg-pastel-surface-soft text-pastel-muted hover:bg-pastel-lavender'
                    }`}
                  >
                    {risk}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Queue List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {filteredItems.length === 0 ? (
              <div className="p-8 text-center text-pastel-muted text-xs font-mono space-y-2">
                <FileCheck className="w-8 h-8 mx-auto text-emerald-500" />
                <p className="font-semibold text-pastel-text">Queue Clear</p>
                <p>No pending review items matching the selected filters.</p>
              </div>
            ) : (
              filteredItems.map((item) => {
                const isSelected = selectedQueueItem?.parcel_id === item.parcel_id;
                return (
                  <div
                    key={item.parcel_id}
                    onClick={() => setSelectedQueueItem(item)}
                    className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all space-y-2 ${
                      isSelected
                        ? 'bg-pastel-lavender/90 border-pastel-action shadow-pastel-sm'
                        : 'bg-pastel-surface-soft hover:bg-white border-pastel-border'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold font-mono text-pastel-text text-sm">
                          {item.parcel_id}
                        </span>
                        <ConfidenceBadge band={item.confidence_band} score={item.confidence_score} />
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded uppercase font-mono font-bold ${
                        item.severity === 'high'
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : 'bg-amber-100 text-amber-800 border border-amber-200'
                      }`}>
                        {item.severity} Risk
                      </span>
                    </div>

                    <p className="text-pastel-text text-xs line-clamp-2 leading-relaxed">
                      {item.description}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-pastel-muted font-mono pt-1">
                      <span>Flag: {item.flag_type}</span>
                      <span className="text-pastel-action hover:underline font-semibold">
                        Click to Inspect →
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

        </div>

        {/* Right Parcel Inspection & Validation Panel (7 cols) */}
        <div className="col-span-12 lg:col-span-7 bg-white rounded-2xl border border-pastel-border shadow-pastel-sm p-6 flex flex-col justify-between overflow-y-auto space-y-6">
          
          {selectedQueueItem ? (
            <div className="space-y-6">
              
              {/* Header */}
              <div className="flex items-start justify-between border-b border-pastel-border pb-4">
                <div>
                  <div className="flex items-center space-x-3">
                    <h2 className="text-xl font-bold font-mono text-pastel-text">
                      {selectedQueueItem.parcel_id}
                    </h2>
                    <StatusBadge status="needs_review" />
                  </div>
                  <p className="text-xs text-pastel-muted mt-1 font-mono">
                    Bengaluru East • Sector 4 • Zone B
                  </p>
                </div>

                <GlowingButton
                  variant="primary-glow"
                  size="sm"
                  icon={MapPin}
                  onClick={() => handleInspectOnMap(selectedQueueItem.parcel_id)}
                >
                  View on Map
                </GlowingButton>
              </div>

              {/* Discrepancy Card */}
              <div className="p-4 bg-rose-50/70 border border-rose-200 rounded-2xl text-xs space-y-2">
                <div className="flex items-center justify-between text-rose-900 font-bold font-mono">
                  <div className="flex items-center space-x-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-700" />
                    <span className="uppercase tracking-wider">CADASTRAL DISCREPANCY DETECTED</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 uppercase font-mono text-[10px]">
                    {selectedQueueItem.flag_type}
                  </span>
                </div>
                <p className="text-slate-800 text-xs leading-relaxed">
                  {selectedQueueItem.description}
                </p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-pastel-surface-soft rounded-xl border border-pastel-border text-xs">
                  <span className="text-pastel-muted text-[10px] uppercase font-mono block">AI CONFIDENCE</span>
                  <span className="text-lg font-bold font-mono text-pastel-text">
                    {(selectedQueueItem.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="p-3 bg-pastel-surface-soft rounded-xl border border-pastel-border text-xs">
                  <span className="text-pastel-muted text-[10px] uppercase font-mono block">SEVERITY LEVEL</span>
                  <span className="text-lg font-bold font-mono uppercase text-amber-700">
                    {selectedQueueItem.severity}
                  </span>
                </div>

                <div className="p-3 bg-pastel-surface-soft rounded-xl border border-pastel-border text-xs">
                  <span className="text-pastel-muted text-[10px] uppercase font-mono block">CALCULATED AREA</span>
                  <span className="text-lg font-bold font-mono text-pastel-text">1,240 m²</span>
                </div>
              </div>

              {/* Boundary Topology Check Details */}
              <div className="space-y-3 p-4 bg-pastel-surface-soft rounded-2xl border border-pastel-border text-xs">
                <h4 className="font-bold text-xs uppercase tracking-wider text-pastel-text font-mono flex items-center space-x-1.5">
                  <ShieldCheck className="w-4 h-4 text-pastel-action" />
                  <span>TOPOLOGICAL INTEGRITY ANALYSIS</span>
                </h4>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center p-2 bg-white rounded-lg border border-pastel-border">
                    <span className="text-pastel-muted">Overlaps with adjacent parcels:</span>
                    <span className="font-mono font-bold text-rose-700">YES (1.8m East)</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-white rounded-lg border border-pastel-border">
                    <span className="text-pastel-muted">Unmapped Spatial Gap:</span>
                    <span className="font-mono font-bold text-emerald-700">NO</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-white rounded-lg border border-pastel-border">
                    <span className="text-pastel-muted">Self-Intersection check:</span>
                    <span className="font-mono font-bold text-emerald-700">PASSED</span>
                  </div>
                </div>
              </div>

              {/* Review Workflow Controls */}
              <div className="pt-4 border-t border-pastel-border space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold font-mono text-pastel-muted uppercase">SURVEYOR ACTION</span>
                  <span className="text-[11px] text-pastel-subtle font-mono">Logged to Audit Trail</span>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <button
                    onClick={() => handleApprove(selectedQueueItem.parcel_id)}
                    className="py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 shadow-pastel-sm"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Approve Parcel</span>
                  </button>

                  <button
                    onClick={() => {
                      selectParcel(selectedQueueItem.parcel_id, true);
                      startEditing();
                      navigate('/dashboard');
                    }}
                    className="py-3 bg-pastel-lavender hover:bg-slate-200 text-pastel-action border border-pastel-border rounded-xl text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 shadow-pastel-sm"
                  >
                    <Edit3 className="w-4 h-4" />
                    <span>Edit Vertices</span>
                  </button>

                  <button
                    onClick={() => handleReject(selectedQueueItem.parcel_id)}
                    className="py-3 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 shadow-pastel-sm"
                  >
                    <Ban className="w-4 h-4" />
                    <span>Reject Parcel</span>
                  </button>
                </div>
              </div>

            </div>
          ) : (
            <div className="p-12 text-center text-pastel-muted text-xs space-y-2 my-auto">
              <Layers className="w-10 h-10 mx-auto text-pastel-subtle" />
              <p className="font-semibold text-pastel-text">No Queue Item Selected</p>
              <p>Choose an item from the left queue list to inspect cadastral details.</p>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
