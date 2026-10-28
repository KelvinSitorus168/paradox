# Robotika — Portofolio UTS & UAS

**Nama:** Kelvin Sitorus · **NPM:** 24081010341
**Program Studi:** Informatika — UPN "Veteran" Jawa Timur
**Mata Kuliah:** Robotika · **Dosen:** Prof. Basuki Rahmat

Repositori ini berisi Project Report hasil belajar saya di mata kuliah Robotika. Isinya mulai dari pemrograman Kit iMCLab: motor DC, Python, Blynk, dan OTA (UTS) sampai integrasi AI–IoT dan Robot Cerdas Bela Negara (BNU) dengan YOLOv8–DeepSORT (UAS). Setiap folder kemajuan berisi ringkasan materi, kode, hasil percobaan, grafik, dan daftar kemampuan yang sudah dikuasai.

📄 **Laporan utama:** [Project Report UTS](UTS/PROJECT_REPORT_UTS.md) · [Project Report UAS](UAS/PROJECT_REPORT_UAS.md)

## Sorotan Hasil
| | |
|---|---|
| UTS M1 — karakterisasi motor iMCLab | kit asli: start dari diam di PWM 170, jenuh 11.880 RPM, τ ≈ 0,6 s; encoder 2 lubang → metode period |
| UTS M2 — PI dari Python | kit asli: Kp 93 RPM/PWM, τ 0,4 s; error akhir ≤ 22 RPM; feedforward mempercepat start 1,65 s → 0,70 s (simulasi: loop 200 ms tidak stabil) |
| UTS M3 — Blynk | kit asli: PI via Blynk menjaga RPM ≤ 0,33 % dari setpoint; simulasi: PI lokal IAE 497 vs cloud (0,3 s) 27.269 → kendali harus lokal |
| UTS M4 — OTA Blynk.Air | v1.0.0 → v1.1.0 berhasil di kit asli (Blynk: *Success*), motor berhenti sebelum update |
| UAS — PID dituning Deep Learning | IAE 620 (terbaik), settling 68 s, overshoot 1,1 % |
| UAS — Deteksi anomali AI–IoT | sensor glitch 4 s, heater melemah 8 s, 0 alarm palsu |
| UAS — YOLOv8 + DeepSORT | ID objek stabil 119/120 frame, perintah robot otomatis via MQTT |

## Struktur & Status
| Bagian | Folder | Isi | Status |
|---|---|---|---|
| UTS | [01 iMCLab Pemrograman Dasar](UTS/01-iMCLab-Pemrograman-Dasar/) | PWM, arah, encoder, karakterisasi motor | ✅ · ✅ uji kit |
| UTS | [02 iMCLab Python](UTS/02-iMCLab-Python/) | serial ESP32↔Python, identifikasi, PI | ✅ · ✅ uji kit |
| UTS | [03 iMCLab Blynk](UTS/03-iMCLab-Blynk/) | dashboard Blynk, PI lokal, analisis latensi | ✅ · ✅ uji kit (⬜ internet putus, latensi) |
| UTS | [04 OTA Blynk](UTS/04-OTA-Blynk/) | Blynk.Air v1.0.0 → v1.1.0, ArduinoOTA | ✅ · ✅ OTA berhasil di kit |
| UTS | [05 Pendukung iTCLab](UTS/05-Pendukung-iTCLab/) | MQTT, ESP32, iTCLab, PID, IoT (Ebook Jilid 1) | ✅ |
| UTS | [Referensi dosen](UTS/referensi_dosen/) | program kelas iMCLab (serial, Python, Blynk), acuan pin | — |
| UAS | [01 Deep Learning Dasar](UAS/01-Deep-Learning-Dasar/) | XOR Keras | ✅ |
| UAS | [02 Tuning PID dengan DL](UAS/02-Tuning-PID-Deep-Learning/) | reproduksi ebook + DL auto-tuner | ✅ sim |
| UAS | [03 Integrasi AI–IoT](UAS/03-Integrasi-AI-IoT/) | deteksi anomali ARX + node AI MQTT | ✅ sim + MQTT |
| UAS | [04 Robot BNU Gen I](UAS/04-Robot-BNU-Generasi-1/) | firmware NodeMCU, web control, simulasi | ✅ sim · ⬜ robot |
| UAS | [05 Robot BNU Gen II](UAS/05-Robot-BNU-Gen2-YOLOv8-DeepSORT/) | YOLOv8, DeepSORT, firmware ESP32 | ✅ · ⬜ robot |
| UAS | [06 Mobile Robot & ROS](UAS/06-Mobile-Robot-ROS/) | kinematika diff vs omni, node ROS 2 | ✅ · ⬜ ROS |

✅ selesai · ⬜ menunggu uji hardware/akun saat praktikum

> **Catatan metode:** modul UTS 01–04 sudah diuji di **kit iMCLab asli** (27–28 Oktober 2026); data kit dan simulasi dipisahkan di tiap laporan (parameter simulasi ternyata berbeda jauh dari kit). Modul UAS dan analisis perbandingan masih berasal dari simulasi (model motor DC, model FOPDT iTCLab dari ebook), digital twin, dan broker MQTT lokal; uji robot/ROS menunggu praktikum. Seluruh sketch Arduino buatan sendiri lolos cek sintaks untuk ESP32 core 2.x & 3.x. Token Blynk dan WiFi tidak ada di repo (placeholder).

## Cara Menjalankan
```bash
pip install -r requirements.txt
python UTS/01-iMCLab-Pemrograman-Dasar/analisis_karakterisasi.py
python UTS/02-iMCLab-Python/pid_python_imclab.py --sim
python UTS/03-iMCLab-Blynk/analisis_blynk.py
python UAS/02-Tuning-PID-Deep-Learning/dl_pid_autotune.py
python UAS/03-Integrasi-AI-IoT/experiment_anomaly.py
```
Kit asli: ganti `--sim` dengan `--port COM5` (sesuaikan port). Firmware `.ino` dibuka di Arduino IDE dengan board *DOIT ESP32 DEVKIT V1* (atau *NodeMCU 1.0* untuk Robot BNU Gen I) dan library **PubSubClient** (MQTT) atau **Blynk** (modul UTS 03–04).

## Referensi Utama
- Basuki Rahmat & Muljono, *Pemrograman Internet of Things (IoT) dengan Arduino dan Python*, Jilid 1 & 2, CV. Eureka Media Aksara.
- Basuki Rahmat, *Integrasi AI dan IoT pada Sistem Kendali Cerdas* (materi kuliah).
- Basuki Rahmat, *Produk Robot Cerdas Bela Negara BNU* — Generasi I, Generasi II (Deep Learning), Generasi II (YOLOv8–DeepSORT), 2025.
- A. A. Rasjid, B. Rahmat, A. N. Sihananto, "Implementasi YOLOv8 Pada Robot Deteksi Objek," *JTSI*, 1(3), 2024. https://doi.org/10.47134/jtsi.v1i3.2969
- J. Azeta et al., "An Android Based Mobile Robot for Monitoring and Surveillance," *Procedia Manufacturing* 35 (2019) 1129–1134.
- R. Raudmäe et al., "ROBOTONT – Open-source and ROS-supported omnidirectional mobile robot for education and research," *HardwareX* 14 (2023) e00436. https://doi.org/10.1016/j.ohx.2023.e00436
- Basuki Rahmat, *iMCLab — Internet-Based Motor Control Lab*. https://github.com/bsrahmat/imclab
- Kode referensi dosen: https://github.com/bsrahmat/ebook-10-11 · https://github.com/bsrahmat/itclab-01 · https://github.com/bsrahmat/imclab
