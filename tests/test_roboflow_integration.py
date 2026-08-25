import os
import sys
import numpy as np
import cv2

# Set up paths to import the segmentation module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from ai.segmentation import segment_with_roboflow

def run_roboflow_test():
    print("==================================================")
    print("Starting Roboflow Integration Verification Test")
    print("==================================================")

    # 1. Create a synthetic test image with a mock building shape (white square on dark background)
    test_image_path = "tests/synthetic_roboflow_test.jpg"
    os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
    
    # 512x512 grayscale/RGB image
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    # Draw some roof-like structure
    cv2.rectangle(img, (150, 150), (350, 350), (200, 200, 200), -1) # Outer wall
    cv2.rectangle(img, (170, 170), (330, 330), (100, 100, 100), -1) # Inner roof
    
    cv2.imwrite(test_image_path, img)
    print(f"Generated synthetic test image: {test_image_path}")

    # 2. Run the segment_with_roboflow function
    visual_output_path = "tests/roboflow_visual_test.png"
    try:
        predictions = segment_with_roboflow(
            image_input=test_image_path,
            api_key="Z1p45q88sPkLrUdN289r",
            workspace="ragul-wwpql",
            workflow_id="map-aoz8d",
            save_visual_path=visual_output_path
        )
        
        print("\n--- Inference Output Results ---")
        print(f"Total detections returned: {len(predictions)}")
        for idx, pred in enumerate(predictions):
            coords_preview = str(pred['points'][:3]) + "..." if len(pred['points']) > 3 else str(pred['points'])
            print(f"[{idx+1}] Class: {pred['class']} | Confidence: {pred['confidence']:.2f} | Polygons Points: {coords_preview}")
        
        if os.path.exists(visual_output_path):
            print(f"\n[SUCCESS] Visualized outline saved to: {visual_output_path}")
        else:
            print("\n[WARNING] Visualized output image was not found.")

    except Exception as e:
        print(f"\n[ERROR] Test run failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    finally:
        # Cleanup synthetic test file
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print(f"Cleaned up test file: {test_image_path}")

if __name__ == "__main__":
    run_roboflow_test()
