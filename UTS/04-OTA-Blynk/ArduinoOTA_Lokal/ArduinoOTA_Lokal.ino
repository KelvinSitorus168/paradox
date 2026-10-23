/*
  ArduinoOTA_Lokal.ino — pembanding: OTA lewat jaringan lokal (tanpa cloud)
  Setelah upload pertama via USB, board muncul di Arduino IDE:
  Tools > Port > Network ports > "imclab-kelvin at 192.168.x.x"
  Kelebihan: cepat, tidak perlu internet. Kekurangan: laptop & ESP32 harus satu WiFi.
*/
#include <WiFi.h>
#include <ArduinoOTA.h>

const char* ssid = "NAMA_WIFI";
const char* password = "PASSWORD_WIFI";
const int IN1 = 27, IN2 = 26, EN = 12;   // pin iMCLab (program dosen)

void setup() {
  Serial.begin(115200);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT); pinMode(EN, OUTPUT);
  digitalWrite(EN, LOW);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.waitForConnectResult() != WL_CONNECTED) { delay(3000); ESP.restart(); }

  ArduinoOTA.setHostname("imclab-kelvin");
  ArduinoOTA.setPassword("ganti-password-ota");          // wajib, agar orang lain di WiFi tidak bisa flash
  ArduinoOTA.onStart([]() { digitalWrite(EN, LOW); Serial.println("[OTA] mulai, motor dihentikan"); });
  ArduinoOTA.onProgress([](unsigned int p, unsigned int total) { Serial.printf("[OTA] %u%%\r", p * 100 / total); });
  ArduinoOTA.onEnd([]() { Serial.println("\n[OTA] selesai"); });
  ArduinoOTA.onError([](ota_error_t e) { Serial.printf("[OTA] error %u\n", e); });
  ArduinoOTA.begin();
  Serial.print("Siap OTA di "); Serial.println(WiFi.localIP());
}

void loop() {
  ArduinoOTA.handle();
}
