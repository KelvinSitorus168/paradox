"""
make_demo_video.py — membuat video uji sintetis dari sample/bus.jpg:
kamera "bergerak" (gambar bergeser kiri-kanan sambil membesar) sehingga objek berpindah posisi
antar-frame. Dipakai untuk menguji tracking tanpa kamera robot.
"""
import os

import cv2
import numpy as np

os.chdir(os.path.dirname(os.path.abspath(__file__)))
img = cv2.imread("sample/bus.jpg")
H, W = img.shape[:2]
out = cv2.VideoWriter("sample/demo_tracking.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (640, 480))
N = 120
for i in range(N):
    # adegan "mendekat": gambar membesar (robot mendekati target) sambil bergeser kiri-kanan
    scale = 0.30 + 0.45 * i / N
    sw, sh = int(W * scale), int(H * scale)
    small = cv2.resize(img, (sw, sh))
    canvas = np.full((480, 640, 3), 90, np.uint8)
    cx = int(320 + 200 * np.sin(2 * np.pi * i / N) - sw / 2)
    cy = int(480 - sh) if sh < 480 else 0
    x0, x1 = max(0, cx), min(640, cx + sw)
    y1 = min(480, cy + sh)
    canvas[cy:y1, x0:x1] = small[0:y1 - cy, x0 - cx:x1 - cx]
    out.write(canvas)
out.release()
print(f"sample/demo_tracking.mp4 dibuat ({N} frame)")
