
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


# Initialize Face Engine (Lazy Load to prevent startup delay)
face_engine = None
face_engine_error = None
faces_db = {}
last_db_refresh = 0

# Shared state for access by other modules (app.py)
last_recognized_face = {
    "name": "Unknown",
    "score": 0.0,
    "time": 0
}

def get_last_face():
    """Returns the last recognized face and its timestamp."""
    return last_recognized_face

def get_face_engine():
    global face_engine, faces_db, last_db_refresh
    if face_engine is None:
        try:
            print("🚀 Loading Face Engine...")
            from robot.camera.face_engine import FaceEngine
            from robot.camera.face_db import load_faces
            face_engine = FaceEngine()
            faces_db = load_faces()
            print("✅ Face Engine Loaded.")
        except Exception as e:
            print(f"❌ Error loading FaceEngine: {e}")
            global face_engine_error
            face_engine_error = str(e)
            face_engine = False # valid but disabled
    
    # Reload DB occasionally (e.g. every 10 seconds)
    import time
    if time.time() - last_db_refresh > 10:
        if face_engine:
             from robot.camera.face_db import load_faces
             faces_db = load_faces()
             last_db_refresh = time.time()
             
    return face_engine

def get_face_engine_error():
    """Returns the initialization error if any."""
    return face_engine_error

def force_reload_faces():
    """Force reloading the face database on the next frame."""
    global last_db_refresh
    last_db_refresh = 0
    print("🔄 Face DB reload requested.")

def gen_frames():
    import time
    from robot.camera.face_db import match_face
    
    while True:
        if camera:
            frame = camera.get_frame()
        else:
            frame = None

        if frame is None:
            # Yield a placeholder frame instead of stopping
            frame = get_placeholder_frame("Wait for Camera...")
            
            # Encode
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1.0)
            continue
        
        try:
            # Face Recognition Overlay
            engine = get_face_engine()
            
            # Frame Skipping Logic
            global frame_count
            if 'frame_count' not in globals(): frame_count = 0
            frame_count += 1
            
            # Use cached faces for 4 frames, update on 5th
            if 'cached_faces' not in globals(): cached_faces = []
            
            if engine:
                # Run detection every 5 frames
                if frame_count % 5 == 0:
                     cached_faces = engine.detect(frame)
                
                faces = cached_faces
                
                for face in faces:
                    # Bounding Box (cast to int)
                    x1, y1, x2, y2 = map(int, face.bbox)
                    

                    # Recognition
                    name, score = match_face(face.embedding, faces_db, threshold=0.5)
                    
                    # UPDATE GLOBAL STATE (For app.py)
                    if name != "Unknown":
                        last_recognized_face["name"] = name
                        last_recognized_face["score"] = float(score)
                        last_recognized_face["time"] = time.time()
                    
                    # Color: Green for known, Red for Unknown
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    
                    # Draw Box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw Name Label
                    label = f"{name} ({score:.2f})"
                    
                    # Background for text
                    cv2.rectangle(frame, (x1, y1 - 30), (x2, y1), color, -1)
                    
                    # Text
                    cv2.putText(
                        frame,
                        label,
                        (x1 + 5, y1 - 7),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )

        except Exception as e:
            # In case of overlay error, print but still yield frame
            print(f"Overlay Error: {e}")

        # Encoding frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def video_stream():
    """Returns a Flask Response with the video stream"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
