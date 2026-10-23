"""
train_yolov8.py — fine-tuning YOLOv8 untuk dataset sendiri (transfer learning).

    # dataset 7 kelas robot BNU (lihat data_bnu.yaml)
    python train_yolov8.py --data data_bnu.yaml --epochs 100

    # uji coba alur training dengan dataset mini COCO8 (8 gambar)
    python train_yolov8.py --data coco8.yaml --epochs 10

Setelah selesai, metrik Precision, Recall, mAP50, mAP50-95 per kelas dicetak
dan bobot terbaik ada di runs/detect/<nama>/weights/best.pt
"""
import argparse

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data_bnu.yaml")
    ap.add_argument("--weights", default="yolov8n.pt")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--name", default="train")
    ap.add_argument("--device", default="cpu", help="'0' untuk GPU NVIDIA")
    args = ap.parse_args()

    model = YOLO(args.weights)                      # mulai dari bobot pralatih COCO
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz,
                device=args.device, name=args.name, exist_ok=True, plots=True)
    m = model.val(data=args.data, device=args.device)
    print(f"\nPrecision={m.box.mp:.3f}  Recall={m.box.mr:.3f}  mAP50={m.box.map50:.3f}  mAP50-95={m.box.map:.3f}")
    print("\nKelas | P | R | mAP50 | mAP50-95")
    for i, c in enumerate(m.box.ap_class_index):
        p, r, ap50, ap = m.box.class_result(i)
        print(f"{model.names[int(c)]} | {p:.3f} | {r:.3f} | {ap50:.3f} | {ap:.3f}")


if __name__ == "__main__":
    main()
