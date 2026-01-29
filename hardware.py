# -*- coding: utf-8 -*-
"""
وحدة التحكم في الأجهزة - Hardware Control
التحكم في السيرفو والبوابات على Raspberry Pi
مع نظام Auto-Reconnect لـ Arduino
"""

import time
import math
import threading

# ============ إعدادات السيرفو ============
ZERO_ANGLE = 0       # نقطة الصفر المرجعية
LOADING_ANGLE = 100  # زاوية أنبوب التحميل
SERVO_DELAY = 0.02   # سرعة الحركة

# إعدادات الصناديق
BOX_CONFIG = {
    1: {'angle': 25,  'pin': 23},  # GPIO 23
    2: {'angle': 65,  'pin': 24},  # GPIO 24
}

# State Tracking
current_carousel_angle = ZERO_ANGLE

# ========== محاولة استيراد مكتبات Raspberry Pi ==========
HAS_GPIO = False
pwm_carousel = None
gate_pwms = {} 

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
    print("✓ تم تحميل مكتبة GPIO بنجاح")
except ImportError:
    print("⚠️ مكتبة GPIO غير متاحة - وضع المحاكاة للسيرفو")

# ========== Arduino Connection ==========
arduino = None
ARDUINO_BAUD_RATE = 9600

def find_arduino_port():
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # Match common Arduino descriptions
            desc = port.description.lower()
            if any(k in desc for k in ['arduino', 'ch340', 'usb', 'acm']):
                print(f"🔍 تم العثور على Arduino: {port.device}")
                return port.device
    except Exception as e:
        print(f"❌ خطأ في البحث عن Arduino: {e}")
    return None

def connect_arduino():
    global arduino
    try:
        import serial
    except ImportError:
        return False

    if arduino is not None and arduino.is_open:
        return True
    
    port = find_arduino_port()
    if not port:
        return False
        
    try:
        arduino = serial.Serial(port, ARDUINO_BAUD_RATE, timeout=1)
        time.sleep(2) # Wait for reboot
        arduino.flush()
        print(f"✅ تم الاتصال بـ Arduino على {port}")
        return True
    except Exception as e:
        print(f"❌ تعذر الاتصال بـ Arduino: {e}")
        arduino = None
        return False

def disconnect_arduino():
    global arduino
    if arduino:
        try:
            arduino.close()
            print("🔌 تم قطع الاتصال بـ Arduino")
        except: pass
        arduino = None

def is_arduino_connected():
    return arduino is not None and arduino.is_open


# ========== GPIO Functions ==========

def setup_gpio():
    global pwm_carousel, gate_pwms
    
    if not HAS_GPIO:
        return False
    
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    CAROUSEL_PIN = 18 
    GPIO.setup(CAROUSEL_PIN, GPIO.OUT)
    
    for box_id, config in BOX_CONFIG.items():
        pin = config['pin']
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 50)
        pwm.start(0)
        gate_pwms[box_id] = pwm
    
    pwm_carousel = GPIO.PWM(CAROUSEL_PIN, 50)
    pwm_carousel.start(0)
    
    print(f"✓ تم تهيئة منافذ GPIO لـ {len(BOX_CONFIG)} صناديق")
    return True

def set_servo_angle(pwm, angle):
    if pwm is None or not hasattr(pwm, 'ChangeDutyCycle'): return
    angle = max(0, min(180, angle))
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)

def smooth_move(pwm, start_angle, end_angle, steps=30):
    if pwm is None or not hasattr(pwm, 'ChangeDutyCycle'):
        print(f"[SMOOTH MOVE Simulation] {start_angle} -> {end_angle}")
        time.sleep(steps * 0.01) # Simulate timing
        return

    for i in range(steps + 1):
        t = i / steps
        eased_t = 0.5 - 0.5 * math.cos(math.pi * t)
        current_angle = start_angle + (end_angle - start_angle) * eased_t
        set_servo_angle(pwm, current_angle)
        time.sleep(SERVO_DELAY)
        
    set_servo_angle(pwm, end_angle)
    time.sleep(0.1)
    if hasattr(pwm, 'ChangeDutyCycle'): pwm.ChangeDutyCycle(0)

def move_servo(pwm, target_angle):
    global current_carousel_angle, pwm_carousel
    
    if pwm == pwm_carousel and pwm_carousel is not None:
        start_angle = current_carousel_angle
        smooth_move(pwm, start_angle, target_angle, steps=40)
        current_carousel_angle = target_angle
    else:
        # Gates or Sim
        start_angle = 0
        if target_angle == 0: start_angle = 90
        smooth_move(pwm, start_angle, target_angle, steps=20)

def load_medicine():
    move_servo(pwm_carousel, LOADING_ANGLE)
    time.sleep(0.7)

def go_home_zero():
    move_servo(pwm_carousel, ZERO_ANGLE)
    time.sleep(0.6)

def dispense_dose(box_id):
    if box_id not in BOX_CONFIG: return False, f"رقم الصندوق {box_id} غير صحيح"
    
    # 1. Try Arduino Command first (Primary for Servo on Arduino)
    if connect_arduino():
        try:
            print(f"📡 Sending OPEN_BOX to Arduino for Box {box_id}...")
            # Note: The Arduino code currently opens the *only* servo it has (medServo).
            # If we had multiple boxes controlled by Arduino, we'd need parameters like OPEN_BOX:1
            # For now, we assume single servo logic or user only cares about 'the' box moving.
            arduino.write(b'OPEN_BOX\n')
            arduino.flush()
            # Wait for Arduino confirmation or assumed timing
            time.sleep(3.5) # Arduino waits 3s then closes
            return True, f"تم صرف جرعة من الصندوق {box_id} (Arduino)"
        except Exception as e:
            print(f"⚠️ Failed to send to Arduino: {e}")
    
    # 2. If Arduino failed or not connected, try Pi GPIO (Legacy/Direct)
    if HAS_GPIO:
        gate_pwm = gate_pwms.get(box_id)
        target_angle = BOX_CONFIG[box_id]['angle']
        
        move_servo(pwm_carousel, target_angle)
        time.sleep(0.6)
        
        move_servo(gate_pwm, 90)
        time.sleep(0.5)
        
        move_servo(gate_pwm, 0)
        time.sleep(0.3)
        
        move_servo(pwm_carousel, ZERO_ANGLE)
        time.sleep(0.4)
        return True, f"تم صرف جرعة من الصندوق {box_id} (GPIO)"

    # 3. Simulation
    if not is_arduino_connected() and not HAS_GPIO:
        print(f"[محاكاة] تدوير {box_id}")
        return True, "تم صرف الجرعة (محاكاة)"
        
    return False, "فشل الاتصال بالأردوينو أو GPIO"


# ========== Robot Control Functions ==========

def start_robot():
    global arduino
    if not connect_arduino(): return False
    try:
        arduino.write(b'START\n')
        arduino.flush()
        return True
    except Exception as e:
        disconnect_arduino()
        return False

def stop_robot():
    global arduino
    if not connect_arduino(): return False
    try:
        arduino.write(b'STOP\n')
        arduino.flush()
        return True
    except Exception as e:
        disconnect_arduino()
        return False

def return_home():
    global arduino
    if not connect_arduino(): return False
    try:
        arduino.write(b'RETURN\n')
        arduino.flush()
        return True
    except Exception as e: return False

def get_robot_status():
    if not is_arduino_connected(): return None
    try:
        if arduino.in_waiting > 0:
            return arduino.readline().decode().strip()
    except: pass
    return None


# ========== RAW CONTROL for TEST PAGE ==========

def move_raw(command: str, safety_timeout: int = None):
    """Send raw command to Arduino (START, STOP, RIGHT, LEFT, REVERSE)."""
    if not connect_arduino(): return False
    try:
        cmd = command.strip().upper()
        arduino.write((cmd + "\n").encode("utf-8"))
        arduino.flush()
        print(f"📡 RAW->Arduino: {cmd}")
        
        if safety_timeout and cmd != "STOP":
            threading.Thread(target=lambda: _auto_stop_after(safety_timeout, cmd), daemon=True).start()
        return True
    except Exception as e:
        print(f"❌ move_raw error: {e}")
        disconnect_arduino()
        return False

def _auto_stop_after(seconds, label):
    time.sleep(seconds)
    stop_robot()
    print(f"[SAFETY] Auto-stop after {seconds}s ({label})")

_last_distance_cm = None

def poll_arduino_lines(max_lines=20):
    global _last_distance_cm
    if not connect_arduino(): return
    try:
        lines_read = 0
        while arduino.in_waiting > 0 and lines_read < max_lines:
            line = arduino.readline().decode(errors="ignore").strip()
            lines_read += 1
            if line.startswith("DISTANCE:"):
                try: _last_distance_cm = float(line.split(":")[1])
                except: pass
            elif line.startswith("STATUS:") or line.startswith("OK:") or line.startswith("OBSTACLE:"):
                print(f"🤖 ARDUINO: {line}")
    except Exception as e: print(f"Poll Error: {e}")

def get_latest_distance():
    poll_arduino_lines()
    return _last_distance_cm

def set_servo_raw(target: str, sid: int, angle: int):
    """Raw control for servos (Test Page)."""
    if target == "carousel":
        move_servo(pwm_carousel if HAS_GPIO else None, int(angle))
        return True, "carousel_ok"
    elif target == "gate":
        if sid not in BOX_CONFIG: return False, "invalid_gate_id"
        pwm = gate_pwms.get(sid) if HAS_GPIO else None
        move_servo(pwm, int(angle))
        return True, f"gate_{sid}_ok"
    return False, "invalid_target"


def cleanup():
    disconnect_arduino()
    if HAS_GPIO:
        try: GPIO.cleanup()
        except: pass
        print("✓ تم تنظيف موارد GPIO")
