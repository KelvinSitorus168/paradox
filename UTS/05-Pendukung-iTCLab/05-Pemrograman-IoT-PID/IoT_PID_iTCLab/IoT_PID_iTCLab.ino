/*
  IoT_PID_iTCLab.ino — pemantauan & pengendalian PID-iTCLab via MQTT
  (berdasarkan Ebook IoT Jilid 1, Bab 6 C–D)

  Library: PubSubClient (Nick O'Leary)
  Broker : broker.hivemq.com : 1883

  Topic publish (setiap 1 s):
    <prefix>/Suhu1      suhu T1 (°C)
    <prefix>/Suhu2      suhu T2 (°C)
    <prefix>/Nilai_op   output PID / heater Q1 (%)
    <prefix>/SetPoint_now  setpoint yang sedang dipakai
  Topic subscribe (diatur dari IoT MQTT Panel / Python):
    <prefix>/SetPoint   setpoint baru (°C)
    <prefix>/Nilai_Kc, <prefix>/Nilai_tauI, <prefix>/Nilai_tauD
    <prefix>/autoSet    1 = kembali ke parameter default
    <prefix>/heater1    0/1 mode on-off manual (PID dimatikan)

  Prefix dibuat unik agar tidak bentrok dengan pengguna lain di broker publik.
*/
#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid     = "NAMA_WIFI";
const char* password = "PASSWORD_WIFI";
#define mqttServer "broker.hivemq.com"
#define mqttPort   1883
const String PREFIX = "kelvin341/itclab";

const int pinT1 = 34, pinT2 = 35, pinQ1 = 32, pinLED = 26;
const int freq = 5000, res = 8, chQ1 = 1, chLED = 0;
const float upper_temperature_limit = 58.0;

const float Kc0 = 10.0, tauI0 = 50.0, tauD0 = 1.0;
float Kc = Kc0, tauI = tauI0, tauD = tauD0;
float sp = 35.0, pv = 0, pv_last = 0, ierr = 0, op = 0;
bool manualMode = false; int manualHeater = 0;
unsigned long ts = 0;

WiFiClient espClient;
PubSubClient client(espClient);

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

float readTemp(int pin) {
  float s = 0;
  for (int i = 0; i < 10; i++) s += analogRead(pin) * 0.322265625 / 10.0;
  return s / 10.0;
}

float pid(float sp, float pv, float pv_last, float &ierr, float dt) {
  float KP = Kc, KI = (tauI > 0) ? Kc / tauI : 0, KD = Kc * tauD;
  float e = sp - pv;
  ierr += KI * e * dt;
  float out = KP * e + ierr - KD * (pv - pv_last) / dt;
  if (out < 0 || out > 100) { ierr -= KI * e * dt; out = constrain(out, 0, 100); }
  return out;
}

void callback(char* topic, byte* payload, unsigned int len) {
  String t = String(topic), v;
  for (unsigned int i = 0; i < len; i++) v += (char)payload[i];
  t.replace(PREFIX + "/", "");
  if      (t == "SetPoint")   sp   = v.toFloat();
  else if (t == "Nilai_Kc")   Kc   = v.toFloat();
  else if (t == "Nilai_tauI") tauI = v.toFloat();
  else if (t == "Nilai_tauD") tauD = v.toFloat();
  else if (t == "autoSet" && v.toInt() == 1) { Kc = Kc0; tauI = tauI0; tauD = tauD0; }
  else if (t == "heater1") { manualMode = true; manualHeater = v.toInt(); }
  else if (t == "mode" && v == "pid") manualMode = false;
  Serial.printf("[MQTT] %s = %s | SP=%.1f Kc=%.2f tauI=%.1f tauD=%.2f\n",
                t.c_str(), v.c_str(), sp, Kc, tauI, tauD);
}

void reconnect() {
  while (!client.connected()) {
    String id = "ESP32-iTCLab-" + String((uint32_t)ESP.getEfuseMac(), HEX);
    Serial.print("MQTT connect... ");
    if (client.connect(id.c_str())) {
      Serial.println("OK");
      const char* subs[] = {"SetPoint", "Nilai_Kc", "Nilai_tauI", "Nilai_tauD", "autoSet", "heater1", "mode"};
      for (auto s : subs) client.subscribe((PREFIX + "/" + s).c_str());
    } else {
      Serial.printf("gagal rc=%d, ulang 5 s\n", client.state());
      delay(5000);
    }
  }
}

void publishF(const char* name, float v) {
  client.publish((PREFIX + "/" + name).c_str(), String(v, 2).c_str());
}

void setup() {
  Serial.begin(115200);
  pwmAttach(pinQ1, chQ1); pwmAttach(pinLED, chLED);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi OK " + WiFi.localIP().toString());
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);
  pv_last = readTemp(pinT1);
  ts = millis();
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  unsigned long now = millis();
  if (now - ts >= 1000) {
    float dt = (now - ts) / 1000.0; ts = now;
    pv = readTemp(pinT1);
    float t2 = readTemp(pinT2);
    if (pv >= upper_temperature_limit) { op = 0; pwmWrite(pinLED, chLED, 255); }
    else {
      op = manualMode ? (manualHeater ? 50.0 : 0.0) : pid(sp, pv, pv_last, ierr, dt);
      pwmWrite(pinLED, chLED, 0);
    }
    pwmWrite(pinQ1, chQ1, int(op * 2.55));
    pv_last = pv;
    publishF("Suhu1", pv); publishF("Suhu2", t2);
    publishF("Nilai_op", op); publishF("SetPoint_now", sp);
  }
}
