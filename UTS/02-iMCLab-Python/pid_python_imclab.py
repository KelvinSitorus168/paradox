"""
pid_python_imclab.py — Laporan Riset Modul 2, eksperimen P2 & P3:
kendali kecepatan motor iMCLab dengan PID yang DIJALANKAN DI PYTHON
(ESP32 hanya sebagai antarmuka sensor/aktuator lewat serial).

Parameter PI dari aturan IMC berdasarkan model hasil P1:
    Kc = tau / (Kp * (tau_c + theta)),   tau_I = tau

Skenario (9 s): setpoint 0 -> 3000 (t=0,5 s) -> 6000 (t=3 s) -> 2000 (t=5,5 s),
gangguan beban (rem) pada t = 7–8,5 s.
  P2  : PI-IMC (Ts = 20 ms) vs P saja
  P3  : pengaruh periode loop Python: Ts = 20, 100, 200 ms

    python pid_python_imclab.py --sim
    python pid_python_imclab.py --port COM9        # kit asli -> lihat main_kit()

Versi kit asli (P2-kit & P3-kit) berbeda dari simulasi karena temuan modul 1:
  - motor baru berputar dari diam pada PWM 170 (gesekan statis), sehingga PI murni
    harus menunggu integrator naik dulu -> dibandingkan dengan PI + feedforward
    dari kurva statis modul 1;
  - encoder 1 kanal tidak tahu arah putar, jadi output PI dibatasi 0..255
    (tanpa membalik arah). Turun kecepatan hanya lewat coasting;
  - model diambil dari model_kit.json (hasil step_test_imclab.py --port).
Skenario kit (12 s): setpoint 0 -> 4000 (0,5 s) -> 7000 (4,5 s) -> 5000 (8 s).
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

KP, TAU, THETA = 43.09, 0.198, 0.0            # dari hasil_identifikasi.txt (P1)
T_END = 9.0


def sp_profile(t):
    return 0 if t < 0.5 else 3000 if t < 3 else 6000 if t < 5.5 else 2000


class PI:
    def __init__(self, Kc, tauI, lo=-255, hi=255):
        self.Kc, self.tauI, self.lo, self.hi, self.I = Kc, tauI, lo, hi, 0.0

    def update(self, sp, pv, dt):
        e = sp - pv
        if self.tauI:
            self.I += self.Kc / self.tauI * e * dt
        u = self.Kc * e + self.I
        if u > self.hi or u < self.lo:                 # anti-windup
            if self.tauI:
                self.I -= self.Kc / self.tauI * e * dt
            u = min(max(u, self.lo), self.hi)
        return u


def run(lab, ctrl, Ts, sim, disturb=True):
    t, sp, pv, u = [], [], [], []
    tk = 0.0
    t0 = time.time()
    while tk < T_END:
        if sim and disturb:
            lab.load = 0.003 if 7.0 <= tk < 8.5 else 0.0
        y = lab.rpm
        s = sp_profile(tk)
        uk = ctrl.update(s, y, Ts) if s > 0 else 0.0
        if s == 0:
            ctrl.I = 0.0
        lab.pwm(round(uk))
        t.append(tk); sp.append(s); pv.append(y); u.append(uk)
        if sim:
            lab.step(Ts)
        else:
            time.sleep(max(0, tk + Ts - (time.time() - t0)))
        tk += Ts
    lab.pwm(0)
    return tuple(map(np.array, (t, sp, pv, u)))


def seg_metrics(t, sp, pv, t_start, t_end, target, prev):
    m = (t >= t_start) & (t < t_end)
    tt, y = t[m] - t_start, pv[m]
    step = target - prev
    if step > 0:
        os_ = max(0, (y.max() - target) / step * 100)
    else:
        os_ = max(0, (target - y.min()) / -step * 100)
    band = 0.03 * abs(target)
    out = np.where(np.abs(y - target) > band)[0]
    settle = np.nan if len(out) and out[-1] == len(y) - 1 else (tt[out[-1] + 1] if len(out) else 0.0)
    sse = abs(np.mean(y[-10:]) - target)
    return os_, settle, sse


def make_lab(sim, port):
    if sim:
        from imclab_sim import iMCLabSim
        return iMCLabSim(method="period")      # sama dengan firmware (2 lubang, metode period)
    from imclab import iMCLab
    return iMCLab(port)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--port")
    ap.add_argument("--from-csv", action="store_true", help="kit asli: buat ulang tabel & grafik dari pid_kit_data.csv")
    args = ap.parse_args()
    if not args.sim:
        return main_kit(args.port, args.from_csv)

    tau_c = 0.1
    Kc = TAU / (KP * (tau_c + THETA))
    tauI = TAU
    print(f"PI-IMC: Kc = {Kc:.4f} PWM/RPM, tauI = {tauI:.3f} s  (tau_c = {tau_c} s)")

    cases = {
        "PI-IMC, Ts=20 ms": (PI(Kc, tauI), 0.02),
        "P saja, Ts=20 ms": (PI(Kc, 0), 0.02),
        "PI-IMC, Ts=100 ms": (PI(Kc, tauI), 0.10),
        "PI-IMC, Ts=200 ms": (PI(Kc, tauI), 0.20),
    }
    res = {}
    for name, (ctrl, Ts) in cases.items():
        res[name] = run(make_lab(args.sim, args.port), ctrl, Ts, args.sim)

    rows = ["| Kasus | Overshoot 0→3000 | Settling ±3 % (s) | Overshoot 3000→6000 | Settling (s) | Error akhir 2000 (RPM) | Turun saat beban (RPM) |",
            "|---|---|---|---|---|---|---|"]
    for name, (t, sp, pv, u) in res.items():
        o1, s1, _ = seg_metrics(t, sp, pv, 0.5, 3.0, 3000, 0)
        o2, s2, _ = seg_metrics(t, sp, pv, 3.0, 5.5, 6000, 3000)
        m3 = (t >= 6.5) & (t < 7.0)
        sse3 = abs(np.mean(pv[m3]) - 2000)
        md = (t >= 7.0) & (t < 8.5)
        dip = 2000 - pv[md].min()
        f = lambda x: "tidak tercapai" if np.isnan(x) else f"{x:.2f}"
        rows.append(f"| {name} | {o1:.1f} % | {f(s1)} | {o2:.1f} % | {f(s2)} | {sse3:.0f} | {dip:.0f} |")
    table = "\n".join(rows)
    print(table)
    open("hasil_pid_python.md", "w", encoding="utf-8").write(("SUMBER: simulasi\n\n" if args.sim else "SUMBER: kit asli\n\n")
                                           + f"PI-IMC: Kc = {Kc:.4f} PWM/RPM, tauI = {tauI:.3f} s\n\n" + table + "\n")

    os.makedirs("img", exist_ok=True)
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for name in ["PI-IMC, Ts=20 ms", "P saja, Ts=20 ms"]:
        t, sp, pv, u = res[name]
        ax[0].plot(t, pv, lw=1.3, label=name); ax[1].plot(t, u, lw=1, label=name)
    ax[0].step(t, sp, "k--", where="post", lw=1, label="setpoint")
    ax[0].axvspan(7, 8.5, color="orange", alpha=.15, label="gangguan beban")
    ax[0].set_ylabel("RPM"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ax[1].set_ylabel("PWM"); ax[1].set_xlabel("Waktu (s)"); ax[1].grid(alpha=.3)
    fig.suptitle("P2 — Kendali kecepatan iMCLab dari Python: PI-IMC vs P saja")
    fig.tight_layout(); fig.savefig("img/p2_pid_vs_p.png", dpi=120)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for name in ["PI-IMC, Ts=20 ms", "PI-IMC, Ts=100 ms", "PI-IMC, Ts=200 ms"]:
        t, sp, pv, u = res[name]
        ax.step(t, pv, where="post", lw=1.2, label=name)
    ax.step(res["PI-IMC, Ts=20 ms"][0], res["PI-IMC, Ts=20 ms"][1], "k--", where="post", lw=1, label="setpoint")
    ax.set_ylabel("RPM"); ax.set_xlabel("Waktu (s)"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    ax.set_title("P3 — Pengaruh periode loop Python (Ts) terhadap kendali")
    fig.tight_layout(); fig.savefig("img/p3_periode_loop.png", dpi=120)


# ---------------------------------------------------------------- kit asli
KIT_SP = [(0.5, 4000), (4.5, 7000), (8.0, 5000)]
KIT_END = 12.0
HERE = os.path.dirname(os.path.abspath(__file__))
STATIC_CSV = os.path.join(HERE, "..", "01-iMCLab-Pemrograman-Dasar", "data_kit.csv")


def kit_sp(t):
    s = 0
    for t0, v in KIT_SP:
        if t >= t0:
            s = v
    return s


def static_curve():
    """Kurva statis kit (modul 1, bagian A): PWM sebagai fungsi RPM, daerah berputar & belum jenuh."""
    pw, rp, sec = [], [], False
    for line in open(STATIC_CSV, encoding="utf-8"):
        line = line.strip()
        if line.startswith("# A"): sec = True; continue
        if line.startswith("# "): sec = sec and not line.startswith("# B"); continue
        if sec and line and line[0].isdigit():
            a, b = map(float, line.split(","))
            if b > 0 and a <= 230:
                pw.append(a); rp.append(b)
    return np.array(rp), np.array(pw)


def run_kit(lab, ctrl, Ts, ff=None):
    t, sp, pv, u, uff = [], [], [], [], []
    t0 = time.time(); k = 0
    while True:
        tk = time.time() - t0
        if tk >= KIT_END:
            break
        y = lab.rpm
        s = kit_sp(tk)
        f = float(np.interp(s, *ff)) if (ff is not None and s > 0) else 0.0
        if s > 0:
            ctrl.lo, ctrl.hi = -f, 255 - f          # anti-windup pada output total (FF + PI) 0..255
            uk = min(max(f + ctrl.update(s, y, Ts), 0), 255)
        else:
            uk, ctrl.I = 0.0, 0.0
        lab.pwm(round(uk))
        t.append(tk); sp.append(s); pv.append(y); u.append(uk); uff.append(f)
        k += 1
        time.sleep(max(0, k * Ts - (time.time() - t0)))
    lab.pwm(0)
    return tuple(map(np.array, (t, sp, pv, u, uff)))


def kit_metrics(t, sp, pv):
    out = []
    edges = [p for p, _ in KIT_SP] + [KIT_END]
    prev = 0
    for (ts, target), te in zip(KIT_SP, edges[1:]):
        m = (t >= ts) & (t < te)
        tt, y = t[m] - ts, pv[m]
        step = target - prev
        os_ = max(0, (y.max() - target) / step * 100) if step > 0 else max(0, (target - y.min()) / -step * 100)
        bad = np.where(np.abs(y - target) > 0.05 * target)[0]
        settle = np.nan if len(bad) and bad[-1] == len(y) - 1 else (tt[bad[-1] + 1] if len(bad) else 0.0)
        last = tt >= tt[-1] - 1.0
        mae = np.mean(np.abs(y[last] - target))
        out.append((target, os_, settle, mae)); prev = target
    return out




def load_kit_csv(names):
    """Baca ulang pid_kit_data.csv (hasil uji kit) untuk membuat tabel & grafik tanpa menjalankan motor."""
    d = {n: [] for n in names}
    for r in csv.DictReader(open(os.path.join(HERE, "pid_kit_data.csv"), encoding="utf-8")):
        d[r["kasus"]].append([float(r[k]) for k in ("t_s", "setpoint", "rpm", "pwm", "pwm_feedforward")])
    return {n: tuple(np.array(v).T) for n, v in d.items()}

def main_kit(port, from_csv=False):
    mfile = os.path.join(HERE, "model_kit.json")
    if os.path.exists(mfile):
        m = json.load(open(mfile)); Kp, tau, theta = m["Kp"], m["tau"], m["theta"]
        src = "model_kit.json (uji step P1 di kit)"
    else:
        Kp, tau, theta = 140.0, 0.6, 0.1
        src = "modul 1 E2/E3 (model_kit.json belum ada)"
    tau_c = max(0.3, theta)                     # SIMC; tau_c dibuat longgar karena gain plant berubah 84-213 RPM/PWM
    Kc = tau / (Kp * (tau_c + theta)); tauI = min(tau, 4 * (tau_c + theta))
    print(f"Model: Kp={Kp:.1f} RPM/PWM, tau={tau:.3f} s, theta={theta:.3f} s  [{src}]")
    print(f"PI-SIMC: Kc = {Kc:.5f} PWM/RPM, tauI = {tauI:.3f} s  (tau_c = {tau_c:.2f} s)")
    ff = static_curve()
    cases = [("PI + feedforward, Ts=50 ms", 0.05, True),
             ("PI saja, Ts=50 ms", 0.05, False),
             ("PI + feedforward, Ts=200 ms", 0.20, True)]
    if from_csv:
        res = load_kit_csv([c[0] for c in cases])
    else:
        from imclab import iMCLab
        lab = iMCLab(port)
        res = {}
        for i, (name, Ts, use_ff) in enumerate(cases):
            if i:
                print("Menunggu motor berhenti (coasting) 15 s ...")
                lab.pwm(0); time.sleep(15)
            print(f"[{i+1}/{len(cases)}] {name} ... ({KIT_END:.0f} s)")
            res[name] = run_kit(lab, PI(Kc, tauI, lo=-255, hi=255), Ts, ff if use_ff else None)
            dt = np.diff(res[name][0])
            print(f"    periode loop nyata: rata-rata {dt.mean()*1000:.0f} ms, maks {dt.max()*1000:.0f} ms")
        lab.close()

        with open(os.path.join(HERE, "pid_kit_data.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["kasus", "t_s", "setpoint", "rpm", "pwm", "pwm_feedforward"])
            for name, (t, sp, pv, u, uff) in res.items():
                for row in zip(t, sp, pv, u, uff):
                    w.writerow([name] + [round(float(x), 4) for x in row])

    rows = ["| Kasus | " + " | ".join(f"Overshoot →{s} | Settling ±5 % (s) | Galat 1 s akhir" for s, _ in
                                        [(v, 0) for _, v in KIT_SP]) + " |",
            "|---|" + "---|---|---|" * len(KIT_SP)]
    for name, (t, sp, pv, u, uff) in res.items():
        cells = []
        for target, os_, st, mae in kit_metrics(t, sp, pv):
            cells += [f"{os_:.1f} %", "tidak tercapai" if np.isnan(st) else f"{st:.2f}", f"{mae:.0f} RPM"]
        rows.append(f"| {name} | " + " | ".join(cells) + " |")
    table = "\n".join(rows)
    print(table)
    open(os.path.join(HERE, "hasil_pid_python_kit.md"), "w", encoding="utf-8").write(
        "SUMBER: kit asli\n\n" + f"Model: Kp={Kp:.1f} RPM/PWM, tau={tau:.3f} s, theta={theta:.3f} s [{src}]\n\n"
        + f"PI-SIMC: Kc = {Kc:.5f} PWM/RPM, tauI = {tauI:.3f} s\n\n" + table + "\n")

    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for name in [c[0] for c in cases[:2]]:
        t, sp, pv, u, uff = res[name]
        ax[0].plot(t, pv, lw=1.3, label=name); ax[1].plot(t, u, lw=1, label=name)
    t, sp = res[cases[0][0]][:2]
    ax[0].step(t, sp, "k--", where="post", lw=1, label="setpoint")
    ax[1].axhline(170, color="gray", ls=":", lw=1); ax[1].text(0.1, 175, "PWM 170: motor mulai berputar dari diam", fontsize=8)
    ax[0].set_ylabel("RPM"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ax[1].set_ylabel("PWM"); ax[1].set_xlabel("Waktu (s)"); ax[1].grid(alpha=.3)
    fig.suptitle("P2 (kit asli) — Kendali kecepatan dari Python: PI + feedforward vs PI saja")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "img/p2_kit_pid.png"), dpi=120)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for name in [cases[0][0], cases[2][0]]:
        t, sp, pv, u, uff = res[name]
        ax.step(t, pv, where="post", lw=1.2, label=name)
    ax.step(*res[cases[0][0]][:2], "k--", where="post", lw=1, label="setpoint")
    ax.set_ylabel("RPM"); ax.set_xlabel("Waktu (s)"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    ax.set_title("P3 (kit asli) — Pengaruh periode loop Python (Ts)")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "img/p3_kit_periode_loop.png"), dpi=120)


if __name__ == "__main__":
    main()
