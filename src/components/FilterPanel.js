import { state } from '../state/appState.js';
import { toggleBuildingLayer, updateBuildingData } from '../layers/buildingLayer.js';
import { toggleRoadLayer, updateRoadData } from '../layers/roadLayer.js';
import { toggleFieldLayer, updateFieldData } from '../layers/fieldLayer.js';

let mapInstance;

export function setupFilterPanel(map) {
    mapInstance = map;
    window.addEventListener('app-state-changed', updateFilters);
}

function updateFilters() {
    const filterContainer = document.getElementById('app-filters');
    if (!filterContainer) return;

    // We can extract unique types from the loaded data
    const buildingTypes = [...new Set(state.features.buildings.map(f => f.properties.building || f.properties.feature_type).filter(Boolean))];
    const roadTypes = [...new Set(state.features.roads.map(f => f.properties.highway).filter(Boolean))];
    const fieldTypes = [...new Set(state.features.fields.map(f => f.properties.landuse || f.properties.natural).filter(Boolean))];

    if (buildingTypes.length === 0 && roadTypes.length === 0 && fieldTypes.length === 0) {
        filterContainer.innerHTML = '<div style="color:#666; font-style:italic;">No features loaded to filter</div>';
        return;
    }

    let html = '';
    
    if (buildingTypes.length > 0) {
        html += `<div style="font-weight:bold; margin-top:5px;">Building Type</div>`;
        buildingTypes.forEach(t => {
            html += `<label style="display:block; font-size:12px;"><input type="checkbox" class="filter-cb" data-source="buildings" data-val="${t}" checked> ${t}</label>`;
        });
    }

    if (roadTypes.length > 0) {
        html += `<div style="font-weight:bold; margin-top:5px;">Road Type</div>`;
        roadTypes.forEach(t => {
            html += `<label style="display:block; font-size:12px;"><input type="checkbox" class="filter-cb" data-source="roads" data-val="${t}" checked> ${t}</label>`;
        });
    }

    if (fieldTypes.length > 0) {
        html += `<div style="font-weight:bold; margin-top:5px;">Field Type</div>`;
        fieldTypes.forEach(t => {
            html += `<label style="display:block; font-size:12px;"><input type="checkbox" class="filter-cb" data-source="fields" data-val="${t}" checked> ${t}</label>`;
        });
    }

    filterContainer.innerHTML = html;

    // Attach listeners
    const checkboxes = filterContainer.querySelectorAll('.filter-cb');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', applyFilters);
    });
}

function applyFilters() {
    const filterContainer = document.getElementById('app-filters');
    const checkboxes = filterContainer.querySelectorAll('.filter-cb');
    
    const activeFilters = {
        buildings: new Set(),
        roads: new Set(),
        fields: new Set()
    };

    checkboxes.forEach(cb => {
        if (cb.checked) {
            activeFilters[cb.dataset.source].add(cb.dataset.val);
        }
    });

    // Apply to Buildings
    const filteredBuildings = state.features.buildings.filter(f => activeFilters.buildings.has(f.properties.building || f.properties.feature_type));
    updateBuildingData(mapInstance, { type: 'FeatureCollection', features: filteredBuildings });

    // Apply to Roads
    const filteredRoads = state.features.roads.filter(f => activeFilters.roads.has(f.properties.highway));
    updateRoadData(mapInstance, { type: 'FeatureCollection', features: filteredRoads });

    // Apply to Fields
    const filteredFields = state.features.fields.filter(f => activeFilters.fields.has(f.properties.landuse || f.properties.natural));
    updateFieldData(mapInstance, { type: 'FeatureCollection', features: filteredFields });
}
