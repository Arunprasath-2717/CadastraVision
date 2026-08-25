import { state } from '../state/appState.js';

export function setupRoadLayer(map) {
    map.addSource('osm-roads', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
    });

    // We can use a single line layer with data-driven styling for road widths/colors
    map.addLayer({
        id: 'roads-line',
        type: 'line',
        source: 'osm-roads',
        paint: {
            'line-color': [
                'case',
                ['boolean', ['feature-state', 'selected'], false],
                '#ffeb3b', // Highlight
                [
                    'match',
                    ['get', 'highway'],
                    ['motorway', 'trunk', 'primary'], '#e74c3c', // Major roads
                    ['secondary', 'tertiary'], '#f39c12',       // Medium roads
                    ['residential', 'service', 'living_street', 'unclassified'], '#bdc3c7', // Local roads
                    /* default paths/tracks */ '#95a5a6'
                ]
            ],
            'line-width': [
                'case',
                ['boolean', ['feature-state', 'selected'], false],
                4, // Highlight width
                [
                    'match',
                    ['get', 'highway'],
                    ['motorway', 'trunk', 'primary'], 4,
                    ['secondary', 'tertiary'], 3,
                    ['residential', 'service', 'living_street', 'unclassified'], 2,
                    /* default */ 1.5
                ]
            ]
        }
    });

    // Selection Interaction
    map.on('click', 'roads-line', (e) => {
        if (state.editingFeature) {
            e.originalEvent.stopPropagation();
            return;
        }

        if (e.features.length > 0) {
            const feature = e.features[0];
            
            if (state.selectedFeature && state.selectedFeature.source !== 'osm-roads') {
                // If the selected feature is from another source, we handle it in main.js
            }

            if (state.selectedFeature) {
                map.setFeatureState(
                    { source: state.selectedFeature.source, id: state.selectedFeature.id },
                    { selected: false }
                );
            }

            state.selectedFeature = feature;
            map.setFeatureState(
                { source: 'osm-roads', id: feature.id },
                { selected: true }
            );

            window.dispatchEvent(new CustomEvent('feature-selected', { detail: feature }));
            
            // Prevent event from bubbling to map empty space click handler
            e.originalEvent.stopPropagation();
        }
    });

    map.on('mouseenter', 'roads-line', () => {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'roads-line', () => {
        map.getCanvas().style.cursor = '';
    });
}

export function updateRoadData(map, geojsonData) {
    const source = map.getSource('osm-roads');
    if (source) {
        source.setData(geojsonData);
    }
}

export function toggleRoadLayer(map, isVisible) {
    const visibility = isVisible ? 'visible' : 'none';
    if (map.getLayer('roads-line')) {
        map.setLayoutProperty('roads-line', 'visibility', visibility);
    }
}
