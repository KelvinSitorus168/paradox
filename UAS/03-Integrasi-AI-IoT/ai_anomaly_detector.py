"""
ai_anomaly_detector.py — modul AI di application layer IoT:
model ARX (AutoRegressive with eXogenous input) yang DIPELAJARI dari data normal
iTCLab untuk memprediksi suhu 1 langkah ke depan:

    T[k+1] = a1*T[k] + a2*T[k-1] + b1*Q[k-d] + b2*Q[k-d-1] + c

Jika selisih prediksi vs pengukuran (residual) melebihi ambang 4σ selama
beberapa sampel berturut-turut, sistem menandai ANOMALI.
"""
import numpy as np


class ArxAnomalyDetector:
    def __init__(self, delay=10, k_sigma=4.0, persist=5, window=30):
        self.d = delay
        self.k = k_sigma
        self.persist = persist
        self.window = window          # residual dirata-rata (CUSUM sederhana)
        self.theta = None
        self.sigma = None

    def _features(self, T, Q, k):
        return np.array([T[k], T[k - 1], Q[k - self.d], Q[k - self.d - 1], 1.0])

    def fit(self, T, Q):
        T, Q = np.asarray(T, float), np.asarray(Q, float)
        ks = range(self.d + 1, len(T) - 1)
        X = np.array([self._features(T, Q, k) for k in ks])
        y = T[self.d + 2:]
        self.theta, *_ = np.linalg.lstsq(X, y, rcond=None)
        res = y - X @ self.theta
        rs = np.convolve(res, np.ones(self.window) / self.window, mode="valid")
        self.sigma = rs.std()
        return self

    def residuals(self, T, Q):
        T, Q = np.asarray(T, float), np.asarray(Q, float)
        r = np.zeros(len(T))
        for k in range(self.d + 1, len(T) - 1):
            r[k + 1] = T[k + 1] - self._features(T, Q, k) @ self.theta
        return r

    def detect(self, T, Q):
        r = self.residuals(T, Q)
        rs = np.convolve(r, np.ones(self.window) / self.window, mode="full")[:len(r)]
        flag = np.abs(rs) > self.k * self.sigma
        alarm = np.zeros(len(r), bool)
        run = 0
        for i, f in enumerate(flag):
            run = run + 1 if f else 0
            alarm[i] = run >= self.persist
        return r, rs, alarm


class OnlineDetector:
    """Versi streaming untuk dipakai di node MQTT (satu sampel per panggilan)."""

    def __init__(self, model: ArxAnomalyDetector):
        self.m = model
        self.T, self.Q, self.r = [], [], []
        self.run = 0

    def update(self, T, Q):
        self.T.append(T); self.Q.append(Q)
        k = len(self.T) - 2
        if k < self.m.d + 1:
            return 0.0, False
        pred = self.m._features(self.T, self.Q, k) @ self.m.theta
        self.r.append(self.T[-1] - pred)
        rs = np.mean(self.r[-self.m.window:])
        self.run = self.run + 1 if abs(rs) > self.m.k * self.m.sigma else 0
        return rs, self.run >= self.m.persist
