"""
imclab.py — client Python untuk Kit iMCLab (firmware imclab_firmware.ino) via serial.
Firmware juga menerima perintah program dosen (1, 0, +, -, PWM:xxx, R).
Antarmuka sama dengan imclab_sim.py:  lab.pwm(u), lab.rpm, lab.step(dt), lab.close()

    from imclab import iMCLab
    lab = iMCLab()            # deteksi port otomatis, atau iMCLab("COM5")
    lab.pwm(150); print(lab.rpm); lab.close()

Butuh: pip install pyserial
"""
import time

import serial
from serial.tools import list_ports


def find_port():
    """Sama seperti notebook dosen: utamakan CP210x/CH340, abaikan port Bluetooth."""
    best = None
    for p in list_ports.comports():
        txt = f"{p.description} {p.manufacturer} {p.hwid}".upper()
        if "BLUETOOTH" in txt:
            continue
        if (p.vid, p.pid) in {(0x10C4, 0xEA60), (0x1A86, 0x7523)} or "CP210" in txt or "CH34" in txt:
            return p.device
        if "USB" in txt or "UART" in txt:
            best = best or p.device
    if best:
        return best
    raise RuntimeError("Kit iMCLab tidak ditemukan. Cek kabel USB & driver CP210x/CH340.")


class iMCLab:
    def __init__(self, port=None, baud=115200):
        self.sp = serial.Serial(port or find_port(), baud, timeout=1)
        time.sleep(2)                       # ESP32 reset saat port dibuka
        self.sp.reset_input_buffer()
        print("Terhubung:", self.send("VER"))
        self.t0 = time.time()

    def send(self, cmd):
        self.sp.write((cmd + "\n").encode())
        return self.sp.readline().decode(errors="ignore").strip()

    def pwm(self, u):
        return int(float(self.send(f"PWM {int(u)}")))

    @property
    def rpm(self):
        return float(self.send("RPM"))

    @property
    def t(self):
        return time.time() - self.t0

    def step(self, dt):
        """Menunggu dt detik (versi kit asli dari step() simulator)."""
        time.sleep(dt)

    def close(self):
        self.send("X")
        self.sp.close()
