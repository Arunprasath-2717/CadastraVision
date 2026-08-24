import { apiRequest } from './apiClient';
import mockQueue from '../mocks/reviewQueue.json';
import mockFlags from '../mocks/flags.json';

let localQueue = [...mockQueue];

/**
 * Validation & Review Queue API Service (PRD-CM-04 Section 19 & Section 3.2)
 * Integration boundary for Arun's topology calculations and Shiva's validation endpoints.
 */
export const validationApi = {
  /**
   * Get Review Queue items below confidence threshold
   */
  async getReviewQueue(filters = {}) {
    const query = new URLSearchParams(filters).toString();
    const res = await apiRequest(`/v1/validations/queue?${query}`);
    if (res && Array.isArray(res)) return res;

    // Filter local queue
    let items = [...localQueue];
    if (filters.feature_type && filters.feature_type !== 'ALL') {
      items = items.filter(i => i.feature_type.toLowerCase().includes(filters.feature_type.toLowerCase()));
    }
    if (filters.flag_type && filters.flag_type !== 'ALL') {
      items = items.filter(i => i.issue.toLowerCase().includes(filters.flag_type.toLowerCase()));
    }
    if (filters.jurisdiction && filters.jurisdiction !== 'ALL') {
      items = items.filter(i => i.jurisdiction === filters.jurisdiction);
    }
    if (filters.sortBy === 'confidence_asc') {
      items.sort((a, b) => a.confidence_score - b.confidence_score);
    }

    return items;
  },

  /**
   * Get Validation Flags on a specific parcel
   */
  async getParcelFlags(parcelId) {
    const res = await apiRequest(`/v1/parcels/${parcelId}/flags`);
    if (res && Array.isArray(res)) return res;

    return mockFlags[parcelId] || [];
  },

  /**
   * Remove item from queue upon review resolution
   */
  removeFromQueue(parcelId) {
    localQueue = localQueue.filter(q => q.parcel_id !== parcelId);
  }
};
