"""
analisis_ota.py — Laporan Riset Modul 4: gambar tata letak flash ESP32 dan
mekanisme dual-bank (A/B) yang membuat OTA aman.

Tabel partisi = "Default 4MB with spiffs" (default.csv arduino-esp32):
    nvs      0x9000   0x5000
    otadata  0xE000   0x2000
    app0     0x10000  0x140000   (ota_0)
    app1     0x150000 0x140000   (ota_1)
    spiffs   0x290000 0x160000
    coredump 0x3F0000 0x10000
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

PART = [("boot+tabel", 0x0, 0x9000, "#999999"), ("nvs", 0x9000, 0x5000, "#c7a0d8"),
        ("otadata", 0xE000, 0x2000, "#e6735c"), ("app0 (ota_0)", 0x10000, 0x140000, "#5b9bd5"),
        ("app1 (ota_1)", 0x150000, 0x140000, "#70ad47"), ("spiffs", 0x290000, 0x160000, "#ffc000"),
        ("coredump", 0x3F0000, 0x10000, "#7f7f7f")]


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs("img", exist_ok=True)
    MB = 1024 * 1024

    # O1: peta flash
    fig, ax = plt.subplots(figsize=(11, 2.6))
    for name, off, size, c in PART:
        ax.barh(0, size / MB, left=off / MB, color=c, edgecolor="k")
        if size >= 0x100000:
            ax.text((off + size / 2) / MB, 0, f"{name}\n{size/MB:.2f} MB", ha="center", va="center", fontsize=9)
    ax.annotate("nvs + otadata\n(penunjuk slot aktif)", xy=(0xE000 / MB, 0.4), xytext=(0.05, 0.9),
                fontsize=8, arrowprops=dict(arrowstyle="->"))
    ax.set_xlim(0, 4); ax.set_ylim(-0.6, 1.2); ax.set_yticks([])
    ax.set_xlabel("Alamat flash (MB) — total 4 MB")
    ax.set_title("O1 — Partisi 'Default 4MB with spiffs': ukuran maksimal firmware OTA = 1,25 MB per slot")
    fig.tight_layout(); fig.savefig("img/o1_partisi_flash.png", dpi=120)

    # O2: mekanisme A/B
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.6))
    states = [("1. Sebelum OTA", "v1.0.0 ✔ AKTIF", "kosong / lama", 0),
              ("2. Saat unduh (Update.writeStream)", "v1.0.0 ✔ AKTIF\n(motor dihentikan)", "menulis v1.1.0…", 0),
              ("3. Setelah Update.end() + restart", "v1.0.0 (cadangan)", "v1.1.0 ✔ AKTIF", 1)]
    for a, (title, s0, s1, act) in zip(axs, states):
        for i, (lbl, txt) in enumerate([("app0", s0), ("app1", s1)]):
            col = "#c6e0b4" if i == act else "#eeeeee"
            a.add_patch(plt.Rectangle((0.1, 0.55 - i * 0.45), 0.8, 0.35, color=col, ec="k"))
            a.text(0.5, 0.725 - i * 0.45, f"{lbl}\n{txt}", ha="center", va="center", fontsize=9)
        a.set_xlim(0, 1); a.set_ylim(0, 1); a.axis("off"); a.set_title(title, fontsize=10)
    for x in (0.355, 0.675):
        fig.add_artist(FancyArrowPatch((x - 0.02, 0.5), (x + 0.02, 0.5), transform=fig.transFigure,
                                       arrowstyle="-|>", mutation_scale=20))
    fig.suptitle("O2 — Dual-bank OTA: firmware baru ditulis ke slot cadangan; jika gagal, slot lama tetap dipakai")
    fig.tight_layout(); fig.savefig("img/o2_dual_bank.png", dpi=120)
    print("img/o1_partisi_flash.png, img/o2_dual_bank.png dibuat")


if __name__ == "__main__":
    main()
