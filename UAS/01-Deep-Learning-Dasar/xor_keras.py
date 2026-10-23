"""
xor_keras.py — Deep Learning meniru gerbang logika XOR (Ebook IoT Jilid 2, Bab 2B)

Arsitektur sama dengan ebook: Dense(2, sigmoid) -> Dense(2, sigmoid) -> Dense(1, sigmoid)
Perbedaan: ebook memakai epochs=100000, batch_size=1 (sangat lama). Di sini dipakai
full-batch (batch_size=4) + learning rate Adam lebih besar agar konvergen dalam
hitungan detik. Hasil akhirnya setara.

Output: img/xor_loss.png, img/xor_prediksi.png, xor_hasil.txt
"""
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


# Data latih XOR (Tabel kebenaran)
XOR_X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
XOR_Y = np.array([[0], [1], [1], [0]], dtype=float)

def build_and_train(seed):
    tf.keras.utils.set_random_seed(seed)
    m = keras.Sequential([
        keras.Input(shape=(2,)),
        layers.Dense(2, activation="sigmoid"),   # lapisan masukan
        layers.Dense(2, activation="sigmoid"),   # lapisan tersembunyi
        layers.Dense(1, activation="sigmoid"),   # lapisan keluaran
    ])
    m.compile(loss="binary_crossentropy", optimizer=keras.optimizers.Adam(0.05), metrics=["accuracy"])
    h = m.fit(XOR_X, XOR_Y, epochs=3000, batch_size=4, verbose=0)
    return m, h


# Jaringan sekecil ini (15 parameter) sering terjebak di local minimum,
# jadi pelatihan diulang dengan 10 inisialisasi bobot (seed) berbeda.
runs = []
for seed in range(10):
    m, h = build_and_train(seed)
    acc_s = np.mean((m.predict(XOR_X, verbose=0) > 0.5) == XOR_Y)
    runs.append((h.history["loss"][-1], seed, acc_s, m, h))
    print(f"seed={seed}  loss akhir={h.history['loss'][-1]:.4f}  akurasi={acc_s*100:.0f}%")
runs.sort(key=lambda r: r[0])
_, best_seed, _, model, hist = runs[0]
n_ok = sum(r[2] == 1.0 for r in runs)
model.summary()
pred = model.predict(XOR_X, verbose=0)
lines = [f"Run berhasil (akurasi 100%): {n_ok}/10 seed",
         "Seed | loss akhir | akurasi"] + [f"{r[1]:>4} | {r[0]:.4f}     | {r[2]*100:.0f}%" for r in sorted(runs, key=lambda r: r[1])] + [
         f"\nModel terbaik: seed {best_seed}", "Input  Target  Prediksi  Dibulatkan"]
for x, y, p in zip(XOR_X.astype(int), XOR_Y.astype(int), pred):
    lines.append(f"{x}   {y[0]}      {p[0]:.4f}    {int(p[0] > 0.5)}")
acc = np.mean((pred > 0.5).astype(int) == XOR_Y)
lines.append(f"\nLoss akhir: {hist.history['loss'][-1]:.5f}   Akurasi: {acc*100:.0f}%")
lines.append(f"Jumlah parameter: {model.count_params()}")
txt = "\n".join(lines)
print(txt)
open("xor_hasil.txt", "w").write(txt + "\n")

os.makedirs("img", exist_ok=True)
plt.figure(figsize=(7, 4))
plt.plot(hist.history["loss"]); plt.yscale("log")
plt.xlabel("Epoch"); plt.ylabel("Binary cross-entropy"); plt.title("Kurva loss pelatihan XOR")
plt.grid(alpha=.3); plt.tight_layout(); plt.savefig("img/xor_loss.png", dpi=120)

# Bidang keputusan (decision boundary)
g = np.linspace(-0.25, 1.25, 200)
xx, yy = np.meshgrid(g, g)
zz = model.predict(np.c_[xx.ravel(), yy.ravel()], verbose=0).reshape(xx.shape)
plt.figure(figsize=(5.5, 5))
plt.contourf(xx, yy, zz, levels=20, cmap="RdBu_r", alpha=.8); plt.colorbar(label="Output jaringan")
plt.contour(xx, yy, zz, levels=[0.5], colors="k", linewidths=2)
plt.scatter(XOR_X[:, 0], XOR_X[:, 1], c=XOR_Y.ravel(), cmap="RdBu_r", edgecolors="k", s=150)
plt.title("Bidang keputusan XOR (garis hitam = 0.5)"); plt.xlabel("x1"); plt.ylabel("x2")
plt.tight_layout(); plt.savefig("img/xor_prediksi.png", dpi=120)
