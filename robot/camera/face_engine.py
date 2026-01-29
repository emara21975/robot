import insightface
import numpy as np
import os

class FaceEngine:
    def __init__(self, det_size=(640, 640)):
        # Initialize FaceAnalysis (retinaface + arcface)
        # providers=['CPUExecutionProvider'] is safer for Pi unless onnxruntime-gpu is installed
        self.app = insightface.app.FaceAnalysis(
            name="buffalo_s", 
            providers=["CPUExecutionProvider"]
        )
        self.app.prepare(ctx_id=0, det_size=det_size)

    def detect(self, frame):
        """
        Detect faces in the frame.
        Returns a list of Face objects (bbox, kps, det_score, landmark_3d_68, pose, embedding, gender, age)
        """
        if frame is None:
            return []
        
        try:
            faces = self.app.get(frame)
            return faces
        except Exception as e:
            print(f"Face Detection Error: {e}")
            return []
