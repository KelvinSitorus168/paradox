// 02_PWM_Fade — mengatur kecerahan LED iTCLab (GPIO 26) dengan PWM (LEDC)
// Mendukung ESP32 Arduino core 2.x (seperti di ebook) dan 3.x.
const int ledPin     = 26;
const int freq       = 5000;
const int ledChannel = 0;
const int resolution = 8;   // 8 bit -> duty 0..255

void pwmBegin() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(ledPin, freq, resolution);
#else
  ledcSetup(ledChannel, freq, resolution);
  ledcAttachPin(ledPin, ledChannel);
#endif
}

void pwmWrite(int duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(ledPin, duty);
#else
  ledcWrite(ledChannel, duty);
#endif
}

void setup() {
  Serial.begin(115200);
  pwmBegin();
}

void loop() {
  for (int duty = 0; duty <= 255; duty++) { pwmWrite(duty); delay(10); }
  for (int duty = 255; duty >= 0; duty--) { pwmWrite(duty); delay(10); }
  Serial.println("Satu siklus fade selesai");
}
