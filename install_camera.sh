#!/bin/bash
# ===================================================
# 📸 تثبيت مكتبات الكاميرا والتعرف على الوجه
# Raspberry Pi Camera & Face Recognition Setup
# ===================================================

echo "=================================================="
echo "🚀 بدء تثبيت مكتبات الكاميرا والذكاء الاصطناعي"
echo "=================================================="
echo ""

# التحقق من Python
echo "1️⃣ التحقق من Python..."
python3 --version
echo ""

# تحديث النظام
echo "2️⃣ تحديث قوائم الحزم..."
sudo apt-get update
echo ""

# تثبيت OpenCV (الطريقة الأسرع - من المستودع)
echo "3️⃣ تثبيت OpenCV من المستودع الرسمي..."
sudo apt-get install -y python3-opencv
echo ""

# تثبيت مكتبات إضافية مطلوبة
echo "4️⃣ تثبيت مكتبات الصور والكاميرا..."
sudo apt-get install -y \
    libatlas-base-dev \
    libjasper-dev \
    libqtgui4 \
    python3-pyqt5 \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    libqt4-test
echo ""

# تثبيت pip packages (بدون InsightFace في البداية)
echo "5️⃣ تثبيت مكتبات Python الأساسية..."
pip3 install --upgrade pip
pip3 install numpy
pip3 install Pillow
echo ""

# اختبار OpenCV
echo "6️⃣ اختبار OpenCV..."
python3 -c "import cv2; print('✅ OpenCV نسخة:', cv2.__version__)" || {
    echo "❌ فشل تثبيت OpenCV!"
    echo "جرب: pip3 install opencv-python-headless"
    exit 1
}
echo ""

# محاولة تثبيت onnxruntime (مطلوب لـ InsightFace)
echo "7️⃣ تثبيت onnxruntime..."
pip3 install onnxruntime || {
    echo "⚠️ تحذير: فشل تثبيت onnxruntime (قد يحتاج مساحة/ذاكرة كبيرة)"
    echo "يمكن المتابعة بدون InsightFace مؤقتاً"
}
echo ""

# محاولة تثبيت InsightFace
echo "8️⃣ تثبيت InsightFace..."
pip3 install insightface || {
    echo "⚠️ تحذير: فشل تثبيت InsightFace"
    echo "يمكن تشغيل النظام بدون التعرف على الوجوه"
}
echo ""

# تنزيل نموذج الوجوه
echo "9️⃣ تحضير مجلد النماذج..."
mkdir -p ~/.insightface/models
echo "ملاحظة: النماذج ستحمل تلقائياً عند أول استخدام"
echo ""

# إنشاء مجلد الوجوه
echo "🔟 إنشاء مجلد الوجوه..."
cd ~/robot
mkdir -p robot/faces
chmod 755 robot/faces
echo ""

# اختبار نهائي
echo "=================================================="
echo "✅ اختبار التثبيت النهائي"
echo "=================================================="
python3 << 'EOF'
import sys
errors = []

try:
    import cv2
    print(f"✅ OpenCV: {cv2.__version__}")
except ImportError as e:
    errors.append(f"❌ OpenCV: {e}")

try:
    import numpy
    print(f"✅ NumPy: {numpy.__version__}")
except ImportError as e:
    errors.append(f"❌ NumPy: {e}")

try:
    import PIL
    print(f"✅ Pillow: {PIL.__version__}")
except ImportError as e:
    errors.append(f"❌ Pillow: {e}")

try:
    import onnxruntime
    print(f"✅ ONNX Runtime: {onnxruntime.__version__}")
except ImportError as e:
    errors.append(f"⚠️  ONNX Runtime: غير مثبت (اختياري)")

try:
    import insightface
    print(f"✅ InsightFace: {insightface.__version__}")
except ImportError as e:
    errors.append(f"⚠️  InsightFace: غير مثبت (اختياري)")

print("\n" + "="*50)
if errors:
    print("⚠️  ملاحظات:")
    for err in errors:
        print(err)
    print("\nيمكن تشغيل النظام الأساسي حتى بدون InsightFace")
else:
    print("🎉 جميع المكتبات مثبتة بنجاح!")
print("="*50)
EOF

echo ""
echo "=================================================="
echo "✨ انتهى التثبيت!"
echo "=================================================="
echo ""
echo "📋 الخطوات التالية:"
echo "1. أعد تشغيل Terminal"
echo "2. شغل السيرفر: python3 app.py"
echo "3. افتح المتصفح: http://192.168.1.68:5000"
echo ""
echo "🆘 إذا استمرت المشاكل:"
echo "   - تأكد من وجود مساحة كافية: df -h"
echo "   - تأكد من الذاكرة: free -h"
echo "   - أعد تشغيل Raspberry Pi"
echo "=================================================="
