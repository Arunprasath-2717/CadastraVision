import os
import sys
import numpy as np
import cv2
import rasterio

# Set up paths to import the segmentation module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from ai.segmentation import segment_with_roboflow

def test_real_image():
    print("==================================================")
    print("Running Roboflow Test on Real Project GeoTIFF Image")
    print("==================================================")

    tiff_path = "C:/Users/ros78/Downloads/6a8750b7510aa7ee517f3ab9.tif"
    if not os.path.exists(tiff_path):
        print(f"[ERROR] Could not find the real TIFF file at: {tiff_path}", file=sys.stderr)
        return

    # 1. Load and crop a 1024x1024 region from the center
    print(f"Reading GeoTIFF image: {tiff_path}...")
    temp_crop_path = "tests/roboflow_real_crop.jpg"
    os.makedirs(os.path.dirname(temp_crop_path), exist_ok=True)

    try:
        img = cv2.imread(tiff_path)
        if img is None:
            raise ValueError(f"Failed to read image using OpenCV: {tiff_path}")
        h, w = img.shape[:2]
        print(f"Original dimensions: {w}x{h}")
        
        # Crop 1024x1024 region from center
        win_size = 1024
        x_offset = (w - win_size) // 2
        y_offset = (h - win_size) // 2
        crop = img[y_offset:y_offset+win_size, x_offset:x_offset+win_size]
        
        cv2.imwrite(temp_crop_path, crop)
        print(f"Cropped 1024x1024 center region and saved to: {temp_crop_path}")

    except Exception as e:
        print(f"[ERROR] Failed to read/crop TIFF: {e}", file=sys.stderr)
        return

    # 2. Run segment_with_roboflow
    visual_output_path = "tests/roboflow_real_output.png"
    print("\nSending crop to Roboflow workflow inference...")
    try:
        predictions = segment_with_roboflow(
            image_input=crop,
            api_key="Z1p45q88sPkLrUdN289r",
            workspace="ragul-wwpql",
            workflow_id="map-aoz8d",
            save_visual_path=visual_output_path,
            confidence=0.25
        )
        
        print("\n--- Inference Output Results ---")
        print(f"Total detections returned: {len(predictions)}")
        for idx, pred in enumerate(predictions):
            coords_preview = str(pred['points'][:3]) + "..." if len(pred['points']) > 3 else str(pred['points'])
            print(f"[{idx+1}] Class: {pred['class']} | Confidence: {pred['confidence']:.2f} | Polygon Points: {coords_preview}")
        
        if os.path.exists(visual_output_path):
            print(f"\n[SUCCESS] Visualized outline saved to: {visual_output_path}")
            # Copy to artifacts directory so user can see it
            artifact_dest = "C:/Users/ros78/.gemini/antigravity-ide/brain/698ae07a-8870-4c2b-b78d-df6a04813c25/roboflow_real_output.png"
            import shutil
            shutil.copyfile(visual_output_path, artifact_dest)
            print(f"Copied visualization to conversation artifacts: {artifact_dest}")
        else:
            print("\n[WARNING] Visualized output image was not found.")

    except Exception as e:
        print(f"\n[ERROR] Test run failed: {e}", file=sys.stderr)
        
    finally:
        # Cleanup temporary cropped file
        if os.path.exists(temp_crop_path):
            os.remove(temp_crop_path)
            print(f"Cleaned up temporary cropped file: {temp_crop_path}")

if __name__ == "__main__":
    test_real_image()
