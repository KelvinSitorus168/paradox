/*
  04_Karakterisasi_Otomatis.ino — eksperimen otomatis untuk laporan riset (data kit asli):
   (A) kurva statis : PWM 0..255 (step 10), tunggu 2 s, rata-rata RPM selama 1 s  (±80 s)
   (B) respons step : setelah motor diam 15 s, PWM 0 -> 200, catat RPM (metode period) tiap 10 ms selama 3 s
   (C) kurva turun  : PWM 250..0 (step 10), tunggu 3 s, rata-rata RPM 1 s -> histeresis gesekan (±110 s)
  Output CSV di Serial Monitor -> salin semua teks ke file data_kit.csv, lalu:
      python analisis_karakterisasi.py --csv data_kit.csv
*/
const int IN1 = 27, IN2 = 26, EN = 12;
const int ENC_PIN = 13, HOLES = 2;
const unsigned long DEBOUNCE_US = 500, TIMEOUT_US = 300000;
const int freq = 30000, res = 8, ch = 0;

volatile unsigned long pulses = 0, nPulse = 0;
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
  if (++fresh > HOLES) { revT[ri] = now - tPulse[idx]; ri = (ri + 1) % NREV; if (nRev < NREV) nRev++; } pulses++;
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

float rpmPeriod() {                      // RPM dari median 5 waktu putaran terakhir
  unsigned long T = revMedianUs();
  return T ? 60.0e6 / (float)T : 0;
}
float rpmWindow(unsigned long ms) {
  noInterrupts(); pulses = 0; interrupts();
  delay(ms);
  noInterrupts(); unsigned long p = pulses; interrupts();
  return p / (float)HOLES / (ms / 1000.0) * 60.0;
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

void setup() {
  Serial.begin(115200);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(ENC_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_PIN), isr, FALLING);
  pwmBegin();
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  delay(2000);

  Serial.println("# A: kurva statis");
  Serial.println("pwm,rpm");
  for (int d = 0; d <= 255; d += 10) {
    pwmWrite(d); delay(2000);
    Serial.printf("%d,%.1f\n", d, rpmWindow(1000));
  }
  // motor meluncur bebas (coasting) saat PWM 0 -> tunggu sampai benar-benar diam (temuan uji variasi PWM)
  pwmWrite(0); delay(15000);

  Serial.println("# B: respons step PWM 0 -> 200");
  Serial.println("t_ms,rpm");
  unsigned long t0 = millis();
  pwmWrite(200);
  for (int k = 0; k < 300; k++) {          // 3 s (tau kit ~0,6 s -> 4 tau ~2,5 s)
    while (millis() - t0 < (unsigned long)k * 10) {}
    Serial.printf("%d,%.1f\n", k * 10, rpmPeriod());
  }

  // (C) motor sedang berputar -> turunkan PWM bertahap: di PWM berapa motor berhenti?
  Serial.println("# C: kurva turun (motor sudah berputar)");
  Serial.println("pwm,rpm");
  for (int d = 250; d >= 0; d -= 10) {
    pwmWrite(d); delay(3000);               // turun lambat karena coasting -> tunggu lebih lama
    Serial.printf("%d,%.1f\n", d, rpmWindow(1000));
  }
  pwmWrite(0);
  Serial.println("# selesai");
}

void loop() {}
