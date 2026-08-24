import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { useMapSelection } from '../../context/MapContext';
import { geoApi } from '../../services/geoApi';
import { ZoomIn, ZoomOut, Compass, Loader2, Maximize2 } from 'lucide-react';

export function MapView() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const {
    activeLayers,
    selectedParcelId,
    selectParcel,
    setMapInstance
  } = useMapSelection();

  const [loading, setLoading] = useState(true);

  // Free OpenAccess Dark / Carto Vector style
  const basemapStyle = {
    version: 8,
    sources: {
      'carto-dark': {
        type: 'raster',
        tiles: [
          'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
          'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
          'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'
        ],
        tileSize: 256,
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap'
      }
    },
    layers: [
      {
        id: 'carto-dark-layer',
        type: 'raster',
        source: 'carto-dark',
        minzoom: 0,
        maxzoom: 20
      }
    ]
  };

  useEffect(() => {
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: basemapStyle,
      center: [77.5946, 12.9716],
      zoom: 16,
      pitch: 25,
      bearing: 0
    });

    mapRef.current = map;
    setMapInstance(map);

    map.on('load', async () => {
      const [parcelsGeoJSON, buildingsGeoJSON, roadsGeoJSON] = await Promise.all([
        geoApi.getParcelGeoJSON(),
        geoApi.getBuildingsGeoJSON(),
        geoApi.getRoadsGeoJSON()
      ]);

      map.addSource('parcels-source', { type: 'geojson', data: parcelsGeoJSON });
      map.addSource('buildings-source', { type: 'geojson', data: buildingsGeoJSON });
      map.addSource('roads-source', { type: 'geojson', data: roadsGeoJSON });

      // Add Roads Layer
      map.addLayer({
        id: 'roads-layer',
        type: 'line',
        source: 'roads-source',
        paint: {
          'line-color': '#38BDF8',
          'line-width': ['get', 'width_m'],
          'line-opacity': 0.75
        }
      });

      // Add Parcels Fill Layer (Pastel Confidence Band Colors)
      map.addLayer({
        id: 'parcels-fill-layer',
        type: 'fill',
        source: 'parcels-source',
        paint: {
          'fill-color': [
            'match',
            ['get', 'confidence_band'],
            'HIGH', 'rgba(16, 185, 129, 0.35)',
            'MEDIUM', 'rgba(245, 158, 11, 0.35)',
            'LOW', 'rgba(239, 68, 68, 0.35)',
            'rgba(88, 118, 201, 0.35)'
          ],
          'fill-outline-color': '#334155'
        }
      });

      // Add Parcels Line Layer
      map.addLayer({
        id: 'parcels-line-layer',
        type: 'line',
        source: 'parcels-source',
        paint: {
          'line-color': [
            'match',
            ['get', 'confidence_band'],
            'HIGH', '#10B981',
            'MEDIUM', '#F59E0B',
            'LOW', '#EF4444',
            '#5876C9'
          ],
          'line-width': 2
        }
      });

      // Selected Parcel Highlight Layer (Periwinkle Glow)
      map.addLayer({
        id: 'parcels-highlight-layer',
        type: 'line',
        source: 'parcels-source',
        filter: ['==', ['get', 'id'], ''],
        paint: {
          'line-color': '#8FA7E8',
          'line-width': 6,
          'line-blur': 1
        }
      });

      // Add Buildings Layer
      map.addLayer({
        id: 'buildings-layer',
        type: 'fill',
        source: 'buildings-source',
        paint: {
          'fill-color': '#94A3B8',
          'fill-opacity': 0.6,
          'fill-outline-color': '#CBD5E1'
        }
      });

      // Add Validation Flags Symbol/Circle Layer
      map.addLayer({
        id: 'validation-flags-layer',
        type: 'circle',
        source: 'parcels-source',
        filter: ['>', ['length', ['get', 'flags']], 0],
        paint: {
          'circle-color': '#EF4444',
          'circle-radius': 8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#FFFFFF'
        }
      });

      // Interactive Click Event
      map.on('click', 'parcels-fill-layer', (e) => {
        if (e.features && e.features.length > 0) {
          const parcelId = e.features[0].properties.id;
          selectParcel(parcelId, false);
        }
      });

      map.on('mouseenter', 'parcels-fill-layer', () => {
        map.getCanvas().style.cursor = 'pointer';
      });

      map.on('mouseleave', 'parcels-fill-layer', () => {
        map.getCanvas().style.cursor = '';
      });

      setLoading(false);
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [selectParcel, setMapInstance]);

  // Update Layer Visibility dynamically
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('parcels-fill-layer')) {
      map.setLayoutProperty('parcels-fill-layer', 'visibility', activeLayers.parcels ? 'visible' : 'none');
      map.setLayoutProperty('parcels-line-layer', 'visibility', activeLayers.parcels ? 'visible' : 'none');
    }
    if (map.getLayer('buildings-layer')) {
      map.setLayoutProperty('buildings-layer', 'visibility', activeLayers.buildings ? 'visible' : 'none');
    }
    if (map.getLayer('roads-layer')) {
      map.setLayoutProperty('roads-layer', 'visibility', activeLayers.roads ? 'visible' : 'none');
    }
    if (map.getLayer('validation-flags-layer')) {
      map.setLayoutProperty('validation-flags-layer', 'visibility', activeLayers.flags ? 'visible' : 'none');
    }
  }, [activeLayers]);

  // Update Selected Parcel Highlight
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('parcels-highlight-layer')) {
      map.setFilter('parcels-highlight-layer', ['==', ['get', 'id'], selectedParcelId || '']);
    }
  }, [selectedParcelId]);

  return (
    <div className="relative w-full h-full min-h-[400px] overflow-hidden rounded-2xl border border-pastel-border bg-white shadow-pastel-md">
      {loading && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/80 backdrop-blur-sm text-pastel-text">
          <div className="flex items-center space-x-3 text-sm font-medium">
            <Loader2 className="w-5 h-5 animate-spin text-pastel-action" />
            <span>Loading MapLibre Web-GIS Vector Layers...</span>
          </div>
        </div>
      )}

      {/* MapLibre DOM Container */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Accessible Floating Map Controls Overlay */}
      <div className="absolute top-4 right-4 z-10 flex flex-col space-y-2">
        <button
          onClick={() => mapRef.current?.zoomIn()}
          title="Zoom In"
          aria-label="Zoom In"
          className="p-2.5 bg-white/95 backdrop-blur-md rounded-xl border border-pastel-border text-pastel-text hover:bg-pastel-surface-soft hover:text-pastel-action transition-all shadow-pastel-sm"
        >
          <ZoomIn className="w-4 h-4" />
        </button>

        <button
          onClick={() => mapRef.current?.zoomOut()}
          title="Zoom Out"
          aria-label="Zoom Out"
          className="p-2.5 bg-white/95 backdrop-blur-md rounded-xl border border-pastel-border text-pastel-text hover:bg-pastel-surface-soft hover:text-pastel-action transition-all shadow-pastel-sm"
        >
          <ZoomOut className="w-4 h-4" />
        </button>

        <button
          onClick={() => mapRef.current?.resetNorthPitch()}
          title="Reset Orientation"
          aria-label="Reset Orientation"
          className="p-2.5 bg-white/95 backdrop-blur-md rounded-xl border border-pastel-border text-pastel-text hover:bg-pastel-surface-soft hover:text-pastel-action transition-all shadow-pastel-sm"
        >
          <Compass className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
