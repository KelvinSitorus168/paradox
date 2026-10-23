"""
itclab.py — client Python untuk Kit iTCLab via port serial.
Antarmuka (T1, T2, Q1(), Q2(), LED(), close) sama dengan itclab_sim.py,
sehingga program eksperimen bisa jalan di hardware maupun simulasi.

Butuh: pip install pyserial
"""
import time

import serial
from serial.tools import list_ports


def find_port():
    for p in list_ports.comports():
        desc = f"{p.description} {p.hwid}".upper()
        if any(k in desc for k in ("CP210", "CH340", "USB", "UART")):
            return p.device
    raise RuntimeError("Kit iTCLab tidak ditemukan. Cek kabel USB / driver CP210x atau CH340.")


class iTCLab:
    def __init__(self, port=None, baud=115200):
        self.sp = serial.Serial(port or find_port(), baud, timeout=2)
        time.sleep(2)                  # ESP32 reset saat port dibuka
        print(self.send("VER"))

    def send(self, cmd):
        self.sp.write((cmd + "\n").encode())
        return self.sp.readline().decode(errors="ignore").strip()

    @property
    def T1(self):
        return float(self.send("T1"))

    @property
    def T2(self):
        return float(self.send("T2"))

    def Q1(self, pct):
        return float(self.send(f"Q1 {pct:.1f}"))

    def Q2(self, pct):
        return float(self.send(f"Q2 {pct:.1f}"))

    def LED(self, pct):
        return float(self.send(f"LED {pct:.1f}"))

    def close(self):
        self.send("X")
        self.sp.close()
