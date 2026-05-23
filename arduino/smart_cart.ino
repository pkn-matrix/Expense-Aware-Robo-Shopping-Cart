// ─────────────────────────────────────────────
//  smart_cart.ino — Arduino Motor & Sensor Code
//  Smart Cart Project — FIXED VERSION
//
//  PIN MAP:
//  2,3,4,5     → L298N #1 IN1-IN4 (Left motors)
//  6,7         → L298N #1 ENA,ENB  (PWM speed)
//  8,9,10,11   → L298N #2 IN1-IN4 (Right motors)
//  12,13       → L298N #2 ENA,ENB  (PWM speed)
//  A0,A1       → Front HC-SR04 TRIG,ECHO
//  A2,A3       → Left  HC-SR04 TRIG,ECHO
//  A4,A5       → Right HC-SR04 TRIG,ECHO
// ─────────────────────────────────────────────

// ── Left Motor Pins (L298N #1) ───────────────
const int LM_IN1 = 2, LM_IN2 = 3;
const int LM_IN3 = 4, LM_IN4 = 5;
const int LM_ENA = 6, LM_ENB = 7;

// ── Right Motor Pins (L298N #2) ──────────────
const int RM_IN1 = 8,  RM_IN2 = 9;
const int RM_IN3 = 10, RM_IN4 = 11;
const int RM_ENA = 12, RM_ENB = 13;

// ── Ultrasonic Sensor Pins ───────────────────
const int FRONT_TRIG = A0, FRONT_ECHO = A1;
const int LEFT_TRIG  = A2, LEFT_ECHO  = A3;
const int RIGHT_TRIG = A4, RIGHT_ECHO = A5;

// ── Settings ─────────────────────────────────
const int MOTOR_SPEED   = 180;   // 0-255
const int TURN_SPEED    = 140;   // Slightly slower for turns
const int OBSTACLE_CM   = 20;    // Stop if closer than this (cm)
const int SENSOR_MS     = 100;   // Sensor check interval (ms)

// ── State ─────────────────────────────────────
char     currentCmd      = 'S';
unsigned long lastSensor = 0;
bool     obstacleActive  = false;

// ─────────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  // Motor pins OUTPUT
  int pins[] = {LM_IN1,LM_IN2,LM_IN3,LM_IN4,LM_ENA,LM_ENB,
                RM_IN1,RM_IN2,RM_IN3,RM_IN4,RM_ENA,RM_ENB};
  for (int p : pins) pinMode(p, OUTPUT);

  // Ultrasonic pins
  pinMode(FRONT_TRIG,OUTPUT); pinMode(FRONT_ECHO,INPUT);
  pinMode(LEFT_TRIG, OUTPUT); pinMode(LEFT_ECHO, INPUT);
  pinMode(RIGHT_TRIG,OUTPUT); pinMode(RIGHT_ECHO,INPUT);

  // Set motor speeds
  analogWrite(LM_ENA, MOTOR_SPEED);
  analogWrite(LM_ENB, MOTOR_SPEED);
  analogWrite(RM_ENA, MOTOR_SPEED);
  analogWrite(RM_ENB, MOTOR_SPEED);

  stopCart();
  delay(500);
  Serial.println("READY");
}

// ─────────────────────────────────────────────
void loop() {

  // ── Read Pi command ──────────────────────
  if (Serial.available() > 0) {
    char c = Serial.read();
    // Accept valid commands only
    if (c=='F'||c=='B'||c=='L'||c=='R'||c=='S') {
      currentCmd = c;
    }
    // Flush remaining bytes
    while (Serial.available()) Serial.read();
  }

  // ── Sensor check every SENSOR_MS ────────
  unsigned long now = millis();
  if (now - lastSensor >= SENSOR_MS) {
    lastSensor = now;

    int fDist = getDistance(FRONT_TRIG, FRONT_ECHO);
    int lDist = getDistance(LEFT_TRIG,  LEFT_ECHO);
    int rDist = getDistance(RIGHT_TRIG, RIGHT_ECHO);

    // Obstacle in front?
    if (fDist > 0 && fDist < OBSTACLE_CM) {
      obstacleActive = true;
      stopCart();
      Serial.println("OBSTACLE");

      // Auto-steer around obstacle
      delay(300);
      if (rDist >= lDist) {
        turnRight();
        delay(400);
      } else {
        turnLeft();
        delay(400);
      }
      stopCart();
      currentCmd = 'S';
      return;
    } else {
      obstacleActive = false;
    }
  }

  // ── Execute command ──────────────────────
  if (!obstacleActive) {
    switch (currentCmd) {
      case 'F': moveForward();  break;
      case 'B': moveBackward(); break;
      case 'L': turnLeft();     break;
      case 'R': turnRight();    break;
      case 'S': stopCart();     break;
    }
  }
}

// ─────────────────────────────────────────────
//  Distance (cm) — returns 999 if no echo
// ─────────────────────────────────────────────
int getDistance(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  long dur = pulseIn(echo, HIGH, 25000UL);
  if (dur == 0) return 999;
  return (int)((dur * 0.034) / 2);
}

// ─────────────────────────────────────────────
//  Motor Functions
// ─────────────────────────────────────────────
void setSpeed(int spd) {
  analogWrite(LM_ENA, spd);
  analogWrite(LM_ENB, spd);
  analogWrite(RM_ENA, spd);
  analogWrite(RM_ENB, spd);
}

void moveForward() {
  setSpeed(MOTOR_SPEED);
  digitalWrite(LM_IN1,HIGH); digitalWrite(LM_IN2,LOW);
  digitalWrite(LM_IN3,HIGH); digitalWrite(LM_IN4,LOW);
  digitalWrite(RM_IN1,HIGH); digitalWrite(RM_IN2,LOW);
  digitalWrite(RM_IN3,HIGH); digitalWrite(RM_IN4,LOW);
}

void moveBackward() {
  setSpeed(MOTOR_SPEED);
  digitalWrite(LM_IN1,LOW); digitalWrite(LM_IN2,HIGH);
  digitalWrite(LM_IN3,LOW); digitalWrite(LM_IN4,HIGH);
  digitalWrite(RM_IN1,LOW); digitalWrite(RM_IN2,HIGH);
  digitalWrite(RM_IN3,LOW); digitalWrite(RM_IN4,HIGH);
}

void turnLeft() {
  setSpeed(TURN_SPEED);
  // Left motors backward, right forward
  digitalWrite(LM_IN1,LOW);  digitalWrite(LM_IN2,HIGH);
  digitalWrite(LM_IN3,LOW);  digitalWrite(LM_IN4,HIGH);
  digitalWrite(RM_IN1,HIGH); digitalWrite(RM_IN2,LOW);
  digitalWrite(RM_IN3,HIGH); digitalWrite(RM_IN4,LOW);
}

void turnRight() {
  setSpeed(TURN_SPEED);
  // Left motors forward, right backward
  digitalWrite(LM_IN1,HIGH); digitalWrite(LM_IN2,LOW);
  digitalWrite(LM_IN3,HIGH); digitalWrite(LM_IN4,LOW);
  digitalWrite(RM_IN1,LOW);  digitalWrite(RM_IN2,HIGH);
  digitalWrite(RM_IN3,LOW);  digitalWrite(RM_IN4,HIGH);
}

void stopCart() {
  // Soft brake — gradual slowdown
  int spd = MOTOR_SPEED;
  while (spd > 0) {
    spd -= 25;
    if (spd < 0) spd = 0;
    setSpeed(spd);
    delay(15);
  }
  // Hard stop
  digitalWrite(LM_IN1,LOW); digitalWrite(LM_IN2,LOW);
  digitalWrite(LM_IN3,LOW); digitalWrite(LM_IN4,LOW);
  digitalWrite(RM_IN1,LOW); digitalWrite(RM_IN2,LOW);
  digitalWrite(RM_IN3,LOW); digitalWrite(RM_IN4,LOW);
}
