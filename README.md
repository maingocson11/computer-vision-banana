# Bài Nhận Diện — README

**Giới thiệu**

Dự án này là một hệ thống mẫu để nhận diện (detection) sử dụng mô hình ONNX, bao gồm phát hiện ảnh tĩnh và phát hiện từ camera. Mục tiêu là cung cấp một bộ công cụ nhỏ gọn để thử nghiệm mô hình ONNX, chạy thử nghiệm trên ảnh, chạy nhận diện thời gian thực từ webcam, và tích hợp giao diện hiển thị (Streamlit / trang web đơn giản). README này mô tả các chức năng chính, cấu trúc file, hướng dẫn cài đặt và cách sử dụng.

**Tính năng chính**

- Nhận diện trên ảnh tĩnh (Image Detection).
- Nhận diện thời gian thực từ camera (Camera Detection / Webcam).
- Hỗ trợ mô hình ONNX đã export (`best.onnx`) và script xuất mô hình (`export_onnx.py`).
- Script kiểm thử mô hình ONNX (`test_onnx.py`).
- Ứng dụng giao diện nhanh bằng `streamlit_app.py` để thử nghiệm nhanh.
- Các trang HTML mẫu (đăng nhập, đăng ký, dashboard, forum, v.v.) để minh họa phần front-end (nếu muốn tích hợp).
- Hỗ trợ phát hiện khuôn mặt bằng Haar Cascade (`haarcascade_frontalface_default.xml`) nếu cần.

**Cấu trúc file quan trọng**

- `best.onnx`: Mô hình ONNX đã train/convert sẵn dùng để inference.
- `export_onnx.py`: Script để export/conver mô hình gốc sang định dạng ONNX.
- `test_onnx.py`: Script để kiểm tra inference trên `best.onnx` (ví dụ chạy kiểm thử trên ảnh mẫu và in kết quả).
- `main.py`: Tập lệnh chính (nếu repo dùng CLI hoặc entrypoint để chạy chức năng chính).
- `streamlit_app.py`: Ứng dụng Streamlit cho phép upload ảnh, xem kết quả nhận diện, và thử camera.
- `pages/1_Image_Detection.py`: Mã cụ thể cho nhận diện ảnh (ví dụ phần demo hoặc module trong app).
- `pages/2_Camera_Detection.py`: Mã cho nhận diện từ camera / webcam.
- `haarcascade_frontalface_default.xml`: Tập tin cascade để phát hiện khuôn mặt (OpenCV).
- `export_onnx.py`: Script để xuất mô hình (nhắc lại vì thường cần chỉnh thông số trước khi dùng).
- `check.py`: Script kiểm tra/tiện ích (các kiểm tra nhanh hoặc helper).
- `database.py`: Mã xử lý lưu trữ/DB nếu giao diện web cần lưu người dùng/bài viết.
- Các file HTML (`login.html`, `register.html`, `dashboard.html`, `forum.html`, `post_detail.html`, `create_post.html`, `edit_profile.html`, `chatbot.html`) và `style.css`: giao diện front-end mẫu.

**Yêu cầu và cài đặt**

- Python 3.8+ (khuyến nghị 3.9+).
- Cài các phụ thuộc bằng `requirements.txt`:

```powershell
pip install -r requirements.txt
```

- Nếu bạn chỉ muốn chạy inference ONNX, cần `onnxruntime` hoặc `onnxruntime-gpu`:

```powershell
pip install onnxruntime
# hoặc nếu có GPU
pip install onnxruntime-gpu
```

**Cách chạy (tổng quan)**

- Chạy ứng dụng Streamlit (giao diện thử nghiệm nhanh):

```powershell
streamlit run streamlit_app.py
```

- Chạy nhận diện ảnh (nếu có script cụ thể trong `pages/1_Image_Detection.py` hoặc `main.py`):

```powershell
python pages/1_Image_Detection.py --input path/to/image.jpg --model best.onnx
# hoặc nếu main.py chứa entry cho image detection
python main.py --mode image --input path/to/image.jpg
```

- Chạy nhận diện camera (webcam):

```powershell
python pages/2_Camera_Detection.py --model best.onnx
# hoặc
python main.py --mode camera
```

- Export mô hình sang ONNX (nếu bạn có mã train gốc):

```powershell
python export_onnx.py --output best.onnx
```

- Kiểm thử mô hình ONNX bằng script test:

```powershell
python test_onnx.py --model best.onnx --test-image tests/sample.jpg
```

(Lưu ý: các tham số CLI bên trên là ví dụ — kiểm tra nội dung script tương ứng để biết tên tham số thực tế.)

**Ghi chú kỹ thuật**

- Inference ONNX: Sử dụng `onnxruntime` để load `best.onnx` và chạy forward. Cần chuẩn hóa ảnh (resize, scale, mean/std) theo cùng chuẩn đã train.
- Camera Detection: Sử dụng OpenCV (`cv2.VideoCapture`) để đọc frame, thực hiện tiền xử lý tương tự ảnh tĩnh, chạy inference và vẽ bounding box/label trên frame.
- Haar Cascade: File `haarcascade_frontalface_default.xml` dùng để phát hiện khuôn mặt bằng OpenCV, có thể dùng kết hợp khi cần phát hiện face trước khi phân loại.
- Nếu muốn tăng tốc inference trên GPU, cài `onnxruntime-gpu` và cấu hình môi trường CUDA/cuDNN phù hợp.

**Kiểm tra và debug nhanh**

- Kiểm tra phiên bản Python:

```powershell
python --version
```

- Kiểm tra package `onnxruntime`:

```powershell
python -c "import onnxruntime; print(onnxruntime.__version__)"
```

- Nếu gặp lỗi load model, đảm bảo `best.onnx` không bị hỏng và tương thích với phiên bản `onnxruntime`.

**Mẹo vận hành**

- Thử chạy `test_onnx.py` trước để đảm bảo mô hình hoạt động trên môi trường hiện tại.
- Sử dụng Streamlit để có giao diện nhanh cho demo trước khi tích hợp vào hệ thống web chính thức.
- Giữ `requirements.txt` cập nhật nếu thêm package mới.

**Tương lai & mở rộng**

- Thêm tính năng lưu kết quả vào `database.py` để theo dõi logs hoặc kết quả người dùng.
- Tích hợp API server (Flask/FastAPI) để nhận file từ client web và trả về kết quả JSON.
- Hỗ trợ batch inference, tối ưu ONNX (quantization, simplification) để tăng tốc.

**Liên hệ / Tài liệu**

- File yêu cầu: `requirements.txt` — kiểm tra và cài đặt.
- Mô tả file chính: xem `pages/1_Image_Detection.py`, `pages/2_Camera_Detection.py`, `streamlit_app.py` để biết chi tiết tham số và cách gọi.

---

Nếu bạn muốn, tôi có thể:
- Chỉnh nội dung README theo phong cách ngắn gọn hoặc chi tiết hơn;
- Tự động chèn ví dụ CLI chính xác sau khi mở các file `main.py`/`pages/*` để lấy tham số thực tế;
- Dịch README sang tiếng Anh.

