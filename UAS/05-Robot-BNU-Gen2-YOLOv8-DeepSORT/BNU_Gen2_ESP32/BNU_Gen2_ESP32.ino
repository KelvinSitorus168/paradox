/*
  BNU_Gen2_ESP32.ino — Robot BNU Generasi II (ESP32 + L298N + 2 motor DC, differential drive)
  Otak (YOLOv8 + DeepSORT) berjalan di laptop; ESP32 hanya menerima perintah via MQTT.

  Topic : kelvin341/bnu/cmd   MAJU | MUNDUR | KIRI | KANAN | STOP | CARI
  Status: kelvin341/bnu/status
  Pin L298N: ENA=14 IN1=27 IN2=26 (motor kiri) | ENB=32 IN3=25 IN4=33 (motor kanan)
*/
#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "NAMA_WIFI";
const char* password = "PASSWORD_WIFI";
const char* mqttServer = "broker.hivemq.com";

const int ENA = 14, IN1 = 27, IN2 = 26;   // kiri
const int ENB = 32, IN3 = 25, IN4 = 33;   // kanan
const int FREQ = 1000, RES = 8, CH_A = 4, CH_B = 5;
const int SPEED = 180, TURN = 140, SEARCH = 110;   // duty 0..255
const unsigned long FAILSAFE_MS = 1000;

WiFiClient net;
PubSubClient client(net);
unsigned long lastCmd = 0;

void pwmAttach(int pin, int ch) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pin, FREQ, RES);
#else
  ledcSetup(ch, FREQ, RES); ledcAttachPin(pin, ch);
#endif
}
void pwmWrite(int pin, int ch, int duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, duty);
#else
  ledcWrite(ch, duty);
#endif
}

// kecepatan bertanda: + maju, - mundur
void motors(int left, int right) {
  digitalWrite(IN1, left > 0);  digitalWrite(IN2, left < 0);
  digitalWrite(IN3, right > 0); digitalWrite(IN4, right < 0);
  pwmWrite(ENA, CH_A, abs(left));
  pwmWrite(ENB, CH_B, abs(right));
}

void execute(const String& c) {
  if      (c == "MAJU")   motors(SPEED, SPEED);
  else if (c == "MUNDUR") motors(-SPEED, -SPEED);
  else if (c == "KIRI")   motors(-TURN, TURN);       // putar di tempat ke kiri
  else if (c == "KANAN")  motors(TURN, -TURN);
  else if (c == "CARI")   motors(-SEARCH, SEARCH);   // putar pelan mencari target
  else                    motors(0, 0);
  client.publish("kelvin341/bnu/status", c.c_str());
}

void callback(char*, byte* p, unsigned int n) {
  String m; for (unsigned int i = 0; i < n; i++) m += (char)p[i];
  m.trim(); m.toUpperCase();
  lastCmd = millis();
  execute(m);
}

void setup() {
  Serial.begin(115200);
  int outs[] = {IN1, IN2, IN3, IN4};
  for (int p : outs) pinMode(p, OUTPUT);
  pwmAttach(ENA, CH_A); pwmAttach(ENB, CH_B);
  motors(0, 0);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  client.setServer(mqttServer, 1883);
  client.setCallback(callback);
}

void loop() {
  while (!client.connected()) {
    if (client.connect(("BNU2-" + String((uint32_t)ESP.getEfuseMac(), HEX)).c_str())) {
      client.subscribe("kelvin341/bnu/cmd");
      client.publish("kelvin341/bnu/status", "ONLINE");
    } else delay(2000);
  }
  client.loop();
  if (lastCmd && millis() - lastCmd > FAILSAFE_MS) { execute("STOP"); lastCmd = 0; }  // aman jika laptop/koneksi putus
}
