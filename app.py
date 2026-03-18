import streamlit as st
import cv2
import time
import os
import sys
from datetime import datetime

# Add project root to path ensuring utils can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.detector import FireDetector
from utils.notifier import AlertSystem
from utils.preprocessing import preprocess_frame
from utils.camera import VideoSource

# ================== CẤU HÌNH ==================
PAGE_TITLE = "🔥 Trần Hiệp - Hệ Thống Cảnh Báo Cháy Thông Minh"
MODEL_PATH = "C:/canhbaochay/bestt.pt" # Đường dẫn mô hình
TELEGRAM_TOKEN = "8209113378:AAHphjx26rUqTFyICfQjCiXE-4vRuihYTH8"
TELEGRAM_CHAT_ID = "5878253794"

st.set_page_config(page_title="FireSentinel AI", page_icon="🔥", layout="wide")

# ================== CSS TÙY CHỈNH (DARK MODE) ==================
st.markdown("""
<style>
    /* Nền chính - Dark Mode */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    /* Tiêu đề */
    h1 {
        color: #FF5252; 
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 800;
        text-shadow: 0 0 10px rgba(255, 82, 82, 0.5);
    }
    /* Các Containers */
    .block-container {
        padding-top: 2rem;
    }
    /* Thẻ Metrics/Stats */
    div[data-testid="stMetricValue"] {
        color: #FF5252;
    }
    /* Hình ảnh Camera */
    div[data-testid="stImage"] > img {
        border: 3px solid #FF5252;
        border-radius: 12px;
        box-shadow: 0 0 20px rgba(255, 82, 82, 0.3);
    }
    /* Nút bấm */
    .stButton > button {
        background: linear-gradient(90deg, #D32F2F, #B71C1C);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 10px rgba(255, 82, 82, 0.6);
        color: #FFFFFF;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #262730;
        border-right: 1px solid #41444C;
    }
    /* Alert Box */
    .stAlert {
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #FF5252;
        border-radius: 8px;
    }
    /* Log Text Area */
    .stTextArea textarea {
        background-color: #1E1E1E;
        color: #00FF00; /* Green console text */
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# ================== KHỞI TẠO HỆ THỐNG ==================
@st.cache_resource
def load_system():
    # Load model o ngoai de tranh lag
    detector = FireDetector(MODEL_PATH, conf_threshold=0.6, persistence_frames=5)
    notifier = AlertSystem(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    return detector, notifier

try:
    detector, notifier = load_system()
except Exception as e:
    st.error(f"Lỗi khởi tạo hệ thống: {e}")
    st.image("https://media.tenor.com/eDchk3srtycAAAAC/pato.gif", caption="Lỗi hệ thống")
    st.stop()

# ================== GIAO DIỆN CHÍNH ==================
st.title(PAGE_TITLE)

# Layout chia cột: Cột chính (Camera + Status) và Sidebar (Settings + History)
# Sidebar Control
with st.sidebar:
    st.header("⚙️ Bảng Điều Khiển")
    
    # Camera Settings
    st.subheader("📸 Cấu hình Camera")
    cam_index = st.selectbox("Chọn nguồn Camera:", [0, 1, 2], index=0, help="Thử đổi số nếu camera không lên.")
    
    run_app = st.toggle("KÍCH HOẠT HỆ THỐNG", value=True)
    st.divider()
    
    # Detection Settings
    confidence = st.slider("Độ nhạy (Confidence)", 0.0, 1.0, 0.5, 0.05)
    detector.conf_threshold = confidence
    
    st.divider()
    test_alert = st.button("🔔 Test Cảnh báo Âm thanh")
    if test_alert:
        notifier.play_sound()

# --- STATUS PANEL & LIVE VIEW ---
# Tạo container cho trạng thái
status_container = st.container()
with status_container:
    # Placeholder cho trạng thái, mặc định là BÌNH THƯỜNG
    status_indicator = st.empty()

# Camera Placeholder
camera_placeholder = st.empty()

# --- HISTORY SECTION ---
st.divider()
st.subheader("📜 Nhật Ký Phát Hiện")
# Tạo 2 cột cho lịch sử: Ảnh gần nhất và List log
hist_col1, hist_col2 = st.columns([1, 2])

with hist_col1:
    st.markdown("**📸 Ảnh Phát Hiện Gần Nhất**")
    alert_img_placeholder = st.empty()

with hist_col2:
    st.markdown("**⏱️ Lịch Sử Sự Kiện**")
    log_list_placeholder = st.empty()

# Nút xóa lịch sử nằm dưới cùng hoặc góc
if st.button("🗑️ Xóa Toàn Bộ Lịch Sử", type="primary"):
    # Xóa dữ liệu trong DB
    if notifier.db.clear_events():
        pass
        
    # Xóa ảnh trong thư mục alerts
    if os.path.exists(notifier.alert_dir):
        for filename in os.listdir(notifier.alert_dir):
            file_path = os.path.join(notifier.alert_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    
    st.toast("Đã xóa toàn bộ lịch sử!", icon="✅")
    time.sleep(1)
    st.rerun()

# Hàm cập nhật giao diện trạng thái
def update_status_display(is_warning, message=""):
    if is_warning:
        status_indicator.markdown(f"""
            <div style='padding: 20px; border-radius: 10px; background-color: #260505; border: 2px solid #FF5252; text-align: center; margin-bottom: 20px;'>
                <h2 style='color: #FF5252; margin:0;'>⚠️ CẢNH BÁO: PHÁT HIỆN CHÁY!</h2>
                <p style='color: #FAFAFA; margin:0;'>{message}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        status_indicator.markdown(f"""
            <div style='padding: 20px; border-radius: 10px; background-color: #05260e; border: 2px solid #00E676; text-align: center; margin-bottom: 20px;'>
                <h2 style='color: #00E676; margin:0;'>✅ TRẠNG THÁI: BÌNH THƯỜNG</h2>
                <p style='color: #FAFAFA; margin:0;'>Hệ thống đang giám sát an toàn</p>
            </div>
        """, unsafe_allow_html=True)

# ================== LOGIC VÒNG LẶP CHÍNH ==================
if run_app:
    # Mở Camera
    try:
        cap = VideoSource(cam_index) # Sử dụng index từ sidebar
    except Exception as e:
        status_indicator.error(f"Không thể kết nối Camera {cam_index}: {e}")
        cap = None

    last_alert_time = 0
    last_log_update = 0
    COOLDOWN = 10 # Giây giữa các lần cảnh báo
    # Init trạng thái ban đầu
    update_status_display(False)
    
    if cap and cap.is_opened():
        while cap.is_opened() and run_app:
            ret, frame = cap.get_frame()
            if not ret:
                st.toast(f"Mất tín hiệu Camera {cam_index}", icon="⚠️")
                time.sleep(1)
                continue
                
            # 1. Tiền xử lý
            processed_frame = preprocess_frame(frame)
            if processed_frame is None:
                continue
            
            # 2. Phát hiện
            annotated_frame, is_fire, results = detector.detect(processed_frame)
            
            # 3. Xử lý cảnh báo & Trạng thái
            if is_fire:
                current_time_epoch = time.time()
                current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Lấy độ tin cậy cao nhất
                max_conf = 0.0
                if results and results.boxes and len(results.boxes.conf) > 0:
                     max_conf = float(results.boxes.conf.max())
                
                # Format tin nhắn theo yêu cầu
                # ⚠️⚠️ CHÁY! ⚠️⚠️
                # Giờ: YYYY-MM-DD HH:MM:SS
                # Tin cậy: 0.82
                msg = f"⚠️⚠️ CHÁY! ⚠️⚠️\nGiờ: {current_time_str}\nTin cậy: {max_conf:.2f}"
                
                # Cập nhật trạng thái CẢNH BÁO
                # Hiển thị trên UI (có thể cần replace \n bằng <br> cho HTML nếu cần, nhưng st.error/markdown thường hiểu)
                # Tuy nhiên function update_status_display đang nhét vào thẻ <p>, nên \n có thể không xuống dòng đẹp.
                # Ta sẽ xử lý msg hiển thị riêng một chút nếu cần, hoặc để notifier gửi đi nguyên bản.
                
                # Cho UI, ta replace \n thành <br> để hiển thị đẹp
                ui_msg = msg.replace("\n", "<br>")
                update_status_display(True, ui_msg)
                
                if current_time_epoch - last_alert_time > COOLDOWN:
                    # Gọi notifier
                    img_path = notifier.trigger_alert(annotated_frame, msg, confidence=max_conf)
                    
                    # Cập nhật ảnh ngay lập tức
                    alert_img_placeholder.image(img_path, caption=f"Phát hiện lúc {datetime.now().strftime('%H:%M:%S')}", use_container_width=True)
                    last_alert_time = current_time_epoch
            else:
                # Cập nhật trạng thái BÌNH THƯỜNG (nếu không có cháy)
                # Để tránh nhấp nháy, ta có thể giữ trạng thái cảnh báo một chút hoặc reset ngay
                # Ở đây reset ngay cho realtime
                update_status_display(False)

            # 4. Hiển thị Camera
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            camera_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
            
            # 5. Cập nhật Log (đọc từ DB định kỳ)
            current_time = time.time()
            if current_time - last_log_update > 2.0:
                try:
                    events = notifier.db.get_recent_events(limit=10)
                    if events:
                        # Tạo bảng markdown
                        md_text = "| Thời Gian | Độ tin cậy | Tin nhắn |\n|---|---|---|\n"
                        for e in events:
                            # Format conf
                            conf_val = f"{e['confidence']:.2f}" if e['confidence'] else "N/A"
                            md_text += f"| {e['timestamp']} | {conf_val} | {e['message'].splitlines()[0]} |\n"
                        
                        log_list_placeholder.markdown(md_text)
                    else:
                        log_list_placeholder.info("Chưa có dữ liệu lịch sử.")
                        
                except Exception as e:
                    print(f"Log read error: {e}")
                last_log_update = current_time
                    
            # Nghỉ rất ngắn
            time.sleep(0.001)
            
        cap.release()
    else:
        st.error("Không tìm thấy Camera. Vui lòng kiểm tra kết nối.")
else:
    status_indicator.info("Hệ thống đang tắt.")
    camera_placeholder.empty()

