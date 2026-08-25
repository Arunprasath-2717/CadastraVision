import { state } from '../state/appState.js';

export function setupStatsPanel() {
    updateStats();
    
    // We can expose updateStats globally or dispatch events to trigger it
    window.addEventListener('app-state-changed', updateStats);
}

export function updateStats() {
    const statsContainer = document.getElementById('app-stats');
    if (!statsContainer) return;

    const bCount = state.features.buildings.length;
    const bMod = state.features.buildings.filter(f => f.properties.modified).length;

    const rCount = state.features.roads.length;
    const rMod = state.features.roads.filter(f => f.properties.modified).length;

    const fCount = state.features.fields.length;
    const fMod = state.features.fields.filter(f => f.properties.modified).length;

    statsContainer.innerHTML = `
        Buildings: ${bCount} <span style="color:#888">(${bMod} modified)</span><br/>
        Roads: ${rCount} <span style="color:#888">(${rMod} modified)</span><br/>
        Fields: ${fCount} <span style="color:#888">(${fMod} modified)</span>
    `;
}
