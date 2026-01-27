
import cv2
import numpy as np
from flask import Response
from robot.camera.camera import camera

# Load Haar Cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def get_placeholder_frame(text="NO CAMERA SIGNAL"):
    """Generate a black frame with text."""
    blank_image = np.zeros((480, 640, 3), np.uint8)
    cv2.putText(blank_image, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 
                1, (0, 0, 255), 2, cv2.LINE_AA)
    
    # Add timestamp
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    cv2.putText(blank_image, ts, (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, (255, 255, 255), 1)
                
    return blank_image

def gen_frames():
    while True:
        if camera:
            frame = camera.get_frame()
        else:
            frame = None

        if frame is None:
            # Yield a placeholder frame instead of stopping
            frame = get_placeholder_frame("Wait for Camera...")
            
            # Encode
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Slow down loop if no camera
            import time
            time.sleep(1.0)
            continue
        
        try:
            # Face Detection Overlay (Lightweight)
            # Use gray for detection to be faster
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Draw rectangles
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Draw Status
            status_text = "Status: Monitoring"
            if len(faces) > 0:
                status_text = f"Status: Face Detected ({len(faces)})"
            
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
        except Exception as e:
            # In case of overlay error, print but still yield frame
            print(f"Overlay Error: {e}")

        # Encoding frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def video_stream():
    """Returns a Flask Response with the video stream"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
