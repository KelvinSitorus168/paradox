"""
step_test.py — uji step (step test) pada iTCLab dan identifikasi model FOPDT.

1. Heater Q1 dinyalakan 50% pada t = 10 s, dimatikan pada t = 600 s.
2. Suhu T1 dicatat setiap 1 s -> CSV + grafik.
3. Parameter Kp, tauP, thetaP diestimasi dengan curve fitting (scipy).

Pemakaian:
    python step_test.py --sim                 # pakai simulator
    python step_test.py --port COM5           # pakai kit iTCLab asli
"""
import argparse
import os
import csv
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize


def run(lab, sim, tf=900):
    t, T1, Q1 = [], [], []
    for k in range(tf + 1):
        q = 50.0 if 10 <= k < 600 else 0.0
        lab.Q1(q)
        t.append(k); T1.append(lab.T1); Q1.append(q)
        if sim:
            lab.step(1.0)
        else:
            time.sleep(1.0)
    lab.close()
    return np.array(t, float), np.array(T1), np.array(Q1)


def fopdt(t, Q, Kp, tauP, thetaP, T0):
    """Simulasi FOPDT diskrit (Euler) untuk curve fitting."""
    y = np.full(len(t), T0)
    nd = int(round(thetaP))
    for k in range(1, len(t)):
        q = Q[k - 1 - nd] if k - 1 - nd >= 0 else 0.0
        y[k] = y[k - 1] + (-(y[k - 1] - T0) + Kp * q) / tauP * (t[k] - t[k - 1])
    return y


def identify(t, T, Q):
    """Grid search thetaP (bilangan bulat, karena delay diskrit) + optimasi Kp & tauP."""
    T0 = T[:10].mean()
    best = None
    for th in range(0, 31):
        obj = lambda p: np.sum((fopdt(t, Q, p[0], p[1], th, T0) - T) ** 2)
        r = minimize(obj, x0=[0.4, 100.0], bounds=[(0.05, 2), (10, 500)], method="L-BFGS-B")
        if best is None or r.fun < best[1]:
            best = ((r.x[0], r.x[1], th), r.fun)
    return best[0], T0, best[1]


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--port", default=None)
    args = ap.parse_args()

    if args.sim:
        from itclab_sim import iTCLabSim
        lab = iTCLabSim()
    else:
        from itclab import iTCLab
        lab = iTCLab(args.port)

    t, T, Q = run(lab, args.sim)
    with open("step_test_data.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_s", "Q1_pct", "T1_C"])
        w.writerows(zip(t, Q, np.round(T, 3)))

    (Kp, tauP, thetaP), T0, sse = identify(t, T, Q)
    rmse = np.sqrt(sse / len(t))
    print(f"Hasil identifikasi FOPDT: Kp={Kp:.3f} C/%  tauP={tauP:.1f} s  thetaP={thetaP:.1f} s  (RMSE={rmse:.3f} C)")

    yfit = fopdt(t, Q, Kp, tauP, thetaP, T0)
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    ax[0].plot(t, T, "r.", ms=2, label="T1 terukur")
    ax[0].plot(t, yfit, "k-", lw=1.5, label=f"FOPDT fit (Kp={Kp:.2f}, τp={tauP:.0f}s, θp={thetaP:.0f}s)")
    ax[0].set_ylabel("Suhu (°C)"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].step(t, Q, "b-", where="post", label="Q1 heater")
    ax[1].set_ylabel("Heater (%)"); ax[1].set_xlabel("Waktu (s)"); ax[1].legend(); ax[1].grid(alpha=.3)
    fig.suptitle("Step Test iTCLab" + (" (simulasi)" if args.sim else ""))
    fig.tight_layout()
    fig.savefig("img/step_test.png", dpi=120)


if __name__ == "__main__":
    main()
