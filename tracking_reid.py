import cv2
import numpy as np
import torch
import sqlite3
import os  
import threading
from pathlib import Path
from boxmot import create_tracker
from ultralytics import YOLO
from scipy.spatial.distance import cosine

# --- SMS INTEGRATION ---
from sms_handler import send_alert_sms

# 🔥 CHANGE: Track last sent count per location
LAST_SENT_COUNT = {}
sms_lock = threading.Lock()

# --- INITIAL SETUP ---
if not os.path.exists("detected_people"):
    os.makedirs("detected_people")

MODEL_PATH = "yolo26s.pt"
REID_WEIGHTS = "osnet_x0_25_msmt17.pt"
DEVICE = "cpu"

VIDEO_REGISTRY = {
    "test_video_01.mp4": {"name": "Puranapul Bridge (Musi)", "lat": 17.3621, "lon": 78.4608},
    "test_video_02.mp4": {"name": "Amberpet Cause Way", "lat": 17.3915, "lon": 78.5222},
    "test_video_03.mp4": {"name": "Tolichowki - Nadeem Colony", "lat": 17.4010, "lon": 78.4095},
    "test_video_04.mp4": {"name": "Begumpet Nala", "lat": 17.4424, "lon": 78.4624},
    "test_video_05.mp4": {"name": "Hussain Sagar Lake Drain", "lat": 17.4230, "lon": 78.4750},
    "test_video_06.mp4": {"name": "Dilsukhnagar Metro Area", "lat": 17.3685, "lon": 78.5247},
    "test_video_07.mp4": {"name": "Himayat Nagar Main Road", "lat": 17.3990, "lon": 78.4830},
    "test_video_08.mp4": {"name": "Banjara Hills Rd No. 10", "lat": 17.4120, "lon": 78.4410},
    "test_video_09.mp4": {"name": "Secunderabad Station Underpass", "lat": 17.4330, "lon": 78.5010},
    "test_video_10.mp4": {"name": "Yousufguda Checkpost", "lat": 17.4300, "lon": 78.4350},
    "test_video_11.mp4": {"name": "Malakpet Station Road", "lat": 17.3788, "lon": 78.4979},
    "test_video_12.mp4": {"name": "Hi-Tech City Junction", "lat": 17.4435, "lon": 78.3772}
}

def clear_old_alerts():
    conn = sqlite3.connect('flood_guardian.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()

    for f in os.listdir("detected_people"):
        if f.endswith(".jpg"):
            os.remove(os.path.join("detected_people", f))

    print("🧹 System Cleaned: Fresh session started.")


class IdentityManager:
    def __init__(self, node_info):
        self.gallery = {}
        self.track_to_gid = {}
        self.next_id = 1
        self.sim_thresh = 0.75
        self.node_info = node_info 

    def get_embedding(self, tracker_obj, box, frame):
        return tracker_obj.model.get_features(np.array([box]), frame)[0]

    def cosine_sim(self, a, b):
        return 1 - cosine(a, b)

    def log_alert(self, gid):
        try:
            conn = sqlite3.connect('flood_guardian.db', timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (person_id, location, lat, lon, status) 
                VALUES (?, ?, ?, ?, ?)
            """, (gid, self.node_info["name"], self.node_info["lat"], self.node_info["lon"], 'Pending'))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DB ERROR]: {e}")

    def assign_id(self, tid, emb, box, frame):
        if tid in self.track_to_gid:
            gid = self.track_to_gid[tid]
            self.gallery[gid].append(emb)
            return gid

        best_id, best_sim = None, 0
        for gid, embs in self.gallery.items():
            sim = self.cosine_sim(emb, np.mean(embs, axis=0))
            if sim > best_sim:
                best_sim, best_id = sim, gid

        if best_sim > self.sim_thresh:
            gid = best_id
            self.gallery[gid].append(emb)
        else:
            # NEW PERSON
            gid = f"{self.node_info['name'][:3]}_{self.next_id}"
            self.gallery[gid] = [emb]

            try:
                x1, y1, x2, y2 = map(int, box)
                crop = frame[y1:y2, x1:x2]
                if crop.size > 0:
                    cv2.imwrite(f"detected_people/person_{gid}.jpg", crop)
            except:
                pass

            self.log_alert(gid)

            # 🔥 UPDATED SMS LOGIC
            total_humans = len(self.gallery)
            loc = self.node_info["name"]

            with sms_lock:
                last = LAST_SENT_COUNT.get(loc, 0)

                # Only send if count increased
                if total_humans > last:
                    LAST_SENT_COUNT[loc] = total_humans

                    send_alert_sms(
                        location=loc,
                        lat=self.node_info["lat"],
                        lon=self.node_info["lon"],
                        count=total_humans
                    )

                    print(f"📡 SMS UPDATED: {loc} | Count: {total_humans}")

            print(f"🚨 {loc} - Person {gid} | Count: {total_humans}")
            self.next_id += 1

        self.track_to_gid[tid] = gid
        return gid


def monitor_node(video_file, node_info, yolo_model):
    path = f"input/videos/{video_file}"
    if not os.path.exists(path):
        return

    cap = cv2.VideoCapture(path)

    tracker = create_tracker(
        tracker_type="botsort",
        tracker_config=Path("custom_tracker.yaml"),
        device=DEVICE,
        reid_weights=Path(REID_WEIGHTS)
    )

    manager = IdentityManager(node_info)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 360))
        results = yolo_model.predict(frame, conf=0.3, verbose=False)

        persons = []
        for r in results:
            if r.boxes is not None:
                dets = r.boxes.data.cpu().numpy()
                persons = [d for d in dets if int(d[5]) == 0]

        if persons:
            tracks = tracker.update(np.array(persons), frame)

            for t in tracks:
                x1, y1, x2, y2, tid = t[:5]
                emb = manager.get_embedding(tracker, [x1, y1, x2, y2], frame)
                manager.assign_id(tid, emb, [x1, y1, x2, y2], frame)

    cap.release()


if __name__ == "__main__":
    clear_old_alerts()
    model = YOLO(MODEL_PATH)

    threads = []

    for v, info in VIDEO_REGISTRY.items():
        t = threading.Thread(target=monitor_node, args=(v, info, model), daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Stopped")