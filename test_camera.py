
import cv2
import time
import os
import sys

# Ensure we can import from the robot package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from robot.camera.adapter import PicameraAdapter, _PICAMERA_AVAILABLE

def test_camera(index=0):
    print(f"\n--- Testing Camera with PicameraAdapter ---")
    
    if not _PICAMERA_AVAILABLE:
        print("❌ Picamera2 library is NOT installed. Cannot proceed.")
        print("Please run: sudo apt install -y python3-picamera2")
        return False

    # Use our new adapter instead of cv2.VideoCapture
    cap = PicameraAdapter(index=index)

    if not cap.isOpened():
        print(f"❌ Failed to open camera via PicameraAdapter")
        return False
    
    print("Reading frames...")
    success_count = 0
    for i in range(10):
        try:
            ret, frame = cap.read()
            if ret:
                print(f"✅ Frame {i+1} captured. Shape: {frame.shape}")
                success_count += 1
                if i == 0:
                    cv2.imwrite(f"debug_cam_picamera.jpg", frame)
            else:
                print(f"⚠️ Frame {i+1} failed.")
                time.sleep(0.2)
        except KeyboardInterrupt:
            break
            
    cap.release()
    return success_count > 0

if __name__ == "__main__":
    print("=== Picamera2 Diagnostic Tool ===")
    
    if test_camera():
        print("\n✅ SUCCESS: Camera is working with Picamera2!")
    else:
        print("\n❌ FAILURE: Could not capture frames.")
        print("Run 'python test_picamera_raw.py' to verify the hardware separately.")
