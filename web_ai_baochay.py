import streamlit as st
import cv2
import os
import time
from ultralytics import YOLO
from datetime import datetime

# ================== CẤU HÌNH ==================
MODEL_PATH = "C:/canhbaochay/bestt.pt"
LOG_FILE = "C:/canhbaochay/fire_log.txt"
ALERT_DIR = "C:/canhbaochay/alerts"

os.makedirs(ALERT_DIR, exist_ok=True)

# 1. Giao diện Web
st.set_page_config(page_title="Hệ thống Giám sát Cháy AI", layout="wide")
st.title("🔥 Giám sát Cháy trực tuyến - hiep tran")

# Chia giao diện thành 2 cột: Trái (Camera) - Phải (Lịch sử & Ảnh)
col_left, col_right = st.columns([2, 1])

# 2. Tải mô hình
@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

model = load_model()

# ================== MỤC 1: CAMERA TRỰC TIẾP (Bên Trái) ==================
with col_left:
    st.subheader("📹 1. Camera Giám Sát Real-time")
    run_app = st.toggle("Kích hoạt Camera AI", value=True)
    frame_placeholder = st.empty()

    if run_app:
        cap = cv2.VideoCapture(0)
        last_save_time = 0
        
        while cap.isOpened() and run_app:
            ret, frame = cap.read()
            if not ret: break

            results = model.predict(frame, conf=0.8, verbose=False)
            annotated_frame = results[0].plot()

            if len(results[0].boxes) > 0:
                current_time = time.time()
                if current_time - last_save_time > 10: 
                    now = datetime.now()
                    img_name = f"fire_{now.strftime('%H%M%S')}.jpg"
                    img_path = os.path.join(ALERT_DIR, img_name)
                    cv2.imwrite(img_path, annotated_frame)
                    
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(f"[{now.strftime('%H:%M:%S')}] 🔥 PHÁT HIỆN CHÁY - Lưu ảnh: {img_name}\n")
                    last_save_time = current_time

            # KHẮC PHỤC LỖI image_c7d5c3: Thay width=None bằng width=700
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", width=700) 

        cap.release()

# ================== MỤC 2 & 3: LỊCH SỬ & ẢNH CHỤP (Bên Phải) ==================
with col_right:
    # MỤC 2: NHẬT KÝ LỊCH SỬ
    st.subheader("📋 2. Nhật ký lịch sử")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()
        st.text_area("Lịch sử phát hiện:", "".join(reversed(logs)), height=300)
    else:
        st.info("Chưa có lịch sử.")

    st.divider()

    # MỤC 3: ẢNH BÁO ĐỘNG ĐÃ CHỤP LẠI
    st.subheader("🖼️ 3. Ảnh bằng chứng mới nhất")
    if os.path.exists(ALERT_DIR):
        images = [f for f in os.listdir(ALERT_DIR) if f.endswith('.jpg')]
        if images:
            # Sắp xếp lấy ảnh mới nhất theo thời gian (image_c768e6)
            images.sort(key=lambda x: os.path.getmtime(os.path.join(ALERT_DIR, x)))
            latest_img_path = os.path.join(ALERT_DIR, images[-1])
            st.image(latest_img_path, caption=f"Bằng chứng: {images[-1]}", width=350)
        else:
            st.info("Chưa có ảnh chụp.")