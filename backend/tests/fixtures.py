"""
GIS test fixtures — deterministic geometries with known expected results.

All coordinates are in EPSG:4326 (Chennai area).
"""

# ── Valid geometries ──────────────────────────────────────────────────────────

VALID_BUILDING = {
    "type": "Polygon",
    "coordinates": [[[80.27, 13.08], [80.271, 13.08], [80.271, 13.081], [80.27, 13.081], [80.27, 13.08]]]
}

VALID_FIELD = {
    "type": "Polygon",
    "coordinates": [[[80.26, 13.07], [80.28, 13.07], [80.28, 13.09], [80.26, 13.09], [80.26, 13.07]]]
}

VALID_ROAD = {
    "type": "LineString",
    "coordinates": [[80.25, 13.08], [80.30, 13.08]]
}

# ── Overlapping polygons (known intersection) ─────────────────────────────────

POLYGON_A = {
    "type": "Polygon",
    "coordinates": [[[80.27, 13.08], [80.272, 13.08], [80.272, 13.082], [80.27, 13.082], [80.27, 13.08]]]
}

POLYGON_B_OVERLAPS_A = {
    "type": "Polygon",
    "coordinates": [[[80.271, 13.079], [80.273, 13.079], [80.273, 13.081], [80.271, 13.081], [80.271, 13.079]]]
}

# ── Adjacent polygons (shared boundary — NOT an overlap) ─────────────────────

POLYGON_C_LEFT = {
    "type": "Polygon",
    "coordinates": [[[80.26, 13.08], [80.265, 13.08], [80.265, 13.085], [80.26, 13.085], [80.26, 13.08]]]
}

POLYGON_D_RIGHT_ADJACENT = {
    "type": "Polygon",
    "coordinates": [[[80.265, 13.08], [80.270, 13.08], [80.270, 13.085], [80.265, 13.085], [80.265, 13.08]]]
}

# ── Gap: two polygons with ~1m space between them ────────────────────────────

POLYGON_E_LEFT = {
    "type": "Polygon",
    "coordinates": [[[80.260, 13.090], [80.264, 13.090], [80.264, 13.094], [80.260, 13.094], [80.260, 13.090]]]
}

POLYGON_F_RIGHT_GAP = {
    "type": "Polygon",
    # Offset ~0.00001 degrees ≈ ~1m eastward
    "coordinates": [[[80.26401, 13.090], [80.268, 13.090], [80.268, 13.094], [80.26401, 13.094], [80.26401, 13.090]]]
}

# ── Self-intersecting (bow-tie) ───────────────────────────────────────────────

SELF_INTERSECTING_POLYGON = {
    "type": "Polygon",
    # Figure-8 / bow-tie: rings cross each other
    "coordinates": [[[80.27, 13.08], [80.272, 13.082], [80.272, 13.08], [80.27, 13.082], [80.27, 13.08]]]
}

# ── Degenerate (too few coordinates) ─────────────────────────────────────────

DEGENERATE_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[80.27, 13.08], [80.271, 13.08], [80.27, 13.08]]]
}

# ── Empty geometry ────────────────────────────────────────────────────────────

EMPTY_GEOMETRY = None

# ── MultiPolygon ─────────────────────────────────────────────────────────────

VALID_MULTIPOLYGON = {
    "type": "MultiPolygon",
    "coordinates": [
        [[[80.27, 13.08], [80.271, 13.08], [80.271, 13.081], [80.27, 13.081], [80.27, 13.08]]],
        [[[80.28, 13.08], [80.281, 13.08], [80.281, 13.081], [80.28, 13.081], [80.28, 13.08]]],
    ]
}

# ── Building inside field (relationship fixture) ──────────────────────────────

BUILDING_INSIDE_FIELD = {
    "type": "Polygon",
    "coordinates": [[[80.263, 13.072], [80.264, 13.072], [80.264, 13.073], [80.263, 13.073], [80.263, 13.072]]]
}
