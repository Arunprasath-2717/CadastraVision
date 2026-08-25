import { fetchBuildingsInBounds, fetchRoadsInBounds, fetchFieldsInBounds } from '../services/overpassService.js';
import { convertOSMToGeoJSON } from '../utils/osmToGeoJSON.js';
import { updateBuildingData, toggleBuildingLayer } from '../layers/buildingLayer.js';
import { updateRoadData, toggleRoadLayer } from '../layers/roadLayer.js';
import { updateFieldData, toggleFieldLayer } from '../layers/fieldLayer.js';
import { state } from '../state/appState.js';

export function setupMapControls(map) {
    const btnLoadBuildings = document.getElementById('btn-load-buildings');
    const btnLoadRoads = document.getElementById('btn-load-roads');
    const btnLoadFields = document.getElementById('btn-load-fields');
    
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMsg = document.getElementById('error-msg');
    
    const toggleBuildings = document.getElementById('toggle-buildings');
    const toggleRoads = document.getElementById('toggle-roads');
    const toggleFields = document.getElementById('toggle-fields');

    async function loadFeature(fetchFn, convertType, stateKey, updateLayerFn, btnElement) {
        const bounds = map.getBounds();
        
        btnElement.disabled = true;
        loadingIndicator.style.display = 'block';
        errorMsg.style.display = 'none';

        try {
            const rawOsmData = await fetchFn(bounds);
            
            if (rawOsmData) {
                const geoJSON = convertOSMToGeoJSON(rawOsmData, convertType);
                
                state.features[stateKey] = geoJSON.features;
                updateLayerFn(map, geoJSON);
                
                window.dispatchEvent(new Event('app-state-changed'));
            }
        } catch (err) {
            console.error(`Error loading ${stateKey}:`, err);
            errorMsg.innerText = err.message || `Failed to load ${stateKey}.`;
            errorMsg.style.display = 'block';
        } finally {
            btnElement.disabled = false;
            loadingIndicator.style.display = 'none';
        }
    }

    btnLoadBuildings.addEventListener('click', () => loadFeature(fetchBuildingsInBounds, 'building', 'buildings', updateBuildingData, btnLoadBuildings));
    btnLoadRoads.addEventListener('click', () => loadFeature(fetchRoadsInBounds, 'road', 'roads', updateRoadData, btnLoadRoads));
    btnLoadFields.addEventListener('click', () => loadFeature(fetchFieldsInBounds, 'field', 'fields', updateFieldData, btnLoadFields));

    toggleBuildings.addEventListener('change', (e) => {
        state.layersVisibility.buildings = e.target.checked;
        toggleBuildingLayer(map, e.target.checked);
    });
    
    toggleRoads.addEventListener('change', (e) => {
        state.layersVisibility.roads = e.target.checked;
        toggleRoadLayer(map, e.target.checked);
    });
    
    toggleFields.addEventListener('change', (e) => {
        state.layersVisibility.fields = e.target.checked;
        toggleFieldLayer(map, e.target.checked);
    });
}
