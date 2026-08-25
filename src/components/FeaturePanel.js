import { enterEditMode, saveEdit, cancelEdit } from './Editor.js';
import { state } from '../state/appState.js';
import { calculateArea, calculateLength, calculateCentroid, calculateDistance, checkOverlapOrContains } from '../utils/geoUtils.js';

export function setupFeaturePanel() {
    const featurePanel = document.getElementById('feature-panel');
    const featureProps = document.getElementById('feature-props');
    const featureGeometry = document.getElementById('feature-geometry');
    const featureRelationships = document.getElementById('feature-relationships');
    const featureStatus = document.getElementById('feature-status');
    const featurePanelTitle = document.getElementById('feature-panel-title');
    
    const btnEdit = document.getElementById('btn-edit-feature');
    const editControls = document.getElementById('edit-controls');
    const btnSave = document.getElementById('btn-save-edit');
    const btnCancel = document.getElementById('btn-cancel-edit');

    btnEdit.addEventListener('click', () => {
        if (!state.selectedFeature) return;
        
        enterEditMode(state.selectedFeature);
        
        featurePanelTitle.innerText = "EDITING";
        btnEdit.style.display = 'none';
        editControls.style.display = 'block';
    });

    btnSave.addEventListener('click', () => {
        saveEdit();
        featurePanelTitle.innerText = "SELECTED";
        btnEdit.style.display = 'block';
        editControls.style.display = 'none';
    });

    btnCancel.addEventListener('click', () => {
        cancelEdit();
        featurePanelTitle.innerText = "SELECTED";
        btnEdit.style.display = 'block';
        editControls.style.display = 'none';
    });

    window.addEventListener('feature-selected', (e) => {
        // Prevent changing selection if we are currently editing
        if (state.editingFeature) {
            alert("Please Save or Cancel your current edit before selecting another feature.");
            return;
        }

        const feature = e.detail;
        
        if (!feature) {
            featurePanel.style.display = 'none';
            return;
        }

        featurePanel.style.display = 'block';
        featureProps.innerHTML = '';
        featureGeometry.innerHTML = '';
        featureRelationships.innerHTML = '';
        
        // Update Status
        const status = feature.properties.status || 'Original';
        featureStatus.innerText = `Status: ${status}`;
        featureStatus.style.color = status === 'Modified' ? '#27ae60' : '#3498db';

        const props = feature.properties;
        const displayKeys = [
            'osm_id', 'feature_type', 
            'building', 'name', 'levels', 'addr:housenumber', 'addr:street', 'addr:city', 
            'highway', 'ref', 'lanes', 'maxspeed', 'surface', 'oneway', 'bridge', 
            'landuse', 'natural', 'crop'
        ];
        
        displayKeys.forEach(key => {
            if (props[key] !== undefined && props[key] !== null && props[key] !== '') {
                const row = document.createElement('div');
                row.className = 'prop-row';
                row.innerHTML = `<span class="prop-key">${key}:</span> <span class="prop-val">${props[key]}</span>`;
                featureProps.appendChild(row);
            }
        });

        Object.keys(props).forEach(key => {
            if (!displayKeys.includes(key) && typeof props[key] !== 'object' && key !== 'modified' && key !== 'status') {
                const row = document.createElement('div');
                row.className = 'prop-row';
                row.innerHTML = `<span class="prop-key" style="font-weight:normal;">${key}:</span> <span class="prop-val">${props[key]}</span>`;
                featureProps.appendChild(row);
            }
        });

        // GEOMETRY
        const centroid = calculateCentroid(feature);
        if (centroid) {
            featureGeometry.innerHTML += `<div><span style="color:#666">Centroid:</span> ${centroid.lat}, ${centroid.lng}</div>`;
        }

        try {
            const bbox = turf.bbox(feature);
            if (bbox) {
                featureGeometry.innerHTML += `<div><span style="color:#666">BBox:</span> [${bbox[0].toFixed(4)}, ${bbox[1].toFixed(4)}, ${bbox[2].toFixed(4)}, ${bbox[3].toFixed(4)}]</div>`;
            }
        } catch(e) {}

        if (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon') {
            const area = calculateArea(feature);
            if (area) {
                featureGeometry.innerHTML += `<div><span style="color:#666">Area:</span> ${area.value} ${area.unit}</div>`;
            }
        } else if (feature.geometry.type === 'LineString' || feature.geometry.type === 'MultiLineString') {
            const length = calculateLength(feature);
            if (length) {
                featureGeometry.innerHTML += `<div><span style="color:#666">Length:</span> ${length.value} ${length.unit}</div>`;
            }
            
            if (feature.geometry.type === 'LineString') {
                const coords = feature.geometry.coordinates;
                if (coords.length > 0) {
                    const start = coords[0];
                    const end = coords[coords.length - 1];
                    featureGeometry.innerHTML += `<div><span style="color:#666">Start:</span> ${start[1].toFixed(5)}, ${start[0].toFixed(5)}</div>`;
                    featureGeometry.innerHTML += `<div><span style="color:#666">End:</span> ${end[1].toFixed(5)}, ${end[0].toFixed(5)}</div>`;
                }
            }
        }

        // RELATIONSHIPS
        let relLines = [];

        if (feature.source === 'osm-buildings') {
            // Find nearest road
            let nearestRoad = null;
            let minDistance = Infinity;
            state.features.roads.forEach(road => {
                const dist = calculateDistance(feature, road);
                if (dist < minDistance) {
                    minDistance = dist;
                    nearestRoad = road;
                }
            });

            if (nearestRoad) {
                const roadName = nearestRoad.properties.name || nearestRoad.properties.highway || nearestRoad.properties.osm_id;
                featureRelationships.innerHTML += `
                    <div style="margin-bottom: 5px;">
                        <span style="color:#666">Nearest Road:</span> ${roadName} <br/>
                        <span style="color:#666">Distance:</span> ${minDistance.toFixed(1)} m
                    </div>`;
                    
                // Generate line for visualization
                try {
                    const c1 = turf.centroid(feature).geometry.coordinates;
                    const c2 = turf.centroid(nearestRoad).geometry.coordinates;
                    relLines.push(turf.lineString([c1, c2]));
                } catch(e) {}
            }

            // Find containing field
            let containingField = null;
            for (let field of state.features.fields) {
                if (checkOverlapOrContains(field, feature)) {
                    containingField = field;
                    break;
                }
            }

            if (containingField) {
                const fieldType = containingField.properties.landuse || containingField.properties.natural || 'open field';
                featureRelationships.innerHTML += `
                    <div>
                        <span style="color:#666">Inside Field:</span> Yes <br/>
                        <span style="color:#666">Field Type:</span> ${fieldType} (ID: ${containingField.properties.osm_id})
                    </div>`;
            }
        } 
        else if (feature.source === 'osm-roads') {
            // Count nearby buildings
            let within25 = 0, within50 = 0, within100 = 0;
            state.features.buildings.forEach(building => {
                const dist = calculateDistance(building, feature);
                if (dist <= 25) within25++;
                if (dist <= 50) within50++;
                if (dist <= 100) within100++;
            });

            featureRelationships.innerHTML += `
                <div><span style="color:#666">Nearby Buildings:</span></div>
                <div>Within 25m: ${within25}</div>
                <div>Within 50m: ${within50}</div>
                <div>Within 100m: ${within100}</div>
            `;
        }
        else if (feature.source === 'osm-fields') {
            // Count buildings inside
            let insideCount = 0;
            state.features.buildings.forEach(building => {
                if (checkOverlapOrContains(feature, building)) {
                    insideCount++;
                }
            });
            featureRelationships.innerHTML += `<div><span style="color:#666">Buildings inside:</span> ${insideCount}</div>`;
        }

        // Draw relationship lines on the map globally
        window.dispatchEvent(new CustomEvent('update-relationship-viz', { detail: relLines }));
    });
}
