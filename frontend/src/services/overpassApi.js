/**
 * Overpass API Service — Fetch live OpenStreetMap vector features
 * (buildings, roads, landuse, boundaries) for visualization on MapLibre canvas.
 */

const OVERPASS_ENDPOINTS = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter'
];

/**
 * Convert raw Overpass JSON elements to a valid GeoJSON FeatureCollection
 */
function overpassToGeoJSON(elements) {
  const features = [];

  elements.forEach(elem => {
    if (elem.type === 'way' && elem.geometry && elem.geometry.length > 1) {
      const coords = elem.geometry.map(pt => [pt.lon, pt.lat]);
      const isClosed = coords.length > 3 &&
        coords[0][0] === coords[coords.length - 1][0] &&
        coords[0][1] === coords[coords.length - 1][1];

      features.push({
        type: 'Feature',
        id: `osm-${elem.type}-${elem.id}`,
        properties: {
          id: `osm-${elem.id}`,
          osm_type: elem.type,
          name: elem.tags?.name || 'OSM Feature',
          building: elem.tags?.building || null,
          highway: elem.tags?.highway || null,
          landuse: elem.tags?.landuse || null,
          source: 'OpenStreetMap (Overpass API)'
        },
        geometry: isClosed
          ? { type: 'Polygon', coordinates: [coords] }
          : { type: 'LineString', coordinates: coords }
      });
    }
  });

  return {
    type: 'FeatureCollection',
    features
  };
}

export const overpassApi = {
  /**
   * Fetch OSM features within a bounding box [minLng, minLat, maxLng, maxLat]
   */
  async fetchBBoxFeatures(bbox = [77.58, 12.96, 77.61, 12.98]) {
    const [minLng, minLat, maxLng, maxLat] = bbox;
    const query = `
      [out:json][timeout:15];
      (
        way["building"](${minLat},${minLng},${maxLat},${maxLng});
        way["highway"](${minLat},${minLng},${maxLat},${maxLng});
      );
      out geom;
    `;

    for (const endpoint of OVERPASS_ENDPOINTS) {
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: `data=${encodeURIComponent(query)}`
        });

        if (response.ok) {
          const data = await response.json();
          if (data.elements) {
            return overpassToGeoJSON(data.elements);
          }
        }
      } catch (err) {
        console.warn(`Overpass API endpoint ${endpoint} failed:`, err);
      }
    }

    return { type: 'FeatureCollection', features: [] };
  }
};
