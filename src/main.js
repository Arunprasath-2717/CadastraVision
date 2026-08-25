import { setupBuildingLayer } from './layers/buildingLayer.js';
import { setupRoadLayer } from './layers/roadLayer.js';
import { setupFieldLayer } from './layers/fieldLayer.js';
import { setupBaseMapLayer } from './layers/baseMapLayer.js';
import { setupMapControls } from './components/MapControls.js';
import { setupFeaturePanel } from './components/FeaturePanel.js';
import { setupEditor } from './components/Editor.js';
import { setupStatsPanel } from './components/StatsPanel.js';
import { setupSearchPanel } from './components/SearchPanel.js';
import { setupFilterPanel } from './components/FilterPanel.js';
import { setupProjectPanel } from './components/ProjectPanel.js';
import { state } from './state/appState.js';

// Center somewhere, e.g., Chennai
const centerLng = 80.2730;
const centerLat = 13.0810;

const map = new maplibregl.Map({
    container: 'map',
    style: 'https://tiles.openfreemap.org/styles/liberty',
    center: [centerLng, centerLat],
    zoom: 17
});

map.on('load', () => {
    // Setup Layers in conceptual order (bottom to top):
    setupBaseMapLayer(map); 
    setupFieldLayer(map);
    setupRoadLayer(map);
    setupBuildingLayer(map);

    // Setup UI Components
    setupProjectPanel(map);
    setupMapControls(map);
    setupFeaturePanel();
    setupStatsPanel();
    setupSearchPanel(map);
    setupFilterPanel(map);
    
    // Setup Editor
    setupEditor(map);

    // Setup Relationship Visualization Layer
    map.addSource('relationship-viz', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
    });
    map.addLayer({
        id: 'relationship-lines',
        type: 'line',
        source: 'relationship-viz',
        paint: {
            'line-color': '#9b59b6', // purple
            'line-width': 2,
            'line-dasharray': [2, 2]
        }
    });

    window.addEventListener('update-relationship-viz', (e) => {
        const lines = e.detail || [];
        const source = map.getSource('relationship-viz');
        if (source) {
            source.setData({
                type: 'FeatureCollection',
                features: lines
            });
        }
    });

    // Handle clicking outside features to deselect
    map.on('click', (e) => {
        if (state.editingFeature) return; // Do not deselect if editing

        // Query rendered features at the click point
        const features = map.queryRenderedFeatures(e.point, {
            layers: ['buildings-fill', 'roads-line', 'fields-fill'] 
        });

        if (features.length === 0) {
            // Clicked on empty space, deselect current
            if (state.selectedFeature) {
                map.setFeatureState(
                    { source: state.selectedFeature.source, id: state.selectedFeature.id },
                    { selected: false }
                );
                state.selectedFeature = null;
                window.dispatchEvent(new CustomEvent('feature-selected', { detail: null }));
                window.dispatchEvent(new CustomEvent('update-relationship-viz', { detail: [] }));
            }
        }
    });
});
