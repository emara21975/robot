
try:
    from picamera2 import Picamera2
    _PICAMERA_AVAILABLE = True
except ImportError:
    _PICAMERA_AVAILABLE = False

import cv2
import time
import numpy as np

class PicameraAdapter:
    """
    A wrapper for Picamera2 that mimics the basic interface of cv2.VideoCapture
    so it can be used as a drop-in replacement in the robot code.
    """
    def __init__(self, index=0, width=640, height=480):
        self.is_running = False
        self.picam2 = None
        
        if not _PICAMERA_AVAILABLE:
            print("❌ Picamera2 library not found. PicameraAdapter will not work.")
            return

        try:
            print("Initializing Picamera2...")
            self.picam2 = Picamera2()
            
            config = self.picam2.create_preview_configuration(
                main={"format": "BGR888", "size": (width, height)}
            )
            self.picam2.configure(config)
            self.picam2.start()
            self.is_running = True
            time.sleep(1) # Warmup
            print("✅ Picamera2 initialized and started.")
            
        except Exception as e:
            print(f"❌ Failed to initialize Picamera2: {e}")
            self.is_running = False

    def isOpened(self):
        return self.is_running

    def read(self):
        """
        Returns (True, frame) if successful, (False, None) otherwise.
        Matches cv2.VideoCapture.read() signature.
        """
        if not self.is_running or self.picam2 is None:
            return False, None
            
        try:
            # capture_array waits for a frame and returns it
            frame = self.picam2.capture_array()
            if frame is None or frame.size == 0:
                return False, None
            return True, frame
        except Exception as e:
            print(f"⚠️ Picamera read error: {e}")
            return False, None

    def release(self):
        if self.picam2 and self.is_running:
            self.picam2.stop()
            self.picam2 = None
        self.is_running = False
        print("Picamera2 released.")

    def set(self, prop, value):
        # Stub to preventing crashing if cv2 props are set
        pass

    def get(self, prop):
        # Stub
        return 0.0

if __name__ == "__main__":
    # Self-test
    cam = PicameraAdapter()
    if cam.isOpened():
        ret, frame = cam.read()
        if ret:
            print(f"Captured frame shape: {frame.shape}")
        cam.release()
