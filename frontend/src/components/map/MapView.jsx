import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { useMapSelection } from '../../context/MapContext';
import { geoApi } from '../../services/geoApi';
import { overpassApi } from '../../services/overpassApi';
import { ZoomIn, ZoomOut, Compass, Loader2, Globe, Layers } from 'lucide-react';

export function MapView() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const {
    activeLayers,
    selectedParcelId,
    selectParcel,
    setMapInstance,
    basemap,
    setBasemap
  } = useMapSelection();
  const selectParcelRef = useRef(selectParcel);

  const [loading, setLoading] = useState(true);
  const [overpassLoading, setOverpassLoading] = useState(false);

  useEffect(() => {
    selectParcelRef.current = selectParcel;
  }, [selectParcel]);

  // OpenFreeMap vector basemap style & dark raster fallback
  const openFreeMapStyle = 'https://tiles.openfreemap.org/styles/liberty';
  const cartoDarkStyle = {
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
        attribution: '&copy; <a href="https://openfreemap.org/">OpenFreeMap</a> &copy; OpenStreetMap'
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

    // Use OpenFreeMap vector style by default, fallback to cartoDark on timeout/network issue
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: openFreeMapStyle,
      center: [77.5946, 12.9716],
      zoom: 16,
      pitch: 25,
      bearing: 0
    });

    mapRef.current = map;
    setMapInstance(map);

    // Fallback handler if vector style fails to load
    map.on('error', (e) => {
      if (e.error?.message?.includes('style') || e.error?.status === 404) {
        console.warn('OpenFreeMap style fetch failed, falling back to Carto Dark:', e);
        map.setStyle(cartoDarkStyle);
      }
    });

    map.on('load', async () => {
      const [parcelsGeoJSON, buildingsGeoJSON, roadsGeoJSON] = await Promise.all([
        geoApi.getParcelGeoJSON(),
        geoApi.getBuildingsGeoJSON(),
        geoApi.getRoadsGeoJSON()
      ]);

      // Fetch Overpass live OpenStreetMap data for area
      setOverpassLoading(true);
      const overpassGeoJSON = await overpassApi.fetchBBoxFeatures([77.58, 12.96, 77.61, 12.98]);
      setOverpassLoading(false);

      map.addSource('parcels-source', { type: 'geojson', data: parcelsGeoJSON });
      map.addSource('buildings-source', { type: 'geojson', data: buildingsGeoJSON });
      map.addSource('roads-source', { type: 'geojson', data: roadsGeoJSON });
      map.addSource('overpass-source', { type: 'geojson', data: overpassGeoJSON });

      // Add Overpass OSM Layer
      map.addLayer({
        id: 'overpass-layer',
        type: 'line',
        source: 'overpass-source',
        paint: {
          'line-color': '#F472B6',
          'line-width': 1.5,
          'line-dasharray': [2, 2],
          'line-opacity': 0.8
        }
      });

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

      // Add Parcels Fill Layer
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

      // Selected Parcel Highlight Layer
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

      // Add Validation Flags Layer
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
          selectParcelRef.current(parcelId, false);
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
  }, [setMapInstance]);

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
    if (map.getLayer('overpass-layer')) {
      map.setLayoutProperty('overpass-layer', 'visibility', activeLayers.overpass ? 'visible' : 'none');
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
    <div className="relative h-full w-full min-h-[400px] overflow-hidden rounded-[21px] border border-[#54ACBF]/30 bg-[radial-gradient(circle_at_top_left,rgba(167,235,242,0.20),transparent_22%),linear-gradient(180deg,#0b2d4a,#011c40)] shadow-[inset_0_0_0_1px_rgba(167,235,242,0.14)]">
      {loading && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-[radial-gradient(circle_at_center,rgba(2,56,89,0.78),rgba(1,28,64,0.92))] backdrop-blur-sm text-white">
          <div className="flex items-center gap-3 rounded-2xl border border-[#A7EBF2]/30 bg-white/5 px-4 py-3 shadow-[0_12px_30px_rgba(1,28,64,0.2)]">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(84,172,191,0.08))]">
              <Loader2 className="h-5 w-5 animate-spin text-[#A7EBF2]" />
              <span className="absolute inset-0 rounded-xl border border-[#A7EBF2]/40 animate-pulse" />
            </div>
            <div className="space-y-1.5">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[#A7EBF2]">Loading OpenFreeMap vector engine</div>
              <div className="h-1.5 w-40 overflow-hidden rounded-full bg-white/10">
                <div className="h-full w-2/3 rounded-full bg-[linear-gradient(90deg,#A7EBF2,#54ACBF,#266580)] animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={mapContainerRef} className="h-full w-full" />

      <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-xl border border-[#A7EBF2]/35 bg-[rgba(1,28,64,0.75)] px-3 py-1.5 text-[11px] font-mono uppercase tracking-[0.18em] text-[#D7F7FF] shadow-[0_12px_24px_rgba(1,28,64,0.18)] backdrop-blur-md">
        <Globe className="h-3.5 w-3.5 text-[#A7EBF2]" />
        <span>OpenFreeMap • MapLibre GL • Overpass OSM</span>
        {overpassLoading && <Loader2 className="h-3 w-3 animate-spin text-[#A7EBF2]" />}
      </div>

      <div className="absolute right-4 top-4 z-10 flex flex-col space-y-2">
        <button
          onClick={() => mapRef.current?.zoomIn()}
          title="Zoom In"
          aria-label="Zoom In"
          className="rounded-xl border border-[#A7EBF2]/30 bg-[rgba(247,252,254,0.9)] p-2.5 text-[#011C40] shadow-[0_10px_22px_rgba(1,28,64,0.1)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#54ACBF] hover:text-[#023859]"
        >
          <ZoomIn className="h-4 w-4" />
        </button>

        <button
          onClick={() => mapRef.current?.zoomOut()}
          title="Zoom Out"
          aria-label="Zoom Out"
          className="rounded-xl border border-[#A7EBF2]/30 bg-[rgba(247,252,254,0.9)] p-2.5 text-[#011C40] shadow-[0_10px_22px_rgba(1,28,64,0.1)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#54ACBF] hover:text-[#023859]"
        >
          <ZoomOut className="h-4 w-4" />
        </button>

        <button
          onClick={() => mapRef.current?.resetNorthPitch()}
          title="Reset Orientation"
          aria-label="Reset Orientation"
          className="rounded-xl border border-[#A7EBF2]/30 bg-[rgba(247,252,254,0.9)] p-2.5 text-[#011C40] shadow-[0_10px_22px_rgba(1,28,64,0.1)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#54ACBF] hover:text-[#023859]"
        >
          <Compass className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
