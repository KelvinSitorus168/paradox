"""
tracking_yolov8_deepsort.py — Robot BNU Generasi II:
YOLOv8 (deteksi) + DeepSORT (pelacakan, ID tetap antar-frame) + logika kendali robot.

Alur per frame:
  kamera -> YOLOv8 -> bounding box -> DeepSORT -> track ID
        -> pilih target (kelas tertentu, ID terkunci) -> perintah robot
        -> (opsional) kirim ke ESP32 lewat MQTT topic kelvin341/bnu/cmd

    python tracking_yolov8_deepsort.py --source sample/demo_tracking.mp4 --target person
    python tracking_yolov8_deepsort.py --source 0 --target bottle --mqtt broker.hivemq.com

Butuh: pip install ultralytics deep-sort-realtime paho-mqtt opencv-python
"""
import argparse
from collections import defaultdict

import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO

TOPIC = "kelvin341/bnu/cmd"


def robot_command(box, frame_w, frame_h, dead=0.15, near=0.55):
    """Ubah posisi target di gambar menjadi perintah gerak robot."""
    if box is None:
        return "CARI"                      # target hilang: putar pelan mencari
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2 / frame_w - 0.5     # -0.5 (kiri) .. 0.5 (kanan)
    tinggi = (y2 - y1) / frame_h           # makin besar = makin dekat
    if tinggi > near:
        return "STOP"
    if cx < -dead:
        return "KIRI"
    if cx > dead:
        return "KANAN"
    return "MAJU"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="0")
    ap.add_argument("--weights", default="yolov8n.pt")
    ap.add_argument("--target", default="person", help="nama kelas yang diikuti robot")
    ap.add_argument("--conf", type=float, default=0.4)
    ap.add_argument("--mqtt", default=None, help="alamat broker untuk mengirim perintah ke robot")
    ap.add_argument("--save", default="img/tracking_output.mp4")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    model = YOLO(args.weights)
    tracker = DeepSort(max_age=15, n_init=2, embedder="mobilenet", half=False)
    cap = cv2.VideoCapture(int(args.source) if args.source.isdigit() else args.source)
    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    w, h = int(cap.get(3)), int(cap.get(4))
    writer = cv2.VideoWriter(args.save, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h)) if args.save else None

    client = None
    if args.mqtt:
        import paho.mqtt.client as mqtt
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(args.mqtt, 1883); client.loop_start()

    locked_id, last_cmd = None, None
    frames_per_id = defaultdict(int)
    cmd_log, n = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        n += 1
        res = model.predict(frame, conf=args.conf, verbose=False)[0]
        dets = []
        for b in res.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            dets.append(([x1, y1, x2 - x1, y2 - y1], float(b.conf), model.names[int(b.cls)]))
        tracks = tracker.update_tracks(dets, frame=frame)

        target_box = None
        candidates = []
        for tr in tracks:
            if not tr.is_confirmed():
                continue
            frames_per_id[tr.track_id] += 1
            l, t, r, btm = tr.to_ltrb()
            cls = tr.get_det_class()
            col = (0, 200, 0) if tr.track_id == locked_id else (200, 120, 0)
            cv2.rectangle(frame, (int(l), int(t)), (int(r), int(btm)), col, 2)
            cv2.putText(frame, f"ID {tr.track_id} {cls}", (int(l), int(t) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
            if cls == args.target:
                candidates.append((tr.track_id, (l, t, r, btm)))
        ids = [c[0] for c in candidates]
        if locked_id not in ids and candidates:                       # kunci target terbesar
            locked_id = max(candidates, key=lambda c: (c[1][2] - c[1][0]) * (c[1][3] - c[1][1]))[0]
        for tid, box in candidates:
            if tid == locked_id:
                target_box = box

        cmd = robot_command(target_box, w, h)
        cmd_log.append(cmd)
        if cmd != last_cmd and client:
            client.publish(TOPIC, cmd)
        last_cmd = cmd
        cv2.putText(frame, f"CMD: {cmd}  target ID: {locked_id}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        if writer:
            writer.write(frame)
        if n in (15, 60, 110):
            cv2.imwrite(f"img/tracking_frame_{n:03d}.jpg", frame)
        if args.show:
            cv2.imshow("BNU Gen II - YOLOv8 + DeepSORT", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    cap.release()
    if writer:
        writer.release()
    print(f"Frame diproses: {n}")
    print("Jumlah frame per track ID:", dict(frames_per_id))
    print("Distribusi perintah robot:", {c: cmd_log.count(c) for c in sorted(set(cmd_log))})


if __name__ == "__main__":
    main()
