import { apiRequest } from './apiClient';
import mockParcelsData from '../mocks/parcels.json';

// Local reactive mock memory state for demo editing / approval persistence
let localParcels = JSON.parse(JSON.stringify(mockParcelsData.features));

/**
 * Parcel Service (PRD-CM-04 Section 3.2 & Section 23)
 */
export const parcelApi = {
  /**
   * Get paginated parcel records
   */
  async getParcels(filters = {}) {
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
    const payload = {
      geometry: newGeometry,
      action_type: actionType,
      user_id: 'USR-4092',
      timestamp: new Date().toISOString()
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
  async approveParcel(parcelId, userId = 'USR-4092') {
    const payload = {
      approving_user_id: userId,
      timestamp: new Date().toISOString()
    };

    const res = await apiRequest(`/v1/parcels/${parcelId}/approve`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res) return res;

    const feature = localParcels.find(f => f.properties.id === parcelId || f.id === parcelId);
    if (feature) {
      feature.properties.validation_status = 'approved';
      feature.properties.flags = [];
    }

    return {
      success: true,
      parcel_id: parcelId,
      status: 'approved',
      export_eligible: true,
      approved_by: userId,
      approved_at: payload.timestamp
    };
  },

  /**
   * Explicit Human Rejection
   */
  async rejectParcel(parcelId, userId = 'USR-4092', reason = 'Boundary error') {
    const payload = {
      rejecting_user_id: userId,
      reason,
      timestamp: new Date().toISOString()
    };

    const res = await apiRequest(`/v1/parcels/${parcelId}/reject`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res) return res;

    const feature = localParcels.find(f => f.properties.id === parcelId || f.id === parcelId);
    if (feature) {
      feature.properties.validation_status = 'rejected';
    }

    return {
      success: true,
      parcel_id: parcelId,
      status: 'rejected',
      export_eligible: false,
      rejected_by: userId,
      rejected_at: payload.timestamp
    };
  }
};
