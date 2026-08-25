import { state } from '../state/appState.js';

export function setupBuildingLayer(map) {
    // Add empty GeoJSON source for buildings
    map.addSource('osm-buildings', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
    });

    // Fill layer
    map.addLayer({
        id: 'buildings-fill',
        type: 'fill',
        source: 'osm-buildings',
        paint: {
            'fill-color': [
                'case',
                ['boolean', ['feature-state', 'selected'], false],
                '#ffeb3b', // Highlight color when selected
                '#4a90e2'  // Default color
            ],
            'fill-opacity': 0.6
        }
    });

    // Outline layer
    map.addLayer({
        id: 'buildings-outline',
        type: 'line',
        source: 'osm-buildings',
        paint: {
            'line-color': '#1f4b7a',
            'line-width': 1
        }
    });

    let hoveredStateId = null;

    // Selection Interaction
    map.on('click', 'buildings-fill', (e) => {
        if (state.editingFeature) {
            e.originalEvent.stopPropagation();
            return; // Prevent selection change while editing
        }

        if (e.features.length > 0) {
            const feature = e.features[0];
            
            // Unselect previously selected feature
            if (state.selectedFeature) {
                map.setFeatureState(
                    { source: state.selectedFeature.source, id: state.selectedFeature.id },
                    { selected: false }
                );
            }

            // Select new feature
            state.selectedFeature = feature;
            map.setFeatureState(
                { source: 'osm-buildings', id: feature.id },
                { selected: true }
            );

            // Dispatch custom event for UI updates
            window.dispatchEvent(new CustomEvent('feature-selected', { detail: feature }));
            
            e.originalEvent.stopPropagation();
        }
    });

    // Change cursor
    map.on('mouseenter', 'buildings-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'buildings-fill', () => {
        map.getCanvas().style.cursor = '';
    });
}

export function updateBuildingData(map, geojsonData) {
    const source = map.getSource('osm-buildings');
    if (source) {
        source.setData(geojsonData);
    }
}

export function toggleBuildingLayer(map, isVisible) {
    const visibility = isVisible ? 'visible' : 'none';
    if (map.getLayer('buildings-fill')) {
        map.setLayoutProperty('buildings-fill', 'visibility', visibility);
        map.setLayoutProperty('buildings-outline', 'visibility', visibility);
    }
}
