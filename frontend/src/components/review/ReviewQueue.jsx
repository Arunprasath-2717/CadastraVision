import React, { useState, useEffect } from 'react';
import { useMapSelection } from '../../context/MapContext';
import { validationApi } from '../../services/validationApi';
import { ConfidenceBadge, StatusBadge } from '../common/Badge';
import { Filter, SortAsc, RefreshCw, AlertCircle, Eye, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';

export function ReviewQueue() {
  const { selectedParcelId, selectParcel, isReviewQueueOpen, setIsReviewQueueOpen } = useMapSelection();

  const [queueItems, setQueueItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [filters, setFilters] = useState({
    feature_type: 'ALL',
    flag_type: 'ALL',
    jurisdiction: 'ALL',
    sortBy: 'confidence_asc',
  });

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await validationApi.getReviewQueue(filters);
      setQueueItems(data);
    } catch (err) {
      setError('Unable to load review queue items.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [filters]);

  if (!isReviewQueueOpen) {
    return (
      <div className="bg-white/95 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-pastel-border shadow-pastel-sm flex items-center justify-between text-xs text-pastel-text">
        <div className="flex items-center space-x-2 font-semibold">
          <ShieldAlert className="w-4 h-4 text-amber-600" />
          <span>Review Queue ({queueItems.length} Flagged Features)</span>
        </div>
        <button
          onClick={() => setIsReviewQueueOpen(true)}
          className="px-3 py-1 bg-pastel-lavender hover:bg-slate-200/60 rounded-xl text-pastel-action font-semibold flex items-center space-x-1 border border-pastel-border shadow-pastel-sm"
        >
          <span>Expand Queue</span>
          <ChevronUp className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-pastel-border shadow-pastel-md text-pastel-text p-4 space-y-3 flex flex-col h-full">
      
      {/* Header & Filter Controls Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-pastel-border pb-3">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-5 h-5 text-amber-600" />
          <h3 className="text-sm font-bold tracking-wider text-pastel-text uppercase font-display">
            Surveyor Review Queue
          </h3>
          <span className="px-2.5 py-0.5 rounded-full bg-pastel-amber/40 border border-amber-300 text-pastel-amber-text text-xs font-mono font-bold">
            {queueItems.length}
          </span>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center space-x-1.5 bg-pastel-surface-soft px-3 py-1.5 rounded-xl border border-pastel-border">
            <Filter className="w-3.5 h-3.5 text-pastel-subtle" />
            <select
              value={filters.flag_type}
              onChange={(e) => setFilters({ ...filters, flag_type: e.target.value })}
              className="bg-transparent text-pastel-text focus:outline-none font-medium"
            >
              <option value="ALL">All Issues</option>
              <option value="overlap">Overlap</option>
              <option value="gap">Gap</option>
              <option value="self_intersection">Self-Intersection</option>
              <option value="low_confidence">Low Confidence</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 bg-pastel-surface-soft px-3 py-1.5 rounded-xl border border-pastel-border">
            <SortAsc className="w-3.5 h-3.5 text-pastel-subtle" />
            <select
              value={filters.sortBy}
              onChange={(e) => setFilters({ ...filters, sortBy: e.target.value })}
              className="bg-transparent text-pastel-text focus:outline-none font-medium"
            >
              <option value="confidence_asc">Sort: Confidence (Low &rarr; High)</option>
              <option value="date_desc">Sort: Newest First</option>
            </select>
          </div>

          <button
            onClick={fetchQueue}
            className="p-2 bg-pastel-surface-soft hover:bg-slate-200/60 rounded-xl border border-pastel-border text-pastel-muted hover:text-pastel-text shadow-pastel-sm"
            title="Refresh Queue"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => setIsReviewQueueOpen(false)}
            className="p-2 bg-pastel-surface-soft hover:bg-slate-200/60 rounded-xl border border-pastel-border text-pastel-muted hover:text-pastel-text ml-2 shadow-pastel-sm"
            title="Collapse Queue"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 overflow-x-auto overflow-y-auto max-h-[220px]">
        {loading ? (
          <div className="py-8 text-center text-xs text-pastel-muted flex items-center justify-center space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-pastel-action" />
            <span>Loading validation review queue...</span>
          </div>
        ) : error ? (
          <div className="py-6 text-center text-xs text-rose-700 flex items-center justify-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            <span>{error}</span>
          </div>
        ) : queueItems.length === 0 ? (
          <div className="py-8 text-center text-xs text-pastel-muted">
            No flagged parcels match your filters. All boundaries in this sector meet validation standards.
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-pastel-border text-pastel-muted font-mono uppercase tracking-wider">
                <th className="py-2.5 px-3">Parcel ID</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Detected Issue / Flag</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-pastel-border/60 font-sans">
              {queueItems.map(item => {
                const isSelected = selectedParcelId === item.parcel_id;
                return (
                  <tr
                    key={item.id}
                    onClick={() => selectParcel(item.parcel_id, true)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-pastel-lavender/70 border-l-4 border-l-pastel-action font-semibold'
                        : 'hover:bg-pastel-surface-soft'
                    }`}
                  >
                    <td className="py-2.5 px-3 font-mono font-bold text-pastel-text flex items-center space-x-1.5">
                      <span>{item.parcel_id}</span>
                      {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-pastel-action animate-ping" />}
                    </td>
                    <td className="py-2.5 px-3">
                      <ConfidenceBadge band={item.confidence_band} score={item.confidence_score} />
                    </td>
                    <td className="py-2.5 px-3 text-pastel-text font-medium">
                      {item.issue}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded-full font-mono uppercase text-[10px] font-semibold ${
                        item.severity === 'high' ? 'bg-pastel-rose/40 text-pastel-rose-text border border-rose-300' : 'bg-pastel-amber/40 text-pastel-amber-text border border-amber-300'
                      }`}>
                        {item.severity}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          selectParcel(item.parcel_id, true);
                        }}
                        className="px-3 py-1 bg-pastel-action hover:bg-pastel-action-hover text-white rounded-lg text-[11px] font-semibold transition-all inline-flex items-center space-x-1 shadow-pastel-sm"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

    </div>
  );
}
