// Service to interact with Overpass API

let activeRequest = null;

async function executeQuery(query) {
    if (activeRequest) {
        activeRequest.abort();
    }
    const controller = new AbortController();
    activeRequest = controller;

    try {
        const response = await fetch('https://overpass-api.de/api/interpreter', {
            method: 'POST',
            body: query,
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error(`Overpass API error: ${response.statusText}`);
        }

        return await response.json();
    } catch (err) {
        if (err.name === 'AbortError') {
            console.log("Previous request aborted.");
            return null;
        }
        throw err;
    } finally {
        if (activeRequest === controller) {
            activeRequest = null;
        }
    }
}

function checkBounds(bounds) {
    const south = bounds._sw.lat;
    const west = bounds._sw.lng;
    const north = bounds._ne.lat;
    const east = bounds._ne.lng;

    const latDiff = Math.abs(north - south);
    const lngDiff = Math.abs(east - west);
    if (latDiff > 0.05 || lngDiff > 0.05) {
        throw new Error("Map area is too large. Please zoom in.");
    }
    return { south, west, north, east };
}

export async function fetchBuildingsInBounds(bounds) {
    const { south, west, north, east } = checkBounds(bounds);
    const query = `
        [out:json][timeout:25];
        (
          way["building"](${south},${west},${north},${east});
          relation["building"](${south},${west},${north},${east});
        );
        out geom;
    `;
    return executeQuery(query);
}

export async function fetchRoadsInBounds(bounds) {
    const { south, west, north, east } = checkBounds(bounds);
    const query = `
        [out:json][timeout:25];
        way["highway"](${south},${west},${north},${east});
        out geom;
    `;
    return executeQuery(query);
}

export async function fetchFieldsInBounds(bounds) {
    const { south, west, north, east } = checkBounds(bounds);
    const query = `
        [out:json][timeout:25];
        (
          way["landuse"="farmland"](${south},${west},${north},${east});
          way["landuse"="meadow"](${south},${west},${north},${east});
          way["landuse"="grass"](${south},${west},${north},${east});
          way["landuse"="orchard"](${south},${west},${north},${east});
          way["landuse"="vineyard"](${south},${west},${north},${east});
          way["natural"="grassland"](${south},${west},${north},${east});
          way["natural"="scrub"](${south},${west},${north},${east});
        );
        out geom;
    `;
    return executeQuery(query);
}
