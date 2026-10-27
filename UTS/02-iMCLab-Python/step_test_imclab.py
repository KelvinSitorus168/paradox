"""
step_test_imclab.py — Laporan Riset Modul 2, eksperimen P1:
uji step dari Python + identifikasi model FOPDT kecepatan motor iMCLab.

Step dilakukan di daerah kerja, BUKAN dari 0, supaya dead-zone (modul 1)
tidak ikut terukur sebagai "waktu tunda":
  simulator : PWM 100 -> 180
  kit asli  : PWM 180 -> 220. Data kit modul 1: dari diam motor baru berputar
              di PWM 170, jadi titik awal harus di atas itu.
Hasil kit disimpan ke model_kit.json dan dipakai otomatis oleh pid_python_imclab.py.

    python step_test_imclab.py --sim          # simulator
    python step_test_imclab.py --port COM5    # kit asli
"""
import argparse
import csv
import json
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize

TS = 0.02          # periode sampling Python (s)


def fopdt(t, u, Kp, tau, theta, y0, u0):
    y = np.full(len(t), y0)
    for k in range(1, len(t)):
        tk = t[k - 1] - theta
        uk = np.interp(tk, t, u) if tk >= t[0] else u0
        y[k] = y[k - 1] + (-(y[k - 1] - y0) + Kp * (uk - u0)) / tau * (t[k] - t[k - 1])
    return y


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--port")
    args = ap.parse_args()
    if args.sim:
        from imclab_sim import iMCLabSim
        lab = iMCLabSim(method="period")       # encoder 2 lubang, metode period
    else:
        from imclab import iMCLab
        lab = iMCLab(args.port)

    U0, U1 = (100, 180) if args.sim else (180, 220)
    PRE, DUR = (1.5, 3.0) if args.sim else (4.0, 4.0)   # kit: tau ~0,6 s -> perlu lebih lama
    t, u, y = [], [], []
    lab.pwm(U0)
    print(f"Menstabilkan motor di PWM {U0} selama {PRE:.0f} s ...")
    for _ in range(int(PRE / TS)):
        lab.pwm(U0)          # kirim ulang tiap siklus: firmware menghentikan motor jika 2 s tanpa perintah (watchdog)
        lab.step(TS)
    print(f"Step PWM {U0} -> {U1}, merekam {DUR:.0f} s ...")
    t0 = time.time()
    for k in range(int(DUR / TS)):
        uk = U1 if k * TS >= 0.5 else U0
        lab.pwm(uk)
        lab.step(TS) if args.sim else time.sleep(max(0, (k + 1) * TS - (time.time() - t0)))
        t.append(k * TS); u.append(uk); y.append(lab.rpm)
    lab.pwm(0)
    lab.close()
    t, u, y = map(np.array, (t, u, y))
    with open("step_test_data.csv" if args.sim else "step_test_data_kit.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_s", "pwm", "rpm"]); w.writerows(zip(t, u, y))

    y0 = y[t < 0.5].mean()
    if y0 <= 0:
        raise SystemExit("RPM sebelum step = 0: motor belum berputar. Cek catu daya motor, lalu ulangi.")
    obj = lambda p: np.sum((fopdt(t, u, p[0], p[1], p[2], y0, U0) - y) ** 2)
    r = minimize(obj, [30, 0.15, 0.03] if args.sim else [120, 0.5, 0.05],
                 bounds=[(1, 400), (0.01, 3), (0, 0.5)], method="Nelder-Mead")
    Kp, tau, theta = r.x
    rmse = np.sqrt(r.fun / len(t))
    txt = (f"Model FOPDT kecepatan iMCLab (PWM {U0}->{U1}): Kp = {Kp:.2f} RPM/PWM, "
           f"tau = {tau*1000:.0f} ms, theta = {theta*1000:.0f} ms, RMSE = {rmse:.1f} RPM")
    print(txt)
    tag = "" if args.sim else "_kit"
    open(f"hasil_identifikasi{tag}.txt", "w", encoding="utf-8").write(("SUMBER: simulasi\n" if args.sim else "SUMBER: kit asli\n") + txt + "\n")
    if not args.sim:
        json.dump({"Kp": Kp, "tau": tau, "theta": theta, "u0": U0, "u1": U1, "rpm0": float(y0), "rmse": rmse},
                  open("model_kit.json", "w"), indent=2)

    plt.figure(figsize=(9, 5))
    plt.step(t, y, "r-", where="post", lw=1, label="RPM terukur (dibaca Python tiap 20 ms)")
    plt.plot(t, fopdt(t, u, Kp, tau, theta, y0, U0), "k--", lw=2,
             label=f"FOPDT: Kp={Kp:.1f} RPM/PWM, τ={tau*1000:.0f} ms, θ={theta*1000:.0f} ms")
    ax2 = plt.gca().twinx(); ax2.step(t, u, "b:", where="post"); ax2.set_ylabel("PWM", color="b"); ax2.set_ylim(0, 300)
    plt.gca().set_xlabel("Waktu (s)")
    plt.sca(plt.gcf().axes[0]); plt.ylabel("RPM"); plt.xlabel("Waktu (s)"); plt.grid(alpha=.3); plt.legend(loc="lower right")
    plt.title("P1 — Uji step dari Python & identifikasi model" + ("" if args.sim else " (kit asli)"))
    plt.tight_layout(); plt.savefig(f"img/p1_step_identifikasi{tag}.png", dpi=120)


if __name__ == "__main__":
    main()
