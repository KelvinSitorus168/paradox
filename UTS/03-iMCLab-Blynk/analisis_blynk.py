"""
analisis_blynk.py — Laporan Riset Modul 3 (simulasi).

B1  Di mana loop PID sebaiknya berjalan?
    (a) LOKAL di ESP32, Ts = 50 ms (desain iMCLab_Blynk.ino)
    (b) REMOTE lewat cloud: RPM dikirim ke server/HP, PWM dikirim balik.
        Ditiru dengan waktu tunda pulang-pergi (round trip) 0,3 s dan 0,8 s,
        Ts = 0,1 s, parameter PI sama.
B2  Apa yang "dilihat" aplikasi Blynk? Data asli vs data yang dikirim dengan
    interval 0,2 s, 0,5 s, 2 s, dan jumlah pesan per detik.

Model motor: ../02-iMCLab-Python/imclab_sim.py (parameter ASUMSI).
"""
import os
import sys
from collections import deque

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "02-iMCLab-Python"))
from imclab_sim import iMCLabSim                    # noqa: E402
from pid_python_imclab import KP, TAU, THETA, PI    # noqa: E402

Kc, tauI = TAU / (KP * (0.1 + THETA)), TAU
T_END = 8.0


def sp_profile(t):
    return 0 if t < 0.5 else 4000 if t < 4.0 else 2500


def run(Ts, delay, kc=None, ti=None):
    """delay = waktu tunda pulang-pergi (s); setengah di jalur sensor, setengah di jalur aktuator."""
    lab = iMCLabSim(method="period")
    ctrl = PI(kc or Kc, ti or tauI)
    nd = int(round(delay / 2 / Ts))
    q_meas, q_cmd = deque([0.0] * nd), deque([0.0] * nd)
    t, pv, out = [], [], []
    tk = 0.0
    while tk < T_END:
        y = lab.rpm
        q_meas.append(y); y_seen = q_meas.popleft() if nd else y
        s = sp_profile(tk)
        u = ctrl.update(s, y_seen, Ts) if s > 0 else 0.0
        q_cmd.append(u); u_app = q_cmd.popleft() if nd else u
        lab.pwm(round(u_app))
        lab.step(Ts)
        t.append(tk); pv.append(lab.rpm_true); out.append(u_app)
        tk += Ts
    return np.array(t), np.array(pv), np.array(out)


def iae(t, pv):
    sp = np.array([sp_profile(x) for x in t])
    return np.trapezoid(np.abs(sp - pv), t)


def main():
    os.chdir(HERE)
    os.makedirs("img", exist_ok=True)
    lines = []

    # ---------- B1 ----------
    cases = [("Lokal ESP32 (Ts 50 ms, delay 0)", 0.05, 0.0),
             ("Remote cloud (Ts 0,1 s, delay 0,3 s)", 0.1, 0.3),
             ("Remote cloud (Ts 0,1 s, delay 0,8 s)", 0.1, 0.8)]
    th_tot = THETA + 0.3 + 0.05                       # delay model + jaringan + setengah Ts
    kc_slow = TAU / (KP * (2 * th_tot + th_tot))      # IMC dengan tau_c = 2 x delay total
    cases.append((f"Remote 0,3 s, PI ditala ulang (Kc={kc_slow:.4f})", 0.1, 0.3, kc_slow))
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for name, Ts, d, *kc in cases:
        t, pv, u = run(Ts, d, *(kc or [None]))
        m = (t > 2.5) & (t < 4.0)
        osc = pv[m].max() - pv[m].min()
        r10 = t[np.argmax(pv >= 0.9 * 4000)] - 0.5 if (pv >= 0.9 * 4000).any() else np.nan
        lines.append(f"B1 {name}: IAE = {iae(t, pv):.0f} RPM·s, ayunan pada SP 4000 (t 2,5–4 s) = {osc:.0f} RPM, waktu capai 90 % = {r10:.2f} s, "
                     f"PWM min/max = {u.min():.0f}/{u.max():.0f}")
        ls = "--" if "ditala" in name else "-"
        ax[0].plot(t, pv, ls, lw=1.3, label=name); ax[1].plot(t, u, ls, lw=1, label=name)
    ax[0].plot(t, [sp_profile(x) for x in t], "k--", lw=1, label="setpoint")
    ax[0].set_ylabel("RPM"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ax[1].set_ylabel("PWM"); ax[1].set_xlabel("Waktu (s)"); ax[1].grid(alpha=.3)
    fig.suptitle("B1 — PID lokal di ESP32 vs PID lewat cloud (latensi internet)")
    fig.tight_layout(); fig.savefig("img/b1_lokal_vs_cloud.png", dpi=120)

    # ---------- B2 ----------
    t, pv, u = run(0.05, 0.0)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(t, pv, "k-", lw=1, label="RPM sebenarnya (ESP32, 50 ms)")
    for iv, c in [(0.2, "tab:blue"), (0.5, "tab:green"), (2.0, "tab:red")]:
        idx = np.arange(0, len(t), int(round(iv / 0.05)))
        ax.step(t[idx], pv[idx], where="post", color=c, lw=1.3, marker="o", ms=3,
                label=f"terlihat di Blynk, interval {iv:g} s")
        n_vals = 2 / iv                         # V1 + V2 per interval
        lines.append(f"B2 interval {iv:g} s: {n_vals:.1f} nilai/detik ke server, "
                     f"{n_vals*3600:.0f} nilai/jam")
    ax.set_ylabel("RPM"); ax.set_xlabel("Waktu (s)"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    ax.set_title("B2 — Pengaruh interval kirim data ke Blynk terhadap grafik aplikasi")
    fig.tight_layout(); fig.savefig("img/b2_interval_kirim.png", dpi=120)

    txt = "\n".join(lines)
    print(txt)
    open("hasil_analisis_blynk.txt", "w").write("SUMBER: simulasi (parameter motor asumsi)\n" + txt + "\n")


if __name__ == "__main__":
    main()
