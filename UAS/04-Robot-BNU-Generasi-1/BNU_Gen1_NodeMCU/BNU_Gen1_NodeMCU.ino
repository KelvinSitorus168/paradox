/*
  BNU_Gen1_NodeMCU.ino — Robot BNU Generasi I (RC car + NodeMCU ESP8266 + L298N)
  Dikendalikan lewat MQTT dari: IoT MQTT Panel (HP), web_control.html (laptop),
  atau program Python pengenal objek (Kinect / kamera).

  Motor M2 (belakang) = penggerak maju/mundur  -> IN1, IN2, ENA
  Motor M1 (depan)    = kemudi kiri/kanan      -> IN3, IN4, ENB

  Topic  : kelvin341/bnu/cmd     payload: MAJU | MUNDUR | KIRI | KANAN | STOP
           kelvin341/bnu/speed   payload: 0..1023 (PWM ESP8266)
  Status : kelvin341/bnu/status
  Library: PubSubClient, board "NodeMCU 1.0 (ESP-12E Module)"
*/
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "NAMA_WIFI";
const char* password = "PASSWORD_WIFI";
const char* mqttServer = "broker.hivemq.com";

#define IN1 D1
#define IN2 D2
#define IN3 D3
#define IN4 D4
#define ENA D5
#define ENB D6

WiFiClient espClient;
PubSubClient client(espClient);
int speedDrive = 800;
unsigned long lastCmd = 0;
const unsigned long FAILSAFE_MS = 1500;   // berhenti jika tidak ada perintah baru

void drive(int dir) {           // 1 maju, -1 mundur, 0 berhenti
  digitalWrite(IN1, dir > 0); digitalWrite(IN2, dir < 0);
  analogWrite(ENA, dir == 0 ? 0 : speedDrive);
}
void steer(int dir) {           // 1 kanan, -1 kiri, 0 lurus
  digitalWrite(IN3, dir > 0); digitalWrite(IN4, dir < 0);
  analogWrite(ENB, dir == 0 ? 0 : 1023);
}

void execute(const String& c) {
  if      (c == "MAJU")   { steer(0);  drive(1); }
  else if (c == "MUNDUR") { steer(0);  drive(-1); }
  else if (c == "KIRI")   { steer(-1); drive(1); }
  else if (c == "KANAN")  { steer(1);  drive(1); }
  else                    { steer(0);  drive(0); }
  client.publish("kelvin341/bnu/status", c.c_str());
}

void callback(char* topic, byte* payload, unsigned int len) {
  String msg; for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
  msg.trim(); msg.toUpperCase();
  if (String(topic).endsWith("/speed")) { speedDrive = constrain(msg.toInt(), 0, 1023); return; }
  lastCmd = millis();
  execute(msg);
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect(("BNU1-" + String(ESP.getChipId())).c_str())) {
      client.subscribe("kelvin341/bnu/cmd");
      client.subscribe("kelvin341/bnu/speed");
      client.publish("kelvin341/bnu/status", "ONLINE");
    } else delay(3000);
  }
}

void setup() {
  Serial.begin(115200);
  int pins[] = {IN1, IN2, IN3, IN4, ENA, ENB};
  for (int p : pins) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println(WiFi.localIP());
  client.setServer(mqttServer, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
  if (lastCmd && millis() - lastCmd > FAILSAFE_MS) { execute("STOP"); lastCmd = 0; }
}
