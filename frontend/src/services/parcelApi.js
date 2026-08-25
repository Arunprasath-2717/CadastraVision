import { apiRequest } from './apiClient';
import mockParcelsData from '../mocks/parcels.json';
import { enqueueOfflineAction, getPendingActions } from '../lib/offlineQueue';

// Local reactive mock memory state for demo editing / approval persistence
let localParcels = JSON.parse(JSON.stringify(mockParcelsData.features));

let isMockRestored = false;
let restorePromise = null;

async function ensureMockStateRestored() {
  if (isMockRestored) return;
  if (!restorePromise) {
    restorePromise = (async () => {
      try {
        const pendingActions = await getPendingActions();
        for (const action of pendingActions) {
          parcelApi.applyMockAction(action);
        }
      } catch (err) {
        console.error('Failed to restore mock state from IndexedDB', err);
      } finally {
        isMockRestored = true;
      }
    })();
  }
  return restorePromise;
}

/**
 * Parcel Service (PRD-CM-04 Section 3.2 & Section 23)
 */
export const parcelApi = {
  /**
   * Get paginated parcel records
   */
  async getParcels(filters = {}) {
    await ensureMockStateRestored();
    const query = new URLSearchParams(filters).toString();
    const res = await apiRequest(`/v1/parcels?${query}`);
    if (res && res.items) return res;

    // Fallback to local mock data
    let items = localParcels.map(f => f.properties);
    if (filters.validation_status) {
      items = items.filter(p => p.validation_status === filters.validation_status);
    }
    if (filters.confidence_band) {
      items = items.filter(p => p.confidence_band === filters.confidence_band);
    }

    return {
      items,
      next_cursor: null,
      total: items.length
    };
  },

  /**
   * Get single parcel details
   */
  async getParcelById(parcelId) {
    await ensureMockStateRestored();
    const res = await apiRequest(`/v1/parcels/${parcelId}`);
    if (res) return res;

    const feature = localParcels.find(f => f.properties.id === parcelId || f.id === parcelId);
    if (feature) {
      return {
        ...feature.properties,
        geometry: feature.geometry
      };
    }
    return null;
  },

  /**
   * Submit vertex edit, split, or merge boundary modification
   * Triggers automatic server re-validation
   */
  async editParcel(parcelId, newGeometry, actionType = 'vertex_edit') {
    await ensureMockStateRestored();
    const payload = {
      idempotency_key: `edit-${parcelId}-${Date.now()}`,
      edit: {
        operation: actionType,
        payload: { geometry: newGeometry }
      },
      notes: `Applied ${actionType}`
    };

    const res = await apiRequest(`/v1/parcels/${parcelId}/edit`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res) return res;

    // Simulate Server Re-validation Response
    const featureIdx = localParcels.findIndex(f => f.properties.id === parcelId || f.id === parcelId);
    if (featureIdx !== -1) {
      localParcels[featureIdx].geometry = newGeometry;
      localParcels[featureIdx].properties.source = 'human-edited';
      localParcels[featureIdx].properties.confidence_score = 0.96;
      localParcels[featureIdx].properties.confidence_band = 'HIGH';
      localParcels[featureIdx].properties.last_updated = new Date().toISOString();
      localParcels[featureIdx].properties.updated_by = 'Muthulakshmi S. (Surveyor)';
      
      if (!navigator.onLine) {
        await enqueueOfflineAction({ type: actionType, parcel_id: parcelId, payload: { geometry: newGeometry } });
      }
    }

    return {
      success: true,
      parcel_id: parcelId,
      revalidation: {
        status: 'PASSED',
        overlap_detected: false,
        gap_detected: false,
        self_intersection: false,
        message: 'Geometry topology re-validated successfully. No self-intersections or overlaps found.',
        revalidated_at: new Date().toISOString()
      }
    };
  },

  /**
   * Explicit Human Approval (PRD Non-Negotiable R1)
   */
  async approveParcel(parcelId, notes = 'Boundary validated and approved') {
    await ensureMockStateRestored();
    const payload = { notes };

    const res = await apiRequest(`/v1/parcels/${parcelId}/approve`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res) return res;

    const feature = localParcels.find(f => f.properties.id === parcelId || f.id === parcelId);
    if (feature) {
      feature.properties.validation_status = 'approved';
      feature.properties.flags = [];
      
      if (!navigator.onLine) {
        await enqueueOfflineAction({ type: 'approve', parcel_id: parcelId, payload: { notes } });
      }
    }

    return {
      success: true,
      parcel_id: parcelId,
      status: 'approved',
      export_eligible: true,
      approved_at: new Date().toISOString()
    };
  },

  /**
   * Explicit Human Rejection
   */
  async rejectParcel(parcelId, reason = 'Boundary error') {
    await ensureMockStateRestored();
    const payload = { reason };

    const res = await apiRequest(`/v1/parcels/${parcelId}/reject`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res) return res;

    const feature = localParcels.find(f => f.properties.id === parcelId || f.id === parcelId);
    if (feature) {
      feature.properties.validation_status = 'rejected';
      
      if (!navigator.onLine) {
        await enqueueOfflineAction({ type: 'reject', parcel_id: parcelId, payload: { reason } });
      }
    }

    return {
      success: true,
      parcel_id: parcelId,
      status: 'rejected',
      export_eligible: false,
      rejected_at: new Date().toISOString()
    };
  },

  /**
   * Apply queued mock actions to the local state when coming online
   */
  applyMockAction(action) {
    const featureIdx = localParcels.findIndex(f => f.properties.id === action.parcel_id || f.id === action.parcel_id);
    if (featureIdx === -1) return false;
    
    if (action.action_type === 'approve') {
      localParcels[featureIdx].properties.validation_status = 'approved';
      localParcels[featureIdx].properties.flags = [];
    } else if (action.action_type === 'reject') {
      localParcels[featureIdx].properties.validation_status = 'rejected';
    } else {
      // assume edit
      localParcels[featureIdx].geometry = action.payload.geometry || localParcels[featureIdx].geometry;
      localParcels[featureIdx].properties.source = 'human-edited';
      localParcels[featureIdx].properties.confidence_score = 0.96;
      localParcels[featureIdx].properties.confidence_band = 'HIGH';
      localParcels[featureIdx].properties.last_updated = action.timestamp || new Date().toISOString();
      localParcels[featureIdx].properties.updated_by = 'Muthulakshmi S. (Surveyor)';
    }
    return true;
  }
};
