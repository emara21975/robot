#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""فحص حالة نظام التحقق"""

from database import get_setting

# فحص القيمة الفعلية
auth_value = get_setting("auth_enabled", "0")

print("=" * 50)
print("📊 فحص حالة نظام التحقق من الوجه")
print("=" * 50)
print(f"القيمة المخزنة: '{auth_value}'")
print(f"النوع: {type(auth_value).__name__}")
print(f"الطول: {len(str(auth_value))}")
print(f"التمثيل: {repr(auth_value)}")
print()

# التحقق من الشرط
val = str(auth_value).strip()
auth_enabled = val == "1"

print(f"بعد المعالجة:")
print(f"  - النص بعد strip: '{val}'")
print(f"  - النتيجة النهائية: {auth_enabled}")
print()

if auth_enabled:
    print("✅ نظام التحقق: مُفعّل")
else:
    print("❌ نظام التحقق: معطّل")
print("=" * 50)
