import { state } from '../state/appState.js';

export function setupFieldLayer(map) {
    map.addSource('osm-fields', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
    });

    // Field fill layer (semi-transparent so satellite shows through)
    map.addLayer({
        id: 'fields-fill',
        type: 'fill',
        source: 'osm-fields',
        paint: {
            'fill-color': [
                'case',
                ['boolean', ['feature-state', 'selected'], false],
                '#ffeb3b', // Highlight color
                '#2ecc71'  // Default green for fields/nature
            ],
            'fill-opacity': 0.4
        }
    });

    // Field outline layer
    map.addLayer({
        id: 'fields-outline',
        type: 'line',
        source: 'osm-fields',
        paint: {
            'line-color': '#27ae60',
            'line-width': 1,
            'line-dasharray': [2, 2]
        }
    });

    // Selection Interaction
    map.on('click', 'fields-fill', (e) => {
        if (state.editingFeature) {
            e.originalEvent.stopPropagation();
            return;
        }

        if (e.features.length > 0) {
            const feature = e.features[0];
            
            if (state.selectedFeature) {
                map.setFeatureState(
                    { source: state.selectedFeature.source, id: state.selectedFeature.id },
                    { selected: false }
                );
            }

            state.selectedFeature = feature;
            map.setFeatureState(
                { source: 'osm-fields', id: feature.id },
                { selected: true }
            );

            window.dispatchEvent(new CustomEvent('feature-selected', { detail: feature }));
            e.originalEvent.stopPropagation();
        }
    });

    map.on('mouseenter', 'fields-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'fields-fill', () => {
        map.getCanvas().style.cursor = '';
    });
}

export function updateFieldData(map, geojsonData) {
    const source = map.getSource('osm-fields');
    if (source) {
        source.setData(geojsonData);
    }
}

export function toggleFieldLayer(map, isVisible) {
    const visibility = isVisible ? 'visible' : 'none';
    if (map.getLayer('fields-fill')) {
        map.setLayoutProperty('fields-fill', 'visibility', visibility);
        map.setLayoutProperty('fields-outline', 'visibility', visibility);
    }
}
