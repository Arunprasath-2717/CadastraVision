import { state } from '../state/appState.js';

const STORAGE_KEY = 'map-intelligence-project';

export function saveProjectToLocalStorage(map) {
    if (state.editingFeature) return; // Do not save during active edit

    state.project.updatedAt = new Date().toISOString();
    
    if (map) {
        const center = map.getCenter();
        state.project.mapView = {
            longitude: center.lng,
            latitude: center.lat,
            zoom: map.getZoom(),
            bearing: map.getBearing(),
            pitch: map.getPitch()
        };
    }

    const exportState = {
        project: state.project,
        features: state.features
    };

    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(exportState));
        window.dispatchEvent(new CustomEvent('project-status-updated', { detail: 'Saved ✓' }));
    } catch (e) {
        console.error("LocalStorage quota exceeded or error:", e);
        window.dispatchEvent(new CustomEvent('project-status-updated', { detail: 'Save Failed' }));
    }
}

export function loadProjectFromLocalStorage() {
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        if (!data) return null;
        return JSON.parse(data);
    } catch (e) {
        console.error("Failed to load project from LocalStorage:", e);
        return null;
    }
}

export function clearLocalStorageProject() {
    localStorage.removeItem(STORAGE_KEY);
}

export function exportProjectFile(map) {
    // Ensure state is up to date
    if (map) {
        const center = map.getCenter();
        state.project.mapView = {
            longitude: center.lng,
            latitude: center.lat,
            zoom: map.getZoom(),
            bearing: map.getBearing(),
            pitch: map.getPitch()
        };
    }
    
    const exportState = {
        project: state.project,
        features: state.features
    };

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportState, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    
    const safeName = state.project.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    downloadAnchorNode.setAttribute("download", `${safeName}.mapproject.json`);
    
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}

export function importProjectFile(file, callback) {
    const reader = new FileReader();
    reader.onload = function(event) {
        try {
            const projectData = JSON.parse(event.target.result);
            
            if (!projectData.project || !projectData.project.version) {
                alert("Unsupported project version or invalid format.");
                return;
            }

            callback(projectData);
        } catch (e) {
            alert("Corrupted project file or invalid JSON.");
        }
    };
    reader.readAsText(file);
}
