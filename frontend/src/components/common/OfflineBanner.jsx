import React from 'react';
import { useOffline } from '../../context/OfflineContext';
import { Wifi, WifiOff, RefreshCw, AlertTriangle } from 'lucide-react';

export function OfflineBanner() {
  const { status, triggerSyncSim } = useOffline();

  if (status.state === 'online' && status.pendingCount === 0) {
    return (
      <div className="cv-status-pill cv-status-online" title="Connected to the CadastraVision services">
        <span className="cv-status-dot" aria-hidden="true" />
        <Wifi className="h-3.5 w-3.5" />
        <span>Online</span>
      </div>
    );
  }

  if (status.state === 'syncing') {
    return (
      <div className="cv-status-pill cv-status-syncing" title="Synchronizing offline actions">
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-pastel-action" />
        <span>Syncing Offline Actions...</span>
      </div>
    );
  }

  if (status.state === 'offline') {
    return (
      <div className="cv-status-pill cv-status-offline" title="The browser is offline">
        <span className="cv-status-dot" aria-hidden="true" />
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
      <div className="cv-status-pill cv-status-conflict" title="Offline actions need attention">
        <span className="cv-status-dot" aria-hidden="true" />
        <AlertTriangle className="w-3.5 h-3.5 text-rose-700" />
        <span>Sync Conflict Detected</span>
      </div>
    );
  }

  return null;
}
