/*
  itclab_firmware.ino — firmware antarmuka serial untuk Kit iTCLab (ESP32)
  Diadaptasi dari firmware TCLab (J. Hedengren) & iTCLab (B. Rahmat).

  Perintah serial (115200 baud, diakhiri '\n', tidak case-sensitive):
    Q1 <0-100>  set heater 1 (%)
    Q2 <0-100>  set heater 2 (%)
    T1          baca suhu T1 (°C)
    T2          baca suhu T2 (°C)
    LED <0-100> set LED (%)
    VER         versi firmware
    X           matikan semua heater

  Pin: T1=34, T2=35, Q1=32, Q2=33, LED=26
*/
#include <Arduino.h>

const String vers = "1.05-kelvin";
const int baud = 115200;
const int pinT1 = 34, pinT2 = 35, pinQ1 = 32, pinQ2 = 33, pinLED = 26;
const int freq = 5000, res = 8;
const int chLED = 0, chQ1 = 1, chQ2 = 2;
const float upper_temperature_limit = 59.0;  // batas aman
const int nSample = 10;                        // rata-rata pembacaan ADC

String cmd;
float val = 0;

// ---------- PWM helper: kompatibel core 2.x & 3.x ----------
void pwmAttach(int pin, int ch) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pin, freq, res);
#else
  ledcSetup(ch, freq, res);
  ledcAttachPin(pin, ch);
#endif
}
void pwmWrite(int pin, int ch, int duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, duty);
#else
  ledcWrite(ch, duty);
#endif
}

float readTemp(int pin) {
  float sum = 0;
  for (int i = 0; i < nSample; i++) sum += analogRead(pin) * 0.322265625 / 10.0;
  return sum / nSample;
}

void heatersOff() {
  pwmWrite(pinQ1, chQ1, 0);
  pwmWrite(pinQ2, chQ2, 0);
}

void parseSerial() {
  String line = Serial.readStringUntil('\n');
  line.trim();
  int idx = line.indexOf(' ');
  cmd = (idx < 0) ? line : line.substring(0, idx);
  cmd.toUpperCase();
  val = (idx < 0) ? 0 : line.substring(idx + 1).toFloat();
}

void dispatch() {
  if (cmd == "Q1" || cmd == "Q2") {
    float q = constrain(val, 0.0, 100.0);
    int duty = int(q * 255.0 / 100.0);
    if (cmd == "Q1") pwmWrite(pinQ1, chQ1, duty);
    else             pwmWrite(pinQ2, chQ2, duty);
    Serial.println(q);
  } else if (cmd == "T1") {
    Serial.println(readTemp(pinT1));
  } else if (cmd == "T2") {
    Serial.println(readTemp(pinT2));
  } else if (cmd == "LED") {
    float l = constrain(val, 0.0, 100.0);
    pwmWrite(pinLED, chLED, int(l * 2.55));
    Serial.println(l);
  } else if (cmd == "V" || cmd == "VER") {
    Serial.println("iTCLab Firmware Version " + vers);
  } else if (cmd == "X") {
    heatersOff();
    Serial.println("Stop");
  } else if (cmd.length() > 0) {
    Serial.println("ERR unknown command");
  }
}

void checkTemp() {
  if (readTemp(pinT1) >= upper_temperature_limit || readTemp(pinT2) >= upper_temperature_limit) {
    heatersOff();
    pwmWrite(pinLED, chLED, 255);   // LED menyala sebagai peringatan
  }
}

void setup() {
  Serial.begin(baud);
  Serial.setTimeout(100);
  pwmAttach(pinQ1, chQ1);
  pwmAttach(pinQ2, chQ2);
  pwmAttach(pinLED, chLED);
  heatersOff();
}

void loop() {
  if (Serial.available()) {
    parseSerial();
    dispatch();
  }
  checkTemp();
}
