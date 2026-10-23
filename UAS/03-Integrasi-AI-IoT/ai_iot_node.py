"""
ai_iot_node.py — node AI di application layer arsitektur IoT-AI-iTCLab.

  [ESP32/iTCLab] --MQTT--> [broker] --MQTT--> [ai_iot_node.py] --MQTT--> [MQTT Panel / Blynk]
                 Suhu1, Nilai_op               model ARX + deteksi anomali    <prefix>/ai/alert
                                                                               <prefix>/ai/residual

1. Mode latih : rekam data normal dari MQTT lalu simpan model (arx_model.npz)
       python ai_iot_node.py --train 600 --broker broker.hivemq.com
2. Mode pantau: deteksi anomali online, publikasikan alert
       python ai_iot_node.py --monitor 900 --broker broker.hivemq.com
"""
import argparse
import queue
import time

import numpy as np
import paho.mqtt.client as mqtt

from ai_anomaly_detector import ArxAnomalyDetector, OnlineDetector

PREFIX = "kelvin341/itclab"


def connect(broker, port, cid):
    q = queue.Queue()
    last = {}

    def on_connect(c, u, f, rc, p):
        c.subscribe(f"{PREFIX}/Suhu1"); c.subscribe(f"{PREFIX}/Nilai_op")

    def on_message(c, u, msg):
        name = msg.topic.split("/")[-1]
        last[name] = float(msg.payload.decode())
        if name == "Nilai_op" and "Suhu1" in last:      # 1 pasang (T, Q) per sampel
            q.put((last["Suhu1"], last["Nilai_op"]))

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cid)
    c.on_connect, c.on_message = on_connect, on_message
    c.connect(broker, port)
    c.loop_start()
    return c, q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="broker.hivemq.com")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--train", type=int, default=0, help="jumlah sampel data normal untuk latih")
    ap.add_argument("--monitor", type=int, default=0, help="jumlah sampel untuk dipantau")
    ap.add_argument("--model", default="arx_model.npz")
    args = ap.parse_args()
    c, q = connect(args.broker, args.port, f"ai-node-{np.random.randint(9999)}")

    if args.train:
        T, Q = [], []
        while len(T) < args.train:
            t, u = q.get(timeout=30); T.append(t); Q.append(u)
        det = ArxAnomalyDetector().fit(T, Q)
        np.savez(args.model, theta=det.theta, sigma=det.sigma)
        print(f"[AI] model dilatih dari {len(T)} sampel; sigma={det.sigma:.4f}")

    if args.monitor:
        z = np.load(args.model)
        det = ArxAnomalyDetector(); det.theta, det.sigma = z["theta"], float(z["sigma"])
        online, prev = OnlineDetector(det), False
        for i in range(args.monitor):
            t, u = q.get(timeout=30)
            rs, alarm = online.update(t, u)
            c.publish(f"{PREFIX}/ai/residual", f"{rs:.4f}")
            if alarm != prev:
                msg = "ANOMALI: perilaku plant tidak sesuai model" if alarm else "NORMAL"
                c.publish(f"{PREFIX}/ai/alert", msg, retain=True)
                print(f"[AI] sampel {i}: {msg} (residual={rs:.4f})")
                prev = alarm
    time.sleep(0.5)
    c.loop_stop(); c.disconnect()


if __name__ == "__main__":
    main()
