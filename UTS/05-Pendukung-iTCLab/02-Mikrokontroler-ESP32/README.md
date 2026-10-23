# 02 — Mikrokontroler DOIT ESP32 DEVKIT V1

**Bagian:** UTS · **Status:** ✅ Kode selesai (lolos cek sintaks) · ⬜ Uji di board

## Tujuan
Mengenal hardware ESP32 dan memprogramnya dengan Arduino IDE sebagai dasar Kit iTCLab dan robot BNU.

## Ringkasan Materi
- **ESP32**: dual-core 240 MHz, WiFi + Bluetooth, ADC 12-bit (0–4095), PWM lewat periferal **LEDC**, logika 3,3 V.
- **Pin pada iTCLab**: T1 = GPIO 34, T2 = GPIO 35 (ADC1, input saja), Q1 = GPIO 32, Q2 = GPIO 33 (heater, PWM), LED = GPIO 26.
- **ADC2 tidak bisa dipakai saat WiFi aktif.** Karena itu sensor iTCLab memakai pin ADC1 (32–39).
- **Setup Arduino IDE**: tambahkan URL board `https://espressif.github.io/arduino-esp32/package_esp32_index.json`, pasang paket *esp32 by Espressif*, pilih board **DOIT ESP32 DEVKIT V1**, baud 115200. Driver USB: CP210x atau CH340.

## Praktik / Kode
| Sketch | Isi |
|---|---|
| [`01_Blink`](01_Blink/01_Blink.ino) | LED onboard GPIO 2 berkedip tiap 1 s |
| [`02_PWM_Fade`](02_PWM_Fade/02_PWM_Fade.ino) | LED iTCLab (GPIO 26) redup–terang dengan PWM 5 kHz, 8 bit |
| [`03_Baca_Analog`](03_Baca_Analog/03_Baca_Analog.ino) | Membaca T1 & T2: `°C = ADC × 0.322265625 / 10` |
| [`04_WiFi_Connect`](04_WiFi_Connect/04_WiFi_Connect.ino) | Koneksi WiFi, tampilkan IP & RSSI, reconnect otomatis |

**Kompatibilitas versi:** ebook memakai API core 2.x (`ledcSetup` + `ledcAttachPin`). Di core 3.x API ini diganti `ledcAttach(pin, freq, res)` dan `ledcWrite(pin, duty)`. Semua sketch di repo ini memakai `#if ESP_ARDUINO_VERSION_MAJOR >= 3`, jadi bisa dikompilasi di kedua versi.

## Hasil
- Semua sketch lolos pemeriksaan sintaks C++ (`g++ -fsyntax-only` dengan header tiruan Arduino) untuk cabang core 2.x maupun 3.x.
- Rumus konversi suhu mengikuti ebook: `°C = ADC × 0.322265625 / 10`, dengan 0,322265625 = 1320/4096. Artinya ADC 12-bit (0–4095) dipetakan ke 0–132 °C. Konstanta ini perlu dicek ulang dengan termometer saat praktik.

## Yang Sudah Saya Kuasai
- [x] Menjelaskan fitur & konfigurasi pin ESP32 yang dipakai iTCLab
- [x] Menulis program GPIO, PWM (LEDC), ADC, dan WiFi
- [x] Menangani perbedaan API LEDC core 2.x vs 3.x
- [ ] Upload & uji langsung di board (dilakukan saat praktikum)

## Referensi
- Rahmat & Muljono, *Pemrograman IoT dengan Arduino dan Python* Jilid 1, Bab 2
