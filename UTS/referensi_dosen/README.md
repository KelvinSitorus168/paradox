# Referensi dari Dosen

File program yang dibagikan Prof. Basuki Rahmat di kelas. Ini menjadi **acuan konfigurasi hardware** untuk seluruh modul UTS.

| File | Isi |
|---|---|
| [`imclab_naik_turun`](imclab_naik_turun/imclab_naik_turun.ino) | Kendali motor lewat Serial: `1` ON, `0` OFF, `+`/`-` PWM ±10, `PWM:xxx` |
| [`Tes_IMCLab_naik_turun.ipynb`](Tes_IMCLab_naik_turun.ipynb) | Program Python (deteksi port otomatis + mode interaktif) untuk sketch di atas |
| [`imclab_Blynk_kelas`](imclab_Blynk_kelas/imclab_Blynk_kelas.ino) | iMCLab + Blynk: RPM (V0), PWM (V1), slider PWM (V2), tombol ON/OFF (V3) |

**Konfigurasi kit yang dipastikan dari file dosen:**

| Item | Nilai |
|---|---|
| Motor | IN1 = GPIO 27, IN2 = GPIO 26, EN (PWM) = GPIO 12, PWM 30 kHz 8-bit |
| Arah "maju" | IN1 HIGH, IN2 LOW |
| Encoder | GPIO 13, `INPUT_PULLUP`, interrupt `FALLING`, debounce 500 µs |
| Lubang piringan | **2** per putaran |
| LED | GPIO 2 |
| USB-serial | Silicon Labs CP210x |

> Template ID dan auth token Blynk di `imclab_Blynk_kelas.ino` **disensor**. Token adalah kunci akses perangkat, jadi tidak boleh diunggah ke repo publik.

> ⚠️ Program dosen memakai API PWM ESP32 **core 2.x** (`ledcSetup`, `ledcAttachPin`). Di Arduino IDE dengan paket *esp32* versi 3.x, program ini akan gagal compile (`'ledcSetup' was not declared`). Solusinya: pasang paket esp32 versi **2.0.17** lewat Boards Manager, atau pakai versi di modul 01–04 yang sudah kompatibel dengan 2.x dan 3.x.
