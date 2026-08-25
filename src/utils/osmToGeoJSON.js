/**
 * Converts Overpass JSON with `out geom;` to a GeoJSON FeatureCollection
 */
export function convertOSMToGeoJSON(osmData, featureType = 'building') {
    const features = [];

    if (!osmData || !osmData.elements) {
        return { type: "FeatureCollection", features };
    }

    osmData.elements.forEach(element => {
        // We only care about elements that have geometry
        // Since we use out geom, ways and relations should have a 'geometry' or 'members' array
        
        let geometry = null;
        const properties = {
            osm_id: element.id,
            osm_type: element.type,
            feature_type: featureType,
            ...element.tags
        };

        if (element.type === 'way' && element.geometry) {
            const coords = element.geometry.map(pt => [pt.lon, pt.lat]);
            const isClosed = coords.length >= 4 && 
                coords[0][0] === coords[coords.length - 1][0] && 
                coords[0][1] === coords[coords.length - 1][1];

            if (featureType === 'road') {
                if (coords.length >= 2) {
                    geometry = {
                        type: "LineString",
                        coordinates: coords
                    };
                }
            } else {
                // Polygon logic for buildings and fields
                if (isClosed) {
                    geometry = {
                        type: "Polygon",
                        coordinates: [coords]
                    };
                } else if (coords.length >= 3) {
                    // Forcibly close incomplete geometries
                    coords.push([...coords[0]]);
                    geometry = {
                        type: "Polygon",
                        coordinates: [coords]
                    };
                }
            }
        } else if (element.type === 'relation' && element.members) {
            if (featureType !== 'road') {
                const outers = element.members
                    .filter(m => m.role === 'outer' && m.type === 'way' && m.geometry)
                    .map(m => m.geometry.map(pt => [pt.lon, pt.lat]));
                
                if (outers.length === 1) {
                    geometry = {
                        type: "Polygon",
                        coordinates: [outers[0]]
                    };
                } else if (outers.length > 1) {
                    geometry = {
                        type: "MultiPolygon",
                        coordinates: outers.map(outer => [outer])
                    };
                }
            }
        }

        if (geometry) {
            features.push({
                type: "Feature",
                id: element.id,
                properties,
                geometry
            });
        }
    });

    return {
        type: "FeatureCollection",
        features
    };
}
