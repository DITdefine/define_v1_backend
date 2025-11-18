import eventlet.wsgi
eventlet.monkey_patch()

import os
import re
import time
import cv2
import sqlite3
import requests
import threading
import torch
from dotenv import load_dotenv
from datetime import datetime
from collections import deque

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from ultralytics import YOLO

import serial
import time



# ===================== 환경 변수 =====================
load_dotenv()
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
OCR_URL = "https://api.upstage.ai/v1/document-digitization"

# ===================== SQLite 초기화 =====================
conn = sqlite3.connect("car_log.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS parking_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_number TEXT,
    vehicle_class TEXT,
    entry_time TEXT,
    exit_time TEXT,
    is_parked BOOLEAN DEFAULT 1,
    fee INTEGER DEFAULT 0
)
""")
conn.commit()

# ===================== YOLO 모델 =====================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ {device.upper()} 모드 사용")
model = YOLO("best10s.pt")
# 모델이 내부적으로 device 관리하므로 추가 처리는 모델에 따라 다름
print("✅ YOLO 모델 로드 완료")

# ===================== Flask 앱 / SocketIO =====================
app = Flask(__name__)
CORS(app)
sio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")  # 변수명을 sio로 분리

# ===================== 공유 변수들 =====================
gate_lock = threading.Lock()
arduino = serial.Serial(port="/dev/cu.usbmodem14101", baudrate=9600, timeout=1)
time.sleep(2) 

def openBar():
    """서보모터를 90도로 이동"""
    arduino.write(b"open\n")

def closeBar():
    """서보모터를 0도로 이동"""
    arduino.write(b"close\n")

def open_gate_sequence():
    if gate_lock.locked():
        return  # 이미 동작 중이면 실행하지 않음
    with gate_lock:
        openBar()
        time.sleep(3)
        closeBar()

latest_frame_lock = threading.Lock()
latest_frame = None

ocr_queue = deque()
ocr_lock = threading.Lock()
vehicle_status = {}  # { vehicle_class: {'last_queue_time': float} }
QUEUE_DELAY = 1.0            # 같은 차량(같은 클래스)을 큐에 넣는 최소 시간(초)

# 차량별 DB 업데이트 쿨다운 (같은 plate가 연속으로 DB에 저장되는 것을 방지)
vehicle_cooldown = {}  # { car_number: last_db_update_time }
DB_COOLDOWN = 3.0  # 초

# 로깅
def log_event(msg):
    ts = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
    entry = f"[{ts}]\n{msg}"
    print(entry)
    try:
        sio.emit("log", entry)
    except Exception:
        pass

# ===================== OCR 호출 =====================
def call_upstage_ocr(image):
    try:
        _, img_encoded = cv2.imencode(".jpg", image)
        img_bytes = img_encoded.tobytes()
        headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
        files = {'document': ('plate_image.jpg', img_bytes, 'image/jpeg')}
        data = {"model": "ocr"}
        resp = requests.post(OCR_URL, headers=headers, files=files, data=data, timeout=10)

        if resp.status_code != 200:
            print(f"❌ OCR 요청 실패: {resp.status_code} {resp.text}")
            return None

        data = resp.json()
        text = data.get("text")
        if not text:
            return None

        plate = text.replace(" ", "")
        match = re.search(r"\d{2,3}[가-힣]\d{4}", plate)
        if match:
            return match.group(0)
        else:
            return None
    except Exception as e:
        log_event(f"⚠️ OCR 예외: {e}")
        return None

# ===================== DB 저장 =====================
def calculate_fee(entry_time, exit_time):
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    start = datetime.strptime(entry_time, fmt)
    end = datetime.strptime(exit_time, fmt)
    duration = (end - start).total_seconds()

    # 분 단위 시간
    minutes = duration / 60

    # 기본 요금
    if minutes <= 30:
        return 1000

    # 추가 시간 요금
    extra_minutes = minutes - 30
    extra_units = int(extra_minutes // 10)
    return 1000 + extra_units * 500


def save_car_log(car_number, vehicle_class=None):
    now = datetime.now().isoformat()
    last_time = vehicle_cooldown.get(car_number, 0)

    if time.time() - last_time < DB_COOLDOWN:
        log_event("⏱️ 중복 저장 방지")
        return

    cursor.execute("""
        SELECT id, entry_time, is_parked FROM parking_log
        WHERE car_number=?
        ORDER BY id DESC LIMIT 1
    """, (car_number,))
    row = cursor.fetchone()

    if row and row[2] == 1:  # 주차중 → 출차 처리
        entry_time = row[1]
        fee = calculate_fee(entry_time, now)

        cursor.execute("""
            UPDATE parking_log
            SET exit_time=?, is_parked=0, fee=?
            WHERE id=?
        """, (now, fee, row[0]))

        log_event(f"💸 출차 완료: {car_number} | 요금: {fee:,}원")

    else:  # 출차 상태 → 새 입차
        cursor.execute("""
            INSERT INTO parking_log(car_number, vehicle_class, entry_time, exit_time, is_parked, fee)
            VALUES (?, ?, ?, NULL, 1, 0)
        """, (car_number, vehicle_class, now))

        log_event(f"🅿️ 입차 기록: {car_number} ({vehicle_class})")
    try:
        threading.Thread(target=open_gate_sequence, daemon=True).start()
        sio.emit("log", "true")
    except Exception:
        pass
    conn.commit()
    vehicle_cooldown[car_number] = time.time()

# ===================== OCR 큐 관리 =====================
def enqueue_plate(plate_img, vehicle_class):
    now_ts = time.time()
    status = vehicle_status.setdefault(vehicle_class, {'last_queue_time': 0})
    if now_ts - status['last_queue_time'] < QUEUE_DELAY:
        return
    with ocr_lock:
        # plate_img은 numpy array
        ocr_queue.append((plate_img.copy(), vehicle_class))
    status['last_queue_time'] = now_ts
    log_event(f"🟨 [YOLO] 차량/번호판 탐지 완료\nOCR 큐에 추가: {vehicle_class}")

# ===================== OCR 워커 =====================
def ocr_worker():
    log_event("OCR worker 시작")
    while True:
        plate_img = None
        vehicle_class = None
        with ocr_lock:
            if ocr_queue:
                plate_img, vehicle_class = ocr_queue.popleft()
        if plate_img is None:
            sio.sleep(0.05)
            continue

        car_number = call_upstage_ocr(plate_img)
        if car_number:
            save_car_log(car_number, vehicle_class)
            # 큐 전체 초기화(성공 시)
            with ocr_lock:
                ocr_queue.clear()
            log_event(f"🟢 OCR 성공: {car_number}\n큐 초기화 완료")
        else:
            log_event("⚠️ OCR 실패(번호판 인식 안됨)")

# ===================== 카메라 캡처 =====================
def camera_capture(device_idx=0, width=640, height=480):
    global latest_frame
    cap = cv2.VideoCapture(device_idx, cv2.CAP_DSHOW if os.name == 'nt' else 0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if not cap.isOpened():
        log_event("❌ Camera open failed")
        return
    log_event("카메라 캡처 시작")
    while True:
        ret, frame = cap.read()
        # frame = cv2.flip(frame, 1) # 영상 좌우 뒤집기
        if ret:
            with latest_frame_lock:
                latest_frame = frame.copy()
        else:
            log_event("카메라 프레임 읽기 실패")
        sio.sleep(0.01)

# ===================== 추론 + emit =====================
def inference_and_emit(fps=15, jpeg_quality=70):
    global latest_frame
    interval = 1.0 / fps
    log_event("Inference/Emit 시작")
    while True:
        start = time.time()
        frame_copy = None
        with latest_frame_lock:
            if latest_frame is not None:
                frame_copy = latest_frame.copy()
        if frame_copy is None:
            sio.sleep(0.01)
            continue

        plate_conf = 0.0
        car_box = None
        vehicle_class = None
        vehicle_conf = 0.0

        # YOLO 추론
        try:
            results = model(frame_copy, imgsz=320, half=(device == "cuda"), verbose=False)
        except Exception as e:
            log_event(f"YOLO error: {e}")
            sio.sleep(0.01)
            continue

        annotated = frame_copy.copy()
        try:
            for box in results[0].boxes:
                conf = float(box.conf.item())
                cls = int(box.cls.item())
                name = model.names[cls].lower()
                xy = [int(x) for x in box.xyxy[0].tolist()]  # [x1, y1, x2, y2]
                # 박스 그리기(신뢰도 임계값)
                if conf > 0.7:
                    log_event(f"클래스: {name}, conf: {conf:.2f}")
                    cv2.rectangle(annotated, (xy[0], xy[1]), (xy[2], xy[3]), (0, 255, 0), 2)
                    cv2.putText(annotated, f"{name} {conf:.2f}", (xy[0], max(15, xy[1]-5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                if name == "plate":
                    plate_conf = max(plate_conf, conf)
                else:
                    car_box = xy
                    vehicle_class = name
                    vehicle_conf = max(vehicle_conf, conf)
        except Exception as e:
            log_event(f"박스 처리 예외: {e}")

        # crop 할 때는 annotated(원본 프레임 기반)에서 자름
        if car_box and plate_conf >= 0.7 and vehicle_conf >= 0.7:
            h, w = annotated.shape[:2]
            x1, y1, x2, y2 = car_box
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)
            plate_img = annotated[y1:y2, x1:x2]
            # 디버그: 로컬에서 확인하고 싶으면 저장하거나 (서버엔 권장하지 않음)
            enqueue_plate(plate_img, vehicle_class)

        # JPEG 인코딩 (emit 용)
        success, buf = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
        if success:
            try:
                sio.emit("video_frame", buf.tobytes())
            except Exception as e:
                log_event(f"emit error: {e}")
        else:
            log_event("JPEG encode failed")

        elapsed = time.time() - start
        sleep_t = interval - elapsed
        if sleep_t > 0:
            sio.sleep(sleep_t)
        else:
            sio.sleep(0.001)

# ===================== 앱 라우트 =====================
@app.route("/")
def home():
    return "Realtime streaming server running"
@app.route("/todayOverview")
def get_today_overview():
    today = datetime.now().strftime("%Y-%m-%d")

    # 오늘 로그
    cursor.execute("""
        SELECT car_number, vehicle_class, entry_time, exit_time, fee, is_parked
        FROM parking_log
        WHERE entry_time LIKE ?
        ORDER BY id DESC
    """, (today + "%",))
    rows = cursor.fetchall()
    logs = [
        {
            "car_number": r[0],
            "vehicle_class": r[1],
            "entry_time": r[2],
            "exit_time": r[3],
            "fee": r[4],
            "is_parked": r[5]
        }
        for r in rows
    ]

    # 현재 주차중 차량 수
    cursor.execute("SELECT COUNT(*) FROM parking_log WHERE is_parked = 1")
    parking_count = cursor.fetchone()[0]

    # 결과 합치기
    return {
        "todayLogs": logs,
        "parkingCount": parking_count
    }

# ===================== 서버 시작 지점 =====================
if __name__ == "__main__":
    # 백그라운드 태스크 등록(Flask-SocketIO 권장 방식)
    sio.start_background_task(camera_capture, 0, 640, 480)
    sio.start_background_task(inference_and_emit, 15, 70)
    sio.start_background_task(ocr_worker)

    # Flask-SocketIO 로 run (eventlet 사용 시)
    sio.run(app, host="0.0.0.0", port=5000)