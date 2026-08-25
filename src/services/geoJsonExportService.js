import { state } from '../state/appState.js';

export function exportGeoJSON() {
    const features = [
        ...state.features.buildings,
        ...state.features.roads,
        ...state.features.fields
    ];

    const geojson = {
        type: "FeatureCollection",
        features: features
    };

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(geojson, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    
    const safeName = state.project.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    downloadAnchorNode.setAttribute("download", `${safeName}.geojson`);
    
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}
