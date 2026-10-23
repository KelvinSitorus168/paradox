"""
analisis_karakterisasi.py — Laporan Riset Modul 1: karakterisasi motor DC iMCLab.

Eksperimen (sama dengan sketch 01 & 04):
  E1  Uji fungsi: maju 2 s, stop 1 s, mundur 2 s, stop 1 s, PWM naik 200->255
  E2  Kurva statis PWM vs RPM  -> dead-zone & linearitas
  E3  Respons step PWM 0 -> 200 -> konstanta waktu mekanik
  E4  Metode ukur RPM dengan piringan 2 lubang: jendela 1 s (program dosen),
      jendela 100 ms, dan metode period (waktu 1 putaran)

Sumber data:
  default      : simulator iMCLab (parameter motor ASUMSI, lihat ../02-iMCLab-Python/imclab_sim.py)
  --csv FILE   : hasil Serial Monitor sketch 04 dari kit asli (bagian A & B)
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "02-iMCLab-Python"))
from imclab_sim import iMCLabSim   # noqa: E402

DT = 0.01


def run(profile, window=1.0, method="period"):
    lab = iMCLabSim(window=window, method=method)
    t, u, w, m = [], [], [], []
    for k, d in enumerate(profile):
        lab.pwm(d); lab.step(DT)
        t.append((k + 1) * DT); u.append(d); w.append(lab.rpm_true); m.append(lab.rpm)
    return map(np.array, (t, u, w, m))


def e1_uji_fungsi():
    prof = [255] * 200 + [0] * 100 + [-255] * 200 + [0] * 100
    for d in range(200, 256, 5):
        prof += [d] * 50
    t, u, w, m = run(prof)
    fig, ax = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
    ax[0].plot(t, w, "k-", lw=1, label="kecepatan sebenarnya")
    ax[0].step(t, m, "r-", where="post", lw=1, label="terukur encoder (metode period)")
    ax[0].axhline(0, color="gray", lw=.5); ax[0].set_ylabel("RPM"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].step(t, u, "b-", where="post"); ax[1].set_ylabel("PWM (−255..255)"); ax[1].set_xlabel("Waktu (s)"); ax[1].grid(alpha=.3)
    for x, lbl in [(1, "MAJU"), (2.5, "STOP"), (4, "MUNDUR"), (5.5, "STOP"), (8.5, "PWM naik 200→255")]:
        ax[1].text(x, 270, lbl, ha="center", fontsize=8)
    ax[1].set_ylim(-300, 320)
    fig.suptitle("E1 — Uji fungsi motor iMCLab (urutan sketch 01_Test_iMCLab)")
    fig.tight_layout(); fig.savefig("img/e1_uji_fungsi.png", dpi=120)
    stop_time = t[np.argmax((t > 2) & (np.abs(w) < 50))] - 2
    return {"rpm_maju_penuh": w[190], "rpm_mundur_penuh": w[490], "waktu_berhenti_s": stop_time,
            "rpm_200": w[650], "rpm_255": w[-1]}


def e2_kurva_statis(csv=None):
    if csv:
        pw, rp = csv
    else:
        pw = np.arange(0, 256, 5)
        rp = []
        for d in pw:
            _, _, _, m = run([d] * 300, window=1.0, method="window")
            rp.append(m[-1])
        rp = np.array(rp)
    moving = rp > 0
    dz = pw[moving][0] if moving.any() else np.nan
    sel = pw >= dz + 20
    a, b = np.polyfit(pw[sel], rp[sel], 1)
    resid = rp[sel] - (a * pw[sel] + b)
    r2 = 1 - np.sum(resid ** 2) / np.sum((rp[sel] - rp[sel].mean()) ** 2)
    plt.figure(figsize=(8, 5))
    plt.plot(pw, rp, "o", ms=4, label="RPM terukur (jendela 1 s)")
    xx = np.linspace(dz, 255, 50)
    plt.plot(xx, a * xx + b, "r--", label=f"regresi linear: RPM = {a:.1f}·PWM {b:+.0f}  (R²={r2:.4f})")
    plt.axvspan(0, dz, color="gray", alpha=.2, label=f"dead-zone (PWM < {dz})")
    plt.xlabel("PWM (0–255)"); plt.ylabel("RPM"); plt.grid(alpha=.3); plt.legend()
    plt.title("E2 — Kurva statis PWM vs kecepatan motor")
    plt.tight_layout(); plt.savefig("img/e2_kurva_statis.png", dpi=120)
    return {"deadzone_pwm": int(dz), "gain_rpm_per_pwm": a, "intercept": b, "r2": r2,
            "rpm_max": rp.max()}


def e3_respons_step(csv=None):
    if csv:
        t, m = csv; w = m
    else:
        t, u, w, m = run([0] * 10 + [200] * 140, method="period")
        t = t - 0.1
    yss = np.mean(w[-20:])
    i63 = np.argmax(w >= 0.632 * yss)
    tau = t[i63]
    i10, i90 = np.argmax(w >= .1 * yss), np.argmax(w >= .9 * yss)
    model = yss * (1 - np.exp(-np.clip(t, 0, None) / tau))
    plt.figure(figsize=(8, 5))
    plt.plot(t, m, ".", ms=4, color="tab:orange", label="RPM terukur (metode period)")
    plt.plot(t, w, "k-", lw=1, label="kecepatan sebenarnya")
    plt.plot(t, model, "r--", label=f"model orde-1: τ = {tau*1000:.0f} ms")
    plt.axhline(0.632 * yss, color="gray", ls=":"); plt.axvline(tau, color="gray", ls=":")
    plt.text(tau, 0.632 * yss * 0.9, "  63,2 %", fontsize=9)
    plt.xlabel("Waktu sejak PWM = 200 (s)"); plt.ylabel("RPM"); plt.grid(alpha=.3); plt.legend()
    plt.title("E3 — Respons step PWM 0 → 200")
    plt.tight_layout(); plt.savefig("img/e3_respons_step.png", dpi=120)
    return {"rpm_steady": yss, "tau_s": tau, "rise_10_90_s": t[i90] - t[i10],
            "settling_4tau_s": 4 * tau}


def e4_resolusi_encoder():
    prof = [0] * 20 + [120] * 130 + [200] * 150
    plt.figure(figsize=(9, 5))
    out = {}
    cases = [("jendela 1 s (program dosen)", 1.0, "window", "tab:green"),
             ("jendela 100 ms", 0.1, "window", "tab:red"),
             ("metode period (1 putaran)", 1.0, "period", "tab:blue")]
    for name, win, meth, c in cases:
        t, u, w, m = run(prof, window=win, method=meth)
        plt.step(t, m, where="post", color=c, lw=1.4, label=name)
        mask = t > 0.2
        res = 60 / (2 * win) if meth == "window" else 0
        out[name] = {"resolusi_rpm": res, "galat_rms": float(np.sqrt(np.mean((m[mask] - w[mask]) ** 2)))}
    plt.plot(t, w, "k-", lw=1, label="kecepatan sebenarnya")
    plt.xlabel("Waktu (s)"); plt.ylabel("RPM"); plt.grid(alpha=.3); plt.legend(fontsize=8)
    plt.title("E4 — Cara mengukur RPM dengan piringan 2 lubang")
    plt.tight_layout(); plt.savefig("img/e4_resolusi_encoder.png", dpi=120)
    return out


def e2_kit(A, C=None):
    """Kurva statis dari kit asli, dibandingkan dengan simulator (parameter asumsi)."""
    pw, rp = A
    moving = rp > 0
    dz_hi = int(pw[moving][0]); dz_lo = int(pw[~moving & (pw < dz_hi)][-1])
    lin = moving & (pw <= 230)                 # di atas 230 RPM sudah jenuh
    a, b = np.polyfit(pw[lin], rp[lin], 1)
    r2 = 1 - np.sum((rp[lin] - (a * pw[lin] + b)) ** 2) / np.sum((rp[lin] - rp[lin].mean()) ** 2)
    sim = []
    for d in pw:
        _, _, _, m = run([d] * 300, window=1.0, method="window"); sim.append(m[-1])
    plt.figure(figsize=(8.5, 5))
    plt.plot(pw, rp, "o-", ms=5, color="tab:blue", label="kit asli (jendela 1 s, sweep naik)")
    if C is not None:
        plt.plot(C[0], C[1], "v-", ms=5, color="tab:green", label="kit asli, sweep turun (motor sudah berputar)")
    plt.plot(pw, sim, "s--", ms=3, color="gray", alpha=.7, label="simulator (parameter asumsi)")
    xx = np.linspace(dz_hi, 230, 20)
    plt.plot(xx, a * xx + b, "r:", lw=2, label=f"regresi PWM {dz_hi}–230: RPM = {a:.0f}·PWM {b:+.0f} (R²={r2:.3f})")
    plt.axvspan(0, (dz_lo + dz_hi) / 2, color="gray", alpha=.15, label=f"motor belum mulai berputar (PWM ≤ {dz_lo})")
    plt.axhspan(rp.max() * .985, rp.max() * 1.015, color="orange", alpha=.25, label=f"jenuh ≈ {rp.max():.0f} RPM (PWM ≥ 240)")
    plt.xlabel("PWM (0–255)"); plt.ylabel("RPM"); plt.grid(alpha=.3); plt.legend(fontsize=8, loc="upper left")
    plt.title("E2 — Kurva statis PWM vs RPM, kit iMCLab asli")
    plt.tight_layout(); plt.savefig("img/e2_kurva_statis_kit.png", dpi=120)
    extra = {}
    if C is not None:
        run_ = C[1] > 0
        extra = {"pwm_berhenti_sweep_turun": int(C[0][run_].min()) - 10 if run_.any() else -1}
    return {**extra, "pwm_mulai_berputar": dz_hi, "pwm_terakhir_diam": dz_lo, "gain_rpm_per_pwm": a,
            "r2": r2, "rpm_max": rp.max(), "rpm_pwm200": float(rp[pw == 200][0])}


def e3_kit(B, rpm_ss_kurva):
    """Respons step kit asli: fit model FOPDT  y = K(1-exp(-(t-θ)/τ))."""
    from scipy.optimize import curve_fit
    t, y = B
    f = lambda t, K, tau, th: np.where(t > th, K * (1 - np.exp(-(t - th) / tau)), 0)
    on = y > 0
    (K, tau, th), _ = curve_fit(f, t[on], y[on], p0=[6000, .5, .1], maxfev=20000)
    f2 = lambda t, tau, th: f(t, rpm_ss_kurva, tau, th)
    (tau2, th2), _ = curve_fit(f2, t[on], y[on], p0=[.5, .1], maxfev=20000)
    t0 = t[np.argmax(on)]
    rmse = np.sqrt(np.mean((f(t[on], K, tau, th) - y[on]) ** 2))
    tt = np.linspace(0, 3, 300)
    plt.figure(figsize=(8.5, 5))
    plt.plot(t, y, ".", ms=5, color="tab:orange", label="kit asli (metode period, tiap 10 ms)")
    plt.plot(tt, f(tt, K, tau, th), "r--", label=f"FOPDT fit bebas: K={K:.0f}, τ={tau*1000:.0f} ms, θ={th*1000:.0f} ms")
    plt.plot(tt, f(tt, rpm_ss_kurva, tau2, th2), "b:", label=f"FOPDT, K = {rpm_ss_kurva:.0f} (dari E2): τ={tau2*1000:.0f} ms")
    plt.axvspan(0, t0, color="gray", alpha=.15, label=f"RPM belum terbaca ({t0*1000:.0f} ms)")
    if t[-1] < 2:
        plt.axvline(t[-1], color="k", lw=.6, ls=":"); plt.text(t[-1] + .01, 300, f" data berhenti\n ({len(t)} sampel)", fontsize=8)
    plt.xlabel("Waktu sejak PWM = 200 (s)"); plt.ylabel("RPM"); plt.grid(alpha=.3); plt.legend(fontsize=8, loc="lower right")
    plt.title("E3 — Respons step PWM 0 → 200, kit iMCLab asli")
    plt.tight_layout(); plt.savefig("img/e3_respons_step_kit.png", dpi=120)
    return {"rpm_awal_terbaca_ms": t0 * 1000, "rpm_akhir": y[-1], "t_akhir_s": t[-1], "K_fit": K, "tau_fit_s": tau,
            "theta_fit_s": th, "rmse_fit": rmse, "tau_Kdari_E2_s": tau2, "theta_Kdari_E2_s": th2,
            "persen_steady_di_akhir": 100 * y[-1] / rpm_ss_kurva}


def load_csv(path):
    A, B, C, sec = [], [], [], None
    for line in open(path):
        line = line.strip()
        if line.startswith("# A"): sec = A; continue
        if line.startswith("# B"): sec = B; continue
        if line.startswith("# C"): sec = C; continue
        if not line or line.startswith("#") or line[0].isalpha() or sec is None: continue
        sec.append([float(x) for x in line.split(",")])
    A, B, C = np.array(A), np.array(B), np.array(C)
    return (A[:, 0], A[:, 1]), (B[:, 0] / 1000, B[:, 1]), ((C[:, 0], C[:, 1]) if len(C) else None)


def main():
    os.chdir(HERE)
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="output Serial sketch 04 dari kit asli")
    args = ap.parse_args()
    A = B = None
    if args.csv:
        A, B, C = load_csv(args.csv)
    lines = []
    if not args.csv:
        lines.append("E1 uji fungsi: " + ", ".join(f"{k}={v:.2f}" for k, v in e1_uji_fungsi().items()))
    if args.csv:
        r2 = e2_kit(A, C); r3 = e3_kit(B, r2["rpm_pwm200"])
    else:
        r2 = e2_kurva_statis(); r3 = e3_respons_step()
    lines.append("E2 kurva statis: " + ", ".join(f"{k}={v:.4g}" for k, v in r2.items()))
    lines.append("E3 respons step: " + ", ".join(f"{k}={v:.4g}" for k, v in r3.items()))
    if not args.csv:
        for k, v in e4_resolusi_encoder().items():
            lines.append(f"E4 {k}: resolusi={v['resolusi_rpm']:.0f} RPM, galat RMS={v['galat_rms']:.1f} RPM")
    txt = "\n".join(lines)
    print(txt)
    open("hasil_karakterisasi_kit.txt" if args.csv else "hasil_karakterisasi.txt", "w").write(("SUMBER: kit asli\n" if args.csv else "SUMBER: simulasi (parameter motor asumsi)\n") + txt + "\n")


if __name__ == "__main__":
    main()
