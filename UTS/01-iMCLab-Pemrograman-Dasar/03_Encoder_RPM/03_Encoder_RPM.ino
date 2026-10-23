/*
  03_Encoder_RPM.ino — membaca kecepatan motor iMCLab dengan encoder optik
  Piringan iMCLab hanya punya 2 LUBANG -> 2 pulsa per putaran. Dua metode dibandingkan:
   (1) WINDOW : hitung pulsa per 1 s (cara program dosen)  -> resolusi 30 RPM, lambat
   (2) PERIOD : ukur waktu 1 putaran penuh (2 pulsa) dengan micros() -> cepat & halus
  Output tiap 100 ms dalam format Serial Plotter Arduino IDE 2:
      PWMx10:...,rpm_window:...,rpm_period:...
  (PWM dikali 10 agar terlihat satu skala dengan RPM)
  Buka Tools > Serial Plotter, 115200 baud. Ketik angka 0..255 lalu SEND untuk mengubah PWM.
*/
const int IN1 = 27, IN2 = 26, EN = 12;
const int ENC_PIN = 13;                 // dari program dosen
const int HOLES = 2;                    // lubang piringan
const unsigned long DEBOUNCE_US = 500;
const unsigned long TIMEOUT_US = 300000; // > 0,3 s tanpa pulsa = berhenti
const int freq = 30000, res = 8, ch = 0;

volatile unsigned long pulses = 0;
volatile unsigned long tPulse[HOLES + 1] = {0};   // waktu pulsa terakhir (cincin)
volatile int idx = 0;
volatile unsigned long nPulse = 0;

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
  tPulse[idx] = now;
  idx = (idx + 1) % (HOLES + 1);
  nPulse++;
  if (++fresh > HOLES) { revT[ri] = now - tPulse[idx]; ri = (ri + 1) % NREV; if (nRev < NREV) nRev++; }
  pulses++;
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

int duty = 200;
unsigned long tPrint = 0, tWin = 0;
float rpmWin = 0;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(50);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(ENC_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_PIN), isr, FALLING);
  pwmBegin();
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);   // arah maju (sama dengan program dosen)
  pwmWrite(duty);
  tPrint = tWin = millis();
}

void loop() {
  unsigned long now = millis();
  if (now - tWin >= 1000) {             // metode WINDOW 1 s
    noInterrupts(); unsigned long p = pulses; pulses = 0; interrupts();
    rpmWin = p / (float)HOLES * 60.0 * 1000.0 / (now - tWin);
    tWin = now;
  }
  if (now - tPrint >= 100) {
    tPrint = now;
    Serial.printf("PWMx10:%d,rpm_window:%.1f,rpm_period:%.1f\n", duty * 10, rpmWin, rpmPeriod());
  }
  if (Serial.available()) {             // baca 1 baris utuh, abaikan baris kosong
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() > 0 && isDigit(line.charAt(0))) {
      duty = constrain(line.toInt(), 0, 255);
      pwmWrite(duty);
    }
  }
}
