/**
 * Official Offline Action Queue & Reconnect Sync Boundary (FR-019, SRS §3.1 & Architecture Skeleton)
 * Provides IndexedDB-backed action queueing for field surveyors working in low-connectivity zones.
 * Integration point for Ragul (Frontend Developer — Offline/PWA).
 */

const DB_NAME = 'cadastralmap_offline_db';
const DB_VERSION = 1;
const STORE_NAME = 'pending_actions';

/**
 * Open or initialize IndexedDB database
 * @returns {Promise<IDBDatabase>}
 */
function openDB() {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      console.warn('IndexedDB not supported in environment.');
      resolve(null);
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'client_action_id' });
      }
    };

    request.onsuccess = (event) => {
      resolve(event.target.result);
    };

    request.onerror = (event) => {
      console.error('IndexedDB open error:', event.target.error);
      reject(event.target.error);
    };
  });
}

/**
 * Enqueue an offline action (Edit, Approve, Reject) with idempotent client_action_id
 * @param {Object} action - { type: 'edit'|'approve'|'reject', parcel_id, payload, timestamp }
 */
export async function enqueueOfflineAction(action) {
  const db = await openDB();
  if (!db) return null;

  const client_action_id = `ACT-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
  const record = {
    client_action_id,
    parcel_id: action.parcel_id,
    action_type: action.type,
    payload: action.payload || {},
    timestamp: action.timestamp || new Date().toISOString(),
    status: 'pending'
  };

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.add(record);

    req.onsuccess = () => {
      window.dispatchEvent(new Event('offlineActionEnqueued'));
      resolve(record);
    };
    req.onerror = (e) => reject(e.target.error);
  });
}

/**
 * Get count of queued pending offline actions
 * @returns {Promise<number>}
 */
export async function getPendingCount() {
  const db = await openDB();
  if (!db) return 0;

  return new Promise((resolve) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req = store.count();

    req.onsuccess = () => resolve(req.result || 0);
    req.onerror = () => resolve(0);
  });
}

/**
 * Get all queued pending offline actions
 * @returns {Promise<Array>}
 */
export async function getPendingActions() {
  const db = await openDB();
  if (!db) return [];

  return new Promise((resolve) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req = store.getAll();

    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => resolve([]);
  });
}

/**
 * Remove a specific queued offline action
 * @param {string} client_action_id
 */
export async function removeOfflineAction(client_action_id) {
  const db = await openDB();
  if (!db) return;

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.delete(client_action_id);

    req.onsuccess = () => resolve(true);
    req.onerror = (e) => reject(e.target.error);
  });
}

/**
 * Clear all pending actions after successful batch sync to /v1/parcels/sync
 */
export async function clearOfflineQueue() {
  const db = await openDB();
  if (!db) return;

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.clear();

    req.onsuccess = () => resolve(true);
    req.onerror = (e) => reject(e.target.error);
  });
}

/**
 * Flush and sync pending actions with backend /v1/parcels/sync endpoint
 */
export async function syncOfflineQueue(apiClient) {
  const actions = await getPendingActions();
  if (actions.length === 0) return { synced: 0, conflicts: 0 };

  try {
    if (apiClient && typeof apiClient.syncOfflineActions === 'function') {
      await apiClient.syncOfflineActions(actions);
      for (const action of actions) {
        await removeOfflineAction(action.client_action_id);
      }
    } else {
      const { parcelApi } = await import('../services/parcelApi.js');
      for (const action of actions) {
        try {
          parcelApi.applyMockAction(action);
          await removeOfflineAction(action.client_action_id);
        } catch (e) {
          console.error('Failed to apply mock action', e);
        }
      }
    }
    
    return { synced: actions.length, conflicts: 0 };
  } catch (err) {
    console.error('Offline batch sync error:', err);
    throw err;
  }
}
