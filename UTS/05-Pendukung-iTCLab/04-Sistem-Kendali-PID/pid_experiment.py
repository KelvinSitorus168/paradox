"""
pid_experiment.py — membandingkan beberapa set parameter PID pada iTCLab
(simulasi FOPDT Kp=0.5, tauP=120 s, thetaP=10 s dari ebook).

Skenario: setpoint 23 °C -> 40 °C pada t = 10 s, durasi 900 s.
Metrik : overshoot, rise time (10-90 %), settling time (±0.5 °C), IAE.
Output : img/pid_comparison.png, img/pid_terms_default.png, pid_results.csv

Pemakaian:  python pid_experiment.py
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "03-Kit-iTCLab"))
from itclab_sim import iTCLabSim       # noqa: E402
from pid_controller import PID         # noqa: E402

Kp, tauP, thetaP = 0.5, 120.0, 10.0


def imc(tauC):
    """Aturan tuning IMC untuk model FOPDT."""
    Kc = (1 / Kp) * (tauP + 0.5 * thetaP) / (tauC + 0.5 * thetaP)
    tauI = tauP + 0.5 * thetaP
    tauD = tauP * thetaP / (2 * tauP + thetaP)
    return Kc, tauI, tauD


CASES = {
    "P saja (Kc=10)":                (10.0, 0.0, 0.0),
    "PI (Kc=10, τI=50)":             (10.0, 50.0, 0.0),
    "PID default ebook (10, 50, 1)": (10.0, 50.0, 1.0),
    "PID IMC agresif":               imc(max(0.1 * tauP, 0.8 * thetaP)),
    "PID IMC moderat":               imc(max(1.0 * tauP, 8.0 * thetaP)),
}


def simulate(Kc, tauI, tauD, tf=900, sp_hi=40.0):
    lab = iTCLabSim(Kp=Kp, tauP=tauP, thetaP=thetaP, seed=1)
    pid = PID(Kc, tauI, tauD)
    n = tf + 1
    t = np.arange(n, dtype=float)
    SP = np.where(t >= 10, sp_hi, 23.0)
    PV, OP, P, I, D = (np.zeros(n) for _ in range(5))
    for k in range(n):
        PV[k] = lab.T1
        OP[k], P[k], I[k], D[k] = pid.update(SP[k], PV[k], 1.0)
        lab.Q1(OP[k])
        lab.step(1.0)
    return t, SP, PV, OP, P, I, D


def metrics(t, SP, PV, sp_hi=40.0, t0=10):
    m = t >= t0
    tt, y = t[m] - t0, PV[m]
    y0, dy = 23.0, sp_hi - 23.0
    os_pct = max(0.0, (y.max() - sp_hi) / dy * 100)
    try:
        t10 = tt[np.argmax(y >= y0 + 0.1 * dy)]
        t90 = tt[np.argmax(y >= y0 + 0.9 * dy)] if (y >= y0 + 0.9 * dy).any() else np.nan
        rise = t90 - t10
    except ValueError:
        rise = np.nan
    outside = np.where(np.abs(y - sp_hi) > 0.5)[0]
    settle = np.nan if len(outside) and outside[-1] == len(y) - 1 else (tt[outside[-1] + 1] if len(outside) else 0.0)
    iae = np.sum(np.abs(SP[m] - y))
    sse = abs(np.mean(y[-60:]) - sp_hi)
    return os_pct, rise, settle, iae, sse


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs("img", exist_ok=True)
    rows = []
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for name, (Kc, tauI, tauD) in CASES.items():
        t, SP, PV, OP, P, I, D = simulate(Kc, tauI, tauD)
        os_pct, rise, settle, iae, sse = metrics(t, SP, PV)
        rows.append([name, round(Kc, 2), round(tauI, 1), round(tauD, 2),
                     round(os_pct, 1), round(rise, 0), settle if np.isnan(settle) else round(settle, 0),
                     round(iae, 0), round(sse, 2)])
        ax[0].plot(t, PV, lw=1.5, label=name)
        ax[1].plot(t, OP, lw=1, label=name)
        if name.startswith("PID default"):
            f2, a2 = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
            a2[0].plot(t, SP, "k--", label="SP"); a2[0].plot(t, PV, "r", label="PV (T1)")
            a2[0].set_ylabel("°C"); a2[0].legend(); a2[0].grid(alpha=.3)
            a2[1].plot(t, P, label="P"); a2[1].plot(t, I, label="I"); a2[1].plot(t, D, label="D")
            a2[1].plot(t, OP, "k", lw=1, label="OP")
            a2[1].set_ylabel("%"); a2[1].set_xlabel("Waktu (s)"); a2[1].legend(); a2[1].grid(alpha=.3)
            f2.suptitle("Kontribusi P, I, D — PID default ebook (simulasi)")
            f2.tight_layout(); f2.savefig("img/pid_terms_default.png", dpi=120)
    ax[0].plot(t, SP, "k--", lw=1, label="Setpoint")
    ax[0].set_ylabel("Suhu T1 (°C)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ax[1].set_ylabel("Heater Q1 (%)"); ax[1].set_xlabel("Waktu (s)"); ax[1].grid(alpha=.3)
    fig.suptitle("Perbandingan parameter PID pada iTCLab (simulasi FOPDT)")
    fig.tight_layout(); fig.savefig("img/pid_comparison.png", dpi=120)

    hdr = ["Kasus", "Kc", "tauI", "tauD", "Overshoot_%", "Rise_s", "Settling_s", "IAE", "Error_akhir_C"]
    with open("pid_results.csv", "w", newline="") as f:
        csv.writer(f).writerows([hdr] + rows)
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for r in rows:
        print("| " + " | ".join("–" if (isinstance(v, float) and np.isnan(v)) else str(v) for v in r) + " |")


if __name__ == "__main__":
    main()
