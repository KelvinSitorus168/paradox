"""
Subscriber MQTT: berlangganan topic "Suhu1" dan "heater1" lalu mencetak
setiap pesan yang masuk (perilaku sama dengan widget di IoT MQTT Panel).

Pemakaian:
    python mqtt_subscriber.py                      # broker.hivemq.com
    python mqtt_subscriber.py --broker localhost
"""
import argparse
import random

import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[CONNECT] kode={reason_code}")
    for t in userdata["topics"]:
        client.subscribe(t, qos=1)
        print(f"[SUBSCRIBE] {t}")


def on_message(client, userdata, msg):
    print(f"[TERIMA] {msg.topic}: {msg.payload.decode()}")
    userdata["count"] += 1
    if userdata["max"] and userdata["count"] >= userdata["max"]:
        client.disconnect()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="broker.hivemq.com")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--max", type=int, default=0, help="berhenti setelah N pesan (0 = terus)")
    args = ap.parse_args()

    userdata = {"topics": ["Suhu1", "heater1"], "count": 0, "max": args.max}
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f"sub-{random.randint(0, 9999)}", userdata=userdata)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.broker, args.port, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()
