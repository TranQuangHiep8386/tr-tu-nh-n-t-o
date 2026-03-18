from ultralytics import YOLO
import cv2

# 1. Load mô hình bạn vừa huấn luyện xong
model = YOLO("C:/canhbaochay/bestt.pt") 

# 2. Chạy nhận diện (0 là Webcam, hoặc thay bằng "video.mp4")
results = model.predict(source="0", show=True, conf=0.6)

# Nhấn 'q' để thoát khi đang xem