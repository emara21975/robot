#include <MPU6050_light.h>
#include <Servo.h>
#include <Wire.h>

MPU6050 mpu(Wire);

// ======= Emergency Button =======
#define EMERGENCY_PIN 7 // زر الطوارئ (Normally Open)

// ======= Medicine Box Servo =======
#define MED_SERVO_PIN 4
Servo medServo;

// زوايا الصندوق
#define BOX_CLOSED_ANGLE 0
#define BOX_OPEN_ANGLE 90

// ======= Emergency State =======
bool emergencyActive = false;
unsigned long emergencyStartMs = 0;
unsigned long emergencyAutoCloseMs = 15000; // 15 ثانية

// ======= L298N ========
int ENA = 5;
int IN1 = 8;
int IN2 = 9;

int ENB = 6;
int IN3 = 10;
int IN4 = 11;

// ======= Ultrasonic ========
int trigPin = 2;
int echoPin = 3;

float distance;
long duration;

// -------- Robot State --------
enum RobotState { IDLE, MOVING, TURNING, EMERGENCY };

RobotState state = IDLE;
bool isReversing = false;

float obstacleDistance = 20.0;

// -------- PID --------
float Kp = 3.0;
float Ki = 0.01;
float Kd = 1.5;

float errorSum = 0;
float lastError = 0;

// -------- Speed Ramp --------
int currentSpeed = 0;
int targetSpeed = 150;
int speedStep = 5;

// -------- Targets --------
float targetYaw = 0;
float turnTargetYaw = 0;
unsigned long turnStartMs = 0;

// ============ Normalize ============
float normalize(float angle) {
  while (angle > 180)
    angle -= 360;
  while (angle < -180)
    angle += 360;
  return angle;
}

// ============ Ultrasonic ============
float getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH, 20000);
  return duration * 0.0343 / 2;
}

// ============ Medicine Box Control ============
void openMedicineBox() { medServo.write(BOX_OPEN_ANGLE); }

void closeMedicineBox() { medServo.write(BOX_CLOSED_ANGLE); }

// ============ Motor Control ============
void stopRobot() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}

void forwardPID(int baseSpeed) {
  mpu.update();
  float yaw = normalize(mpu.getAngleZ());
  float error = normalize(yaw - targetYaw);

  errorSum += error;
  float derivative = error - lastError;
  lastError = error;

  float correction = Kp * error + Ki * errorSum + Kd * derivative;

  int L = constrain(baseSpeed - correction, 0, 255);
  int R = constrain(baseSpeed + correction, 0, 255);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, L);
  analogWrite(ENB, R);
}

void backwardPID(int baseSpeed) {
  mpu.update();
  float yaw = normalize(mpu.getAngleZ());
  float error = normalize(yaw - targetYaw);

  errorSum += error;
  float derivative = error - lastError;
  lastError = error;

  float correction = Kp * error + Ki * errorSum + Kd * derivative;

  // Reverse correction logic (inverted steering)
  int L = constrain(baseSpeed + correction, 0, 255);
  int R = constrain(baseSpeed - correction, 0, 255);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, L);
  analogWrite(ENB, R);
}

// ============ Turn In Place Logic ============
void startTurnDegrees(float deltaDeg) {
  mpu.update();
  float yaw = normalize(mpu.getAngleZ());
  turnTargetYaw = normalize(yaw + deltaDeg);

  errorSum = 0;
  lastError = 0;
  turnStartMs = millis();

  state = TURNING;
  currentSpeed = 0;

  Serial.print("TURN_DEG:");
  Serial.println(deltaDeg);
  Serial.print("FROM:");
  Serial.println(yaw);
  Serial.print("TARGET:");
  Serial.println(turnTargetYaw);
}

void turnInPlace() {
  mpu.update();
  float yaw = normalize(mpu.getAngleZ());
  float error = normalize(turnTargetYaw - yaw);

  // Threshold to stop turning (3 degrees)
  if (abs(error) < 3) {
    stopRobot();
    delay(500);

    // Default behavior: Go IDLE after turn
    state = IDLE;
    Serial.println("STATUS:TURN_COMPLETE");
    return;
  }

  int turnSpeed = 100; // Fixed turn speed

  if (error > 0) {
    // Turn Right (CW)
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  } else {
    // Turn Left (CCW)
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  }

  analogWrite(ENA, turnSpeed);
  analogWrite(ENB, turnSpeed);
}

// ============ Emergency Logic ============
// void checkEmergencyButton() {
//   // Physical Button Disabled
// }

void handleEmergencyState() {
  stopRobot();

  // Auto Close after timeout
  if (millis() - emergencyStartMs >= emergencyAutoCloseMs) {
    closeMedicineBox();
    emergencyActive = false;
    state = IDLE;

    Serial.println("🟢 EMERGENCY CLOSED: SYSTEM RESET TO IDLE");
  }
}

// ============ Setup ============
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(50);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Emergency Setup
  // Physical Button Disabled by User Request
  // pinMode(EMERGENCY_PIN, INPUT_PULLDOWN);

  medServo.attach(MED_SERVO_PIN);
  closeMedicineBox();

  Wire.begin();
  mpu.begin();
  delay(1000);
  mpu.calcOffsets();

  Serial.println("READY");
}

// ============ Command Handler ============
void checkSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readString();
    command.trim();
    command.toUpperCase();

    // Serial.print("CMD="); Serial.println(command);

    if (command == "START" || command == "GO") {
      mpu.update();
      targetYaw = normalize(mpu.getAngleZ());
      state = MOVING;
      isReversing = false;
      Serial.println("OK:MOVING_FWD");

    } else if (command == "STOP") {
      state = IDLE;
      stopRobot();
      Serial.println("OK:STOPPED");

    } else if (command == "RIGHT") {
      startTurnDegrees(90);
      Serial.println("OK:TURN_RIGHT");

    } else if (command == "LEFT") {
      startTurnDegrees(-90);
      Serial.println("OK:TURN_LEFT");

    } else if (command == "REVERSE") {
      mpu.update();
      targetYaw = normalize(mpu.getAngleZ());
      state = MOVING;
      isReversing = true;
      Serial.println("OK:RAW_REVERSE");

    } else if (command == "RETURN") {
      // Chain: Turn 180 -> Wait for next command (or User sends Start)
      startTurnDegrees(180);
      Serial.println("OK:STARTING_RETURN");

    } else if (command == "OPEN_BOX") {
      openMedicineBox();
      Serial.println("OK:BOX_OPENED");
      // Auto close after 3 seconds for safety
      delay(3000);
      closeMedicineBox();
      Serial.println("OK:BOX_CLOSED");
    }
  }
}

// ============ Main Loop ============
static unsigned long lastPrintTime = 0;

void loop() {
  // 1. Emergency Check (Disabled)
  // checkEmergencyButton();

  // 2. Emergency Handler
  if (state == EMERGENCY) {
    handleEmergencyState();
    delay(20);
    return; // Skip everything else
  }

  checkSerialCommands();

  if (state == TURNING) {
    turnInPlace();
  } else if (state == MOVING) {
    distance = getDistance();

    if (millis() - lastPrintTime >= 200) {
      lastPrintTime = millis();
      Serial.print("DISTANCE:");
      Serial.println(distance);
    }

    // Safety Stop
    if (distance > 0 && distance <= obstacleDistance) {
      state = IDLE;
      stopRobot();
      currentSpeed = 0;
      Serial.println("OBSTACLE:STOPPED");
    } else {
      if (currentSpeed < targetSpeed)
        currentSpeed += speedStep;

      if (isReversing)
        backwardPID(currentSpeed);
      else
        forwardPID(currentSpeed);
    }
  } else {
    stopRobot();
  }

  delay(50);
}
