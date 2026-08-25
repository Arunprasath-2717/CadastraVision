export function setupBaseMapLayer(map) {
    // Esri World Imagery (No API key required for standard web use)
    // Attribution must be provided
    const esriAttribution = 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community';

    map.addSource('satellite-imagery', {
        type: 'raster',
        tiles: [
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        ],
        tileSize: 256,
        attribution: esriAttribution
    });

    // Add satellite layer below all our custom feature overlays, 
    // but on top of the standard OpenFreeMap basemap.
    // We can insert it before 'buildings-fill' which ensures it sits right below our custom layers.
    // If 'buildings-fill' doesn't exist yet, it will just add it at the top, but we call this after setting up custom layers.
    
    // Actually, it's safer to just add it and it will cover the basemap.
    // Then we just make sure to add our custom layers AFTER this satellite layer, OR use the beforeId.
    // Since we want this to be a toggleable base map, let's add it before 'buildings-fill' if it exists.
    
    const firstCustomLayerId = 'buildings-fill';
    
    if (map.getLayer(firstCustomLayerId)) {
        map.addLayer({
            id: 'satellite-layer',
            type: 'raster',
            source: 'satellite-imagery',
            layout: {
                visibility: 'none' // Hidden by default
            }
        }, firstCustomLayerId);
    } else {
        map.addLayer({
            id: 'satellite-layer',
            type: 'raster',
            source: 'satellite-imagery',
            layout: {
                visibility: 'none' // Hidden by default
            }
        });
    }

    // Setup UI listener
    const radios = document.querySelectorAll('input[name="basemap"]');
    radios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const mode = e.target.value;
            if (mode === 'satellite') {
                map.setLayoutProperty('satellite-layer', 'visibility', 'visible');
            } else {
                map.setLayoutProperty('satellite-layer', 'visibility', 'none');
            }
        });
    });
}
