"""
robot_sim_mqtt.py — simulasi robot BNU Gen I (mobil RC, model kinematika sepeda/Ackermann)
yang menerima perintah MQTT persis seperti NodeMCU. Lintasan disimpan sebagai grafik.

    python robot_sim_mqtt.py --broker localhost --duration 15
"""
import argparse
import math
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt

TOPIC = "kelvin341/bnu/cmd"
V = 0.5                 # m/s kecepatan maju
L = 0.25                # m jarak sumbu roda (wheelbase)
STEER = math.radians(30)
FAILSAFE = 1.5          # s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="broker.hivemq.com")
    ap.add_argument("--duration", type=float, default=20)
    ap.add_argument("--out", default="img/lintasan_robot.png")
    args = ap.parse_args()

    st = {"cmd": "STOP", "t": 0.0}
    def on_msg(c, u, m):
        st["cmd"], st["t"] = m.payload.decode().strip().upper(), time.time()
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.on_message = on_msg
    c.on_connect = lambda c, u, f, rc, p: c.subscribe(TOPIC)
    c.connect(args.broker, 1883); c.loop_start()

    x = y = th = 0.0
    xs, ys, cmds = [0.0], [0.0], []
    dt, t0 = 0.05, time.time()
    while time.time() - t0 < args.duration:
        cmd = st["cmd"] if time.time() - st["t"] < FAILSAFE else "STOP"
        v = {"MAJU": V, "KIRI": V, "KANAN": V, "MUNDUR": -V}.get(cmd, 0.0)
        delta = {"KIRI": STEER, "KANAN": -STEER}.get(cmd, 0.0)
        x += v * math.cos(th) * dt
        y += v * math.sin(th) * dt
        th += v / L * math.tan(delta) * dt
        xs.append(x); ys.append(y); cmds.append(cmd)
        time.sleep(dt)
    c.loop_stop(); c.disconnect()

    dist = sum(math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(len(xs) - 1))
    print(f"Posisi akhir: x={x:.2f} m, y={y:.2f} m, heading={math.degrees(th) % 360:.0f}°, jarak tempuh={dist:.2f} m")
    print("Perintah diterima (jumlah langkah 50 ms):", {k: cmds.count(k) for k in sorted(set(cmds))})
    plt.figure(figsize=(6, 6))
    plt.plot(xs, ys, "b-"); plt.plot(xs[0], ys[0], "go", ms=10, label="start"); plt.plot(x, y, "rs", ms=10, label="akhir")
    plt.axis("equal"); plt.grid(alpha=.3); plt.legend(); plt.xlabel("x (m)"); plt.ylabel("y (m)")
    plt.title("Lintasan simulasi Robot BNU Gen I dari perintah MQTT")
    plt.tight_layout(); plt.savefig(args.out, dpi=120)


if __name__ == "__main__":
    main()
