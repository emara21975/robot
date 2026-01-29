#!/bin/bash
# ===================================================
# 🤖 تثبيت مكتبات التعرف على الوجوه - Raspberry Pi
# 🐍 Python 3.11 Edition (Stable for AI/ONNX)
# ===================================================

echo "=================================================="
echo "🚀 بدء تثبيت البيئة المستقرة (Python 3.11)"
echo "=================================================="

# 1. Install Dependencies for building ONNX (since wheels might be missing for Py3.13)
echo ""
echo "1️⃣ تثبيت أدوات البناء (لضمان عمل ONNX على أي إصدار Python)..."
sudo apt-get update
sudo apt-get install -y python3-dev python3-venv cmake protobuf-compiler libprotobuf-dev

# 2. Setup venv (using system default python)
echo ""
echo "2️⃣ تنظيف البيئات القديمة وإنشاء بيئة جديدة (venv)..."
rm -rf venv venv311 .venv
python3 -m venv venv
source venv/bin/activate

echo ""
echo "3️⃣ تحديث pip..."
pip install --upgrade pip setuptools wheel

# 3. Install Libraries
echo ""
echo "4️⃣ تثبيت المكتبات (سيتم بناء ONNX إذا لزم الأمر)..."
# We DO NOT pin versions here strictly, to allow compiling latest onnx if needed
# But we pin numpy to be safe(r) if possible, though newer OpenCV might want newer numpy.
# Let's trust the solver but give it build tools.

pip install numpy==1.26.4
pip install onnx  # Will compile from source if no wheel, now that we have protobuf-compiler
pip install onnxruntime
pip install insightface
pip install opencv-python-headless flask pyserial RPi.GPIO scikit-image

echo ""
echo "=================================================="
echo "✅ اكتمل التثبيت بنجاح!"
echo "=================================================="

echo ""
echo "🔍 فحص التثبيت..."
python3 << 'EOF'
import sys
try:
    import numpy
    import ml_dtypes
    import onnx
    import onnxruntime
    from insightface.app import FaceAnalysis
    
    print("\n" + "="*40)
    print(f"python: {sys.version.split()[0]}")
    print(f"numpy: {numpy.__version__}")
    print(f"ml_dtypes: {ml_dtypes.__version__}")
    print(f"onnx: {onnx.__version__}")
    print(f"onnxruntime: {onnxruntime.__version__}")
    
    app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    print("✅ FaceEngine: LOADED SUCCESSFULLY")
    print("="*40)
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    sys.exit(1)
EOF

echo ""
echo "=================================================="
echo "🎯 الخطوة الأخيرة والمهمة جدًا!"
echo "=================================================="
echo "لكي يعمل السيرفر بهذه المكتبات، يجب عليك استخدام البيئة الجديدة."
echo "نفذ هذا الأمر لتشغيل السيرفر:"
echo ""
echo "source venv311/bin/activate"
echo "python app.py"
echo ""
echo "=================================================="
