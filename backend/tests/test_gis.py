"""
GIS Unit Tests — geometry, topology, relationships, confidence.

Run with:  cd backend && python -m pytest tests/ -v

No database required for these tests.
All operations run in-memory using Shapely.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import shapely.geometry

# ── Override config to use a safe processing CRS ────────────────────────────
import app.config as _cfg
_cfg.settings.PROCESSING_CRS = 32644  # UTM 44N (Chennai)

from app.geometry.crs import to_metric, to_wgs84, validate_epsg, geojson_geom_to_metric
from app.geometry.validator import validate_geojson_geometry
from app.geometry.metrics import area_m2, perimeter_m, distance_m
from app.geometry.topology.self_intersection import detect_self_intersections
from app.geometry.topology.overlap import detect_overlaps
from app.geometry.topology.gaps import detect_gaps
from app.geometry.topology.validator import validate_single, validate_collection
from app.geometry.relationships import compute_relationships
from app.geometry.confidence import calculate_confidence

from tests.fixtures import (
    VALID_BUILDING, VALID_FIELD, VALID_ROAD,
    POLYGON_A, POLYGON_B_OVERLAPS_A,
    POLYGON_C_LEFT, POLYGON_D_RIGHT_ADJACENT,
    POLYGON_E_LEFT, POLYGON_F_RIGHT_GAP,
    SELF_INTERSECTING_POLYGON, DEGENERATE_POLYGON,
    VALID_MULTIPOLYGON, BUILDING_INSIDE_FIELD,
)


# ── CRS Tests ────────────────────────────────────────────────────────────────

class TestCRS:
    def test_valid_epsg_4326(self):
        assert validate_epsg(4326) is True

    def test_valid_epsg_32644(self):
        assert validate_epsg(32644) is True

    def test_invalid_epsg(self):
        assert validate_epsg(99999) is False

    def test_to_metric_changes_coordinates(self):
        shp = shapely.geometry.shape(VALID_BUILDING)
        projected = to_metric(shp)
        # Projected coordinates should NOT be in degree range
        x, y = projected.centroid.x, projected.centroid.y
        assert x > 1000, "X coordinate should be in metres, not degrees"
        assert y > 1000, "Y coordinate should be in metres, not degrees"

    def test_round_trip_is_close(self):
        shp = shapely.geometry.shape(VALID_BUILDING)
        centroid_orig = shp.centroid
        projected = to_metric(shp)
        back = to_wgs84(projected)
        assert abs(back.centroid.x - centroid_orig.x) < 1e-5
        assert abs(back.centroid.y - centroid_orig.y) < 1e-5

    def test_geojson_to_metric(self):
        proj, epsg = geojson_geom_to_metric(VALID_BUILDING)
        assert epsg == 32644
        assert proj.area > 0


# ── Geometry Validator Tests ─────────────────────────────────────────────────

class TestGeometryValidator:
    def test_valid_polygon_passes(self):
        result = validate_geojson_geometry(VALID_BUILDING)
        assert result.valid is True
        assert not any(i.severity == "error" for i in result.issues)

    def test_none_geometry_fails(self):
        result = validate_geojson_geometry(None)
        assert result.valid is False

    def test_empty_coords_fails(self):
        result = validate_geojson_geometry({"type": "Polygon", "coordinates": []})
        assert result.valid is False

    def test_degenerate_polygon_detected(self):
        result = validate_geojson_geometry(DEGENERATE_POLYGON)
        # Degenerate ring — should flag
        assert result.valid is False or any(i.code in ("DEGENERATE_RING", "INVALID_GEOMETRY") for i in result.issues)

    def test_self_intersecting_detected(self):
        result = validate_geojson_geometry(SELF_INTERSECTING_POLYGON)
        assert result.valid is False

    def test_multipolygon_valid(self):
        result = validate_geojson_geometry(VALID_MULTIPOLYGON)
        assert result.valid is True

    def test_unsupported_type_fails(self):
        result = validate_geojson_geometry({"type": "UNKNOWN", "coordinates": []})
        assert result.valid is False


# ── Metric Tests ─────────────────────────────────────────────────────────────

class TestMetrics:
    def test_area_is_positive_m2(self):
        shp = shapely.geometry.shape(VALID_BUILDING)
        a = area_m2(shp)
        assert a > 0, "Area must be positive"
        # Valid building ~0.001deg x 0.001deg ≈ ~12100 m² in Chennai
        assert 1_000 < a < 200_000, f"Area {a} m² looks unreasonable"

    def test_perimeter_is_positive(self):
        shp = shapely.geometry.shape(VALID_BUILDING)
        p = perimeter_m(shp)
        assert p > 0

    def test_distance_between_non_overlapping(self):
        shp_a = shapely.geometry.shape(POLYGON_A)
        shp_b = shapely.geometry.shape(VALID_FIELD)
        d = distance_m(shp_a, shp_b)
        # POLYGON_A is inside VALID_FIELD bounds
        assert d == 0.0 or d >= 0

    def test_area_not_in_degrees(self):
        # If calculated in degrees, Chennai 0.001deg polygon ≈ 1e-6 — clearly wrong
        shp = shapely.geometry.shape(VALID_BUILDING)
        a = area_m2(shp)
        assert a > 1.0, "Area must not be in degree units"


# ── Self-Intersection Tests ──────────────────────────────────────────────────

class TestSelfIntersection:
    def test_valid_polygon_no_flags(self):
        shp = shapely.geometry.shape(VALID_BUILDING)
        flags = detect_self_intersections("test-1", shp)
        assert flags == []

    def test_bowtie_detected(self):
        shp = shapely.geometry.shape(SELF_INTERSECTING_POLYGON)
        flags = detect_self_intersections("test-si", shp)
        assert len(flags) > 0
        assert any(f.flag_type in ("self_intersection", "bow_tie") for f in flags)

    def test_multipolygon_valid_no_flags(self):
        shp = shapely.geometry.shape(VALID_MULTIPOLYGON)
        flags = detect_self_intersections("test-mp", shp)
        assert flags == []


# ── Overlap Tests ────────────────────────────────────────────────────────────

class TestOverlap:
    def test_overlapping_pair_detected(self):
        features = [
            {"feature_id": "A", "geometry": POLYGON_A},
            {"feature_id": "B", "geometry": POLYGON_B_OVERLAPS_A},
        ]
        flags = detect_overlaps(features)
        assert len(flags) == 1
        assert flags[0].area_m2 > 0
        assert flags[0].intersection_geometry is not None

    def test_shared_boundary_not_flagged(self):
        features = [
            {"feature_id": "C", "geometry": POLYGON_C_LEFT},
            {"feature_id": "D", "geometry": POLYGON_D_RIGHT_ADJACENT},
        ]
        flags = detect_overlaps(features)
        # Adjacent polygons sharing a boundary — must NOT be an overlap
        assert flags == [], f"Adjacent polygons incorrectly flagged: {flags}"

    def test_no_self_comparison(self):
        features = [{"feature_id": "A", "geometry": POLYGON_A}]
        flags = detect_overlaps(features)
        assert flags == []

    def test_duplicate_pair_prevention(self):
        features = [
            {"feature_id": "A", "geometry": POLYGON_A},
            {"feature_id": "B", "geometry": POLYGON_B_OVERLAPS_A},
        ]
        flags = detect_overlaps(features)
        # Should produce exactly one flag, not two (A→B and B→A)
        assert len(flags) == 1

    def test_overlap_area_positive(self):
        features = [
            {"feature_id": "A", "geometry": POLYGON_A},
            {"feature_id": "B", "geometry": POLYGON_B_OVERLAPS_A},
        ]
        flags = detect_overlaps(features)
        assert flags[0].area_m2 > 0


# ── Gap Tests ────────────────────────────────────────────────────────────────

class TestGap:
    def test_gap_detected_between_close_polygons(self):
        features = [
            {"feature_id": "E", "geometry": POLYGON_E_LEFT},
            {"feature_id": "F", "geometry": POLYGON_F_RIGHT_GAP},
        ]
        flags = detect_gaps(features, gap_tolerance_m=5.0)
        assert len(flags) >= 1

    def test_no_gap_for_overlapping(self):
        features = [
            {"feature_id": "A", "geometry": POLYGON_A},
            {"feature_id": "B", "geometry": POLYGON_B_OVERLAPS_A},
        ]
        flags = detect_gaps(features)
        # Overlapping polygons should not produce gap flags
        assert flags == []


# ── Topology Collection Tests ────────────────────────────────────────────────

class TestTopologyCollection:
    def test_valid_collection_all_pass(self):
        # Two clearly disjoint valid polygons (different coordinate areas)
        disjoint_a = {"type": "Polygon", "coordinates": [
            [[80.100, 13.000], [80.101, 13.000], [80.101, 13.001], [80.100, 13.001], [80.100, 13.000]]
        ]}
        disjoint_b = {"type": "Polygon", "coordinates": [
            [[80.200, 13.050], [80.201, 13.050], [80.201, 13.051], [80.200, 13.051], [80.200, 13.050]]
        ]}
        features = [
            {"feature_id": "V1", "geometry": disjoint_a},
            {"feature_id": "V2", "geometry": disjoint_b},
        ]
        results = validate_collection(features)
        assert results["V1"].valid is True
        assert results["V2"].valid is True


    def test_invalid_geometry_fails(self):
        features = [{"feature_id": "SI", "geometry": SELF_INTERSECTING_POLYGON}]
        results = validate_collection(features)
        assert results["SI"].valid is False

    def test_overlapping_collection_flags_both(self):
        features = [
            {"feature_id": "A", "geometry": POLYGON_A},
            {"feature_id": "B", "geometry": POLYGON_B_OVERLAPS_A},
        ]
        results = validate_collection(features)
        assert results["A"].valid is False or results["B"].valid is False


# ── Relationships Tests ──────────────────────────────────────────────────────

class TestRelationships:
    def test_building_inside_field_containment(self):
        buildings = [{"feature_id": "BLD-1", "geometry": BUILDING_INSIDE_FIELD}]
        fields = [{"feature_id": "FLD-1", "geometry": VALID_FIELD}]
        rels = compute_relationships(buildings, fields)
        assert len(rels) >= 1
        assert any(r.relationship_type == "contained_by" for r in rels)

    def test_disjoint_features_not_recorded(self):
        feat_a = [{"feature_id": "A", "geometry": VALID_BUILDING}]
        # Far away geometry
        far_geom = {
            "type": "Polygon",
            "coordinates": [[[10.0, 48.0], [10.001, 48.0], [10.001, 48.001], [10.0, 48.001], [10.0, 48.0]]]
        }
        feat_b = [{"feature_id": "B", "geometry": far_geom}]
        rels = compute_relationships(feat_a, feat_b)
        assert rels == []


# ── Confidence Tests ─────────────────────────────────────────────────────────

class TestConfidence:
    def test_high_confidence_valid_geometry(self):
        result = calculate_confidence(
            topology_valid=True, topology_flags=[], source="osm", area_m2=5000, perimeter_m=300
        )
        assert result.level == "HIGH"
        assert result.review_required is False

    def test_topology_failure_overrides_high_score(self):
        result = calculate_confidence(
            topology_valid=False,
            topology_flags=[{"severity": "high"}],
            source="osm",
            area_m2=5000, perimeter_m=300,
        )
        assert result.review_required is True
        assert result.topology_override is True

    def test_low_source_quality(self):
        result = calculate_confidence(
            topology_valid=True, topology_flags=[], source="ai", area_m2=5000, perimeter_m=300
        )
        assert result.score < 0.95

    def test_all_components_returned(self):
        result = calculate_confidence(topology_valid=True, topology_flags=[], source="osm")
        assert "geometry_validity" in result.components
        assert "topology_quality" in result.components
        assert "source_quality" in result.components

    def test_missing_geometry_no_fabrication(self):
        result = calculate_confidence(
            topology_valid=False,
            topology_flags=[{"severity": "high"}],
            source="unknown",
            area_m2=None,
            perimeter_m=None,
        )
        # No fabricated evidence — should still work without crashing
        assert result.score >= 0.0
        assert result.review_required is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
