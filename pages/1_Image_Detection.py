import streamlit as st
from ultralytics import YOLO
from PIL import Image
import io
from database import save_detection_result
import streamlit.components.v1 as components

st.set_page_config(page_title="Nhận diện qua ảnh", page_icon="📁", layout="wide")

def apply_custom_css():
    """Hàm để nhúng CSS tùy chỉnh vào ứng dụng Streamlit."""
    st.markdown(
        """
    <style>
        /* --- Biến màu sắc và phông chữ toàn cục --- */
        :root {
            --primary-color: #4A90E2;      /* Màu xanh dương dịu mắt */
            --secondary-color: #50E3C2;    /* Màu xanh bạc hà cho điểm nhấn */
            --background-color: #F5F7FA;   /* Màu nền xám rất nhạt */
            --surface-color: #ffffff;
            --text-color: #212529;
            --border-color: #dee2e6;
            --hover-color: #E8F0FE;        /* Màu nền khi di chuột qua */
            --success-color: #4CAF50;
            --danger-color: #dc3545;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        body {
            font-family: var(--font-family);
            background-color: var(--background-color);
            color: black;
        }
        .main { background-color: var(--background-color); }
        header[data-testid="stHeader"], footer { display: none !important; }
        .main .block-container { padding: 1rem 2rem; }
        .stButton>button {
            border-radius: 8px;
            color: #fff;
            background-color: var(--primary-color);
            border: 1px solid var(--primary-color);
            transition: all 0.2s ease-in-out;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stButton>button:hover {
            background-color: #357ABD;
            border-color: #357ABD;
            transform: scale(1.02);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* --- CSS cho giao diện tải tệp tùy chỉnh (Phương pháp JavaScript) --- */
        /* 1. Giao diện tùy chỉnh cho khu vực tải tệp */
        .custom-file-uploader {
            border: 2px dashed var(--primary-color);
            border-radius: 15px;
            background-color: #F8FBFF;
            transition: background-color 0.3s, border-color 0.3s;
            margin-bottom: 1rem;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
        }
        .custom-file-uploader:hover {
            background-color: var(--hover-color);
            border-color: #357ABD;
        }
        .upload-icon { 
            font-size: 3rem; 
            color: var(--primary-color); 
        }
        .upload-text { 
            font-size: 1.1rem; 
            color: #555; 
            margin-top: 0.5rem; 
        }
        .upload-text span { 
            color: var(--primary-color); 
            font-weight: bold; 
        }

        /* 2. Ẩn hoàn toàn tiện ích file_uploader gốc của Streamlit */
        div[data-testid="stFileUploader"] {
            display: none;
        }

        /* 3. (Tùy chọn) Ẩn thông báo "No file selected" nếu cần */
        div[data-testid="stFileUploader"] > div:first-child {
            display: none;
        }

        /* 4. (Tùy chọn) Ẩn khu vực hiển thị tên tệp đã tải lên (vì chúng ta sẽ tự hiển thị ảnh) */
        div[data-testid="stFileUploadDropzone"] + div {
            display: none;
        }
    </style>""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Đang tải mô hình nhận diện...")
def load_model():
    model = YOLO("yolov8n.onnx")
    return model

def process_and_save_image(image_bytes, source_filename, username, model):
    image = Image.open(image_bytes)
    st.image(image, caption=f"Ảnh gốc: {source_filename}", use_column_width=True)
    with st.spinner("Đang xử lý..."):
        results = model(image)
        annotated_image = results[0].plot()
        annotated_image_pil = Image.fromarray(annotated_image[..., ::-1])
        num_objects = len(results[0].boxes)
        save_detection_result(username, source_filename, num_objects, annotated_image_pil)
        st.image(annotated_image_pil, caption="Ảnh đã nhận diện", use_column_width=True)
        st.success(f"Xử lý thành công! Tìm thấy **{num_objects}** đối tượng. Kết quả đã được lưu.")

# --- Main Logic ---
apply_custom_css()
model = load_model()

# Lấy username từ session_state
username = st.session_state.get("username")
if not username:
    st.warning("Không tìm thấy thông tin người dùng. Lịch sử sẽ không được lưu. Vui lòng truy cập từ trang Dashboard.")
    st.stop()

st.markdown("<h1>📁 Nhận diện đối tượng qua ảnh</h1>", unsafe_allow_html=True)
st.info("Tải lên một hình ảnh để hệ thống phân tích và nhận diện các đối tượng có trong đó.")

# --- Giao diện tải tệp tùy chỉnh (Phương pháp JavaScript) ---

# 1. Hiển thị giao diện tùy chỉnh bằng st.markdown
st.markdown("""
    <div id="custom-uploader" class="custom-file-uploader">
        <div class="upload-icon">☁️</div>
        <p class="upload-text">
            Kéo và thả tệp vào đây hoặc <span style="color: var(--primary-color); font-weight: bold;">nhấn để chọn tệp</span>
        </p>
    </div>
""", unsafe_allow_html=True)

# 2. Đặt tiện ích file_uploader (sẽ bị ẩn bởi CSS)
uploaded_file = st.file_uploader("Chọn ảnh", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

# 3. Sử dụng JavaScript để liên kết giao diện tùy chỉnh với nút tải tệp bị ẩn
components.html(
    """
<script>
    const customUploader = window.parent.document.getElementById('custom-uploader');
    const streamlitUploader = window.parent.document.querySelector('div[data-testid="stFileUploader"] button');

    if (customUploader && streamlitUploader) {
        customUploader.onclick = function () {
            streamlitUploader.click();
        }
    }
</script>
""", height=0, width=0)

if uploaded_file is not None:
    # Hiển thị ảnh đã tải lên ngay lập tức
    st.image(uploaded_file, caption="Ảnh đã chọn", width=300)
    if st.button("Bắt đầu nhận diện", use_container_width=True):
        process_and_save_image(io.BytesIO(uploaded_file.getvalue()), uploaded_file.name, username, model)
