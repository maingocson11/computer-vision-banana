import streamlit as st
from ultralytics import YOLO
from database import save_detection_result, get_user_details, db
from detection_labels import apply_vietnamese_banana_label
from banana_ripeness import annotate_banana_ripeness, format_ripeness_summary
from PIL import Image
import io
st.set_page_config(page_title="Nhận Diện AI", page_icon="🍌", layout="wide")
def apply_custom_css():
    """Hàm để nhúng CSS tùy chỉnh vào ứng dụng Streamlit."""
    st.markdown(
        """
    <style>
        /* --- Biến màu sắc và phông chữ toàn cục --- */
            :root {
            --button-color: #FFC0CB;        /* Pink */
            --button-hover: #FFB6C1;
                --primary-color: #4A90E2;      /* Màu xanh dương dịu mắt */
                --secondary-color: #50E3C2;     /* Màu xanh bạc hà cho điểm nhấn */
                --background-color: #E0F7FA;    /* Cyan nhạt/Xanh da trời rất nhạt */
                --surface-color: #FFFFFF;
                --text-main: #000000;           /* Đen tuyền */
                --text-light: #333333;
                --border-color: #B2EBF2;      /* vàng nhạt cho viền */
                --hover-color: #fff3c4;        /* Màu nền khi di chuột qua */
                --success-color: #4CAF50;
                --danger-color: #dc3545;
                --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            }

        /* Override Streamlit theme - chuyển toàn bộ thành light mode */
        /* Áp dụng nền xanh nhạt cho toàn bộ ứng dụng */
        [data-testid="stAppViewContainer"] {
            background-color: var(--background-color) !important;
        }
        
        [data-testid="stMainBlockContainer"] {
            padding: 2rem;
            max-width: 1200px;
        }
        
        /* Đổi tất cả text màu trắng sang đen */
        * {
            color: #000000 !important;
        }
        
        /* Giữ lại màu xanh dương cho primary elements */
        h1, h2, h3, h4, h5, h6, .app-header h1 {
            color: var(--primary-color) !important;
        }
        
        /* Giữ link màu xanh */
        a {
            color: var(--primary-color) !important;
        }

        /* --- Thiết lập chung cho trang --- */
        body {
            font-family: var(--font-family);
            background: linear-gradient(180deg, #ffe6f0 0%, #fff0f5 100%);
            color: #1b1b1b;
        }

        .main { background: linear-gradient(180deg, #ffe6f0 0%, #fff0f5 100%); }

        /* Ẩn header và footer mặc định của Streamlit */
        header[data-testid="stHeader"], footer {
            display: none !important;
        }

        /* Sidebar custom (left vertical menu) */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #b2ebf2 0%, #80deea 100%);
            padding-top: 1rem;
            border-right: 1px solid var(--border-color);
            min-width: 220px;
        }
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
            color: var(--primary-color);
        }
        section[data-testid="stSidebar"] a {
            display: block;
            padding: 10px 12px;
            margin: 6px 8px;
            color: #2b2b2b;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.15s ease-in-out, transform 0.08s;
        }
        section[data-testid="stSidebar"] a:hover {
            background: var(--hover-color);
            transform: translateX(4px);
        }
        section[data-testid="stSidebar"] .sidebar-header {
            display: flex; align-items: center; gap: 10px; padding: 8px 12px; margin-bottom: 6px;
        }

        /* Căn chỉnh layout chính */
        .main .block-container {
            padding: 1rem 2rem;
        }

        /* --- Custom Header --- */
        
        .app-header h1 {
            font-size: 1.8rem;
            color: var(--primary-color);
            margin-bottom: 0.25rem;
        }
        .app-header p {
            margin: 0;
            font-size: 1rem;
            color: #555;
        }

        /* Tùy chỉnh nút bấm */
        .stButton>button {
            width: 200px !important;
            border-radius: 8px;
            background-color: var(--button-color) !important;
            color: var(--text-main) !important; /* Chữ đen trên nền hồng */
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

        /* Custom file uploader styling */
        .custom-upload-zone {
            
            border-radius: 12px;
            padding: 2.5rem;
            text-align: center;
            background: var(--surface-color);
            border: 2px dashed var(--button-color); /* Viền hồng */
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 1.5rem;
        }
        .custom-upload-zone:hover {
            border-color: #357ABD;
            background-color: #FFF0F5; /* Lavender Blush (Hồng cực nhạt) khi hover */
            box-shadow: 0 4px 12px rgba(74, 144, 226, 0.15);
        }
        .upload-icon-custom {
        color: #FF69B4; /* Icon màu hồng đậm hơn để nổi bật */
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        .upload-text-custom {
            font-size: 1.1rem;
            color: #333;
            margin: 0.5rem 0;
            font-weight: 500;
        }
        .upload-subtitle {
            font-size: 0.95rem;
            color: #666;
            margin-top: 0.5rem;
        }
        .file-input-hidden {
            display: none;
        }
        
        .custom-upload-box {
            border: 2px dashed var(--primary-color);
            border-radius: 12px;
            padding: 3rem 2rem;
            text-align: center;
            background: linear-gradient(135deg, #f0f7ff 0%, #fffbf0 100%);
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            max-width: 500px;
        }
        
        .custom-upload-box:hover {
            border-color: #357ABD;
            background: linear-gradient(135deg, #e8f2ff 0%, #fff5e6 100%);
            box-shadow: 0 6px 16px rgba(74, 144, 226, 0.2);
        }
        
        .custom-upload-box.drag-over {
            border-color: #357ABD;
            background: linear-gradient(135deg, #d4e8ff 0%, #fff0cc 100%);
            box-shadow: 0 8px 20px rgba(74, 144, 226, 0.25);
        }
        
        .upload-icon {
            font-size: 3.5rem;
            margin-bottom: 0.8rem;
        }
        
        .upload-title {
            font-size: 1.2rem;
            color: #333;
            margin: 0.5rem 0;
            font-weight: 600;
        }
        
        .upload-subtitle {
            font-size: 0.95rem;
            color: #666;
            margin-top: 0.5rem;
        }
        
        .upload-hint {
            font-size: 0.85rem;
            color: #999;
            margin-top: 1rem;
            font-style: italic;
        }
    </style>""", unsafe_allow_html=True)


# Tải mô hình YOLOv7 (bạn có thể thay đổi bằng tệp .pt của mình nếu có)
# Lần chạy đầu tiên có thể mất một chút thời gian để tải mô hình
@st.cache_resource(show_spinner="Đang tải mô hình nhận diện...")
def load_model():
    model = YOLO("yolov8n.onnx")  # Sử dụng mô hình ONNX
    apply_vietnamese_banana_label(model)
    return model

model = load_model()
BANANA_CLASS_IDS = apply_vietnamese_banana_label(model)

# Áp dụng CSS tùy chỉnh
apply_custom_css()

# Lấy username từ query_params và lưu vào session_state để dùng chung cho các trang
if "username" not in st.session_state:
    try:
        username_from_query = st.query_params.get("username")
        st.session_state.username = username_from_query
    except:
        st.session_state.username = None

if not st.session_state.get("username"):
    # Hiển thị form login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 2rem;">
            <h1 style="color: #4A90E2; font-size: 2.5rem; margin-bottom: 0.5rem;">🍌</h1>
            <h2 style="color: #333; margin-bottom: 2rem;">Hệ Thống Nhận Diện Đối Tượng</h2>
            <p style="font-size: 1rem; color: #666; margin-bottom: 2rem;">Vui lòng nhập tên người dùng để tiếp tục</p>
        </div>
        """, unsafe_allow_html=True)
        
        username_input = st.text_input("👤 Tên người dùng:", placeholder="Nhập username của bạn", key="login_input")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            if st.button("🚀 Tiếp tục", use_container_width=True):
                if username_input.strip():
                    st.session_state.username = username_input.strip()
                    st.rerun()
                else:
                    st.error("❌ Vui lòng nhập tên người dùng!")
    
    st.stop()

# Lấy thông tin avatar
try:
    user_details = get_user_details(st.session_state.username)
    avatar_id = user_details.get("avatar_id") if user_details else None
    avatar_url = f"http://127.0.0.1:8000/avatar/{avatar_id}" if avatar_id else ""
except:
    avatar_id = None
    avatar_url = ""

# --- Fixed left menu (menu cứng) and main header ---
if st.session_state.get('page') == 'camera':
    st.session_state['page'] = None

with st.container():
    left_col, main_col = st.columns([0.22, 0.78])

    # Left fixed menu
    with left_col:
        # Use Streamlit's image loader so the app serves the file correctly
        try:
            c1, c2 = st.columns([0.12, 0.88])
            with c1:
                st.image("images/logo.png", width=100)
            with c2:
                st.markdown("<div style='font-weight:600;color:var(--primary-color);'></div>", unsafe_allow_html=True)
        except Exception:
            # Fallback to simple HTML if file not found or image can't be loaded
            st.markdown(
                """<div class="sidebar-header"><div style="font-weight:600;color:var(--primary-color);"></div></div>""",
                unsafe_allow_html=True,
            )
        st.markdown("---")

        # Main app pages (fixed menu buttons styled like Thống kê)
        if st.button("📷 Phân tích ảnh"):
            st.session_state['page'] = 'image'

        # Placeholder menu items (can be replaced with real targets)
        if st.button("📊 Thống kê"):
            st.session_state['page'] = 'stats'
        
        st.markdown("---")
        st.markdown("<a href='http://127.0.0.1:8000/dashboard'>⬅️ Quay lại Dashboard</a>", unsafe_allow_html=True)

    # Main content (header + rest)
    with main_col:
        st.markdown('<div class="app-header">', unsafe_allow_html=True)

        col1, col2 = st.columns([0.1, 0.9]) # Chia cột cho avatar và tiêu đề
        with col1:
            if avatar_url:
                st.image(avatar_url, width=60)
        with col2:
            st.markdown(
                f"""
                <h1>HỆ THỐNG NHẬN DIỆN ĐỐI TƯỢNG</h1>
                <p>Xin chào, <strong>{st.session_state.username}</strong>! Chọn một chức năng bên trái để bắt đầu.</p>
                """,
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # --- Render selected page (stats/image) if chosen ---
        selected = st.session_state.get('page', None)
        if selected == 'image':
            st.markdown("<h2>📷 Phân tích ảnh</h2>", unsafe_allow_html=True)
            if st.button("⬅️ Quay lại", key="back_image"):
                st.session_state['page'] = None
            
            st.markdown("---")
            
            # Hiển thị Streamlit file uploader với CSS custom (giao diện chỉnh sửa)
            st.markdown("""
                <style>
                    /* Chỉnh sửa giao diện file uploader thành màu xanh biển */
                    .stFileUploader > div {
                        background: linear-gradient(135deg, #00bcd4 0%, #00acc1 100%) !important;
                        border: 2px solid #00897b !important;
                        border-radius: 12px !important;
                        padding: 3rem 2rem !important;
                        text-align: center !important;
                    }
                    
                    .stFileUploader > div:hover {
                        border-color: #006064 !important;
                        background: linear-gradient(135deg, #00acc1 0%, #0097a7 100%) !important;
                        box-shadow: 0 6px 16px rgba(0, 188, 212, 0.3) !important;
                    }
                    
                    .stFileUploader label {
                        color: red !important;
                        font-size: 1.1rem !important;
                        font-weight: 600 !important;
                    }
                    
                    .stFileUploader p {
                        color: red !important;
                    }
                    
                    /* Nút Browse files màu đỏ */
                    .stFileUploader button {
                        background-color: #dc3545 !important;
                        border: 1px solid #dc3545 !important;
                        color: #ffffff !important;
                    }
                    
                    .stFileUploader button:hover {
                        background-color: #c82333 !important;
                        border-color: #c82333 !important;
                    }
                    
                    /* Thêm icon ☁️ */
                    .stFileUploader > div::before {
                        content: '☁️';
                        display: block;
                        font-size: 3.5rem;
                        margin-bottom: 0.8rem;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # File uploader hiển thị với giao diện custom
            uploaded_file = st.file_uploader(
                "Kéo và thả ảnh vào đây hoặc nhấn để chọn tệp",
                type=["jpg", "jpeg", "png", "bmp", "webp"],
                key="simple_uploader"
            )
            
            if uploaded_file is not None:
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown("**Ảnh đã chọn**")
                    st.image(uploaded_file, use_column_width=True)
                
                with col2:
                    st.markdown("**Thông tin tệp**")
                    st.info(f"📄 **Tên tệp:** {uploaded_file.name}\n\n📊 **Kích thước:** {uploaded_file.size / 1024:.2f} KB")
                
                st.markdown("---")
                if st.button("🚀 Bắt đầu nhận diện", use_container_width=True, key="detect_image"):
                    image = Image.open(uploaded_file)
                    with st.spinner("⏳ Đang phân tích ảnh..."):
                        results = model(image, classes=BANANA_CLASS_IDS or None)
                        annotated_image_pil, ripeness_summary = annotate_banana_ripeness(image, results[0])
                        num_bananas = len(results[0].boxes)
                        save_detection_result(st.session_state.username, uploaded_file.name, num_bananas, annotated_image_pil)
                        
                        st.markdown("**Kết quả nhận diện**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Ảnh gốc**")
                            st.image(image, use_column_width=True)
                        with col2:
                            st.markdown("**Ảnh đã xử lý**")
                            st.image(annotated_image_pil, use_column_width=True)
                        
                        st.success(
                            f"✅ Xử lý thành công!\n\n"
                            f"🍌 Tìm thấy **{num_bananas}** quả chuối.\n\n"
                            f"{format_ripeness_summary(ripeness_summary)}\n\n"
                            "Kết quả đã được lưu vào cơ sở dữ liệu."
                        )

        elif selected == 'stats':
            st.markdown("<h2>📊 Thống kê nhận diện</h2>", unsafe_allow_html=True)
            # Back button to return to default view
            if st.button("⬅️ Quay lại"):
                st.session_state['page'] = None

            try:
                try:
                    import pandas as pd
                except Exception:
                    pd = None

                # Total detections
                total = int(db.fs.files.count_documents({}))

                # Unique users
                unique_users = len(db.fs.files.distinct('username'))

                # Average objects per image
                agg_avg = list(db.fs.files.aggregate([
                    {"$match": {"num_objects": {"$exists": True}}},
                    {"$group": {"_id": None, "avgObjects": {"$avg": "$num_objects"}}}
                ]))
                avg_objects = round(agg_avg[0]['avgObjects'], 2) if agg_avg else 0

                # Detections per user (all users)
                user_counts = list(db.fs.files.aggregate([
                    {"$group": {"_id": "$username", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]))

                # Detections over time (by day)
                timeline = list(db.fs.files.aggregate([
                    {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$uploadDate"}}, "count": {"$sum": 1}}},
                    {"$sort": {"_id": 1}}
                ]))

                # Display metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Tổng số lượt phân tích", total)
                m2.metric("Người dùng khác nhau", unique_users)
                m3.metric("Trung bình objects/ảnh", avg_objects)

                # Users detection counts table (per account)
                if user_counts:
                    users_data = [{"username": (t['_id'] if t['_id'] is not None else 'Unknown'), "count": t['count']} for t in user_counts]
                    st.markdown("**Số ảnh đã nhận diện theo tài khoản**")
                    if pd is not None:
                        df_users = pd.DataFrame(users_data)
                        st.dataframe(df_users)
                        try:
                            csv = df_users.to_csv(index=False).encode('utf-8')
                            st.download_button("Tải CSV", data=csv, file_name="user_detection_counts.csv", mime="text/csv")
                        except Exception:
                            pass
                    else:
                        st.table(users_data)

                # Timeline chart
                if timeline:
                    time_data = [{"date": t['_id'], "count": t['count']} for t in timeline]
                    if pd is not None:
                        df_time = pd.DataFrame(time_data)
                        df_time['date'] = pd.to_datetime(df_time['date'])
                        df_time = df_time.set_index('date').sort_index()
                        st.markdown("**Số lượt phân tích theo ngày**")
                        st.line_chart(df_time)
                    else:
                        # Fallback: simple table and bar chart using dict lists
                        st.markdown("**Số lượt phân tích theo ngày**")
                        st.table(time_data)

            except Exception as e:
                st.error(f"Không thể tải dữ liệu thống kê: {e}")

st.markdown("<br>", unsafe_allow_html=True)
