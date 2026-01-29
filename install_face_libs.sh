#!/bin/bash
# ===================================================
# 🤖 تثبيت مكتبات التعرف على الوجوه - Raspberry Pi
# 🐍 Python 3.11 Edition (Stable for AI/ONNX)
# ===================================================

echo "=================================================="
echo "🚀 بدء تثبيت البيئة المستقرة (Python 3.11)"
echo "=================================================="

# 1. Install Python 3.11 if missing
echo ""
echo "1️⃣ التأكد من وجود Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    echo "⚠️ Python 3.11 غير موجود. جاري التثبيت..."
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
else
    echo "✅ Python 3.11 موجود."
fi

# 2. Setup venv311
echo ""
echo "2️⃣ إنشاء بيئة افتراضية جديدة (venv311)..."
if [ -d "venv311" ]; then
    echo "⚠️ تم العثور على venv311 سابق. جاري الحذف لضمان نظافة البيئة..."
    rm -rf venv311
fi

python3.11 -m venv venv311
source venv311/bin/activate

echo ""
echo "3️⃣ تحديث pip..."
pip install --upgrade pip

# 3. Install Golden Combination
echo ""
echo "4️⃣ تثبيت الخلطة الذهبية (Golden Combo)..."
# pinned versions known to work on ARM64/Pi
pip install \
numpy==1.26.4 \
ml_dtypes==0.4.1 \
onnx==1.14.1 \
onnxruntime==1.23.2 \
insightface==0.7.3 \
opencv-python-headless \
flask \
pyserial \
"RPi.GPIO" \
scikit-image

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
