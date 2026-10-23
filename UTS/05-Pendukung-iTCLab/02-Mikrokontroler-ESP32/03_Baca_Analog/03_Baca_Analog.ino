// 03_Baca_Analog — membaca sensor suhu T1 (GPIO 34) & T2 (GPIO 35) pada iTCLab
// Konversi mengikuti ebook: degC = ADC * 0.322265625, lalu /10 -> Celsius
const int pinT1 = 34;
const int pinT2 = 35;

void setup() {
  Serial.begin(115200);
}

void loop() {
  int raw1 = analogRead(pinT1);   // ADC 12 bit: 0..4095
  int raw2 = analogRead(pinT2);
  float t1 = raw1 * 0.322265625 / 10.0;
  float t2 = raw2 * 0.322265625 / 10.0;
  Serial.printf("ADC1=%4d  T1=%.2f C | ADC2=%4d  T2=%.2f C\n", raw1, t1, raw2, t2);
  delay(1000);
}
