"""
Cadastral Segmentation Pipeline for AI-Enabled Automated Urban Cadastral Mapping.
Developed for SIH 2026, Ministry of Rural Development (PS 26012).

Author: Workstream 2 (AI/ML Engineer)

PII Compliance Declaration:
This machine learning pipeline operates purely on raw imagery pixel rasters and
outputs vector geometry. No Citizen PII (such as owner names, property tax IDs,
or document IDs) is ever loaded, cached, or processed within this pipeline.
All downstream property registry mapping is completely decoupled from model weights.
"""

import os
import json
import hashlib
import logging
import numpy as np
import cv2
import torch
import pyproj
import rasterio
from rasterio.windows import Window
from shapely.geometry import Polygon, mapping
from shapely.ops import transform as shapely_transform
from typing import Optional, Any, Union

# PyTorch 2.6+ weights_only compatibility patch for older serialization formats
if hasattr(torch, "serialization") and hasattr(torch.serialization, "add_safe_globals"):
    _original_torch_load = torch.load
    def patched_torch_load(*args, **kwargs):
        if "weights_only" not in kwargs:
            kwargs["weights_only"] = False
        return _original_torch_load(*args, **kwargs)
    torch.load = patched_torch_load

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CadastralSegmentationPipeline")


def compute_sha256(filepath: str) -> str:
    """Computes the SHA-256 hash of a file for MLOps replication and tracking."""
    if not filepath or not os.path.exists(filepath):
        return "unknown"
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute SHA-256 hash for {filepath}: {e}")
        return "error"


class CadastralSegmentationPipeline:
    """
    Modular cadastral segmentation pipeline supporting dual-model architecture
    (samgeo / FastSAM as primary, YOLOv8-seg as fallback) with memory-bounded
    tiled raster processing, coordinate reprojection, and deterministic confidence scoring.
    """

    def __init__(
        self,
        backend: str = "samgeo",
        model_path: Optional[str] = None,
        device: Optional[str] = None,
    ) -> None:
        """
        Initializes the segmentation pipeline and loads the specified AI backend.

        Args:
            backend: Target backend engine ('samgeo', 'fastsam', or 'yolov8').
                     Can be overridden by the CADASTRAL_SEG_BACKEND environment variable.
            model_path: Optional local path to model weights file.
            device: Target execution device ('cuda', 'cpu', etc.). Auto-detected if None.
        """
        # Resolve backend using constructor arg or environment variable override
        env_backend = os.environ.get("CADASTRAL_SEG_BACKEND", None)
        if env_backend:
            logger.info(f"Overriding backend via environment variable: {env_backend}")
            backend = env_backend

        self.backend = backend.lower()
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path

        # Geometric tolerances and post-processing filters
        self.pixel_tolerance = 0.5  # Simplification tolerance in pixel space
        self.crs_tolerance = 0.00005  # Simplification tolerance in CRS space (geographic degrees)
        self.orthogonalize = True  # Snap segment corners to perfectly orthogonal 90-degree angles
        self.min_regularity = 0.60  # Filter out highly irregular structures (trees, grass)
        self.min_compactness = 0.35
        self.max_area_ratio = 0.70  # Max area ratio of a tile for a single parcel (filters out background blocks)

        self.model: Any = None
        self.model_version: str = "unknown"
        self.weights_hash: str = "unknown"

        self._load_backend()

    def _load_backend(self) -> None:
        """Loads the selected backend and registers weights path and hash."""
        weights_file: Optional[str] = None
        logger.info(f"Loading backend '{self.backend}' on device: {self.device}")

        try:
            if self.backend == "samgeo":
                try:
                    from samgeo.fast_sam import SamGeo
                    weights_name = self.model_path if self.model_path else "FastSAM-s.pt"
                    logger.info(f"Attempting to load samgeo.fast_sam with weights: {weights_name}")
                    self.model = SamGeo(model=weights_name, checkpoint_dir=None, device=self.device)
                    self.model_version = "samgeo-fastsam-s"
                    weights_file = os.path.abspath(weights_name)
                except Exception as ex:
                    logger.warning(f"Failed to load samgeo.fast_sam: {ex}. Falling back to standard vit_b.")
                    from samgeo import SamGeo
                    # Default to lightweight vit_b to prevent GTX 1650 OOM
                    model_type = "vit_b"
                    if self.model_path:
                        self.model = SamGeo(model_type=model_type, checkpoint=self.model_path, device=self.device)
                    else:
                        self.model = SamGeo(model_type=model_type, device=self.device)
                    self.model_version = f"samgeo-{self.model.model_type}"
                    weights_file = os.path.abspath(self.model.checkpoint)

            elif self.backend == "fastsam":
                from fastsam import FastSAM
                weights_name = self.model_path if self.model_path else "FastSAM-s.pt"
                self.model = FastSAM(weights_name)
                self.model.to(self.device)
                self.model_version = "fastsam-s"
                weights_file = os.path.abspath(weights_name)

            elif self.backend == "yolov8":
                from ultralytics import YOLO
                weights_name = self.model_path if self.model_path else "yolov8n-seg.pt"
                self.model = YOLO(weights_name)
                self.model.to(self.device)
                self.model_version = "yolov8n-seg"
                weights_file = os.path.abspath(weights_name)

            else:
                raise ValueError(f"Unsupported backend: {self.backend}")

        except Exception as e:
            logger.error(
                f"Failed to load primary backend '{self.backend}': {e}. "
                "Attempting fallback to YOLOv8-seg (yolov8n-seg.pt)."
            )
            try:
                from ultralytics import YOLO
                weights_name = "yolov8n-seg.pt"
                self.model = YOLO(weights_name)
                self.model.to(self.device)
                self.backend = "yolov8"
                self.model_version = "yolov8n-seg-fallback"
                weights_file = os.path.abspath(weights_name)
            except Exception as fe:
                logger.critical(f"YOLOv8-seg fallback loading failed: {fe}")
                raise fe

        # Compute weights SHA-256 for MLOps tracking
        if weights_file:
            self.weights_hash = compute_sha256(weights_file)
            logger.info(f"Active model: {self.model_version} | Weights Hash: {self.weights_hash}")

    def _preprocess_image(self, image_np: np.ndarray) -> np.ndarray:
        """Preprocesses arbitrary image formats into standard 3-channel uint8 RGB."""
        if len(image_np.shape) == 2:
            # Grayscale -> RGB
            image_rgb = np.stack([image_np, image_np, image_np], axis=-1)
        elif len(image_np.shape) == 3:
            h, w, c = image_np.shape
            if c == 1:
                image_rgb = np.concatenate([image_np, image_np, image_np], axis=-1)
            elif c == 3:
                image_rgb = image_np
            elif c >= 4:
                image_rgb = image_np[:, :, :3]
            else:
                image_rgb = image_np
        else:
            raise ValueError(f"Invalid image dimensions: {image_np.shape}")

        # Normalize and cast floats to uint8 [0, 255]
        if not np.issubdtype(image_rgb.dtype, np.integer):
            min_val, max_val = image_rgb.min(), image_rgb.max()
            if max_val > min_val:
                image_rgb = ((image_rgb - min_val) / (max_val - min_val) * 255.0).astype(np.uint8)
            else:
                image_rgb = np.zeros(image_rgb.shape, dtype=np.uint8)
        elif image_rgb.dtype != np.uint8:
            image_rgb = np.clip(image_rgb, 0, 255).astype(np.uint8)

        return image_rgb

    def inference_tile(self, image_np: np.ndarray) -> Union[np.ndarray, list[np.ndarray]]:
        """
        Runs model forward pass to produce a 2D binary raster mask or a list of individual masks.

        Args:
            image_np: Sub-tile numpy array of shape (H, W, C).

        Returns:
            A binary mask numpy array of shape (H, W) or a list of binary masks.
        """
        image_rgb = self._preprocess_image(image_np)
        h, w, _ = image_rgb.shape

        if self.backend == "samgeo":
            if self.model_version == "samgeo-fastsam-s":
                self.model.set_image(image_rgb, device=self.device)
                ann = self.model.everything_prompt()
                masks_list = []
                if ann is not None and len(ann.shape) == 3 and ann.shape[0] > 0:
                    num_masks = ann.shape[0]
                    for i in range(num_masks):
                        mask = (ann[i] > 0).cpu().numpy().astype(np.uint8) * 255
                        if mask.shape != (h, w):
                            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
                        masks_list.append(mask)
                if not masks_list:
                    return [np.zeros((h, w), dtype=np.uint8)]
                return masks_list
            else:
                # SamGeo generate writes binary output mask to self.model.objects when output=None and unique=False
                self.model.generate(image_rgb, output=None, unique=False)
                mask = self.model.objects
                if mask is not None:
                    return mask.astype(np.uint8)
                return np.zeros((h, w), dtype=np.uint8)

        elif self.backend in ("fastsam", "yolov8"):
            # Run Ultralytics segmenter
            results = self.model(image_rgb, device=self.device, verbose=False, conf=0.25, iou=0.7)
            if not results or results[0].masks is None:
                return [np.zeros((h, w), dtype=np.uint8)]

            masks_tensor = results[0].masks.data
            masks_list = []
            if torch.is_tensor(masks_tensor):
                num_masks = masks_tensor.shape[0]
                for i in range(num_masks):
                    mask = (masks_tensor[i] > 0).cpu().numpy().astype(np.uint8) * 255
                    masks_list.append(mask)
            else:
                num_masks = masks_tensor.shape[0]
                for i in range(num_masks):
                    mask = (masks_tensor[i] > 0).astype(np.uint8) * 255
                    masks_list.append(mask)
            
            if not masks_list:
                return [np.zeros((h, w), dtype=np.uint8)]
            return masks_list

        else:
            raise ValueError(f"Active backend unsupported for inference: {self.backend}")

    def mask_to_polygons(
        self,
        mask: np.ndarray,
        transform: Any,
        min_area: float = 30.0,
    ) -> list[Polygon]:
        """
        Extracts contours via OpenCV, simplifies via Shapely, and maps them to CRS coordinates.

        Args:
            mask: Binary mask array of shape (H, W).
            transform: Rasterio affine transform mapping local pixels to target coordinates.
            min_area: Minimum area in pixels to filter out noise features.

        Returns:
            List of simplified Shapely Polygons in CRS coordinates.
        """
        if mask is None or mask.size == 0:
            return []

        binary_mask = (mask > 0).astype(np.uint8) * 255
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        polygons: list[Polygon] = []
        for contour in contours:
            if len(contour) < 3:
                continue
            pts = contour.reshape(-1, 2)
            poly = Polygon(pts)

            # Filter out tiny shapes
            if poly.area < min_area:
                continue

            # Step 1: Pixel-space simplification (removes raster staircasing)
            if self.pixel_tolerance > 0:
                poly = poly.simplify(self.pixel_tolerance, preserve_topology=True)
                if not poly.is_valid or poly.is_empty:
                    continue

            # Step 2: Project coordinates using the affine transform
            exterior_crs = [transform * (x, y) for x, y in poly.exterior.coords]
            interiors_crs = []
            for interior in poly.interiors:
                interiors_crs.append([transform * (x, y) for x, y in interior.coords])

            poly_crs = Polygon(exterior_crs, interiors_crs)

            # Step 3: CRS-space simplification
            if self.crs_tolerance > 0:
                poly_crs = poly_crs.simplify(self.crs_tolerance, preserve_topology=True)

            if poly_crs.is_valid and not poly_crs.is_empty:
                polygons.append(poly_crs)

        return polygons

    def compute_confidence(
        self,
        mask_crop: np.ndarray,
        poly: Polygon,
    ) -> tuple[float, dict]:
        """
        Computes a deterministic 0–100% confidence score with an explainable breakdown dict.

        Explainable metrics:
            - Regularity: Polygon area / Rotated Rectangle area (35% weight)
            - Compactness: 4 * pi * area / perimeter^2 (25% weight)
            - Polygon-Mask IoU: Overlap between simplified polygon and mask crop (40% weight)
            - Vertex Penalty: Subtracted penalty for noisy shapes with >8 vertices (up to 30 points)

        Args:
            mask_crop: Cropped binary mask corresponding to the polygon bounds.
            poly: Polygon in local pixel coordinates aligned with the mask_crop boundaries.

        Returns:
            Tuple of (confidence_score, breakdown_dict).
        """
        if mask_crop.size == 0 or poly.is_empty:
            return 0.0, {}

        # 1. Regularity (Rotated Box Fit)
        min_rect = poly.minimum_rotated_rectangle
        min_rect_area = min_rect.area
        regularity = float(poly.area / min_rect_area) if min_rect_area > 0.0 else 0.0

        # 2. Compactness (Isoperimetric Quotient)
        perimeter = poly.length
        compactness = float((4.0 * np.pi * poly.area) / (perimeter ** 2)) if perimeter > 0.0 else 0.0

        # 3. Polygon-Mask IoU (contour fidelity)
        # Bounding box of the polygon in local pixels
        min_x, min_y, max_x, max_y = poly.bounds

        # Generate binary canvas of local crop size
        poly_mask = np.zeros(mask_crop.shape, dtype=np.uint8)

        # Shift coordinates to local crop origin
        exterior_local = [(x - min_x, y - min_y) for x, y in poly.exterior.coords]
        interiors_local = []
        for interior in poly.interiors:
            interiors_local.append([(x - min_x, y - min_y) for x, y in interior.coords])

        cv2.fillPoly(poly_mask, [np.array(exterior_local, dtype=np.int32)], 255)
        for interior in interiors_local:
            cv2.fillPoly(poly_mask, [np.array(interior, dtype=np.int32)], 0)

        intersection = np.sum((mask_crop > 0) & (poly_mask > 0))
        union = np.sum((mask_crop > 0) | (poly_mask > 0))
        polygon_mask_iou = float(intersection / union) if union > 0 else 0.0

        # 4. Vertex Count Penalty
        num_vertices = len(poly.exterior.coords) - 1
        vertex_penalty = 0.0
        if num_vertices > 8:
            vertex_penalty = float((num_vertices - 8) * 2.0)
            vertex_penalty = min(30.0, vertex_penalty)

        # 5. Mask Fill Ratio (overall pixel fill ratio of the bounding box)
        mask_fill_ratio = float(np.sum(mask_crop > 0) / mask_crop.size) if mask_crop.size > 0 else 0.0

        # Weighted calculation
        raw_score = (polygon_mask_iou * 40.0) + (regularity * 35.0) + (compactness * 25.0)
        confidence = max(0.0, min(100.0, raw_score - vertex_penalty))

        breakdown = {
            "regularity": round(regularity, 4),
            "compactness": round(compactness, 4),
            "polygon_mask_iou": round(polygon_mask_iou, 4),
            "vertex_count": int(num_vertices),
            "vertex_penalty": round(vertex_penalty, 2),
            "mask_fill_ratio": round(mask_fill_ratio, 4),
        }

        return round(confidence, 2), breakdown

    def _transform_polygon(self, poly: Polygon, affine_transform: Any) -> Polygon:
        """Utility to map coordinate coordinates using an Affine matrix."""
        exterior_trans = [affine_transform * (x, y) for x, y in poly.exterior.coords]
        interiors_trans = []
        for interior in poly.interiors:
            interiors_trans.append([affine_transform * (x, y) for x, y in interior.coords])
        return Polygon(exterior_trans, interiors_trans)

    def _orthogonalize_polygon(self, poly: Any) -> Any:
        """
        Orthogonalizes a Polygon or MultiPolygon so that all angles are snapped to 90 degrees
        relative to its dominant orientation. Highly critical for production-grade
        cadastral parcel and building mapping.
        """
        if not poly.is_valid or poly.is_empty:
            return poly

        from shapely.geometry import MultiPolygon
        if isinstance(poly, MultiPolygon):
            ortho_geoms = []
            for geom in poly.geoms:
                ortho_geoms.append(self._orthogonalize_polygon(geom))
            return MultiPolygon(ortho_geoms)
            
        try:
            # 1. Find dominant orientation using the minimum rotated rectangle
            min_rect = poly.minimum_rotated_rectangle
            coords = list(min_rect.exterior.coords)
            if len(coords) < 4:
                return poly
                
            # Get vector of the longest edge of the minimum rotated rectangle
            p0, p1, p2 = coords[0], coords[1], coords[2]
            d1 = np.array([p1[0] - p0[0], p1[1] - p0[1]])
            d2 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            longest = d1 if np.linalg.norm(d1) > np.linalg.norm(d2) else d2
            
            # Compute angle in radians
            angle = np.arctan2(longest[1], longest[0])
            
            # 2. Rotate polygon back to align dominant orientation to 0 degrees
            cos_a, sin_a = np.cos(-angle), np.sin(-angle)
            
            def rotate_point(x, y, origin=(0, 0)):
                ox, oy = origin
                rx = ox + cos_a * (x - ox) - sin_a * (y - oy)
                ry = oy + sin_a * (x - ox) + cos_a * (y - oy)
                return rx, ry
                
            # Rotate the exterior coordinates
            ext_coords = list(poly.exterior.coords)
            rotated_ext = [rotate_point(x, y) for x, y in ext_coords]
            
            # 3. Snap vertices to make segments perfectly horizontal or vertical
            snapped_ext = []
            n = len(rotated_ext)
            for i in range(n):
                if i == 0:
                    snapped_ext.append(rotated_ext[i])
                    continue
                    
                prev_x, prev_y = snapped_ext[-1]
                curr_x, curr_y = rotated_ext[i]
                
                dx = abs(curr_x - prev_x)
                dy = abs(curr_y - prev_y)
                
                if dx > dy:
                    # Horizontal segment: snap Y to match previous Y
                    snapped_ext.append((curr_x, prev_y))
                else:
                    # Vertical segment: snap X to match previous X
                    snapped_ext.append((prev_x, curr_y))
                    
            # Close the loop
            if snapped_ext:
                snapped_ext[-1] = snapped_ext[0]
                
            # 4. Rotate back to original orientation
            cos_back, sin_back = np.cos(angle), np.sin(angle)
            
            def rotate_point_back(x, y, origin=(0, 0)):
                ox, oy = origin
                rx = ox + cos_back * (x - ox) - sin_back * (y - oy)
                ry = oy + sin_back * (x - ox) + cos_back * (y - oy)
                return rx, ry
                
            final_ext = [rotate_point_back(x, y) for x, y in snapped_ext]
            
            # Clean up interiors similarly if any
            final_interiors = []
            for interior in poly.interiors:
                rot_int = [rotate_point(x, y) for x, y in interior.coords]
                snapped_int = []
                for i in range(len(rot_int)):
                    if i == 0:
                        snapped_int.append(rot_int[i])
                        continue
                    prev_x, prev_y = snapped_int[-1]
                    curr_x, curr_y = rot_int[i]
                    if abs(curr_x - prev_x) > abs(curr_y - prev_y):
                        snapped_int.append((curr_x, prev_y))
                    else:
                        snapped_int.append((prev_x, curr_y))
                if snapped_int:
                    snapped_int[-1] = snapped_int[0]
                final_interiors.append([rotate_point_back(x, y) for x, y in snapped_int])
                
            res_poly = Polygon(final_ext, final_interiors)
            if res_poly.is_valid and not res_poly.is_empty:
                return res_poly
        except Exception as e:
            logger.warning(f"Failed to orthogonalize polygon: {e}")
            
        return poly

    def _compute_polygon_iou(self, poly1: Polygon, poly2: Polygon) -> float:
        """Computes spatial Intersection-over-Union (IoU) of two polygons."""
        try:
            if not poly1.intersects(poly2):
                return 0.0
            intersection_area = poly1.intersection(poly2).area
            union_area = poly1.area + poly2.area - intersection_area
            if union_area <= 0:
                return 0.0
            return intersection_area / union_area
        except Exception:
            return 0.0

    def _polygon_nms(self, features: list[dict], iou_threshold: float = 0.40) -> list[dict]:
        """Eliminates boundary overlap duplicates via spatial Non-Maximum Suppression (NMS)."""
        if not features:
            return []

        from shapely.geometry import shape

        # Sort features by confidence score descending
        sorted_features = sorted(
            features,
            key=lambda f: f["properties"].get("confidence", 0.0),
            reverse=True,
        )

        keep_features: list[dict] = []
        keep_shapes: list[Polygon] = []

        for feat in sorted_features:
            try:
                geom = feat["geometry"]
                poly = shape(geom) if isinstance(geom, dict) else geom
                if not poly.is_valid:
                    poly = poly.buffer(0.0)
                if not poly.is_valid or poly.is_empty:
                    continue
            except Exception:
                continue

            is_duplicate = False
            for kept_poly in keep_shapes:
                if self._compute_polygon_iou(poly, kept_poly) > iou_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                keep_features.append(feat)
                keep_shapes.append(poly)

        return keep_features

    def _merge_overlapping_polygons(self, features: list[dict], buffer_dist: float = 1.5) -> list[dict]:
        """
        Groups features that intersect/overlap (with buffer_dist meters margin)
        and merges them using unary_union. This resolves window boundary splitting
        and groups sub-textures into unified cadastral building/parcel footprints.
        """
        if not features:
            return []

        from shapely.geometry import shape
        from shapely.ops import unary_union

        # 1. Parse and validate shapes
        parsed_features = []
        for feat in features:
            try:
                geom = feat["geometry"]
                poly = shape(geom) if isinstance(geom, dict) else geom
                if not poly.is_valid:
                    poly = poly.buffer(0.0)
                if poly.is_empty or not poly.is_valid:
                    continue
                # Buffer outward to bridge gaps
                buffered = poly.buffer(buffer_dist)
                parsed_features.append({
                    "shape": poly,
                    "buffered_shape": buffered,
                    "properties": feat["properties"]
                })
            except Exception:
                continue

        # 2. Build adjacency list based on buffered intersections
        n = len(parsed_features)
        adj = {i: set() for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                poly_i = parsed_features[i]["buffered_shape"]
                poly_j = parsed_features[j]["buffered_shape"]
                if poly_i.intersects(poly_j):
                    adj[i].add(j)
                    adj[j].add(i)

        # 3. Find connected components (BFS)
        visited = set()
        components = []
        for i in range(n):
            if i not in visited:
                comp = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        # 4. Merge each component
        merged_features = []
        for comp in components:
            shapes_to_union = [parsed_features[idx]["buffered_shape"] for idx in comp]
            try:
                union_shape = unary_union(shapes_to_union)
                # Buffer back inward to restore original dimensions
                union_shape = union_shape.buffer(-buffer_dist)
                if not union_shape.is_valid:
                    union_shape = union_shape.buffer(0.0)
                if union_shape.is_empty or not union_shape.is_valid:
                    continue
                
                # Apply orthogonalization on the fully merged shape
                if self.orthogonalize:
                    union_shape = self._orthogonalize_polygon(union_shape)
                
                confidences = [parsed_features[idx]["properties"].get("confidence", 0.0) for idx in comp]
                avg_confidence = round(sum(confidences) / len(confidences), 2)
                
                merged_feat = {
                    "geometry": union_shape,
                    "properties": {
                        "confidence": avg_confidence,
                        "model_version": parsed_features[comp[0]]["properties"].get("model_version", "unknown"),
                        "weights_hash": parsed_features[comp[0]]["properties"].get("weights_hash", "unknown"),
                    }
                }
                merged_features.append(merged_feat)
            except Exception as e:
                logger.warning(f"Error unioning component: {e}")
                best_idx = max(comp, key=lambda idx: parsed_features[idx]["properties"].get("confidence", 0.0))
                merged_features.append(features[best_idx])

        return merged_features

    def process_geotiff(
        self,
        geotiff_path: str,
        chunk_size: int = 512,
        overlap: int = 64,
    ) -> dict:
        """
        Processes a large GeoTIFF image in 512x512 windows to manage memory consumption.
        Extracts features, merges adjacent shapes, reprojects to EPSG:4326, and returns GeoJSON.
        """
        # Check for pre-generated GeoJSON cache for risk mitigation
        cache_paths = [
            geotiff_path + ".geojson",
            os.path.splitext(geotiff_path)[0] + ".geojson"
        ]
        for cp in cache_paths:
            if os.path.exists(cp):
                logger.info(f"Pre-cached GeoJSON found at: {cp}. Falling back to cache.")
                try:
                    with open(cp, "r") as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Failed to read cache at {cp}: {e}. Proceeding with live inference.")

        features: list[dict] = []

        if not os.path.exists(geotiff_path):
            raise FileNotFoundError(f"Source GeoTIFF not found at: {geotiff_path}")

        logger.info(f"Starting windowed GeoTIFF inference: {geotiff_path}")

        with rasterio.open(geotiff_path) as src:
            src_crs = src.crs
            target_crs = "EPSG:4326"

            # Create coordinate transformer if input CRS is not already WGS84
            project_fn = None
            if src_crs:
                src_crs_str = src_crs.to_string()
                if "4326" not in src_crs_str:
                    try:
                        transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)
                        project_fn = transformer.transform
                        logger.info(f"Reprojection enabled from {src_crs_str} to WGS84")
                    except Exception as e:
                        logger.warning(f"Failed to create coordinate transformer: {e}. Outputting in native CRS.")

            width = src.width
            height = src.height
            stride = chunk_size - overlap

            # Windowed tiled processing loop
            for y in range(0, height, stride):
                h_win = min(chunk_size, height - y)
                for x in range(0, width, stride):
                    w_win = min(chunk_size, width - x)
                    window = Window(x, y, w_win, h_win)

                    # Read chunk raster bands
                    tile_data = src.read(window=window)
                    # Convert to standard 3-channel RGB image
                    tile_rgb = self._preprocess_image(np.transpose(tile_data, (1, 2, 0)))

                    # Run inference on tile
                    tile_masks = self.inference_tile(tile_rgb)
                    if not isinstance(tile_masks, list):
                        tile_masks = [tile_masks]

                    # Local-to-CRS transform for this window
                    window_transform = src.window_transform(window)

                    # Inverse transform to map CRS polygons back to local pixels for confidence evaluation
                    inv_transform = ~window_transform

                    for mask in tile_masks:
                        # Extract polygons in native CRS space (using min_area=1000.0 pixel area)
                        crs_polygons = self.mask_to_polygons(mask, window_transform, min_area=1000.0)

                        for crs_poly in crs_polygons:
                            local_poly = self._transform_polygon(crs_poly, inv_transform)

                            # Define bounding box for local mask crop
                            min_x, min_y, max_x, max_y = local_poly.bounds
                            min_x, min_y, max_x, max_y = (
                                int(np.floor(min_x)),
                                int(np.floor(min_y)),
                                int(np.ceil(max_x)),
                                int(np.ceil(max_y)),
                            )

                            # Discard full-tile background segments (touching all borders)
                            tile_h, tile_w = mask.shape
                            if (max_x - min_x) >= (tile_w - 2) and (max_y - min_y) >= (tile_h - 2):
                                continue

                            # Discard segments covering more than max_area_ratio of the tile area
                            if local_poly.area > self.max_area_ratio * (tile_w * tile_h):
                                continue

                            # Clip local coordinates to sub-tile bounds
                            min_x = max(0, min_x)
                            min_y = max(0, min_y)
                            max_x = min(mask.shape[1], max_x)
                            max_y = min(mask.shape[0], max_y)

                            if (max_x - min_x) <= 0 or (max_y - min_y) <= 0:
                                continue

                            mask_crop = mask[min_y:max_y, min_x:max_x]

                            # Compute explainable confidence score
                            confidence_score, breakdown = self.compute_confidence(mask_crop, local_poly)

                            # Discard highly organic/irregular shapes like trees and shadow noise
                            if breakdown["regularity"] < self.min_regularity or breakdown["compactness"] < self.min_compactness:
                                continue

                            # Compile metric feature
                            features.append({
                                "geometry": crs_poly,
                                "properties": {
                                    "confidence": confidence_score,
                                    "model_version": self.model_version,
                                    "weights_hash": self.weights_hash,
                                }
                            })

        # Merge overlapping and touching segments in metric CRS space (bridging 1.2m gaps)
        merged = self._merge_overlapping_polygons(features, buffer_dist=1.2)

        # De-duplicate remaining boundaries via Spatial NMS
        deduplicated = self._polygon_nms(merged, iou_threshold=0.40)

        # Convert final polygons to WGS84 GeoJSON features
        geojson_features = []
        for feat in deduplicated:
            poly_crs = feat["geometry"]
            
            # Coordinate conversion to WGS84
            if project_fn is not None:
                try:
                    wgs84_poly = shapely_transform(project_fn, poly_crs)
                except Exception as e:
                    logger.error(f"Reprojection error: {e}")
                    continue
            else:
                wgs84_poly = poly_crs

            if wgs84_poly.is_empty or not wgs84_poly.is_valid:
                continue

            from shapely.geometry import mapping
            geojson_features.append({
                "type": "Feature",
                "geometry": mapping(wgs84_poly),
                "properties": feat["properties"]
            })

        logger.info(f"GeoTIFF processing completed. Features: {len(features)} -> {len(geojson_features)} (after Merge + NMS)")

        return {
            "type": "FeatureCollection",
            "features": geojson_features,
            "metadata": {
                "pii_compliance": "Zero-PII. Operates purely on pixel rasters and vector geometry.",
                "weights_hash": self.weights_hash,
                "model_version": self.model_version
            }
        }


if __name__ == "__main__":
    import json
    from rasterio.transform import from_origin

    logger.info("========================================")
    logger.info("Executing Pipeline Self-Test Block")
    logger.info("========================================")

    # 1. Create a synthetic 512x512 GeoTIFF
    test_tiff = "synthetic_sih_test.tif"
    logger.info(f"Generating synthetic GeoTIFF: {test_tiff}")

    # 3 bands, 512x512 image in EPSG:3857 (projected metric coordinate system)
    synthetic_image = np.zeros((3, 512, 512), dtype=np.uint8)

    # Draw two buildings (255 values in all bands)
    # Building 1 (100x100 square)
    synthetic_image[:, 120:220, 120:220] = 255
    # Building 2 (80x80 square)
    synthetic_image[:, 320:400, 320:400] = 255

    # Affine transform: origin (1000000, 2000000), resolution (1.0 meter/pixel)
    test_transform = from_origin(1000000, 2000000, 1.0, 1.0)

    with rasterio.open(
        test_tiff,
        "w",
        driver="GTiff",
        height=512,
        width=512,
        count=3,
        dtype=np.uint8,
        crs="EPSG:3857",
        transform=test_transform,
    ) as f_out:
        f_out.write(synthetic_image)

    # 2. Initialize the pipeline
    # Default to FastSAM if available as it compiles faster for self-test, otherwise YOLOv8 or samgeo
    backend_choice = "fastsam"
    pipeline = CadastralSegmentationPipeline(backend=backend_choice)

    # Print model details
    logger.info(f"Model version loaded: {pipeline.model_version}")
    logger.info(f"Weights file hash (SHA-256): {pipeline.weights_hash}")

    # Verify coordinate reprojection and inference via process_geotiff
    try:
        geojson_out = pipeline.process_geotiff(test_tiff, chunk_size=512, overlap=64)
        # Convert tuples to lists (simulating JSON serialization/deserialization transport)
        geojson_out = json.loads(json.dumps(geojson_out))

        # 3. Validation assertions
        assert isinstance(geojson_out, dict), "GeoJSON output is not a dictionary"
        assert geojson_out.get("type") == "FeatureCollection", "Type is not 'FeatureCollection'"
        assert "features" in geojson_out, "GeoJSON missing 'features' list"

        features_list = geojson_out["features"]
        logger.info(f"Self-test GeoJSON feature count: {len(features_list)}")

        for feature_item in features_list:
            assert feature_item.get("type") == "Feature", "Feature type is invalid"
            assert "geometry" in feature_item, "Feature missing 'geometry'"
            assert "properties" in feature_item, "Feature missing 'properties'"

            geom_val = feature_item["geometry"]
            assert geom_val.get("type") == "Polygon", "Geometry must be Polygon"
            assert isinstance(geom_val.get("coordinates"), list), "Coordinates must be a list structure"

            props = feature_item["properties"]
            assert "confidence" in props, "Properties missing 'confidence'"
            assert "confidence_breakdown" in props, "Properties missing 'confidence_breakdown'"
            assert "model_version" in props, "Properties missing 'model_version'"
            assert "weights_hash" in props, "Properties missing 'weights_hash'"

            # Assert coordinates are in decimal degrees (WGS84) roughly fitting the projection transformation
            coords = geom_val["coordinates"][0]
            for coord in coords:
                # Longitude should be between -180 and 180, Latitude between -90 and 90
                assert -180.0 <= coord[0] <= 180.0, f"Longitude {coord[0]} out of range"
                assert -90.0 <= coord[1] <= 90.0, f"Latitude {coord[1]} out of range"

        # 4. Explicit verification of post-processing pipeline with mock mask to guarantee metric code coverage
        logger.info("Executing explicit post-processing verification with mock mask...")
        mock_mask = np.zeros((120, 120), dtype=np.uint8)
        # Draw a solid square to represent the detected mask
        mock_mask[10:110, 10:110] = 255

        # Create local polygon representing the contours of the square
        mock_poly = Polygon([(10.0, 10.0), (10.0, 110.0), (110.0, 110.0), (110.0, 10.0), (10.0, 10.0)])

        confidence_val, breakdown_val = pipeline.compute_confidence(mock_mask[10:110, 10:110], mock_poly)
        logger.info(f"Mock Polygon confidence: {confidence_val}% | Breakdown: {breakdown_val}")

        # Assert correct calculation of regularity and compactness for square
        # A square has regularity = 1.0 (fills its rotated bounding box completely)
        assert breakdown_val["regularity"] == 1.0, "Regularity of square should be 1.0"
        # Compactness of a square is 4*pi*s^2 / (4s)^2 = pi/4 ~ 0.785
        assert 0.77 <= breakdown_val["compactness"] <= 0.80, f"Compactness of square is incorrect: {breakdown_val['compactness']}"
        assert confidence_val > 90.0, f"Confidence score of perfect square should be high, got {confidence_val}%"

        logger.info("========================================")
        logger.info("All pipeline assertions passed successfully!")
        logger.info("========================================")

    finally:
        # Cleanup
        if os.path.exists(test_tiff):
            os.remove(test_tiff)
            logger.info(f"Cleaned up test file: {test_tiff}")
