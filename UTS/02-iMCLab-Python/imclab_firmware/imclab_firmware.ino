/*
  imclab_firmware.ino — firmware serial iMCLab untuk kendali dari Python
  KOMPATIBEL dengan protokol program dosen (imclab_naik_turun.ino), ditambah
  perintah untuk eksperimen kendali:

    Perintah dosen : 1 = ON (duty terakhir/200), 0 = OFF, + / - = PWM ±10,
                     PWM:xxx = set duty 0..255, R = tampilkan RPM & PWM
    Tambahan       : PWM <-255..255>  set PWM bertanda (negatif = mundur), balas nilai
                     RPM              balas RPM (angka saja, untuk Python)
                     CNT              jumlah pulsa encoder total
                     VER              versi firmware
                     X                stop
  RPM diukur dengan metode PERIOD (waktu 1 putaran = 2 pulsa) karena piringan
  hanya punya 2 lubang. Watchdog: motor berhenti jika 2 s tidak ada perintah
  (hanya aktif setelah perintah 'PWM <n>' dari Python).
*/
#include <Arduino.h>

const String VERS = "iMCLab-serial 2.0 (kelvin341)";
const int IN1 = 27, IN2 = 26, EN = 12, LED_PIN = 2;
const int ENC_PIN = 13, HOLES = 2;
const unsigned long DEBOUNCE_US = 500, TIMEOUT_US = 300000;
const int freq = 30000, res = 8, ch = 0;
const unsigned long WATCHDOG_MS = 2000;

volatile unsigned long nPulse = 0;
volatile unsigned long tPulse[HOLES + 1] = {0};
volatile int idx = 0;
int u = 0, lastDuty = 200;
bool watchdogOn = false;
unsigned long tLastCmd = 0;

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

float rpm() {                      // RPM dari median 5 waktu putaran terakhir
  unsigned long T = revMedianUs();
  return T ? (u < 0 ? -1 : 1) * 60.0e6 / (float)T : 0;
}

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
void motor(int v) {
  u = constrain(v, -255, 255);
  digitalWrite(IN1, u > 0); digitalWrite(IN2, u < 0);
  pwmWrite(abs(u));
  digitalWrite(LED_PIN, u != 0);
  if (u > 0) lastDuty = u;
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(20);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT); pinMode(LED_PIN, OUTPUT);
  pinMode(ENC_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_PIN), isr, FALLING);
  pwmBegin(); motor(0);
}

void loop() {
  unsigned long now = millis();
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n'); line.trim();
    String up = line; up.toUpperCase();
    tLastCmd = now;
    if      (up == "1")  { motor(lastDuty); Serial.printf("Motor ON, duty = %d\n", u); }
    else if (up == "0")  { motor(0); watchdogOn = false; Serial.println("Motor OFF, duty = 0"); }
    else if (up == "+")  { motor(min(255, abs(u) + 10)); Serial.printf("Kecepatan NAIK, duty = %d\n", u); }
    else if (up == "-")  { motor(max(0, abs(u) - 10)); Serial.printf("Kecepatan TURUN, duty = %d\n", u); }
    else if (up == "R")  { Serial.printf("RPM = %.1f | PWM = %d\n", rpm(), u); }
    else if (up.startsWith("PWM:")) { motor(constrain(up.substring(4).toInt(), 0, 255)); Serial.printf("Set duty = %d\n", u); }
    else if (up.startsWith("PWM ")) { motor(up.substring(4).toInt()); watchdogOn = true; Serial.println(u); }
    else if (up == "RPM") Serial.println(rpm(), 1);
    else if (up == "CNT") Serial.println(nPulse);
    else if (up == "VER" || up == "V") Serial.println(VERS);
    else if (up == "X")  { motor(0); watchdogOn = false; Serial.println("Stop"); }
    else if (up.length()) Serial.println("Perintah tidak dikenal: " + line);
  }
  if (watchdogOn && u != 0 && now - tLastCmd > WATCHDOG_MS) motor(0);   // Python crash -> motor berhenti
}
