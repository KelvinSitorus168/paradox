"""
teleop_mqtt.py — kendali robot BNU dari keyboard laptop via MQTT.
    w = MAJU, s = MUNDUR, a = KIRI, d = KANAN, spasi = STOP, q = keluar
Mode skrip (untuk pengujian):  python teleop_mqtt.py --script "MAJU:3,KIRI:2,MAJU:2,STOP:1"
"""
import argparse
import sys
import time

import paho.mqtt.client as mqtt

TOPIC = "kelvin341/bnu/cmd"
KEYS = {"w": "MAJU", "s": "MUNDUR", "a": "KIRI", "d": "KANAN", " ": "STOP"}


def getch():
    try:
        import msvcrt                      # Windows
        return msvcrt.getwch()
    except ImportError:
        import termios, tty                # Linux / macOS
        fd = sys.stdin.fileno(); old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd); return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="broker.hivemq.com")
    ap.add_argument("--script", default=None, help="urutan PERINTAH:detik dipisah koma")
    args = ap.parse_args()
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.connect(args.broker, 1883); c.loop_start()

    if args.script:
        for item in args.script.split(","):
            cmd, dur = item.split(":")
            t_end = time.time() + float(dur)
            while time.time() < t_end:            # kirim ulang tiap 0,5 s (failsafe robot 1,5 s)
                c.publish(TOPIC, cmd); time.sleep(0.5)
            print(f"[teleop] {cmd} selama {dur} s")
    else:
        print("w/a/s/d untuk bergerak, spasi STOP, q keluar")
        while (k := getch().lower()) != "q":
            if k in KEYS:
                c.publish(TOPIC, KEYS[k]); print(KEYS[k])
        c.publish(TOPIC, "STOP")
    time.sleep(0.3); c.loop_stop(); c.disconnect()


if __name__ == "__main__":
    main()
