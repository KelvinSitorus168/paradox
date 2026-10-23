"""
iot_dashboard.py — pemantau & pengendali PID-iTCLab via MQTT dari laptop.
- Subscribe Suhu1, Nilai_op, SetPoint_now -> simpan ke CSV + grafik
- Bisa mengirim perintah (SetPoint, Kc, tauI, tauD) dari daftar jadwal

    python iot_dashboard.py --broker broker.hivemq.com --duration 120
    python iot_dashboard.py --set SetPoint=45            # kirim 1 perintah
"""
import argparse
import csv
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt

PREFIX = "kelvin341/itclab"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="broker.hivemq.com")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--duration", type=float, default=60, help="lama memantau (detik nyata)")
    ap.add_argument("--set", action="append", default=[],
                    help="perintah 'Nama=nilai@detik', contoh SetPoint=45@20")
    ap.add_argument("--out", default="iot_log")
    args = ap.parse_args()

    log, last = [], {}

    def on_connect(c, u, f, rc, p):
        for s in ["Suhu1", "Nilai_op", "SetPoint_now"]:
            c.subscribe(f"{PREFIX}/{s}")

    def on_message(c, u, msg):
        name = msg.topic.split("/")[-1]
        last[name] = float(msg.payload.decode())
        if name == "SetPoint_now" and {"Suhu1", "Nilai_op"} <= last.keys():
            log.append((len(log), last["SetPoint_now"], last["Suhu1"], last["Nilai_op"]))

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="dash-kelvin341")
    c.on_connect, c.on_message = on_connect, on_message
    c.connect(args.broker, args.port)
    c.loop_start()

    cmds = []
    for s in args.set:
        kv, _, at = s.partition("@")
        k, v = kv.split("=")
        cmds.append((float(at or 0), k, v))
    t0 = time.time()
    while time.time() - t0 < args.duration:
        now = time.time() - t0
        for cmd in [x for x in cmds if x[0] <= now]:
            c.publish(f"{PREFIX}/{cmd[1]}", cmd[2])
            print(f"[dash] kirim {cmd[1]}={cmd[2]}")
            cmds.remove(cmd)
        time.sleep(0.1)
    c.loop_stop()
    c.disconnect()

    if not log:
        print("Tidak ada data diterima.")
        return
    with open(args.out + ".csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["sampel", "SetPoint", "Suhu1", "Nilai_op"]); w.writerows(log)
    n, sp, pv, op = zip(*log)
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    ax[0].plot(n, sp, "k--", label="SetPoint"); ax[0].plot(n, pv, "r", label="Suhu1")
    ax[0].set_ylabel("°C"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(n, op, "b", label="Nilai_op (heater %)")
    ax[1].set_ylabel("%"); ax[1].set_xlabel("Sampel (1 sampel = 1 s waktu plant)"); ax[1].legend(); ax[1].grid(alpha=.3)
    fig.suptitle("Data PID-iTCLab diterima lewat MQTT")
    fig.tight_layout(); fig.savefig(f"img/{args.out}.png", dpi=120)
    print(f"{len(log)} sampel tersimpan -> {args.out}.csv, img/{args.out}.png")


if __name__ == "__main__":
    main()
