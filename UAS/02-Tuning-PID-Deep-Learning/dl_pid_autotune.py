"""
dl_pid_autotune.py — pengembangan dari contoh ebook: Deep Learning sebagai
"auto-tuner" PID untuk plant FOPDT (seperti iTCLab).

Ide:
  1. Buat dataset: untuk banyak rasio delay r = thetaP/tauP, cari parameter PID
     OPTIMAL lewat simulasi + optimasi numerik (meminimalkan ITAE + penalti
     overshoot + penalti variasi sinyal kendali).
     Semua besaran dibuat tak berdimensi:
        Kc*Kp,  tauI/tauP,  tauD/tauP   sebagai fungsi dari r.
  2. Latih jaringan Keras: input log(r) -> output parameter PID (log).
  3. Pakai model untuk menala PID iTCLab dari hasil step test
     (Kp=0.5 °C/%, tauP=120 s, thetaP=10 s) lalu bandingkan dengan
     parameter default ebook dan tuning IMC.

Output: dataset_pid_optimal.csv, img/dl_autotune_*.png, dl_autotune_hasil.md
Butuh : numpy, scipy, numba, tensorflow, matplotlib
"""
import os
import sys

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from numba import njit
from scipy.optimize import minimize
from tensorflow import keras
from tensorflow.keras import layers

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "UTS", "05-Pendukung-iTCLab", "03-Kit-iTCLab"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "UTS", "05-Pendukung-iTCLab", "04-Sistem-Kendali-PID"))
from itclab_sim import iTCLabSim                    # noqa: E402
from pid_controller import PID                      # noqa: E402
from pid_experiment import metrics, imc             # noqa: E402

UMAX = 3.0   # batas sinyal kendali tak berdimensi (≈ iTCLab: 100 % vs 34 % kebutuhan steady-state)


@njit(cache=True)
def sim_cost(Kc, tauI, tauD, r, dt=0.02, umax=UMAX):
    """Simulasi FOPDT tak berdimensi (Kp=1, tauP=1, theta=r), SP step 0->1."""
    T = 8.0 + 6.0 * r
    N = int(T / dt)
    nd = max(1, int(round(r / dt)))
    ubuf = np.zeros(nd)
    y = 0.0; ylast = 0.0; ierr = 0.0; ulast = 0.0
    itae = 0.0; ymax = 0.0; tv = 0.0
    for k in range(N):
        t = k * dt
        e = 1.0 - y
        ierr += Kc / tauI * e * dt
        u = Kc * e + ierr - Kc * tauD * (y - ylast) / dt
        if u > umax or u < 0.0:
            ierr -= Kc / tauI * e * dt
            u = min(max(u, 0.0), umax)
        tv += abs(u - ulast); ulast = u
        ud = ubuf[k % nd]; ubuf[k % nd] = u
        ylast = y
        y += (-y + ud) * dt
        itae += t * abs(e) * dt
        if y > ymax:
            ymax = y
    os_ = max(0.0, ymax - 1.0)
    return itae + 50.0 * os_ * os_ + 0.002 * tv


def optimal_pid(r):
    """Cari (Kc*Kp, tauI/tauP, tauD/tauP) optimal untuk rasio delay r."""
    tauC = max(0.1, 0.8 * r)
    x0 = np.log([(1 + 0.5 * r) / (tauC + 0.5 * r), 1 + 0.5 * r, r / (2 + r) + 1e-3])
    f = lambda z: sim_cost(*np.exp(z), r)
    best = minimize(f, x0, method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-6, "maxiter": 2000})
    for _ in range(2):                                  # restart untuk hindari local minimum
        cand = minimize(f, best.x + np.random.normal(0, 0.3, 3), method="Nelder-Mead",
                        options={"xatol": 1e-4, "fatol": 1e-6, "maxiter": 2000})
        if cand.fun < best.fun:
            best = cand
    return np.exp(best.x), best.fun


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    np.random.seed(0)
    tf.keras.utils.set_random_seed(0)
    os.makedirs("img", exist_ok=True)

    # ---------- 1. dataset ----------
    R = np.geomspace(0.02, 1.0, 60)
    Y = []
    for r in R:
        p, c = optimal_pid(r)
        Y.append(p)
    Y = np.array(Y)
    np.savetxt("dataset_pid_optimal.csv", np.c_[R, Y], delimiter=",",
               header="r_theta_per_tau,Kc_x_Kp,tauI_per_tauP,tauD_per_tauP", comments="", fmt="%.6f")
    print(f"Dataset: {len(R)} sampel")

    # ---------- 2. latih DL ----------
    Xn = np.log(R)[:, None]
    Yn = np.log(Y + 1e-3)
    mu, sd = Yn.mean(0), Yn.std(0)
    test = np.arange(len(R)) % 5 == 2                    # 20 % data uji
    model = keras.Sequential([
        keras.Input(shape=(1,)),
        layers.Dense(16, activation="tanh"),
        layers.Dense(16, activation="tanh"),
        layers.Dense(3),
    ])
    model.compile(optimizer=keras.optimizers.Adam(0.01), loss="mse")
    hist = model.fit(Xn[~test], (Yn[~test] - mu) / sd, epochs=1500, batch_size=48, verbose=0,
                     validation_data=(Xn[test], (Yn[test] - mu) / sd))

    def predict(r):
        z = model.predict(np.log([[r]]), verbose=0)[0] * sd + mu
        return np.exp(z) - 1e-3

    P = np.array([predict(r) for r in R])
    r2 = [1 - np.sum((Y[test, j] - P[test, j]) ** 2) / np.sum((Y[test, j] - Y[test, j].mean()) ** 2) for j in range(3)]
    print("R² data uji (Kc*Kp, tauI/tauP, tauD/tauP):", np.round(r2, 3))

    names = ["Kc·Kp", "τI / τp", "τD / τp"]
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
    for j in range(3):
        ax[j].plot(R[~test], Y[~test, j], "ko", ms=4, label="Optimal (latih)")
        ax[j].plot(R[test], Y[test, j], "gs", ms=6, label="Optimal (uji)")
        ax[j].plot(R, P[:, j], "r-", lw=2, label="Prediksi DL")
        ax[j].set_xscale("log"); ax[j].set_xlabel("r = θp / τp"); ax[j].set_title(f"{names[j]}  (R² uji={r2[j]:.3f})")
        ax[j].grid(alpha=.3)
    ax[0].legend()
    fig.tight_layout(); fig.savefig("img/dl_autotune_mapping.png", dpi=120)

    plt.figure(figsize=(6, 3.5))
    plt.plot(hist.history["loss"], label="latih"); plt.plot(hist.history["val_loss"], label="uji")
    plt.yscale("log"); plt.xlabel("Epoch"); plt.ylabel("MSE"); plt.legend(); plt.grid(alpha=.3)
    plt.title("Kurva pelatihan DL auto-tuner"); plt.tight_layout(); plt.savefig("img/dl_autotune_loss.png", dpi=120)

    # ---------- 3. terapkan ke iTCLab ----------
    Kp, tauP, thetaP = 0.5, 120.0, 10.0       # hasil step test (UTS/03)
    k1, k2, k3 = predict(thetaP / tauP)
    dl = (k1 / Kp, k2 * tauP, k3 * tauP)
    cases = {
        "PID default ebook": (10.0, 50.0, 1.0),
        "PID IMC agresif": imc(max(0.1 * tauP, 0.8 * thetaP)),
        "PID IMC moderat": imc(max(1.0 * tauP, 8.0 * thetaP)),
        "PID hasil Deep Learning": dl,
    }
    rows = []
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for name, (Kc, tauI, tauD) in cases.items():
        lab = iTCLabSim(seed=1)
        pid = PID(Kc, tauI, tauD)
        t = np.arange(901.0); SP = np.where(t >= 10, 40.0, 23.0)
        PV = np.zeros_like(t); OP = np.zeros_like(t)
        for k in range(len(t)):
            PV[k] = lab.T1
            OP[k] = pid.update(SP[k], PV[k], 1.0)[0]
            lab.Q1(OP[k]); lab.step(1.0)
        os_p, rise, settle, iae, sse = metrics(t, SP, PV)
        rows.append((name, Kc, tauI, tauD, os_p, rise, settle, iae, np.std(np.diff(OP[300:]))))
        ax[0].plot(t, PV, lw=1.5, label=name); ax[1].plot(t, OP, lw=1, label=name)
    ax[0].plot(t, SP, "k--", lw=1, label="Setpoint")
    ax[0].set_ylabel("T1 (°C)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ax[1].set_ylabel("Q1 (%)"); ax[1].set_xlabel("Waktu (s)"); ax[1].grid(alpha=.3)
    fig.suptitle("Tuning PID iTCLab: ebook vs IMC vs Deep Learning (simulasi)")
    fig.tight_layout(); fig.savefig("img/dl_autotune_itclab.png", dpi=120)

    md = ["| Metode | Kc | τI (s) | τD (s) | Overshoot (%) | Rise (s) | Settling ±0.5 °C (s) | IAE | Aktivitas heater* |",
          "|---|---|---|---|---|---|---|---|---|"]
    for n_, Kc, tI, tD, o, ri, se, ia, act in rows:
        md.append(f"| {n_} | {Kc:.2f} | {tI:.1f} | {tD:.2f} | {o:.1f} | {ri:.0f} | {se:.0f} | {ia:.0f} | {act:.2f} |")
    md.append("\n*Aktivitas heater = simpangan baku perubahan Q1 per detik setelah t = 300 s (makin kecil makin halus).")
    md.append(f"\nR² data uji: Kc·Kp={r2[0]:.3f}, τI/τp={r2[1]:.3f}, τD/τp={r2[2]:.3f}")
    open("dl_autotune_hasil.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
