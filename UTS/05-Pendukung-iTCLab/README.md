# 05 — Materi Pendukung: iTCLab, PID, dan IoT MQTT

Folder ini berisi latihan dari **Ebook IoT Jilid 1** (Kit iTCLab, kendali suhu). Isinya tidak termasuk syarat minimal UTS (yang memakai Kit iMCLab, modul 01–04), tetapi menjadi fondasi teori yang dipakai di modul iMCLab dan di UAS: model FOPDT, PID, tuning IMC, MQTT, dan digital twin.

| Folder | Isi | Hasil utama |
|---|---|---|
| [01-Konsep-IoT-MQTT](01-Konsep-IoT-MQTT/) | publisher/subscriber MQTT | 5/5 pesan diterima (broker lokal) |
| [02-Mikrokontroler-ESP32](02-Mikrokontroler-ESP32/) | 4 sketch dasar ESP32 | lolos cek sintaks core 2.x & 3.x |
| [03-Kit-iTCLab](03-Kit-iTCLab/) | firmware serial, client Python, simulator, step test | Kp 0,50 °C/%, τ 120 s, θ 10 s |
| [04-Sistem-Kendali-PID](04-Sistem-Kendali-PID/) | 5 set parameter PID | default ebook: overshoot 2,1 %, settling 74 s |
| [05-Pemrograman-IoT-PID](05-Pemrograman-IoT-PID/) | PID-iTCLab via MQTT + digital twin | setpoint & Kc diubah dari jarak jauh |

Simulator dan PID di folder 03–04 juga dipakai oleh skrip UAS (folder `UAS/02` dan `UAS/03`).
