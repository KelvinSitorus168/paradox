/*
  02_Kecepatan_PWM.ino — mengatur arah & kecepatan motor iMCLab dari Serial Monitor
  Ketik angka -255..255 lalu Enter:  positif = maju, negatif = mundur, 0 = berhenti
*/
const int IN1 = 27, IN2 = 26, EN = 12;
const int freq = 30000, res = 8, ch = 0;

void pwmBegin() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(EN, freq, res);
#else
  ledcSetup(ch, freq, res); ledcAttachPin(EN, ch);
#endif
}
void pwmWrite(int d) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(EN, d);
#else
  ledcWrite(ch, d);
#endif
}

void motor(int u) {                      // u: -255..255
  u = constrain(u, -255, 255);
  digitalWrite(IN1, u > 0 ? HIGH : LOW);
  digitalWrite(IN2, u < 0 ? HIGH : LOW);
  pwmWrite(abs(u));
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(50);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pwmBegin(); motor(0);
  Serial.println("Ketik PWM -255..255");
}

void loop() {
  if (Serial.available()) {             // baca 1 baris utuh, abaikan baris kosong
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) return;
    int u = line.toInt();
    motor(u);
    Serial.printf("PWM = %d (%.0f %%), arah = %s\n", u, abs(u) / 2.55,
                  u > 0 ? "MAJU" : (u < 0 ? "MUNDUR" : "STOP"));
  }
}
