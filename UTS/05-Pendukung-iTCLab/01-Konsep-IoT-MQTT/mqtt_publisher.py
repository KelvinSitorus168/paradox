"""
Publisher MQTT sederhana: mensimulasikan sensor suhu iTCLab yang mengirim
data ke topic "Suhu1" setiap 1 detik.

Pemakaian:
    python mqtt_publisher.py                       # broker.hivemq.com
    python mqtt_publisher.py --broker localhost    # broker lokal
"""
import argparse
import random
import time

import paho.mqtt.client as mqtt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="broker.hivemq.com")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--topic", default="Suhu1")
    ap.add_argument("--n", type=int, default=10, help="jumlah pesan")
    args = ap.parse_args()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"pub-{random.randint(0, 9999)}")
    client.connect(args.broker, args.port, keepalive=60)
    client.loop_start()

    suhu = 25.0
    for i in range(args.n):
        suhu += random.uniform(-0.2, 0.6)          # suhu naik perlahan
        payload = f"{suhu:.2f}"
        info = client.publish(args.topic, payload, qos=1)
        info.wait_for_publish()
        print(f"[PUBLISH] {args.topic} -> {payload}")
        time.sleep(1)

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
