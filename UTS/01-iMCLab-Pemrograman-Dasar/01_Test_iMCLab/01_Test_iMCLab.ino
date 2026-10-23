/*
  01_Test_iMCLab.ino — uji fungsi Kit iMCLab
  Diadaptasi dari contoh dosen: https://github.com/bsrahmat/imclab/blob/main/01-Test_iMCLab.ino
  Perubahan: kompatibel ESP32 core 2.x & 3.x, PWM diset saat maju/mundur,
             dan dutyCycle direset agar siklus percepatan berulang.

  Urutan: maju penuh 2 s -> berhenti 1 s -> mundur penuh 2 s -> berhenti 1 s
          -> maju dengan PWM naik 200..255 (step 5 tiap 0,5 s)
*/
const int motor1Pin1 = 27;   // IN1
const int motor1Pin2 = 26;   // IN2
const int enable1Pin = 12;   // EN (PWM)

const int freq = 30000;      // 30 kHz: di atas pendengaran, motor tidak berdenging
const int pwmChannel = 0;
const int resolution = 8;    // duty 0..255
int dutyCycle = 200;

void pwmBegin() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(enable1Pin, freq, resolution);
#else
  ledcSetup(pwmChannel, freq, resolution);
  ledcAttachPin(enable1Pin, pwmChannel);
#endif
}
void pwmWrite(int duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(enable1Pin, duty);
#else
  ledcWrite(pwmChannel, duty);
#endif
}

void setup() {
  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pwmBegin();
  Serial.begin(115200);
  Serial.println("Testing DC Motor...");
}

void loop() {
  Serial.println("Moving Forward");
  pwmWrite(255);
  digitalWrite(motor1Pin1, LOW);  digitalWrite(motor1Pin2, HIGH);
  delay(2000);

  Serial.println("Motor stopped");
  digitalWrite(motor1Pin1, LOW);  digitalWrite(motor1Pin2, LOW);
  delay(1000);

  Serial.println("Moving Backwards");
  digitalWrite(motor1Pin1, HIGH); digitalWrite(motor1Pin2, LOW);
  delay(2000);

  Serial.println("Motor stopped");
  digitalWrite(motor1Pin1, LOW);  digitalWrite(motor1Pin2, LOW);
  delay(1000);

  digitalWrite(motor1Pin1, HIGH); digitalWrite(motor1Pin2, LOW);
  for (dutyCycle = 200; dutyCycle <= 255; dutyCycle += 5) {
    pwmWrite(dutyCycle);
    Serial.print("Forward with duty cycle: ");
    Serial.println(dutyCycle);
    delay(500);
  }
}
