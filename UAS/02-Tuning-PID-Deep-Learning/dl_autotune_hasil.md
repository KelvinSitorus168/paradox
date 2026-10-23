| Metode | Kc | τI (s) | τD (s) | Overshoot (%) | Rise (s) | Settling ±0.5 °C (s) | IAE | Aktivitas heater* |
|---|---|---|---|---|---|---|---|---|
| PID default ebook | 10.00 | 50.0 | 1.00 | 2.1 | 45 | 74 | 643 | 1.87 |
| PID IMC agresif | 14.71 | 125.0 | 4.80 | 1.3 | 53 | 193 | 765 | 10.11 |
| PID IMC moderat | 2.00 | 125.0 | 4.80 | 1.1 | 250 | 430 | 2129 | 1.29 |
| PID hasil Deep Learning | 13.33 | 43.9 | 1.08 | 1.1 | 41 | 68 | 620 | 2.63 |

*Aktivitas heater = simpangan baku perubahan Q1 per detik setelah t = 300 s (makin kecil makin halus).

R² data uji: Kc·Kp=0.859, τI/τp=0.979, τD/τp=0.995
