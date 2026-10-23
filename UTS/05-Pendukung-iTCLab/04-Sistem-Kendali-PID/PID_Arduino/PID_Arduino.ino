/*
  PID_Arduino.ino — kendali suhu T1 iTCLab dengan PID (berdasarkan Ebook IoT Jilid 1, Bab 5)
  - Setpoint default 40 °C
  - Output heater Q1 0..100 %  -> PWM 0..255
  - Derivative on measurement (menghindari "derivative kick")
  - Anti-reset windup saat output saturasi
  - Kirim "SP <nilai>" lewat Serial Monitor untuk mengubah setpoint
*/
#include <Arduino.h>

const int pinT1 = 34, pinQ1 = 32, pinLED = 26;
const int freq = 5000, res = 8, chQ1 = 1, chLED = 0;
const float upper_temperature_limit = 58.0;

float Kc = 10.0;    // %Heater / °C
float tauI = 50.0;  // s
float tauD = 1.0;   // s

float sp = 40.0, pv = 0, pv_last = 0, ierr = 0, op = 0;
unsigned long ts = 0;

void pwmAttach(int pin, int ch) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pin, freq, res);
#else
  ledcSetup(ch, freq, res); ledcAttachPin(pin, ch);
#endif
}
void pwmWrite(int pin, int ch, int duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, duty);
#else
  ledcWrite(ch, duty);
#endif
}

float readT1() {
  float s = 0;
  for (int i = 0; i < 10; i++) s += analogRead(pinT1) * 0.322265625 / 10.0;
  return s / 10.0;
}

float pid(float sp, float pv, float pv_last, float &ierr, float dt) {
  const float KP = Kc, KI = Kc / tauI, KD = Kc * tauD;
  const float ophi = 100, oplo = 0;
  float error = sp - pv;
  ierr += KI * error * dt;
  float dpv = (pv - pv_last) / dt;
  float P = KP * error, I = ierr, D = -KD * dpv;
  float out = P + I + D;
  if (out < oplo || out > ophi) {        // anti-reset windup
    ierr -= KI * error * dt;
    out = constrain(out, oplo, ophi);
  }
  Serial.printf("sp=%.2f pv=%.2f op=%.2f P=%.2f I=%.2f D=%.2f\n", sp, pv, out, P, ierr, D);
  return out;
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(50);
  pwmAttach(pinQ1, chQ1);
  pwmAttach(pinLED, chLED);
  pv_last = readT1();
  ts = millis();
}

void loop() {
  if (Serial.available()) {                 // perintah "SP 45"
    String s = Serial.readStringUntil('\n'); s.trim(); s.toUpperCase();
    if (s.startsWith("SP ")) sp = s.substring(3).toFloat();
  }
  unsigned long now = millis();
  if (now - ts >= 1000) {
    float dt = (now - ts) / 1000.0;
    ts = now;
    pv = readT1();
    if (pv >= upper_temperature_limit) {    // pengaman
      op = 0; pwmWrite(pinLED, chLED, 255);
    } else {
      op = pid(sp, pv, pv_last, ierr, dt);
      pwmWrite(pinLED, chLED, 0);
    }
    pwmWrite(pinQ1, chQ1, int(op * 2.55));
    pv_last = pv;
  }
}
