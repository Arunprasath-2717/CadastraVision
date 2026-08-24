import { apiRequest } from './apiClient';
import mockParcels from '../mocks/parcels.json';
import mockBuildings from '../mocks/buildings.json';
import mockRoads from '../mocks/roads.json';

/**
 * GeoJSON & Vector Tile API Service (PRD-CM-04 Section 13 & Section 3.2)
 * Abstracted map data service returning GeoJSON FeatureCollections
 */
export const geoApi = {
  /**
   * Get GeoJSON FeatureCollection of parcels styled with confidence score & status metadata
   */
  async getParcelGeoJSON() {
    const res = await apiRequest('/v1/geo/parcels');
    if (res && res.type === 'FeatureCollection') return res;

    return mockParcels;
  },

  /**
   * Get Buildings GeoJSON
   */
  async getBuildingsGeoJSON() {
    const res = await apiRequest('/v1/geo/buildings');
    if (res && res.type === 'FeatureCollection') return res;

    return mockBuildings;
  },

  /**
   * Get Roads GeoJSON
   */
  async getRoadsGeoJSON() {
    const res = await apiRequest('/v1/geo/roads');
    if (res && res.type === 'FeatureCollection') return res;

    return mockRoads;
  }
};
