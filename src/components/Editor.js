import { state } from '../state/appState.js';
import { updateBuildingData } from '../layers/buildingLayer.js';
import { updateRoadData } from '../layers/roadLayer.js';
import { updateFieldData } from '../layers/fieldLayer.js';

let draw;
let mapInstance;

export function setupEditor(map) {
    mapInstance = map;

    draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
            polygon: false,
            trash: false
        },
        defaultMode: 'simple_select'
    });

    map.addControl(draw, 'top-right');
}

export function enterEditMode(feature) {
    if (!feature) return;

    state.editingFeature = JSON.parse(JSON.stringify(feature)); // deep copy
    state.originalGeometry = JSON.parse(JSON.stringify(feature.geometry));

    // Add to draw
    draw.add(state.editingFeature);
    
    // Switch draw mode based on geometry type
    if (feature.geometry.type === 'LineString' || feature.geometry.type === 'MultiLineString') {
        draw.changeMode('direct_select', { featureId: feature.id });
    } else {
        draw.changeMode('direct_select', { featureId: feature.id });
    }

    // Hide original feature from our layer by temporarily removing it from state
    removeFeatureFromStateLayer(feature);
}

export function saveEdit() {
    if (!state.editingFeature) return;

    const drawnFeatures = draw.getAll();
    if (drawnFeatures.features.length === 0) return;

    const modifiedGeo = drawnFeatures.features[0].geometry;

    // Basic Validation
    if (!validateGeometry(modifiedGeo)) {
        alert("Invalid geometry. Save aborted.");
        return;
    }

    // Update state feature
    const updatedFeature = state.editingFeature;
    updatedFeature.geometry = modifiedGeo;
    updatedFeature.properties.modified = true;
    updatedFeature.properties.status = 'Modified';

    // Put back into state layer
    addFeatureToStateLayer(updatedFeature);

    // Cleanup
    draw.deleteAll();
    state.editingFeature = null;
    state.originalGeometry = null;

    window.dispatchEvent(new Event('app-state-changed'));

    // Reselect
    window.dispatchEvent(new CustomEvent('feature-selected', { detail: updatedFeature }));
}

export function cancelEdit() {
    if (!state.editingFeature) return;

    // Restore original geometry
    const originalFeature = state.editingFeature;
    originalFeature.geometry = state.originalGeometry;

    // Put back into state layer
    addFeatureToStateLayer(originalFeature);

    // Cleanup
    draw.deleteAll();
    state.editingFeature = null;
    state.originalGeometry = null;

    // Reselect
    window.dispatchEvent(new CustomEvent('feature-selected', { detail: originalFeature }));
}

function removeFeatureFromStateLayer(feature) {
    let sourceKey = getSourceKey(feature.source);
    if (!sourceKey) return;
    
    state.features[sourceKey] = state.features[sourceKey].filter(f => f.id !== feature.id);
    updateLayerData(sourceKey);
}

function addFeatureToStateLayer(feature) {
    let sourceKey = getSourceKey(feature.source);
    if (!sourceKey) return;

    // Check if it already exists, replace it
    const idx = state.features[sourceKey].findIndex(f => f.id === feature.id);
    if (idx !== -1) {
        state.features[sourceKey][idx] = feature;
    } else {
        state.features[sourceKey].push(feature);
    }
    updateLayerData(sourceKey);
}

function getSourceKey(source) {
    if (source === 'osm-buildings') return 'buildings';
    if (source === 'osm-roads') return 'roads';
    if (source === 'osm-fields') return 'fields';
    return null;
}

function updateLayerData(sourceKey) {
    const geoJSON = {
        type: 'FeatureCollection',
        features: state.features[sourceKey]
    };
    if (sourceKey === 'buildings') updateBuildingData(mapInstance, geoJSON);
    if (sourceKey === 'roads') updateRoadData(mapInstance, geoJSON);
    if (sourceKey === 'fields') updateFieldData(mapInstance, geoJSON);
}

function validateGeometry(geometry) {
    if (!geometry || !geometry.coordinates) return false;
    
    if (geometry.type === 'Polygon') {
        const ring = geometry.coordinates[0];
        if (!ring || ring.length < 4) return false; // Must have at least 4 points (3 distinct + 1 closed)
        const first = ring[0];
        const last = ring[ring.length - 1];
        if (first[0] !== last[0] || first[1] !== last[1]) return false; // Must be closed
    } else if (geometry.type === 'LineString') {
        if (geometry.coordinates.length < 2) return false;
    }
    
    return true;
}
