
import cv2
import time

def test_camera(index):
    print(f"Testing camera index {index}...")
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"❌ Failed to open camera index {index}")
        return False
    
    # Try to read a few frames
    print("Camera opened. Reading frames...")
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            print(f"✅ Frame {i+1} captured successfully. Resolution: {frame.shape}")
            if i == 5:
                cv2.imwrite(f"test_camera_{index}.jpg", frame)
                print(f"📸 Saved snapshot to test_camera_{index}.jpg")
            time.sleep(0.1)
        else:
            print(f"⚠️ Frame {i+1} failed to read.")
            
    cap.release()
    return True

if __name__ == "__main__":
    print("=== Camera Diagnostic Tool ===")
    
    # Test index 0
    if not test_camera(0):
        # Test index 1 if 0 fails
        test_camera(1)
        
    print("=== Test Complete ===")
