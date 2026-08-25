import { state } from '../state/appState.js';
import { updateBuildingData } from '../layers/buildingLayer.js';
import { updateRoadData } from '../layers/roadLayer.js';
import { updateFieldData } from '../layers/fieldLayer.js';
import { 
    saveProjectToLocalStorage, 
    loadProjectFromLocalStorage, 
    clearLocalStorageProject, 
    exportProjectFile, 
    importProjectFile 
} from '../services/projectStorageService.js';
import { exportGeoJSON } from '../services/geoJsonExportService.js';
import { importGeoJSONFile } from '../services/geoJsonImportService.js';

let mapInstance;

export function setupProjectPanel(map) {
    mapInstance = map;
    
    const projectNameInput = document.getElementById('project-name-input');
    const projectStatusText = document.getElementById('project-status-text');

    const btnNew = document.getElementById('btn-new-project');
    const btnSave = document.getElementById('btn-save-project');
    const btnLoad = document.getElementById('btn-load-project');
    const btnImportProject = document.getElementById('btn-import-project');
    const btnExportProject = document.getElementById('btn-export-project');
    const btnImportGeoJSON = document.getElementById('btn-import-geojson');
    const btnExportGeoJSON = document.getElementById('btn-export-geojson');

    // Create hidden file inputs
    const fileInputProject = document.createElement('input');
    fileInputProject.type = 'file';
    fileInputProject.accept = '.json';
    fileInputProject.style.display = 'none';
    document.body.appendChild(fileInputProject);

    const fileInputGeoJSON = document.createElement('input');
    fileInputGeoJSON.type = 'file';
    fileInputGeoJSON.accept = '.geojson,.json';
    fileInputGeoJSON.style.display = 'none';
    document.body.appendChild(fileInputGeoJSON);

    // Initial load
    const saved = loadProjectFromLocalStorage();
    if (saved) {
        applyProjectState(saved);
        projectStatusText.innerText = 'Saved ✓';
    }

    projectNameInput.addEventListener('change', (e) => {
        state.project.name = e.target.value;
        saveProjectToLocalStorage(map);
    });

    window.addEventListener('project-status-updated', (e) => {
        projectStatusText.innerText = e.detail;
    });

    window.addEventListener('app-state-changed', () => {
        if (!state.editingFeature) { // Debounce/throttle in real app, but auto-save on change
            saveProjectToLocalStorage(mapInstance);
        }
    });

    // Buttons
    btnNew.addEventListener('click', () => {
        if (confirm("Start a new project? This will clear all data.")) {
            clearLocalStorageProject();
            state.features.buildings = [];
            state.features.roads = [];
            state.features.fields = [];
            state.project.name = "Untitled Project";
            projectNameInput.value = state.project.name;
            
            refreshLayers();
            projectStatusText.innerText = 'Unsaved';
            window.dispatchEvent(new Event('app-state-changed'));
        }
    });

    btnSave.addEventListener('click', () => {
        saveProjectToLocalStorage(mapInstance);
    });

    btnLoad.addEventListener('click', () => {
        const loaded = loadProjectFromLocalStorage();
        if (loaded) {
            applyProjectState(loaded);
        } else {
            alert("No saved project found in LocalStorage.");
        }
    });

    btnExportProject.addEventListener('click', () => {
        exportProjectFile(mapInstance);
    });

    btnExportGeoJSON.addEventListener('click', () => {
        exportGeoJSON();
    });

    btnImportProject.addEventListener('click', () => {
        fileInputProject.click();
    });

    fileInputProject.addEventListener('change', (e) => {
        if (e.target.files.length === 0) return;
        
        if (hasModifiedFeatures() && !confirm("You have unsaved local changes. Replace current project?")) {
            e.target.value = '';
            return;
        }

        importProjectFile(e.target.files[0], (projectData) => {
            applyProjectState(projectData);
            e.target.value = '';
        });
    });

    btnImportGeoJSON.addEventListener('click', () => {
        fileInputGeoJSON.click();
    });

    fileInputGeoJSON.addEventListener('change', (e) => {
        if (e.target.files.length === 0) return;
        
        importGeoJSONFile(e.target.files[0], (featuresList) => {
            if (featuresList.length === 0) return;

            // Compute stats for preview
            const counts = { buildings: 0, roads: 0, fields: 0 };
            featuresList.forEach(f => { counts[f.classification]++; });
            
            const preview = `IMPORT PREVIEW\nBuildings: ${counts.buildings}\nRoads: ${counts.roads}\nFields: ${counts.fields}\n\nProceed with import?`;
            if (!confirm(preview)) {
                e.target.value = '';
                return;
            }

            const isReplace = confirm("Do you want to REPLACE the current project data?\n\n[OK] = Replace all data\n[Cancel] = Add to existing data");
            
            if (hasModifiedFeatures() && isReplace && !confirm("You have unsaved local changes. Proceed with replace?")) {
                 e.target.value = '';
                 return;
            }

            if (isReplace) {
                // Replace
                state.features.buildings = [];
                state.features.roads = [];
                state.features.fields = [];
            }

            featuresList.forEach(item => {
                const arr = state.features[item.classification];
                // Check dupes
                const exists = arr.find(f => f.id === item.feature.id);
                if (exists) {
                    // Update existing
                    Object.assign(exists, item.feature);
                } else {
                    arr.push(item.feature);
                }
            });

            refreshLayers();
            window.dispatchEvent(new Event('app-state-changed'));
            e.target.value = '';
        });
    });

    // Handle map movement debounce to save view
    let moveTimeout;
    mapInstance.on('moveend', () => {
        clearTimeout(moveTimeout);
        moveTimeout = setTimeout(() => {
            if (!state.editingFeature) {
                saveProjectToLocalStorage(mapInstance);
            }
        }, 1000);
    });
}

function applyProjectState(data) {
    if (data.project) {
        state.project = data.project;
        document.getElementById('project-name-input').value = state.project.name;
    }
    
    if (data.features) {
        state.features = data.features;
    }

    refreshLayers();
    
    // Restore map view
    if (state.project.mapView) {
        mapInstance.jumpTo({
            center: [state.project.mapView.longitude, state.project.mapView.latitude],
            zoom: state.project.mapView.zoom,
            bearing: state.project.mapView.bearing || 0,
            pitch: state.project.mapView.pitch || 0
        });
    }

    // Clear selection
    state.selectedFeature = null;
    window.dispatchEvent(new CustomEvent('feature-selected', { detail: null }));
    window.dispatchEvent(new Event('app-state-changed'));
}

function refreshLayers() {
    updateBuildingData(mapInstance, { type: 'FeatureCollection', features: state.features.buildings });
    updateRoadData(mapInstance, { type: 'FeatureCollection', features: state.features.roads });
    updateFieldData(mapInstance, { type: 'FeatureCollection', features: state.features.fields });
}

function hasModifiedFeatures() {
    const check = (arr) => arr.some(f => f.properties.modified);
    return check(state.features.buildings) || check(state.features.roads) || check(state.features.fields);
}
