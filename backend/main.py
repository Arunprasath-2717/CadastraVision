import os
import sys
import time
import json
import logging
import tempfile
import shutil
import cv2
import numpy as np
import rasterio
import pyproj
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Setup paths to import database and ai-service modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "ai-service"))

from database.db_manager import DatabaseManager
from ai.segmentation import CadastralSegmentationPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CadastralBackend")

app = FastAPI(
    title="CadastraVision Backend Service",
    description="Backend API Gateway with SQLite Temporal Logging and GIS Visualization integration.",
    version="1.0.0"
)

# CORS Setup for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database manager
db = DatabaseManager()

# Static directories for serving visualization PNGs
STATIC_DIR = os.path.join(current_dir, "static")
VIS_DIR = os.path.join(STATIC_DIR, "visualizations")
os.makedirs(VIS_DIR, exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/health")
def health_check():
    """Returns service health status and DB check."""
    try:
        queries = db.get_queries()
        db_status = "connected"
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "pii_compliance": "Zero-PII. Citizens names or tax identifiers are not collected."
    }

@app.post("/api/segment")
async def segment_geotiff(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    backend: Optional[str] = Form(None),
    chunk_size: int = Form(512),
    overlap: int = Form(64)
):
    """
    Accepts GeoTIFF upload, runs segmentation, logs to SQLite database,
    saves visualized high-contrast PNG, and returns the GeoJSON features.
    """
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise HTTPException(status_code=400, detail="Invalid chunk_size or overlap parameters.")

    filename = file.filename if file.filename else "uploaded_raster.tif"
    temp_tiff_path = os.path.join(tempfile.gettempdir(), f"backend_{os.getpid()}_{filename}")

    # Start timing
    start_time = time.time()

    # Save uploaded file bytes to temp path
    try:
        logger.info(f"Saving uploaded GeoTIFF to temp: {temp_tiff_path}")
        with open(temp_tiff_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(temp_tiff_path)
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        if os.path.exists(temp_tiff_path):
            os.remove(temp_tiff_path)
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")

    # Create coordinate bounds and retrieve metadata from geotiff before processing
    bbox_str = None
    try:
        with rasterio.open(temp_tiff_path) as src:
            left, bottom, right, top = src.bounds
            src_crs = src.crs
            
            if src_crs:
                src_crs_str = src_crs.to_string()
                if "4326" not in src_crs_str:
                    try:
                        transformer = pyproj.Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
                        lng_min, lat_min = transformer.transform(left, bottom)
                        lng_max, lat_max = transformer.transform(right, top)
                    except Exception as e:
                        logger.warning(f"Failed to reproject bounds: {e}")
                        lng_min, lat_min, lng_max, lat_max = left, bottom, right, top
                else:
                    lng_min, lat_min, lng_max, lat_max = left, bottom, right, top
            else:
                lng_min, lat_min, lng_max, lat_max = left, bottom, right, top
            
            # WGS84 bounding box format: [[lat_min, lng_min], [lat_max, lng_max]]
            bbox_str = json.dumps([[lat_min, lng_min], [lat_max, lng_max]])
    except Exception as e:
        logger.warning(f"Failed to parse GeoTIFF metadata bounds: {e}")

    # 1. Create a processing query entry in database
    resolved_backend = backend if backend else os.environ.get("CADASTRAL_SEG_BACKEND", "samgeo")
    query_id = db.create_query(
        filename=filename,
        file_size=file_size,
        backend=resolved_backend,
        chunk_size=chunk_size,
        overlap=overlap,
        bbox=bbox_str
    )

    # 2. Execute segmentation pipeline
    try:
        logger.info(f"Instantiating segmentation pipeline on backend '{resolved_backend}'")
        pipeline = CadastralSegmentationPipeline(backend=resolved_backend)
        geojson_out = pipeline.process_geotiff(temp_tiff_path, chunk_size=chunk_size, overlap=overlap)
        
        # 3. Create high-contrast visual image tracing (Yellow border outlines BGR=(0, 255, 255), thickness=3px)
        logger.info("Generating high-contrast visualization overlay image")
        with rasterio.open(temp_tiff_path) as src:
            count = src.count
            if count >= 3:
                tile_data = src.read([1, 2, 3])
                img = np.transpose(tile_data, (1, 2, 0))
            else:
                tile_data = src.read(1)
                img = np.stack([tile_data, tile_data, tile_data], axis=-1)
                
            img_rgb = pipeline._preprocess_image(img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

            src_crs = src.crs
            project_back = None
            if src_crs and "4326" not in src_crs.to_string():
                try:
                    transformer = pyproj.Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
                    project_back = transformer.transform
                except Exception as e:
                    logger.warning(f"Could not build inverse CRS transformer: {e}")

            features = geojson_out.get("features", [])
            for feature in features:
                geom = feature.get("geometry")
                if not geom or geom.get("type") != "Polygon":
                    continue
                
                coords = geom["coordinates"][0]
                pixel_pts = []
                for pt in coords:
                    if project_back:
                        x, y = project_back(pt[0], pt[1])
                    else:
                        x, y = pt[0], pt[1]
                    
                    col, row = ~src.transform * (x, y)
                    pixel_pts.append([int(col), int(row)])

                pts_array = np.array(pixel_pts, dtype=np.int32)
                # Pure BGR Yellow = (0, 255, 255), thickness = 3px
                cv2.polylines(img_bgr, [pts_array], isClosed=True, color=(0, 255, 255), thickness=3)

            # Save visual image
            vis_png_filename = f"{query_id}.png"
            vis_png_path = os.path.join(VIS_DIR, vis_png_filename)
            cv2.imwrite(vis_png_path, img_bgr)
            logger.info(f"Saved visualization PNG to {vis_png_path}")

        # 4. Insert extracted parcels into the database
        db.insert_parcels(query_id, features)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        db.update_query_status(query_id, "success", duration_ms)
        
        # Build clean output mapping
        result = db.get_query(query_id)
        return result

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        db.update_query_status(query_id, "failed", duration_ms)
        logger.error(f"Error processing segmentation for query ID {query_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Segmentation processing failed: {str(e)}")
        
    finally:
        # Schedule cleanup of temp GeoTIFF to save disk space
        if os.path.exists(temp_tiff_path):
            background_tasks.add_task(os.remove, temp_tiff_path)
            logger.info(f"Scheduled cleanup for temp GeoTIFF: {temp_tiff_path}")

@app.get("/api/history")
def get_query_history():
    """Lists history of query runs, including run dates, file sizes, and average parcel confidence."""
    return db.get_queries()

@app.get("/api/history/{query_id}")
def get_query_details(query_id: int):
    """Retrieves full GeoJSON features and details of a past query."""
    data = db.get_query(query_id)
    if not data:
        raise HTTPException(status_code=404, detail="Query run not found.")
    return data

@app.delete("/api/history/{query_id}")
def delete_query_run(query_id: int):
    """Deletes the query entry, associated parcels, and physical visualization PNG files."""
    # Delete physical visualization PNG file
    vis_png_path = os.path.join(VIS_DIR, f"{query_id}.png")
    if os.path.exists(vis_png_path):
        try:
            os.remove(vis_png_path)
            logger.info(f"Deleted physical visualization file: {vis_png_path}")
        except Exception as e:
            logger.error(f"Failed to delete visualization image: {e}")
            
    success = db.delete_query(query_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete query from database.")
    return {"status": "success", "detail": f"Query ID {query_id} deleted."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
