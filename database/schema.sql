-- SQL Database Schema for CadastraVision Temporal Query Logging and Spatial Cache

-- Table to store metadata for each image segmentation run
CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_size INTEGER,
    backend TEXT,
    chunk_size INTEGER,
    overlap INTEGER,
    status TEXT, -- "processing", "success", "failed"
    duration_ms INTEGER,
    bbox TEXT, -- JSON string of WGS84 bounding box [[lat_min, lng_min], [lat_max, lng_max]]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store individual extracted building footprints/parcels
CREATE TABLE IF NOT EXISTS parcels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER NOT NULL,
    confidence REAL,
    regularity REAL,
    compactness REAL,
    vertex_count INTEGER,
    mask_fill_ratio REAL,
    tile_x INTEGER,
    tile_y INTEGER,
    geometry TEXT NOT NULL, -- GeoJSON Geometry String
    FOREIGN KEY(query_id) REFERENCES queries(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_parcels_query_id ON parcels(query_id);
CREATE INDEX IF NOT EXISTS idx_queries_created_at ON queries(created_at DESC);
