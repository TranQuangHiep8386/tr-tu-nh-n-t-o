from ultralytics import YOLO

if __name__ == '__main__':
    # 1. Khởi tạo mô hình YOLOv11 nano cho Segmentation
    model = YOLO("yolo11n-seg.pt") 

    # 2. Huấn luyện mô hình
    model.train(
        data="C:/canhbaochay/Fire and Smoke Segmentation.v6i.yolov11/data.yaml",
        epochs=50,         # Bạn có thể để 100, nhưng 50 là đủ để test trước
        imgsz=640,
        device='cpu',      # Bắt buộc dùng 'cpu' vì máy bạn chưa nhận GPU
        project="FireDetection",
        name="v1"
    )