"""
itclab_sim.py — simulator Kit iTCLab dengan model FOPDT
(First Order Plus Dead Time), memakai parameter dari Ebook IoT Jilid 1:

    tauP * dT/dt = -(T - Tss) + Kp * Q(t - thetaP)

    Kp     = 0.5  °C/%   (gain proses)
    tauP   = 120  s      (konstanta waktu)
    thetaP = 10   s      (waktu tunda)
    Tss    = 23   °C     (suhu ruang)

Antarmuka sama dengan itclab.py. Waktu disimulasikan: setiap
pemanggilan step(dt) memajukan waktu simulasi sebesar dt detik.
"""
from collections import deque

import numpy as np


class iTCLabSim:
    def __init__(self, Kp=0.5, tauP=120.0, thetaP=10.0, Tss=23.0, dt=1.0, noise=0.05, seed=0):
        self.Kp, self.tauP, self.thetaP, self.Tss = Kp, tauP, thetaP, Tss
        self.dt = dt
        self.noise = noise
        self.rng = np.random.default_rng(seed)
        self._T = [Tss, Tss]
        self._Q = [0.0, 0.0]
        nd = max(1, int(round(thetaP / dt)))
        self._buf = [deque([0.0] * nd, maxlen=nd), deque([0.0] * nd, maxlen=nd)]

    def _read(self, i):
        return self._T[i] + self.rng.normal(0, self.noise)

    @property
    def T1(self):
        return self._read(0)

    @property
    def T2(self):
        return self._read(1)

    def Q1(self, pct):
        self._Q[0] = float(np.clip(pct, 0, 100))
        return self._Q[0]

    def Q2(self, pct):
        self._Q[1] = float(np.clip(pct, 0, 100))
        return self._Q[1]

    def LED(self, pct):
        return pct

    def step(self, dt=None):
        """Majukan simulasi satu langkah waktu."""
        dt = dt or self.dt
        for i in range(2):
            q_delay = self._buf[i][0]          # Q dari thetaP detik lalu
            self._buf[i].append(self._Q[i])
            dT = (-(self._T[i] - self.Tss) + self.Kp * q_delay) / self.tauP
            self._T[i] += dT * dt

    def close(self):
        self.Q1(0)
        self.Q2(0)
