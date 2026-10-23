"""
deteksi_yolov8.py — deteksi objek dengan YOLOv8 (gambar, folder, video, atau webcam).

    python deteksi_yolov8.py --source gambar.jpg
    python deteksi_yolov8.py --source 0            # webcam laptop
    python deteksi_yolov8.py --source data/images --weights runs/detect/train/weights/best.pt

Kelas yang relevan untuk robot BNU (COCO): person, bottle, chair, potted plant, ...
Untuk 7 kelas di artikel (botol, kursi, manusia, pot, galon, tong sampah, ember)
pakai bobot hasil train_yolov8.py.
"""
import argparse
import os
from collections import Counter

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--weights", default="yolov8n.pt")
    ap.add_argument("--conf", type=float, default=0.4)
    ap.add_argument("--out", default="img")
    args = ap.parse_args()

    model = YOLO(args.weights)
    src = int(args.source) if args.source.isdigit() else args.source
    os.makedirs(args.out, exist_ok=True)
    for res in model.predict(src, conf=args.conf, stream=True, verbose=False):
        names = [model.names[int(c)] for c in res.boxes.cls]
        ms = sum(res.speed.values())
        print(f"{os.path.basename(res.path)}: {dict(Counter(names))}  ({ms:.0f} ms/gambar)")
        for b, n in zip(res.boxes, names):
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            print(f"   {n:<12} conf={float(b.conf):.2f}  box=({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f})")
        if isinstance(src, str):
            res.save(filename=os.path.join(args.out, "deteksi_" + os.path.basename(res.path)))


if __name__ == "__main__":
    main()
