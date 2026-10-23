"""
virtual_itclab_mqtt.py — "digital twin" ESP32 + iTCLab.
Menjalankan simulator FOPDT + PID dan berkomunikasi lewat MQTT dengan
topic yang SAMA PERSIS dengan IoT_PID_iTCLab.ino, sehingga dashboard
(IoT MQTT Panel / iot_dashboard.py) bisa diuji tanpa hardware.

    python virtual_itclab_mqtt.py --broker broker.hivemq.com --speed 10
--speed 10 artinya 1 detik nyata = 10 detik simulasi.
"""
import argparse
import os
import sys
import time

import paho.mqtt.client as mqtt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "03-Kit-iTCLab"))
sys.path.insert(0, os.path.join(HERE, "..", "04-Sistem-Kendali-PID"))
from itclab_sim import iTCLabSim      # noqa: E402
from pid_controller import PID        # noqa: E402

PREFIX = "kelvin341/itclab"
DEFAULT = (10.0, 50.0, 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="broker.hivemq.com")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--speed", type=float, default=10.0)
    ap.add_argument("--duration", type=float, default=0, help="detik simulasi (0 = terus)")
    ap.add_argument("--fault-at", type=int, default=-1,
                    help="detik simulasi saat heater melemah (Kp 0.5->0.3), untuk uji deteksi anomali")
    args = ap.parse_args()

    lab = iTCLabSim(seed=2)
    pid = PID(*DEFAULT)
    state = {"sp": 35.0}

    def on_connect(c, u, f, rc, p):
        for s in ["SetPoint", "Nilai_Kc", "Nilai_tauI", "Nilai_tauD", "autoSet"]:
            c.subscribe(f"{PREFIX}/{s}")
        print("[twin] terhubung & subscribe")

    def on_message(c, u, msg):
        name, v = msg.topic.split("/")[-1], msg.payload.decode()
        if name == "SetPoint":
            state["sp"] = float(v)
        elif name == "Nilai_Kc":
            pid.Kc = float(v)
        elif name == "Nilai_tauI":
            pid.tauI = float(v)
        elif name == "Nilai_tauD":
            pid.tauD = float(v)
        elif name == "autoSet" and v.strip() == "1":
            pid.Kc, pid.tauI, pid.tauD = DEFAULT
        print(f"[twin] {name}={v}")

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="twin-kelvin341")
    c.on_connect, c.on_message = on_connect, on_message
    c.connect(args.broker, args.port)
    c.loop_start()
    time.sleep(1)

    k = 0
    while not args.duration or k < args.duration:
        if k == args.fault_at:
            lab.Kp = 0.3
            print(f"[twin] FAULT disuntikkan pada t={k} s")
        pv = lab.T1
        op, *_ = pid.update(state["sp"], pv, 1.0)
        lab.Q1(op)
        lab.step(1.0)
        for name, val in [("Suhu1", pv), ("Suhu2", lab.T2), ("Nilai_op", op), ("SetPoint_now", state["sp"])]:
            c.publish(f"{PREFIX}/{name}", f"{val:.2f}")
        k += 1
        time.sleep(1.0 / args.speed)
    c.loop_stop()
    c.disconnect()


if __name__ == "__main__":
    main()
