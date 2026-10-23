"""
experiment_anomaly.py — uji deteksi anomali AI pada sistem PID-iTCLab (simulasi).

Data latih : operasi normal 1500 s dengan beberapa perubahan setpoint.
Data uji   : 1200 s dengan 2 gangguan yang disuntikkan:
   (a) t = 400–430 s : sensor T1 "glitch" +3 °C (kabel longgar)
   (b) t ≥ 800 s     : efisiensi heater turun 40 % (Kp 0.5 -> 0.3), mis. heater rusak
Output: img/anomaly_detection.png, anomaly_hasil.txt
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "UTS", "05-Pendukung-iTCLab", "03-Kit-iTCLab"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "UTS", "05-Pendukung-iTCLab", "04-Sistem-Kendali-PID"))
from itclab_sim import iTCLabSim                  # noqa: E402
from pid_controller import PID                    # noqa: E402
from ai_anomaly_detector import ArxAnomalyDetector  # noqa: E402


def run(n, sp_fn, seed, glitch=None, kp_drop_at=None):
    lab = iTCLabSim(seed=seed)
    pid = PID(10.0, 50.0, 1.0)
    T, Q, SP = np.zeros(n), np.zeros(n), np.zeros(n)
    for k in range(n):
        if kp_drop_at is not None and k == kp_drop_at:
            lab.Kp = 0.3
        meas = lab.T1
        if glitch and glitch[0] <= k < glitch[1]:
            meas += 3.0
        T[k], SP[k] = meas, sp_fn(k)
        Q[k] = pid.update(SP[k], T[k], 1.0)[0]
        lab.Q1(Q[k]); lab.step(1.0)
    return T, Q, SP


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs("img", exist_ok=True)
    sp_train = lambda k: [35, 45, 30, 40, 50][min(k // 300, 4)]
    Ttr, Qtr, _ = run(1500, sp_train, seed=10)
    det = ArxAnomalyDetector(delay=10).fit(Ttr, Qtr)

    sp_test = lambda k: 40 if k < 600 else 45
    T, Q, SP = run(1200, sp_test, seed=11, glitch=(400, 430), kp_drop_at=800)
    r, rs, alarm = det.detect(T, Q)

    t = np.arange(len(T))
    first = lambda a, b: next((i for i in range(a, b) if alarm[i]), None)
    g, f = first(400, 600), first(800, 1200)
    fa = int(alarm[:400].sum() + alarm[600:800].sum())
    txt = (f"Parameter ARX (a1,a2,b1,b2,c): {np.round(det.theta, 5).tolist()}\n"
           f"Sigma residual (rata-rata {det.window} sampel): {det.sigma:.4f} °C, ambang = {det.k*det.sigma:.4f} °C\n"
           f"Gangguan (a) sensor glitch t=400 s  -> terdeteksi t={g} s (delay {g-400 if g else '-'} s)\n"
           f"Gangguan (b) heater turun t=800 s   -> terdeteksi t={f} s (delay {f-800 if f else '-'} s)\n"
           f"Alarm palsu di periode normal: {fa} sampel")
    print(txt); open("anomaly_hasil.txt", "w").write(txt + "\n")

    fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    ax[0].plot(t, SP, "k--", label="SetPoint"); ax[0].plot(t, T, "r", lw=1, label="T1 terukur")
    ax[0].axvspan(400, 430, color="orange", alpha=.3, label="(a) sensor glitch")
    ax[0].axvspan(800, 1200, color="purple", alpha=.1, label="(b) heater melemah")
    ax[0].set_ylabel("°C"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ax[1].plot(t, Q, "b", lw=1); ax[1].set_ylabel("Q1 (%)"); ax[1].grid(alpha=.3)
    ax[2].plot(t, rs, "g", lw=1, label="residual rata-rata")
    ax[2].axhline(det.k * det.sigma, color="k", ls=":"); ax[2].axhline(-det.k * det.sigma, color="k", ls=":", label="ambang ±4σ")
    ax[2].fill_between(t, rs.min(), rs.max(), where=alarm, color="red", alpha=.2, label="ALARM")
    ax[2].set_ylabel("Residual (°C)"); ax[2].set_xlabel("Waktu (s)"); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
    fig.suptitle("Deteksi anomali berbasis model ARX pada PID-iTCLab (simulasi)")
    fig.tight_layout(); fig.savefig("img/anomaly_detection.png", dpi=120)


if __name__ == "__main__":
    main()
