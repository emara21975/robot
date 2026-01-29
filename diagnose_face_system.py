#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 تشخيص شامل لنظام التعرف على الوجوه
"""

import sys
import os

print("=" * 60)
print("🔍 تشخيص نظام التعرف على الوجوه")
print("=" * 60)

# 1. فحص المكتبات الأساسية
print("\n1️⃣ فحص المكتبات الأساسية:")
print("-" * 60)

libraries = {
    'cv2': 'OpenCV',
    'numpy': 'NumPy',
    'onnxruntime': 'ONNX Runtime',
    'insightface': 'InsightFace'
}

missing_libs = []

for module, name in libraries.items():
    try:
        lib = __import__(module)
        version = getattr(lib, '__version__', 'غير معروف')
        print(f"✅ {name}: {version}")
    except ImportError as e:
        print(f"❌ {name}: غير مثبت - {e}")
        missing_libs.append(name)

if missing_libs:
    print(f"\n⚠️  المكتبات المفقودة: {', '.join(missing_libs)}")
    print("\n🛠️  للتثبيت:")
    print("   bash install_face_libs.sh")
    sys.exit(1)

# 2. فحص محرك التعرف على الوجوه
print("\n2️⃣ فحص محرك التعرف على الوجوه:")
print("-" * 60)

try:
    from insightface.app import FaceAnalysis
    print("⏳ تحميل النموذج buffalo_l...")
    
    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    print("✅ المحرك جاهز!")
    print(f"   النماذج المحملة: {len(app.models)} نموذج")
    
except Exception as e:
    print(f"❌ فشل تحميل المحرك: {e}")
    print("\n🛠️  الحل:")
    print("   1. تأكد من اتصال الإنترنت (لتحميل النموذج أول مرة)")
    print("   2. شغل: bash install_face_libs.sh")
    sys.exit(1)

# 3. فحص الكاميرا
print("\n3️⃣ فحص الكاميرا:")
print("-" * 60)

try:
    import cv2
    camera = cv2.VideoCapture(0)
    
    if camera.isOpened():
        ret, frame = camera.read()
        if ret:
            h, w = frame.shape[:2]
            print(f"✅ الكاميرا تعمل!")
            print(f"   الدقة: {w}x{h}")
            
            # اختبار الكشف
            faces = app.get(frame)
            print(f"   الوجوه المكتشفة: {len(faces)}")
            
            if len(faces) > 0:
                print("   ✅ تم رصد وجه - النظام يعمل بشكل كامل!")
            else:
                print("   ⚠️  لم يتم رصد وجه (تأكد من النظر للكاميرا)")
        else:
            print("❌ فشل قراءة الإطار من الكاميرا")
        camera.release()
    else:
        print("❌ الكاميرا غير متاحة")
        print("   تأكد من توصيل الكاميرا أو تمكينها في raspi-config")
        
except Exception as e:
    print(f"❌ خطأ في الكاميرا: {e}")

# 4. فحص ملفات المشروع
print("\n4️⃣ فحص ملفات المشروع:")
print("-" * 60)

required_files = [
    'app.py',
    'robot/camera/stream.py',
    'robot/camera/face_engine.py',
    'robot/camera/face_db.py'
]

for file_path in required_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path} - مفقود!")

# 5. فحص مجلد الوجوه
print("\n5️⃣ فحص مجلد الوجوه:")
print("-" * 60)

faces_dir = "robot/faces"
if os.path.exists(faces_dir):
    files = os.listdir(faces_dir)
    npy_files = [f for f in files if f.endswith('.npy')]
    print(f"✅ المجلد موجود")
    print(f"   الوجوه المسجلة: {len(npy_files)}")
    if npy_files:
        for face_file in npy_files:
            name = face_file.replace('.npy', '')
            print(f"   - {name}")
else:
    print(f"⚠️  المجلد غير موجود - سيتم إنشاؤه تلقائياً")
    os.makedirs(faces_dir, exist_ok=True)

# النتيجة النهائية
print("\n" + "=" * 60)
if not missing_libs:
    print("🎉 النظام جاهز للعمل!")
    print("=" * 60)
    print("\n🚀 الخطوات التالية:")
    print("   1. شغل السيرفر: python app.py")
    print("   2. افتح: http://192.168.1.68:5000/patient")
    print("   3. للتسجيل: http://192.168.1.68:5000/enroll")
else:
    print("⚠️  يوجد مشاكل تحتاج حل!")
    print("=" * 60)
    print("\n🛠️  شغل: bash install_face_libs.sh")

print("=" * 60)
