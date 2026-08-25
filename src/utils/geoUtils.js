// Geospatial Utilities wrapping Turf.js

export function calculateArea(feature) {
    if (feature.geometry.type !== 'Polygon' && feature.geometry.type !== 'MultiPolygon') {
        return null;
    }
    const areaSqMeters = turf.area(feature);
    
    if (areaSqMeters > 10000) {
        // Return hectares
        const hectares = areaSqMeters / 10000;
        return { value: hectares.toFixed(2), unit: 'hectares' };
    }
    return { value: areaSqMeters.toFixed(1), unit: 'm²' };
}

export function calculateLength(feature) {
    if (feature.geometry.type !== 'LineString' && feature.geometry.type !== 'MultiLineString') {
        return null;
    }
    const lengthKm = turf.length(feature);
    const lengthMeters = lengthKm * 1000;
    
    if (lengthMeters > 1000) {
        return { value: lengthKm.toFixed(2), unit: 'km' };
    }
    return { value: lengthMeters.toFixed(1), unit: 'm' };
}

export function calculateCentroid(feature) {
    try {
        const center = turf.centroid(feature);
        return {
            lng: center.geometry.coordinates[0].toFixed(5),
            lat: center.geometry.coordinates[1].toFixed(5)
        };
    } catch (e) {
        return null;
    }
}

export function calculateDistance(featA, featB) {
    try {
        let minDist = Infinity;
        
        // If A is Polygon and B is LineString, measure from A's vertices to B
        if ((featA.geometry.type === 'Polygon' || featA.geometry.type === 'MultiPolygon') && 
            (featB.geometry.type === 'LineString' || featB.geometry.type === 'MultiLineString')) {
            const coords = turf.coordAll(featA);
            for (let coord of coords) {
                const pt = turf.point(coord);
                const dist = turf.pointToLineDistance(pt, featB, { units: 'meters' });
                if (dist < minDist) minDist = dist;
            }
            return minDist;
        }

        // If A is LineString and B is Polygon, flip it
        if ((featB.geometry.type === 'Polygon' || featB.geometry.type === 'MultiPolygon') && 
            (featA.geometry.type === 'LineString' || featA.geometry.type === 'MultiLineString')) {
            const coords = turf.coordAll(featB);
            for (let coord of coords) {
                const pt = turf.point(coord);
                const dist = turf.pointToLineDistance(pt, featA, { units: 'meters' });
                if (dist < minDist) minDist = dist;
            }
            return minDist;
        }

        // Default to centroid distance if both are polygons or both are lines for simplicity,
        // or just use turf.distance
        const centerA = turf.centroid(featA);
        const centerB = turf.centroid(featB);
        const distKm = turf.distance(centerA, centerB);
        return distKm * 1000; 
    } catch(e) {
        return Infinity;
    }
}

export function checkOverlapOrContains(polyFeat, pointFeat) {
    try {
        const center = turf.centroid(pointFeat);
        return turf.booleanPointInPolygon(center, polyFeat);
    } catch(e) {
        return false;
    }
}
