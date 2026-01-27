
import cv2
import threading
import time
import numpy as np

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        
        # Check if opened
        if not self.cap.isOpened():
            print("❌ Camera Error: Could not open video device 0. Trying 1...")
            self.cap = cv2.VideoCapture(1)
            if not self.cap.isOpened():
                print("❌ Camera Error: Could not open video device 1 either.")
                self.frame = None
            else:
                print("✅ Camera opened on device 1")
        else:
             print("✅ Camera opened on device 0")

        # Set lower resolution for performance on Pi
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.is_running = True
        self.current_frame = None
        self.lock = threading.Lock()

        # Start background thread
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.is_running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.current_frame = frame
                else:
                    print("⚠️ Camera warning: Can't receive frame (stream end?). Exiting ...")
                    # Try to reconnect?
                    time.sleep(2)
            else:
                print("⚠️ Camera not opened, retrying...")
                time.sleep(2)
                
            time.sleep(0.01) # Small sleep to reduce CPU usage

    def get_frame(self):
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None

    def stop(self):
        self.is_running = False
        if self.thread.is_alive():
            self.thread.join()
        if self.cap:
            self.cap.release()

# Global Camera Singleton
try:
    camera = Camera()
except Exception as e:
    print(f"❌ Critical Camera Init Error: {e}")
    camera = None
