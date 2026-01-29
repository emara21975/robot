#!/bin/bash
# ===================================================
# 🤖 تثبيت مكتبات التعرف على الوجوه - Raspberry Pi
# ===================================================

echo "=================================================="
echo "🚀 بدء تثبيت مكتبات نظام التعرف على الوجوه"
echo "=================================================="

# التحقق من وجود venv
if [ ! -d "venv" ]; then
    echo "⚠️  لا يوجد venv - سيتم الإنشاء..."
    python3 -m venv venv
fi

# تفعيل venv
source venv/bin/activate

echo ""
echo "1️⃣ تحديث pip..."
pip install --upgrade pip

echo ""
echo "2️⃣ تثبيت المتطلبات الأساسية..."
sudo apt-get update
sudo apt-get install -y python3-opencv libopenblas-dev

echo ""
echo "3️⃣ تثبيت OpenCV..."
pip install opencv-python

echo ""
echo "4️⃣ تثبيت ONNX Runtime (نسخة CPU)..."
pip install onnxruntime==1.17.3

echo ""
echo "5️⃣ تثبيت InsightFace..."
pip install insightface==0.7.3

echo ""
echo "6️⃣ تثبيت مكتبات إضافية..."
pip install numpy scikit-image

echo ""
echo "=================================================="
echo "✅ اكتمل التثبيت!"
echo "=================================================="

echo ""
echo "🔍 التحقق من المكتبات..."
python3 << 'EOF'
import sys

print("\n" + "="*50)
print("📦 فحص المكتبات المثبتة")
print("="*50)

# Test OpenCV
try:
    import cv2
    print(f"✅ OpenCV: {cv2.__version__}")
except ImportError as e:
    print(f"❌ OpenCV: {e}")
    sys.exit(1)

# Test ONNX Runtime
try:
    import onnxruntime as ort
    print(f"✅ ONNX Runtime: {ort.__version__}")
    print(f"   الجهاز: {ort.get_device()}")
except ImportError as e:
    print(f"❌ ONNX Runtime: {e}")
    sys.exit(1)

# Test InsightFace
try:
    import insightface
    print(f"✅ InsightFace: {insightface.__version__}")
except ImportError as e:
    print(f"❌ InsightFace: {e}")
    sys.exit(1)

print("="*50)
print("🎉 جميع المكتبات مثبتة وجاهزة!")
print("="*50)
EOF

echo ""
echo "🧪 اختبار محرك التعرف على الوجوه..."
python3 << 'EOF'
try:
    print("\n⏳ تحميل محرك InsightFace...")
    from insightface.app import FaceAnalysis
    
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    print("✅ FaceEngine جاهز للعمل!")
    print("   النموذج: buffalo_l")
    print("   المعالج: CPU")
    
except Exception as e:
    print(f"❌ فشل تحميل المحرك: {e}")
    exit(1)
EOF

echo ""
echo "=================================================="
echo "🎯 الخطوات التالية:"
echo "=================================================="
echo "1. شغل السيرفر:"
echo "   python app.py"
echo ""
echo "2. افتح المتصفح على:"
echo "   http://192.168.1.68:5000/patient"
echo ""
echo "3. يجب أن ترى:"
echo "   ✅ بث الفيديو"
echo "   ✅ مربع أحمر حول وجهك"
echo "   ✅ Unknown (إذا لم تسجل بعد)"
echo ""
echo "4. للتسجيل:"
echo "   http://192.168.1.68:5000/enroll"
echo "=================================================="
