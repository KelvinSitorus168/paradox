/*
  00_Cari_Pin_Encoder.ino — VERIFIKASI pin encoder iMCLab (opsional)
  Program dosen memakai GPIO 13. Sketch ini membuktikannya secara eksperimen:
  hasil yang diharapkan ">>> PIN ENCODER = GPIO 13".
  Cara kerja: motor diputar (PWM 200), lalu setiap pin kandidat dibaca berulang-ulang.
  Pin yang nilainya berganti-ganti HIGH/LOW ratusan kali = pin encoder.
  Lalu motor dimatikan dan diukur lagi untuk memastikan (pin encoder harus diam).

  Upload, buka Serial Monitor 115200, tekan tombol EN/RESET di board.
  Catatan: adaptor DC harus tercolok agar motor berputar.
*/
const int IN1 = 27, IN2 = 26, EN = 12;      // pin motor (dari program dosen)
const int freq = 30000, res = 8, ch = 0;

// semua pin yang aman dibaca sebagai input (tanpa pin motor, flash, dan UART0)
const int CAND[] = {2, 4, 5, 13, 14, 15, 18, 19, 21, 22, 23, 25, 32, 33, 34, 35, 36, 39};
const int N = sizeof(CAND) / sizeof(CAND[0]);

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

long countEdges(int pin, unsigned long ms) {
  long edges = 0;
  int last = digitalRead(pin);
  unsigned long t0 = millis();
  while (millis() - t0 < ms) {
    int v = digitalRead(pin);
    if (v != last) { edges++; last = v; }
  }
  return edges;
}

void scan(long* out) {
  for (int i = 0; i < N; i++) out[i] = countEdges(CAND[i], 500);
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  for (int i = 0; i < N; i++) pinMode(CAND[i], CAND[i] >= 34 ? INPUT : INPUT_PULLUP);  // 34-39 tanpa pull-up
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pwmBegin();

  long on[N], off[N];
  Serial.println("\n=== Cari pin encoder iMCLab ===");
  Serial.println("Motor BERPUTAR (PWM 200)...");
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW); pwmWrite(200);
  delay(1500);
  scan(on);

  Serial.println("Motor DIAM...");
  pwmWrite(0); digitalWrite(IN1, LOW);
  delay(1500);
  scan(off);

  Serial.println("\nGPIO | tepi/0,5s (motor jalan) | tepi/0,5s (motor diam)");
  int best = -1; long bestVal = 0;
  for (int i = 0; i < N; i++) {
    Serial.printf("%4d | %22ld | %20ld\n", CAND[i], on[i], off[i]);
    if (on[i] > bestVal && off[i] < 5) { bestVal = on[i]; best = i; }
  }
  if (best >= 0 && bestVal > 20) {
    Serial.printf("\n>>> PIN ENCODER = GPIO %d  (%ld tepi per 0,5 s saat motor jalan)\n", CAND[best], bestVal);
    Serial.println(">>> Ganti ENC_PIN di semua sketch dengan angka ini.");
  } else {
    Serial.println("\n>>> Tidak ada pin yang jelas. Cek adaptor DC tercolok & motor benar-benar berputar.");
  }
}

void loop() {}
