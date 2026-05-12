/**
 * ESP32 Lower-level Controller for TrashBot
 * Responsibilities:
 *   - Motor control (PWM via TB6612/L298N)
 *   - Wheel encoder odometry
 *   - IMU heading (BNO055 or MPU6050)
 *   - Ultrasonic obstacle detection
 *   - Serial protocol with Orange Pi (ROS2 upper computer)
 *
 * Protocol (binary, 115200 baud):
 *   ESP32 -> Pi: [header 0xAA 0x55] [seq] [type] [payload...] [checksum]
 *   Pi -> ESP32: [header 0xAA 0x55] [seq] [cmd] [payload...] [checksum]
 */

#include <Arduino.h>
#include <WiFi.h>

// ============ Pin definitions ============
// Motor A (left)
#define MOTOR_L_PWM     25
#define MOTOR_L_IN1     26
#define MOTOR_L_IN2     27

// Motor B (right)
#define MOTOR_R_PWM     14
#define MOTOR_R_IN1     12
#define MOTOR_R_IN2     13

// Wheel encoders
#define ENC_L_A         32
#define ENC_L_B         33
#define ENC_R_A         18
#define ENC_R_B         19

// Ultrasonic sensors (front, left, right)
#define US_FRONT_TRIG   4
#define US_FRONT_ECHO   16
#define US_LEFT_TRIG    17
#define US_LEFT_ECHO    5
#define US_RIGHT_TRIG   21
#define US_RIGHT_ECHO   22

// Buzzer
#define BUZZER_PIN      23

// LED status
#define LED_PIN         2

// ============ Constants ============
#define WHEEL_DIAMETER_MM   65.0
#define ENCODER_PPR         11.0        // pulses per revolution
#define WHEEL_BASE_MM       150.0
#define MAX_PWM             255
#define SERIAL_BAUD         115200

// ============ Serial protocol ============
#define MSG_HEADER1         0xAA
#define MSG_HEADER2         0x55

// Types: ESP32 -> Pi
#define TYPE_ODOM           0x01
#define TYPE_ULTRASONIC     0x02
#define TYPE_IMU            0x03
#define TYPE_STATUS         0x04

// Commands: Pi -> ESP32
#define CMD_STOP            0x01
#define CMD_DRIVE           0x02        // left_pwm, right_pwm (int8)
#define CMD_SET_SPEED       0x03        // linear(float), angular(float)
#define CMD_BEEP            0x04
#define CMD_GET_STATUS      0x05
#define CMD_RESET_ODOM      0x06

// ============ State ============
volatile int32_t enc_left = 0;
volatile int32_t enc_right = 0;
float odom_x = 0.0, odom_y = 0.0, odom_theta = 0.0;
float imu_heading = 0.0;
uint8_t seq_out = 0;
uint32_t last_cmd_time = 0;
uint32_t last_publish_time = 0;

// Command state
int8_t cmd_left_pwm = 0;
int8_t cmd_right_pwm = 0;
bool watchdog_triggered = false;

// ============ Encoder ISRs ============
void IRAM_ATTR enc_left_isr() {
    enc_left += digitalRead(ENC_L_B) ? 1 : -1;
}
void IRAM_ATTR enc_right_isr() {
    enc_right += digitalRead(ENC_R_B) ? 1 : -1;
}

// ============ Motor control ============
void motor_init() {
    pinMode(MOTOR_L_PWM, OUTPUT);
    pinMode(MOTOR_L_IN1, OUTPUT);
    pinMode(MOTOR_L_IN2, OUTPUT);
    pinMode(MOTOR_R_PWM, OUTPUT);
    pinMode(MOTOR_R_IN1, OUTPUT);
    pinMode(MOTOR_R_IN2, OUTPUT);

    ledcSetup(0, 20000, 8);  // 20kHz PWM, 8-bit
    ledcSetup(1, 20000, 8);
    ledcAttachPin(MOTOR_L_PWM, 0);
    ledcAttachPin(MOTOR_R_PWM, 1);
}

void set_motor_pwm(int8_t left, int8_t right) {
    // Left motor
    if (left > 0) {
        digitalWrite(MOTOR_L_IN1, HIGH);
        digitalWrite(MOTOR_L_IN2, LOW);
        ledcWrite(0, left);
    } else if (left < 0) {
        digitalWrite(MOTOR_L_IN1, LOW);
        digitalWrite(MOTOR_L_IN2, HIGH);
        ledcWrite(0, -left);
    } else {
        digitalWrite(MOTOR_L_IN1, LOW);
        digitalWrite(MOTOR_L_IN2, LOW);
        ledcWrite(0, 0);
    }

    // Right motor
    if (right > 0) {
        digitalWrite(MOTOR_R_IN1, HIGH);
        digitalWrite(MOTOR_R_IN2, LOW);
        ledcWrite(1, right);
    } else if (right < 0) {
        digitalWrite(MOTOR_R_IN1, LOW);
        digitalWrite(MOTOR_R_IN2, HIGH);
        ledcWrite(1, -right);
    } else {
        digitalWrite(MOTOR_R_IN1, LOW);
        digitalWrite(MOTOR_R_IN2, LOW);
        ledcWrite(1, 0);
    }
}

void diff_drive(float linear, float angular) {
    // Differential drive kinematics
    // linear: m/s, angular: rad/s
    float vl = linear - angular * (WHEEL_BASE_MM / 2000.0);
    float vr = linear + angular * (WHEEL_BASE_MM / 2000.0);

    // Clamp to [-1.0, 1.0]
    float max_abs = max(abs(vl), abs(vr));
    if (max_abs > 1.0) {
        vl /= max_abs;
        vr /= max_abs;
    }

    cmd_left_pwm = (int8_t)(vl * MAX_PWM);
    cmd_right_pwm = (int8_t)(vr * MAX_PWM);
    set_motor_pwm(cmd_left_pwm, cmd_right_pwm);
}

// ============ Odometry ============
void update_odometry(float dt) {
    // Convert encoder counts to distance
    float dist_per_pulse = (WHEEL_DIAMETER_MM * PI) / ENCODER_PPR;

    float dl = (enc_left * dist_per_pulse) / 1000.0;  // meters
    float dr = (enc_right * dist_per_pulse) / 1000.0;

    float d = (dl + dr) / 2.0;
    float dtheta = (dr - dl) / (WHEEL_BASE_MM / 1000.0);

    odom_theta += dtheta;
    odom_x += d * cos(odom_theta);
    odom_y += d * sin(odom_theta);

    // Reset encoder counters
    enc_left = 0;
    enc_right = 0;
}

// ============ Ultrasonic ============
float read_ultrasonic(uint8_t trig_pin, uint8_t echo_pin) {
    digitalWrite(trig_pin, LOW);
    delayMicroseconds(2);
    digitalWrite(trig_pin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trig_pin, LOW);

    long duration = pulseIn(echo_pin, HIGH, 30000);  // 30ms timeout
    if (duration == 0) return 4.0;  // out of range
    return duration * 0.0343 / 2.0 / 100.0;  // cm -> meters
}

// ============ Serial protocol ============
void send_packet(uint8_t type, const uint8_t* data, uint8_t len) {
    uint8_t checksum = 0;
    Serial.write(MSG_HEADER1);
    Serial.write(MSG_HEADER2);
    Serial.write(seq_out);
    Serial.write(type);
    Serial.write(len);
    checksum = seq_out ^ type ^ len;

    for (uint8_t i = 0; i < len; i++) {
        Serial.write(data[i]);
        checksum ^= data[i];
    }
    Serial.write(checksum);
    seq_out++;
}

void send_odometry() {
    uint8_t buf[20];
    memcpy(&buf[0], &odom_x, 4);
    memcpy(&buf[4], &odom_y, 4);
    memcpy(&buf[8], &odom_theta, 4);
    memcpy(&buf[12], &enc_left, 4);
    memcpy(&buf[16], &enc_right, 4);
    send_packet(TYPE_ODOM, buf, 20);
}

void send_ultrasonic(float front, float left, float right) {
    uint8_t buf[12];
    memcpy(&buf[0], &front, 4);
    memcpy(&buf[4], &left, 4);
    memcpy(&buf[8], &right, 4);
    send_packet(TYPE_ULTRASONIC, buf, 12);
}

void send_imu(float heading) {
    uint8_t buf[4];
    memcpy(&buf[0], &heading, 4);
    send_packet(TYPE_IMU, buf, 4);
}

void send_status(uint8_t state, uint8_t watchdog) {
    uint8_t buf[4];
    buf[0] = state;
    buf[1] = watchdog;
    buf[2] = (uint8_t)(analogRead(34) * 3.3 / 4095.0 * 100);  // battery approx
    buf[3] = seq_out;
    send_packet(TYPE_STATUS, buf, 4);
}

void handle_command() {
    while (Serial.available() >= 7) {
        // Parse packet
        uint8_t h1 = Serial.read();
        if (h1 != MSG_HEADER1) continue;
        uint8_t h2 = Serial.read();
        if (h2 != MSG_HEADER2) continue;

        uint8_t seq = Serial.read();
        uint8_t cmd = Serial.read();
        uint8_t len = Serial.read();

        if (Serial.available() < len) {
            // Wait for more data
            return;
        }

        uint8_t payload[32];
        Serial.readBytes(payload, min(len, (uint8_t)32));
        uint8_t checksum = Serial.read();

        // Verify checksum
        uint8_t calc = seq ^ cmd ^ len;
        for (uint8_t i = 0; i < len; i++) calc ^= payload[i];
        if (calc != checksum) {
            Serial.println("Checksum error");
            continue;
        }

        last_cmd_time = millis();
        watchdog_triggered = true;

        switch (cmd) {
            case CMD_STOP:
                set_motor_pwm(0, 0);
                cmd_left_pwm = 0;
                cmd_right_pwm = 0;
                break;

            case CMD_DRIVE:
                if (len >= 2) {
                    set_motor_pwm(payload[0], payload[1]);
                    cmd_left_pwm = payload[0];
                    cmd_right_pwm = payload[1];
                }
                break;

            case CMD_SET_SPEED:
                if (len >= 8) {
                    float lin, ang;
                    memcpy(&lin, &payload[0], 4);
                    memcpy(&ang, &payload[4], 4);
                    diff_drive(lin, ang);
                }
                break;

            case CMD_BEEP:
                tone(BUZZER_PIN, 1000, 100);
                break;

            case CMD_RESET_ODOM:
                odom_x = 0; odom_y = 0; odom_theta = 0;
                enc_left = 0; enc_right = 0;
                break;

            default:
                break;
        }
    }
}

// ============ Setup ============
void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(1000);
    Serial.println("ESP32 TrashBot starting");

    // LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    // Ultrasonic triggers as outputs
    pinMode(US_FRONT_TRIG, OUTPUT);
    pinMode(US_LEFT_TRIG, OUTPUT);
    pinMode(US_RIGHT_TRIG, OUTPUT);
    pinMode(US_FRONT_ECHO, INPUT);
    pinMode(US_LEFT_ECHO, INPUT);
    pinMode(US_RIGHT_ECHO, INPUT);

    pinMode(BUZZER_PIN, OUTPUT);

    // Motor init
    motor_init();

    // Encoder interrupts
    pinMode(ENC_L_A, INPUT_PULLUP);
    pinMode(ENC_L_B, INPUT_PULLUP);
    pinMode(ENC_R_A, INPUT_PULLUP);
    pinMode(ENC_R_B, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(ENC_L_A), enc_left_isr, RISING);
    attachInterrupt(digitalPinToInterrupt(ENC_R_A), enc_right_isr, RISING);

    // Startup beep
    tone(BUZZER_PIN, 800, 150);
    delay(200);
    tone(BUZZER_PIN, 1200, 150);

    digitalWrite(LED_PIN, HIGH);
    Serial.println("Ready");
}

// ============ Main loop ============
void loop() {
    uint32_t now = millis();
    static uint32_t last_update = 0;

    // Process incoming commands from Orange Pi
    handle_command();

    // Publish data at 50Hz
    if (now - last_update >= 20) {
        last_update = now;
        float dt = (now - last_update) / 1000.0;

        // Update odometry
        update_odometry(dt / 1000.0);

        // Read ultrasonic sensors
        float us_front = read_ultrasonic(US_FRONT_TRIG, US_FRONT_ECHO);
        float us_left = read_ultrasonic(US_LEFT_TRIG, US_LEFT_ECHO);
        float us_right = read_ultrasonic(US_RIGHT_TRIG, US_RIGHT_ECHO);

        // Send telemetry
        send_odometry();
        send_ultrasonic(us_front, us_left, us_right);
        send_imu(imu_heading);
        send_status(0, watchdog_triggered ? 1 : 0);

        // Safety: stop if front obstacle too close
        if (us_front < 0.15 && cmd_left_pwm != 0) {
            set_motor_pwm(0, 0);
            tone(BUZZER_PIN, 2000, 50);
        }

        // Watchdog: stop if no command for 500ms
        if (now - last_cmd_time > 500 && cmd_left_pwm != 0) {
            set_motor_pwm(0, 0);
        }
    }

    // Status LED blink
    digitalWrite(LED_PIN, (millis() % 1000 < 500) ? HIGH : LOW);
}
