# export_onnx.py
from ultralytics import YOLO

def export_model_to_onnx():
    """Chuyển đổi mô hình PyTorch sang định dạng ONNX."""
    print("Bắt đầu quá trình chuyển đổi mô hình sang ONNX...")
    # Sử dụng yolov8n.pt vì best.pt không có
    model = YOLO("yolov8n.pt")  
    model.export(format="onnx", imgsz=640)  # Xuất ra file best.onnx
    print("Chuyển đổi thành công! Đã tạo file yolov8n.onnx.")

if __name__ == "__main__":
    export_model_to_onnx()