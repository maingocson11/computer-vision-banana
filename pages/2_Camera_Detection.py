import streamlit as st
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

st.set_page_config(page_title="Nhận diện qua Camera", page_icon="📸", layout="wide")

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
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--background-color);
            color: black;
        }
        .main { background-color: var(--background-color); }
        header[data-testid="stHeader"], footer { display: none !important; }
        .main .block-container { padding: 1rem 2rem; }
    </style>""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Đang tải mô hình nhận diện...")
def load_model():
    model = YOLO("yolov8n.onnx")
    return model

class YOLOVideoTransformer(VideoTransformerBase):
    def __init__(self, model):
        self.model = model

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.model(img)
        annotated_image = results[0].plot()
        return annotated_image

# --- Main Logic ---
apply_custom_css()
model = load_model()

# Lấy username từ session state thay vì query params
username = st.session_state.get("username")
if not username:
    st.warning("Không tìm thấy thông tin người dùng. Vui lòng truy cập từ trang Dashboard.")
    st.stop()

st.markdown("<h1>📸 Nhận diện đối tượng qua Camera</h1>", unsafe_allow_html=True)
st.info("Bật camera của bạn và hệ thống sẽ bắt đầu nhận diện trong thời gian thực. Lưu ý: chức năng này không lưu lại lịch sử.")

webrtc_streamer(
    key="camera-detection",
    video_transformer_factory=lambda: YOLOVideoTransformer(model),
    media_stream_constraints={"video": True, "audio": False},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)
