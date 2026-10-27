SUMBER: kit asli

Model: Kp=93.3 RPM/PWM, tau=0.403 s, theta=0.032 s [model_kit.json (uji step P1 di kit)]

PI-SIMC: Kc = 0.01298 PWM/RPM, tauI = 0.403 s

| Kasus | Overshoot →4000 | Settling ±5 % (s) | Galat 1 s akhir | Overshoot →7000 | Settling ±5 % (s) | Galat 1 s akhir | Overshoot →5000 | Settling ±5 % (s) | Galat 1 s akhir |
|---|---|---|---|---|---|---|---|---|---|
| PI + feedforward, Ts=50 ms | 4.8 % | 0.45 | 6 RPM | 16.4 % | 0.95 | 15 RPM | 18.4 % | 1.55 | 22 RPM |
| PI saja, Ts=50 ms | 1.2 % | 2.25 | 34 RPM | 1.7 % | 0.50 | 19 RPM | 3.6 % | 0.70 | 5 RPM |
| PI + feedforward, Ts=200 ms | 0.3 % | 0.70 | 7 RPM | 13.9 % | 0.90 | 22 RPM | 22.6 % | 1.60 | 9 RPM |
