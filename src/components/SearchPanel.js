import { state } from '../state/appState.js';

export function setupSearchPanel(map) {
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        const results = [];
        const allFeatures = [
            ...state.features.buildings.map(f => ({...f, _source: 'osm-buildings'})),
            ...state.features.roads.map(f => ({...f, _source: 'osm-roads'})),
            ...state.features.fields.map(f => ({...f, _source: 'osm-fields'}))
        ];

        for (const feature of allFeatures) {
            if (results.length >= 20) break; // limit to 20 results

            const props = feature.properties;
            const searchableText = [
                props.osm_id,
                props.name,
                props.building,
                props.highway,
                props.landuse,
                props.natural,
                props.feature_type
            ].filter(Boolean).join(' ').toLowerCase();

            if (searchableText.includes(query)) {
                results.push(feature);
            }
        }

        renderResults(results, searchResults, map);
    });

    // Close search results if clicked outside
    document.addEventListener('click', (e) => {
        if (e.target !== searchInput && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
}

function renderResults(results, container, map) {
    if (results.length === 0) {
        container.innerHTML = '<div style="color: #666; font-style: italic;">No results found</div>';
        container.style.display = 'block';
        return;
    }

    container.innerHTML = '';
    
    results.forEach(feature => {
        const div = document.createElement('div');
        div.style.padding = '5px';
        div.style.cursor = 'pointer';
        div.style.borderBottom = '1px solid #eee';
        
        const props = feature.properties;
        const type = feature._source.replace('osm-', '');
        const name = props.name || props.highway || props.building || props.landuse || props.natural || 'Unnamed';
        
        div.innerHTML = `<strong>${type}</strong>: ${name} <span style="color:#888; font-size:10px;">(ID: ${props.osm_id})</span>`;
        
        div.addEventListener('mouseenter', () => { div.style.backgroundColor = '#eaeaea'; });
        div.addEventListener('mouseleave', () => { div.style.backgroundColor = 'transparent'; });
        
        div.addEventListener('click', () => {
            // Restore original .source expected by MapLibre selection logic
            feature.source = feature._source;
            delete feature._source;

            // Trigger selection
            window.dispatchEvent(new CustomEvent('feature-selected', { detail: feature }));
            
            // Fly to feature if centroid available
            try {
                const center = turf.centroid(feature);
                map.flyTo({
                    center: center.geometry.coordinates,
                    zoom: 18,
                    essential: true
                });
            } catch(e) {}
            
            container.style.display = 'none';
        });

        container.appendChild(div);
    });

    container.style.display = 'block';
}
