import React from 'react';
import { useOffline } from '../../context/OfflineContext';
import { Wifi, WifiOff, RefreshCw, AlertTriangle } from 'lucide-react';

/**
 * Pastel Offline Status Banner (PRD-CM-04 Section 25 & Ragul's PWA module)
 */
export function OfflineBanner() {
  const { status, triggerSyncSim } = useOffline();

  if (status.state === 'online' && status.pendingCount === 0) {
    return (
      <div className="flex items-center space-x-1.5 text-xs text-pastel-mint-text font-medium px-2.5 py-1 bg-pastel-mint/30 border border-emerald-200 rounded-full">
        <Wifi className="w-3.5 h-3.5 text-emerald-700" />
        <span>Online</span>
      </div>
    );
  }

  if (status.state === 'syncing') {
    return (
      <div className="flex items-center space-x-1.5 text-xs text-pastel-action font-medium px-2.5 py-1 bg-blue-50 border border-blue-200 rounded-full animate-pulse">
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-pastel-action" />
        <span>Syncing Offline Actions...</span>
      </div>
    );
  }

  if (status.state === 'offline') {
    return (
      <div className="flex items-center space-x-2 text-xs text-pastel-amber-text font-medium px-2.5 py-1 bg-pastel-amber/40 border border-amber-200 rounded-full">
        <WifiOff className="w-3.5 h-3.5 text-amber-700" />
        <span>Offline Mode ({status.pendingCount} pending)</span>
        <button
          onClick={triggerSyncSim}
          className="ml-1 text-[11px] underline hover:text-amber-900"
        >
          Sync Now
        </button>
      </div>
    );
  }

  if (status.state === 'sync_conflict') {
    return (
      <div className="flex items-center space-x-1.5 text-xs text-pastel-rose-text font-medium px-2.5 py-1 bg-pastel-rose/40 border border-rose-200 rounded-full">
        <AlertTriangle className="w-3.5 h-3.5 text-rose-700" />
        <span>Sync Conflict Detected</span>
      </div>
    );
  }

  return null;
}
