"""
imclab_sim.py — simulator Kit iMCLab (Internet-Based Motor Control Lab).

Hardware asli (github.com/bsrahmat/imclab): ESP32 DevKit + IC driver motor
(H-bridge) + motor DC kecil + piringan dengan 2 LUBANG + sensor optik (encoder)
+ LED. Konfigurasi dari program dosen (UTS/referensi_dosen): IN1 = GPIO 27,
IN2 = GPIO 26, EN (PWM) = GPIO 12, encoder = GPIO 13 (FALLING), LED = GPIO 2.

Dua cara mengukur RPM (parameter `method`):
  "window" : hitung pulsa dalam jendela waktu tetap (cara program dosen, jendela 1 s)
  "period" : ukur waktu 1 putaran penuh (2 pulsa terakhir) -> cepat & halus
             walau lubangnya sedikit; 0 RPM jika tidak ada pulsa > timeout

Model fisika motor DC (induktansi diabaikan karena L/R << J/b):
    i      = (V - Ke*w) / R
    J dw/dt = Kt*i - b*w - Tc*sign(w)       (Tc = gesekan Coulomb -> dead-zone PWM)
    V      = duty/255 * (Vs - Vdrop)

PERHATIAN: nilai parameter di bawah adalah ASUMSI motor DC tipe 130 dengan
catu 12 V, bukan hasil ukur kit. Setelah praktikum, ganti dengan hasil
identifikasi dari kit asli (modul 02, step_test_imclab.py).

Antarmuka sama dengan imclab.py (kit asli):
    lab.pwm(-255..255)   lab.rpm   lab.step(dt)   lab.close()
"""
import numpy as np


class iMCLabSim:
    def __init__(self, Vs=12.0, Vdrop=1.8, R=3.0, Ke=0.0085, J=5e-6, b=1e-6, Tc=4e-3,
                 slots=2, window=1.0, method="window", timeout=0.3, seed=0):
        self.Vs, self.Vdrop, self.R, self.Ke, self.Kt = Vs, Vdrop, R, Ke, Ke
        self.J, self.b, self.Tc = J, b, Tc
        self.slots = slots              # jumlah lubang piringan encoder (kit: 2)
        self.window = window            # jendela hitung pulsa (metode "window")
        self.method = method
        self.timeout = timeout          # metode "period": dianggap berhenti jika tak ada pulsa
        self._pulse_t = []              # waktu pulsa terakhir (metode "period")
        self.rng = np.random.default_rng(seed)
        self.w = 0.0                    # kecepatan sudut (rad/s)
        self.theta = 0.0                # sudut total (rad) untuk encoder
        self.duty = 0
        self._pulses = 0
        self._t_win = 0.0
        self._rpm_meas = 0.0
        self.t = 0.0
        self.load = 0.0                 # torsi beban/gangguan (N·m), melawan arah putar

    # ---------------- aktuator ----------------
    def pwm(self, duty):
        self.duty = int(np.clip(duty, -255, 255))
        return self.duty

    # ---------------- sensor ----------------
    @property
    def rpm(self):
        """RPM terukur encoder (terkuantisasi, diperbarui tiap `window` detik)."""
        return self._rpm_meas

    @property
    def rpm_true(self):
        return self.w * 60 / (2 * np.pi)

    # ---------------- dinamika ----------------
    def _deriv(self, w):
        V = self.duty / 255 * (self.Vs - self.Vdrop)
        i = (V - self.Ke * w) / self.R
        Tm = self.Kt * i - self.b * w - self.load * (np.sign(w) if w else np.sign(self.duty))
        if abs(w) < 1e-3:                       # diam: gesekan statis menahan
            return 0.0 if abs(Tm) <= self.Tc else (Tm - np.sign(Tm) * self.Tc) / self.J
        return (Tm - np.sign(w) * self.Tc) / self.J

    def step(self, dt=0.01, h=5e-4):
        n = max(1, int(round(dt / h)))
        for _ in range(n):
            w_new = self.w + self._deriv(self.w) * h
            if self.w != 0 and np.sign(w_new) != np.sign(self.w) and abs(self.duty) == 0:
                w_new = 0.0                     # gesekan menghentikan, tidak berbalik
            self.w = w_new
            old = self.theta
            self.theta += self.w * h
            # pulsa encoder = jumlah lubang yang lewat sensor
            n_new = abs(int(np.floor(self.theta / (2 * np.pi / self.slots)))
                        - int(np.floor(old / (2 * np.pi / self.slots))))
            self._pulses += n_new
            self.t += h
            if self.method == "window":
                self._t_win += h
                if self._t_win >= self.window - 1e-12:
                    self._rpm_meas = self._pulses / self.slots / self._t_win * 60 * np.sign(self.w if self.w else 1)
                    self._pulses, self._t_win = 0, 0.0
            else:
                seg = 2 * np.pi / self.slots
                for j in range(n_new):              # waktu persis tiap lubang lewat (interpolasi)
                    b = (np.floor(old / seg) + 1 + j) * seg if self.theta > old else (np.ceil(old / seg) - 1 - j) * seg
                    frac = (b - old) / (self.theta - old)
                    self._pulse_t.append(self.t - h + frac * h)
                    self._pulse_t = self._pulse_t[-(self.slots + 1):]
                    if len(self._pulse_t) > self.slots:
                        rev_time = self._pulse_t[-1] - self._pulse_t[0]
                        self._rpm_meas = 60.0 / rev_time * np.sign(self.w if self.w else 1)
                if self._pulse_t and self.t - self._pulse_t[-1] > self.timeout:
                    self._rpm_meas = 0.0

    def close(self):
        self.pwm(0)
