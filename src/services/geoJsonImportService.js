export function importGeoJSONFile(file, callback) {
    const reader = new FileReader();
    reader.onload = function(event) {
        try {
            const geojson = JSON.parse(event.target.result);
            
            if (geojson.type !== 'FeatureCollection' || !Array.isArray(geojson.features)) {
                alert("Invalid GeoJSON. Must be a FeatureCollection.");
                return;
            }

            let validFeatures = [];
            let invalidCount = 0;

            geojson.features.forEach(f => {
                if (f.type !== 'Feature' || !f.geometry) {
                    invalidCount++;
                    return;
                }

                // Accept Polygon, MultiPolygon, LineString, MultiLineString
                const t = f.geometry.type;
                if (t === 'Polygon' || t === 'MultiPolygon' || t === 'LineString' || t === 'MultiLineString') {
                    // Try to determine layer
                    const props = f.properties || {};
                    let classification = 'unknown';

                    if (props.feature_type === 'building' || props.building) {
                        classification = 'buildings';
                        f.source = 'osm-buildings';
                    } else if (props.feature_type === 'road' || props.highway) {
                        classification = 'roads';
                        f.source = 'osm-roads';
                    } else if (props.feature_type === 'field' || props.landuse || props.natural || props.crop) {
                        classification = 'fields';
                        f.source = 'osm-fields';
                    }

                    if (classification !== 'unknown') {
                        validFeatures.push({ feature: f, classification });
                    } else {
                        invalidCount++;
                    }
                } else {
                    invalidCount++;
                }
            });

            if (invalidCount > 0) {
                console.warn(`${invalidCount} features were skipped (unsupported geometry or unknown classification).`);
            }

            callback(validFeatures);

        } catch (e) {
            alert("Corrupted file or invalid JSON.");
        }
    };
    reader.readAsText(file);
}
