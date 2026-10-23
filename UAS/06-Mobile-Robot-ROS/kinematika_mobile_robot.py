"""
kinematika_mobile_robot.py — perbandingan kinematika:
  (1) Differential drive (Robot BNU Gen II, robot Android Azeta dkk.)
  (2) Omnidirectional 3 roda / Kiwi drive (Robotont, roda dipasang tiap 120°)

Tugas: mengikuti lintasan persegi 1 m x 1 m sambil menghadap ke arah yang sama.
- Omni   : bisa bergerak ke samping tanpa berputar (holonomic).
- Diff   : harus berhenti dan berputar 90° di tiap sudut (non-holonomic).

Output: img/kinematika_lintasan.png, img/kinematika_kecepatan_roda.png, kinematika_hasil.txt
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R_WHEEL = 0.035   # m  jari-jari roda omni (nilai asumsi)
L_OMNI = 0.146    # m  jarak pusat robot ke roda (nilai asumsi)
B_DIFF = 0.20     # m  jarak antar roda differential drive
ANG = np.radians([60, 180, 300])     # posisi sudut 3 roda omni (berjarak 120°)


def omni_ik(vx, vy, w):
    """Inverse kinematics Kiwi drive: kecepatan robot (frame robot) -> kecepatan sudut roda (rad/s)."""
    J = np.array([[-np.sin(a), np.cos(a), L_OMNI] for a in ANG])
    return J @ np.array([vx, vy, w]) / R_WHEEL


def omni_fk(wheels):
    J = np.array([[-np.sin(a), np.cos(a), L_OMNI] for a in ANG])
    return np.linalg.solve(J, np.asarray(wheels) * R_WHEEL)


def diff_ik(v, w):
    return np.array([(v - w * B_DIFF / 2), (v + w * B_DIFF / 2)]) / R_WHEEL


def simulate_omni(dt=0.02, v=0.2):
    segs = [(v, 0), (0, v), (-v, 0), (0, -v)]           # maju, geser kiri, mundur, geser kanan
    x = y = th = 0.0; P, W = [(0, 0, 0)], []
    for vx, vy in segs:
        for _ in range(int(1.0 / v / dt)):
            wh = omni_ik(vx, vy, 0.0); W.append(wh)
            bvx, bvy, bw = omni_fk(wh)                   # forward kinematics (cek konsistensi)
            x += (bvx * np.cos(th) - bvy * np.sin(th)) * dt
            y += (bvx * np.sin(th) + bvy * np.cos(th)) * dt
            th += bw * dt
            P.append((x, y, th))
    return np.array(P), np.array(W)


def simulate_diff(dt=0.02, v=0.2, w=np.pi / 4):
    x = y = th = 0.0; P, W = [(0, 0, 0)], []
    for _ in range(4):
        for _ in range(int(1.0 / v / dt)):              # lurus 1 m
            W.append(diff_ik(v, 0)); x += v * np.cos(th) * dt; y += v * np.sin(th) * dt; P.append((x, y, th))
        for _ in range(int((np.pi / 2) / w / dt)):      # putar di tempat 90°
            W.append(diff_ik(0, w)); th += w * dt; P.append((x, y, th))
    return np.array(P), np.array(W)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs("img", exist_ok=True)
    Po, Wo = simulate_omni(); Pd, Wd = simulate_diff()
    t_o, t_d = len(Wo) * 0.02, len(Wd) * 0.02

    lines = ["Contoh inverse kinematics Kiwi drive (rad/s per roda):"]
    for name, cmd in [("maju 0.2 m/s", (0.2, 0, 0)), ("geser kiri 0.2 m/s", (0, 0.2, 0)), ("putar 1 rad/s", (0, 0, 1.0))]:
        wh = omni_ik(*cmd); back = omni_fk(wh)
        lines.append(f"  {name:<20} -> roda = {np.round(wh, 2).tolist()}  | FK kembali = {np.round(back, 3).tolist()}")
    lines += [f"\nOmni  : waktu tempuh persegi = {t_o:.1f} s, error posisi akhir = {np.hypot(*Po[-1, :2])*1000:.1f} mm, "
              f"orientasi akhir = {np.degrees(Po[-1, 2]):.1f}°",
              f"Diff  : waktu tempuh persegi = {t_d:.1f} s, error posisi akhir = {np.hypot(*Pd[-1, :2])*1000:.1f} mm, "
              f"total rotasi = {np.degrees(Pd[-1, 2]):.0f}° (berhenti & berputar 4 x 90°)"]
    txt = "\n".join(lines); print(txt); open("kinematika_hasil.txt", "w").write(txt + "\n")

    fig, ax = plt.subplots(1, 2, figsize=(11, 5))
    for a, P, title in [(ax[0], Pd, "Differential drive"), (ax[1], Po, "Omnidirectional (Kiwi, Robotont)")]:
        a.plot(P[:, 0], P[:, 1], "b-", lw=1.5)
        for i in range(0, len(P), 40):
            a.arrow(P[i, 0], P[i, 1], 0.08 * np.cos(P[i, 2]), 0.08 * np.sin(P[i, 2]), head_width=0.03, color="r")
        a.set_title(title); a.axis("equal"); a.grid(alpha=.3); a.set_xlabel("x (m)"); a.set_ylabel("y (m)")
    fig.suptitle("Lintasan persegi 1 m — panah merah = arah hadap robot")
    fig.tight_layout(); fig.savefig("img/kinematika_lintasan.png", dpi=120)

    fig, ax = plt.subplots(2, 1, figsize=(10, 6))
    td, to = np.arange(len(Wd)) * 0.02, np.arange(len(Wo)) * 0.02
    ax[0].plot(td, Wd[:, 0], label="roda kiri"); ax[0].plot(td, Wd[:, 1], label="roda kanan")
    ax[0].set_title("Differential drive"); ax[0].set_ylabel("rad/s"); ax[0].legend(); ax[0].grid(alpha=.3)
    for i in range(3):
        ax[1].plot(to, Wo[:, i], label=f"roda {i+1} ({int(np.degrees(ANG[i]))}°)")
    ax[1].set_title("Kiwi drive (3 roda omni)"); ax[1].set_ylabel("rad/s"); ax[1].set_xlabel("Waktu (s)")
    ax[1].legend(); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig("img/kinematika_kecepatan_roda.png", dpi=120)


if __name__ == "__main__":
    main()
