"""
dl_pid_ebook.py — reproduksi contoh Ebook IoT Jilid 2, Bab 2C:
Deep Learning memetakan [error, delta_error] -> [Kc, tauI, tauD],
lalu parameter hasil prediksi dipakai mengendalikan proses orde-1 + delay
(Kp=4, taup=3, thetap=1) dengan setpoint step 0 -> 4.

Output: img/dl_pid_ebook.png, dl_pid_ebook_hasil.txt
"""
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from scipy.integrate import odeint
from tensorflow import keras
from tensorflow.keras import layers

tf.keras.utils.set_random_seed(1)

# Data latih dari ebook: [e, delta_e] -> [Kc, tauI, tauD]
X = np.array([[1, 1], [0.4, 1.2], [1.2, 0.1], [1, 0.1]])
y = np.array([[0.25, 4.31, 0.20], [0.2, 4.1, 0.1], [0.1, 4.0, 0], [0.1, 4.0, 0]])

# Catatan: keluaran sigmoid hanya 0..1, padahal tauI ~4. Di ebook hal ini membuat
# tauI keluaran ~0.7. Di sini target diskalakan (dibagi 5) supaya model bisa
# benar-benar meniru label, lalu hasil prediksi dikalikan 5 lagi.
SCALE = 5.0
model = keras.Sequential([
    keras.Input(shape=(2,)),
    layers.Dense(2, activation="sigmoid"),
    layers.Dense(3, activation="sigmoid"),
    layers.Dense(3, activation="sigmoid"),
])
model.compile(loss="mse", optimizer=keras.optimizers.Adam(0.05))
model.fit(X, y / SCALE, epochs=2000, batch_size=4, verbose=0)

out = model.predict(np.array([[1, 1]]), verbose=0)[0] * SCALE
Kc, tauI, tauD = [float(v) for v in out]

# ---- simulasi PID seperti di ebook ----
n, tf_, SP_start = 501, 50.0, 2.0


def process(yv, t, u):
    Kp, taup, thetap = 4.0, 3.0, 1.0
    return 0.0 if t < (thetap + SP_start) else (1.0 / taup) * (-yv + Kp * u)


def pid_sim(Kc, tauI, tauD):
    t = np.linspace(0, tf_, n)
    P, I, D, e, OP, PV = (np.zeros(n) for _ in range(6))
    SP = np.where(t >= SP_start, 4.0, 0.0)
    y0 = 0.0
    for i in range(1, n):
        yy = odeint(process, y0, [t[i - 1], t[i]], args=(OP[i - 1],))
        y0 = yy[1][0]; PV[i] = y0
        e[i] = SP[i] - PV[i]; dt = t[i] - t[i - 1]
        P[i] = Kc * e[i]
        I[i] = I[i - 1] + (Kc / tauI) * e[i] * dt
        D[i] = -Kc * tauD * (PV[i] - PV[i - 1]) / dt
        OP[i] = P[i] + I[i] + D[i]
    return t, SP, PV, OP


t, SP, PV, OP = pid_sim(Kc, tauI, tauD)
iae = np.sum(np.abs(SP - PV)) * (t[1] - t[0])
txt = (f"Prediksi DL untuk input [e=1, delta_e=1]: Kc={Kc:.4f}, tauI={tauI:.4f}, tauD={tauD:.4f}\n"
       f"Label target ebook             : Kc=0.25,   tauI=4.31,   tauD=0.20\n"
       f"Respons: PV akhir={PV[-1]:.3f} (SP=4), overshoot={(PV.max()-4)/4*100:.1f}%, IAE={iae:.2f}")
print(txt); open("dl_pid_ebook_hasil.txt", "w").write(txt + "\n")

os.makedirs("img", exist_ok=True)
fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
ax[0].plot(t, SP, "k-", label="SP"); ax[0].plot(t, PV, "r:", lw=2, label="PV")
ax[0].set_title(f"PID dengan parameter hasil Deep Learning (Kc={Kc:.2f}, τI={tauI:.2f}, τD={tauD:.2f})")
ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].plot(t, OP, "b", label="OP"); ax[1].set_xlabel("Waktu"); ax[1].legend(); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig("img/dl_pid_ebook.png", dpi=120)
