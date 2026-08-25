import os
import sys
import json
import time

# Set up paths to import the segmentation module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from ai.segmentation import CadastralSegmentationPipeline

def run_full_pipeline():
    print("==================================================")
    print("Running Roboflow Backend on Full 8000x6000 GeoTIFF")
    print("==================================================")

    tiff_path = "C:/Users/ros78/Downloads/6a8750b7510aa7ee517f3ab9.tif"
    if not os.path.exists(tiff_path):
        print(f"[ERROR] Could not find the file: {tiff_path}", file=sys.stderr)
        return

    # Initialize the pipeline with the roboflow backend
    print("Initializing CadastralSegmentationPipeline with 'roboflow' backend...")
    pipeline = CadastralSegmentationPipeline(backend="roboflow")
    
    start_time = time.time()
    
    try:
        # Run process_geotiff (which divides the image into 512x512 tiles)
        print("Starting windowed GeoTIFF inference. This will process 512x512 tiles...")
        geojson_out = pipeline.process_geotiff(tiff_path, chunk_size=512, overlap=64)
        
        duration = time.time() - start_time
        print(f"\n[SUCCESS] Completed in {duration:.2f} seconds!")
        
        features = geojson_out.get("features", [])
        print(f"Total building shapes extracted: {len(features)}")
        
        # Save output GeoJSON
        output_json_path = "tests/roboflow_full_output.geojson"
        with open(output_json_path, "w") as f:
            json.dump(geojson_out, f, indent=2)
        print(f"Saved full GeoJSON output to: {output_json_path}")
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline run failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_full_pipeline()
