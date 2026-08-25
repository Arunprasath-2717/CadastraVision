import os
import sqlite3
import json
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger("DatabaseManager")

class DatabaseManager:
    def __init__(self, db_path: str = None) -> None:
        if db_path is None:
            # Default to database directory of SIH model
            db_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(db_dir, "cadastra.db")
        self.db_path = db_path
        self.initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_db(self) -> None:
        """Loads and executes the schema.sql file if the database is not initialized."""
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(db_dir, exist_ok=True)
        
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
        if not os.path.exists(schema_path):
            logger.error(f"Schema file not found at {schema_path}")
            return

        with open(schema_path, "r") as f:
            schema_sql = f.read()

        conn = self._get_connection()
        try:
            conn.executescript(schema_sql)
            conn.commit()
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
        finally:
            conn.close()

    def create_query(
        self,
        filename: str,
        file_size: Optional[int] = None,
        backend: Optional[str] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        bbox: Optional[str] = None,
    ) -> int:
        """Creates a new query log entry with status 'processing'."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO queries (filename, file_size, backend, chunk_size, overlap, bbox, status)
                VALUES (?, ?, ?, ?, ?, ?, 'processing')
                """,
                (filename, file_size, backend, chunk_size, overlap, bbox)
            )
            conn.commit()
            query_id = cursor.lastrowid
            logger.info(f"Created query log ID {query_id} for {filename}")
            return query_id
        except Exception as e:
            logger.error(f"Error creating query log: {e}")
            raise e
        finally:
            conn.close()

    def update_query_status(self, query_id: int, status: str, duration_ms: int) -> None:
        """Updates the status and duration of a query log entry."""
        conn = self._get_connection()
        try:
            conn.execute(
                """
                UPDATE queries
                SET status = ?, duration_ms = ?
                WHERE id = ?
                """,
                (status, duration_ms, query_id)
            )
            conn.commit()
            logger.info(f"Updated query ID {query_id} to status: {status} in {duration_ms}ms")
        except Exception as e:
            logger.error(f"Error updating query status: {e}")
            raise e
        finally:
            conn.close()

    def insert_parcels(self, query_id: int, features: List[Dict[str, Any]]) -> None:
        """Inserts a list of GeoJSON features as parcels associated with the query ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            for feat in features:
                geometry = json.dumps(feat.get("geometry", {}))
                props = feat.get("properties", {})
                confidence = props.get("confidence")
                
                breakdown = props.get("confidence_breakdown", {})
                regularity = breakdown.get("regularity")
                compactness = breakdown.get("compactness")
                vertex_count = breakdown.get("vertex_count")
                mask_fill_ratio = breakdown.get("mask_fill_ratio")
                
                tile_coords = props.get("tile_coords")
                tile_x, tile_y = None, None
                if tile_coords:
                    if isinstance(tile_coords, list) and len(tile_coords) > 0:
                        tile_x = tile_coords[0][0] if isinstance(tile_coords[0], list) else tile_coords[0]
                        tile_y = tile_coords[0][1] if isinstance(tile_coords[0], list) else tile_coords[1]
                    elif isinstance(tile_coords, tuple) or isinstance(tile_coords, list):
                        tile_x = tile_coords[0]
                        tile_y = tile_coords[1]

                cursor.execute(
                    """
                    INSERT INTO parcels (
                        query_id, confidence, regularity, compactness,
                        vertex_count, mask_fill_ratio, tile_x, tile_y, geometry
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        query_id, confidence, regularity, compactness,
                        vertex_count, mask_fill_ratio, tile_x, tile_y, geometry
                    )
                )
            conn.commit()
            logger.info(f"Successfully inserted {len(features)} parcels for query ID {query_id}")
        except Exception as e:
            logger.rollback()
            logger.error(f"Error inserting parcels: {e}")
            raise e
        finally:
            conn.close()

    def get_queries(self) -> List[Dict[str, Any]]:
        """Returns all queries with count of parcels and average confidence."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT q.id, q.filename, q.file_size, q.backend, q.chunk_size, q.overlap, 
                       q.status, q.duration_ms, q.bbox, q.created_at,
                       COUNT(p.id) AS parcel_count,
                       ROUND(AVG(p.confidence), 2) AS avg_confidence
                FROM queries q
                LEFT JOIN parcels p ON q.id = p.query_id
                GROUP BY q.id
                ORDER BY q.created_at DESC
                """
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Error fetching queries: {e}")
            return []
        finally:
            conn.close()

    def get_query(self, query_id: int) -> Optional[Dict[str, Any]]:
        """Returns the query details and its full GeoJSON feature collection."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Fetch query metadata
            cursor.execute("SELECT * FROM queries WHERE id = ?", (query_id,))
            query_row = cursor.fetchone()
            if not query_row:
                return None
            
            query_data = dict(query_row)

            # Fetch parcels
            cursor.execute("SELECT * FROM parcels WHERE query_id = ?", (query_id,))
            parcel_rows = cursor.fetchall()

            features = []
            for r in parcel_rows:
                geom = json.loads(r["geometry"])
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "id": r["id"],
                        "confidence": r["confidence"],
                        "confidence_breakdown": {
                            "regularity": r["regularity"],
                            "compactness": r["compactness"],
                            "vertex_count": r["vertex_count"],
                            "mask_fill_ratio": r["mask_fill_ratio"],
                        },
                        "tile_coords": [r["tile_x"], r["tile_y"]] if r["tile_x"] is not None else None
                    }
                })

            geojson = {
                "type": "FeatureCollection",
                "features": features,
                "metadata": {
                    "pii_compliance": "Zero-PII. Operates purely on pixel rasters and vector geometry.",
                    "backend": query_data["backend"],
                    "query_id": query_id,
                    "filename": query_data["filename"],
                    "bbox": json.loads(query_data["bbox"]) if query_data["bbox"] else None
                }
            }
            query_data["geojson"] = geojson
            return query_data
        except Exception as e:
            logger.error(f"Error fetching query ID {query_id}: {e}")
            return None
        finally:
            conn.close()

    def delete_query(self, query_id: int) -> bool:
        """Deletes a query and its parcels from the database."""
        conn = self._get_connection()
        try:
            # Foreign keys cascade deletion will take care of parcels
            conn.execute("DELETE FROM queries WHERE id = ?", (query_id,))
            conn.commit()
            logger.info(f"Deleted query ID {query_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting query: {e}")
            return False
        finally:
            conn.close()
