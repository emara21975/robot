from picamera2 import Picamera2
import cv2
import time
import numpy as np

try:
    print("Initializing Picamera2...")
    picam2 = Picamera2()

    print("Configuring camera (640x480 BGR)...")
    config = picam2.create_preview_configuration(
        main={"format": "BGR888", "size": (640, 480)}
    )
    picam2.configure(config)

    print("Starting camera...")
    picam2.start()
    time.sleep(2) # Warmup

    print("Camera started successfully. Capturing 10 frames...")

    for i in range(10):
        # capture_array() returns a numpy array (image)
        frame = picam2.capture_array()
        
        if frame is not None and frame.size > 0:
            print(f"✅ Frame {i+1} captured. Shape: {frame.shape}")
            # If we are in a GUI environment, show it. Otherwise just print.
            # cv2.imshow("Picamera2 Test", frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
        else:
            print(f"⚠️ Frame {i+1} empty/failed.")
        
        time.sleep(0.1)

    picam2.stop()
    print("Test Complete. Picamera2 is working.")
    # cv2.destroyAllWindows()

except ModuleNotFoundError:
    print("❌ Error: 'picamera2' module not found.")
    print("Please install it using: sudo apt install -y python3-picamera2")
except Exception as e:
    print(f"❌ An error occurred: {e}")
