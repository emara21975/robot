
import threading
import time
import numpy as np
# Try importing Picamera2 and libcamera controls
try:
    from picamera2 import Picamera2
    try:
        from libcamera import controls
    except ImportError:
        controls = None # Fallback if controls cannot be imported directly
    _PICAMERA_AVAILABLE = True
except ImportError:
    _PICAMERA_AVAILABLE = False
    print("❌ Picamera2 library not found. Camera will be disabled.")

class Camera:
    def __init__(self, width=1280, height=720):
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        self.picam2 = None
        
        if _PICAMERA_AVAILABLE:
            try:
                print(f"Initializing Picamera2 with resolution {width}x{height}...")
                self.picam2 = Picamera2()
                
                # Create configuration with FrameRate control
                config = self.picam2.create_preview_configuration(
                    main={"format": "BGR888", "size": (width, height)},
                    controls={"FrameRate": 30}
                )
                self.picam2.configure(config)
                
                # Apply ISP Controls if available
                if controls:
                    print("⚙️ Applying advanced ISP controls...")
                    try:
                        self.picam2.set_controls({
                            controls.AeEnable: True,
                            controls.AwbEnable: True,
                            controls.AeMeteringMode: controls.AeMeteringModeEnum.CentreWeighted,
                            controls.NoiseReductionMode: controls.NoiseReductionModeEnum.HighQuality,
                            controls.Sharpness: 1.2,
                            controls.Contrast: 1.1,
                            controls.Brightness: 0.0,
                            controls.Saturation: 1.1
                        })
                    except Exception as e_ctrl:
                        print(f"⚠️ Failed to set some ISP controls: {e_ctrl}")
                else:
                     print("⚠️ libcamera.controls not available, skipping advanced tuning.")

                self.picam2.start()
                self.running = True
                
                # Start background update thread
                self.thread = threading.Thread(target=self._update, daemon=True)
                self.thread.start()
                
                print("✅ Camera started with Picamera2 (HD + ISP Tuned)")
            except Exception as e:
                print(f"❌ Failed to initialize Picamera2: {e}")
                self.running = False
        else:
            print("⚠️ Running in headless/mock mode (No Picamera2)")

    def _update(self):
        """Background thread to capture frames continuously."""
        while self.running:
            try:
                # capture_array blocks until a new frame is ready
                frame = self.picam2.capture_array()
                if frame is not None and frame.size > 0:
                    with self.lock:
                        self.frame = frame
                # No sleep needed here as capture_array is blocking/synced to framerate
            except Exception as e:
                print(f"⚠️ Camera capture error: {e}")
                time.sleep(1)

    def get_frame(self):
        """Return the latest frame."""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
        return None

    def stop(self):
        self.running = False
        if self.picam2:
            self.picam2.stop()
        print("Camera stopped.")

# Global Singleton
try:
    camera = Camera()
except Exception as e:
    print(f"❌ Critical Camera Init Error: {e}")
    camera = None
