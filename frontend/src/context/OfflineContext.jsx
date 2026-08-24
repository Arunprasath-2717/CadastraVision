import React, { createContext, useContext, useState, useEffect } from 'react';
import { getPendingCount, enqueueOfflineAction, syncOfflineQueue } from '../lib/offlineQueue';

const OfflineContext = createContext(null);

export function OfflineProvider({ children }) {
  const [status, setStatus] = useState({
    state: navigator.onLine ? 'online' : 'offline',
    pendingCount: 0,
    lastSyncedAt: new Date().toLocaleTimeString()
  });

  const refreshPendingCount = async () => {
    const count = await getPendingCount();
    setStatus(prev => ({ ...prev, pendingCount: count }));
  };

  useEffect(() => {
    refreshPendingCount();

    const handleOnline = () => {
      setStatus(prev => ({ ...prev, state: 'online' }));
      triggerSyncSim();
    };
    const handleOffline = () => {
      setStatus(prev => ({ ...prev, state: 'offline' }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const queueAction = async (action) => {
    await enqueueOfflineAction(action);
    await refreshPendingCount();
  };

  const triggerSyncSim = async () => {
    setStatus(prev => ({ ...prev, state: 'syncing' }));
    try {
      await syncOfflineQueue();
      setStatus(prev => ({
        ...prev,
        state: 'online',
        pendingCount: 0,
        lastSyncedAt: new Date().toLocaleTimeString()
      }));
    } catch (e) {
      setStatus(prev => ({ ...prev, state: 'sync_conflict' }));
    }
  };

  return (
    <OfflineContext.Provider value={{ status, setStatus, queueAction, triggerSyncSim }}>
      {children}
    </OfflineContext.Provider>
  );
}

export function useOffline() {
  const context = useContext(OfflineContext);
  if (!context) {
    throw new Error('useOffline must be used within an OfflineProvider');
  }
  return context;
}
