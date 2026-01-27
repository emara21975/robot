# -*- coding: utf-8 -*-
"""
نظام التعرّف على الوجه للروبوت الطبي (النسخة الحديثة - InsightFace)
يعتمد على FaceEngine و FaceDB
"""

import time
import numpy as np

# Lazy imports handled inside functions to avoid circular deps or startup lag
shared_camera = None

try:
    from robot.camera.camera import camera as shared_camera
except ImportError:
    shared_camera = None
    print("⚠️ فشل استيراد الكاميرا المشتركة")

MAX_VERIFY_SECONDS = 10
MAX_ATTEMPTS = 15  # Increased attempts since InsightFace is faster

def check_face_auth(frame=None):
    """
    التحقق من هوية الشخص أمام الكاميرا using InsightFace.
    Args:
        frame: إطار الصورة (اختياري).
    Returns:
        (bool, str): (هل تم التعرف؟, الرسالة)
    """
    # 1. Get Camera Frame
    if frame is None:
        if shared_camera is None:
            return False, "خطأ: الكاميرا غير متصلة بالنظام"
        frame = shared_camera.get_frame()

    if frame is None:
        return False, "تعذر الحصول على صورة من الكاميرا"

    # 2. Get Engine & DB (Lazy Load)
    try:
        from robot.camera.stream import get_face_engine
        from robot.camera.face_db import match_face, load_faces
        
        engine = get_face_engine()
        # Note: In a real optimized scenario, we shouldn't load_faces every time if it's slow,
        # but get_face_engine handles some caching. 
        # For auth, we specifically want the latest DB, but let's trust the stream module's cache/refresh logic for now 
        # or just load it here if needed. 
        # Better: stream.py maintains 'faces_db' global.
        from robot.camera.stream import faces_db 
        
        if not engine:
            return False, "محرك الوجوه غير جاهز"
            
        if not faces_db:
             # Try allowing if no faces registered? (Dev mode)
             # return True, "وضغ التطوير: لا توجد وجوه مسجلة"
             return False, "لا توجد وجوه مسجلة في النظام"

    except ImportError:
         return False, "خطأ في استيراد مكتبات التعرف على الوجه"

    # 3. Detect & Match
    try:
        faces = engine.detect(frame)
        
        if len(faces) == 0:
            return False, "لم يتم العثور على وجه"
            
        # Check all faces
        for face in faces:
            name, score = match_face(face.embedding, faces_db, threshold=0.5)
            if name != "Unknown":
                return True, f"تم التعرف على: {name}"
                
        return False, "وجه غير معروف"

    except Exception as e:
        print(f"❌ خطأ تقني في check_face_auth: {e}")
        return False, "خطأ في المعالجة"

def verify_with_timeout():
    """التحقق مع مهلة زمنية ومحاولات متعددة"""
    start = time.time()
    attempts = 0
    
    print(f"🕵️ بدء التحقق من الوجه (Timeout={MAX_VERIFY_SECONDS}s)...")

    while (time.time() - start) < MAX_VERIFY_SECONDS:
        attempts += 1
        
        is_verified, msg = check_face_auth()
        
        if is_verified:
            print(f"✅ {msg}")
            return {"verified": True, "reason": "FACE_MATCH", "message": msg}
        
        # Wait a bit between attempts (InsightFace is fast, but let's not spam)
        time.sleep(0.3)

    return {"verified": False, "reason": "TIMEOUT_OR_NO_MATCH", "message": "انتهت المهلة: لم يتم التعرف على الوجه"}
