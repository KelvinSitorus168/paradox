/*
  iMCLab_Blynk.ino — pengembangan dari program kelas (imclab_Blynk_kelas.ino):
  monitoring RPM + kendali PWM manual (SAMA dengan program dosen) DITAMBAH
  mode kendali kecepatan otomatis (PI) yang berjalan LOKAL di ESP32.

  Library: Blynk (Library Manager: "Blynk by Blynk", diuji v1.4.0) · Board: DOIT ESP32 DEVKIT V1
  WiFi harus 2,4 GHz. Isi token/WiFi hanya di salinan di luar repo, jangan di-commit.

  Datastream (V0–V3 sama dengan template kelas "IMCLab Test"):
    V0  RPM          double  0..10000   ESP32 -> app   Gauge + Chart
    V1  PWM          int     0..255     ESP32 -> app   Label/Chart
    V2  PWM slider   int     0..255     app -> ESP32   Slider (mode manual)
    V3  ON/OFF       int     0/1        app -> ESP32   Switch
    --- tambahan ---
    V4  SetPoint RPM int     0..9000    app -> ESP32   Slider (mode PI)
    V5  Mode         int     0/1        app -> ESP32   Switch (0 manual, 1 PI)
    V6  Kc           double             app -> ESP32   Numeric input
    V7  tauI (s)     double             app -> ESP32   Numeric input
    V8  Status       string             ESP32 -> app   Label
*/
#define BLYNK_TEMPLATE_ID   "TMPLxxxxxxx"        // dari Blynk.Console (jangan di-commit token asli!)
#define BLYNK_TEMPLATE_NAME "IMCLab Test"
#define BLYNK_AUTH_TOKEN    "ISI_AUTH_TOKEN"
#define BLYNK_PRINT Serial

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>

char ssid[] = "nama_wifi";
char pass[] = "password";

// ---------- pin iMCLab (dari program dosen) ----------
const int IN1 = 27, IN2 = 26, EN = 12, LED_PIN = 2;
const int ENC_PIN = 13, HOLES = 2;
const unsigned long DEBOUNCE_US = 500, TIMEOUT_US = 300000;
const int freq = 30000, res = 8, ch = 0;

// ---------- encoder: metode period (waktu 1 putaran) ----------
volatile unsigned long nPulse = 0;
volatile unsigned long tPulse[HOLES + 1] = {0};
volatile int idx = 0;
const int NREV = 5;                    // jumlah waktu putaran untuk median
volatile unsigned long revT[NREV] = {0}; // waktu putaran terakhir (us) -> median
volatile int ri = 0, nRev = 0, fresh = 0;   // fresh = pulsa sejak mulai berputar
void IRAM_ATTR isr() {
  unsigned long now = micros();
  int last = (idx + HOLES) % (HOLES + 1);
  unsigned long dt = now - tPulse[last];
  if (nPulse && dt < DEBOUNCE_US) return;
  // filter 1: interval < 30 % rata-rata setengah putaran terakhir = pulsa palsu.
  // (dibanding rata-rata, bukan interval sebelumnya, karena 2 lubang tidak tepat 180 derajat)
  if (nRev && dt < TIMEOUT_US && dt * 100 * HOLES < revT[(ri + NREV - 1) % NREV] * 30) return;
  if (nPulse && dt >= TIMEOUT_US) { nRev = 0; fresh = 0; }   // mulai lagi dari diam
  tPulse[idx] = now; idx = (idx + 1) % (HOLES + 1);
  nPulse++;
  if (++fresh > HOLES) { revT[ri] = now - tPulse[idx]; ri = (ri + 1) % NREV; if (nRev < NREV) nRev++; }
}
// filter 2: median 5 waktu putaran terakhir -> bacaan aneh akibat pulsa palsu tidak lolos
unsigned long revMedianUs() {
  unsigned long v[NREV];
  noInterrupts();
  for (int i = 0; i < NREV; i++) v[i] = revT[i];
  unsigned long tN = tPulse[(idx + HOLES) % (HOLES + 1)];
  int k = nRev;
  interrupts();
  if (k < NREV || micros() - tN > TIMEOUT_US) return 0;
  for (int i = 1; i < NREV; i++) {                 // insertion sort 5 elemen
    unsigned long x = v[i]; int j = i - 1;
    while (j >= 0 && v[j] > x) { v[j + 1] = v[j]; j--; }
    v[j + 1] = x;
  }
  return v[NREV / 2];
}

float readRPM() {                      // RPM dari median 5 waktu putaran terakhir
  unsigned long T = revMedianUs();
  return T ? 60.0e6 / (float)T : 0;
}

// ---------- state ----------
const float TS = 0.05;                   // periode PI 50 ms
float Kc = 0.013, tauI = 0.40;           // dari identifikasi kit asli (modul 02): Kp 93 RPM/PWM, tau 0,40 s
const float I_PRELOAD = 170;             // dead-zone kit: motor baru berputar dari diam di PWM ±170 (modul 01)
float sp = 0, rpm = 0, I = 0;
int dutyManual = 200, duty = 0, mode = 0;
bool motorOn = false;
BlynkTimer timer;

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
void applyMotor(int d) {
  duty = constrain(d, 0, 255);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);   // arah maju (sama dengan program dosen)
  pwmWrite(duty);
  digitalWrite(LED_PIN, duty > 0);
}

// ---------- loop kendali LOKAL 50 ms (tetap jalan walau internet putus) ----------
void controlTask() {
  rpm = readRPM();
  if (!motorOn) { applyMotor(0); I = 0; return; }
  if (mode == 0) { applyMotor(dutyManual); I = 0; return; }
  float e = sp - rpm;
  I += Kc / tauI * e * TS;
  float out = Kc * e + I;
  if (out > 255 || out < 0) { I -= Kc / tauI * e * TS; out = constrain(out, 0, 255); }
  applyMotor((int)round(out));
}

void sendTask() {                        // 500 ms -> cloud
  Blynk.virtualWrite(V0, rpm);
  Blynk.virtualWrite(V1, duty);
}

void status() {
  String s = String(motorOn ? "ON" : "OFF") + (mode ? " | PI SP=" + String(sp, 0) : " | manual PWM=" + String(dutyManual));
  Blynk.virtualWrite(V8, s);
  Serial.println(s);
}

BLYNK_WRITE(V2) { dutyManual = constrain(param.asInt(), 0, 255); status(); }
BLYNK_WRITE(V3) { motorOn = param.asInt(); I = mode ? I_PRELOAD : 0; status(); }
BLYNK_WRITE(V4) { sp = param.asFloat(); status(); }
BLYNK_WRITE(V5) { mode = param.asInt(); I = mode ? I_PRELOAD : 0; status(); }
BLYNK_WRITE(V6) { if (param.asFloat() > 0) Kc = param.asFloat(); }
BLYNK_WRITE(V7) { if (param.asFloat() > 0) tauI = param.asFloat(); }

BLYNK_CONNECTED() {                      // ambil nilai terakhir dari server saat (re)connect
  Blynk.syncVirtual(V2, V3, V4, V5, V6, V7);
}

void setup() {
  Serial.begin(115200);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT); pinMode(LED_PIN, OUTPUT);
  pinMode(ENC_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_PIN), isr, FALLING);
  pwmBegin(); applyMotor(0);
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  timer.setInterval(50L, controlTask);
  timer.setInterval(500L, sendTask);
}

void loop() {
  Blynk.run();       // jangan virtualWrite langsung di loop() (flood)
  timer.run();
}
