// 04_WiFi_Connect — menghubungkan ESP32 ke WiFi (dasar untuk IoT/MQTT)
#include <WiFi.h>

const char* ssid     = "NAMA_WIFI";      // ganti
const char* password = "PASSWORD_WIFI";  // ganti

void setup() {
  Serial.begin(115200);
  Serial.printf("Menghubungkan ke %s", ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi terhubung!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("RSSI: ");
  Serial.println(WiFi.RSSI());
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Koneksi putus, mencoba ulang...");
    WiFi.reconnect();
  }
  delay(5000);
}
