import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import date
import json
import time
from supabase import create_client, Client
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="SmartWallet '25", layout="wide", page_icon="⚡")

# --- 2. KẾT NỐI SUPABASE (GIỮ NGUYÊN) ---
try:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("❌ Chưa cấu hình Supabase Secret! Vào Settings trên Streamlit Cloud để thêm.")
    st.stop()

# --- 3. SIÊU CSS: NEON TEAL + DEEP PURPLE + FROSTED GLASS ---
def load_css():
    st.markdown("""
    <style>
        /* --- TỔNG THỂ --- */
        /* Nền Deep Purple Gradient */
        .stApp {
            background: linear-gradient(145deg, #0f0c29, #302b63, #24243e);
            color: #e0e0ff; /* Màu chữ sáng hơi xanh */
            font-family: 'Inter', sans-serif; /* Gợi ý font hiện đại (nếu máy có) */
        }
        
        /* Ẩn Header mặc định của Streamlit */
        header[data-testid="stHeader"] {
            visibility: hidden;
        }

        /* --- HIỆU ỨNG KÍNH MỜ (GLASSMORPHISM) --- */
        /* Áp dụng cho Sidebar và các Container chính */
        section[data-testid="stSidebar"],
        div[data-testid="stVerticalBlock"] > div.stContainer {
            background: rgba(255, 255, 255, 0.03) !important; /* Nền siêu trong suốt */
            backdrop-filter: blur(12px); /* Hiệu ứng mờ kính */
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08); /* Viền kính mỏng */
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3); /* Đổ bóng sâu */
            border-radius: 16px;
        }
        
        /* Sidebar cụ thể */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(0, 242, 195, 0.1); /* Viền phải hơi xanh */
        }

        /* --- CÁC THẺ SỐ LIỆU (METRIC CARDS) --- */
        div[data-testid="stMetric"] {
            background: rgba(0, 0, 0, 0.2) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 242, 195, 0.3); /* Viền Neon Teal */
            border-radius: 15px;
            padding: 15px;
            box-shadow: 0 0 15px rgba(0, 242, 195, 0.1); /* Glow nhẹ */
            transition: transform 0.3s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px); /* Hiệu ứng nổi khi di chuột */
            box-shadow: 0 0 20px rgba(0, 242, 195, 0.3);
        }
        /* Màu chữ label và giá trị */
        div[data-testid="stMetricLabel"] label { color: #a0a0c0 !important; }
        div[data-testid="stMetricValue"] {
            color: #00f2c3 !important; /* Màu Neon Teal */
            text-shadow: 0 0 10px rgba(0, 242, 195, 0.5); /* Chữ phát sáng */
            font-weight: 800;
        }

        /* --- INPUTS & WIDGETS (STYLE FIGMA DARK MODE) --- */
        /* Các ô nhập liệu, selectbox */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stTextArea textarea {
            background-color: rgba(0, 0, 0, 0.2) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
        }
        /* Khi click vào (Focus) -> Viền Neon Teal phát sáng */
        .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
            border-color: #00f2c3 !important;
            box-shadow: 0 0 10px rgba(0, 242, 195, 0.4) !important;
        }
        /* Checkbox và Radio */
        .stCheckbox span, .stRadio span { color: #e0e0ff !important; }

        /* --- NÚT BẤM (NEON BUTTONS) --- */
        .stButton button {
            border-radius: 12px !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
        }
        /* Nút chính (Primary - Lưu) */
        .stButton button[kind="primary"] {
            background: linear-gradient(90deg, #00f2c3, #00c9a7) !important; /* Gradient Teal */
            color: #0f0c29 !important; /* Chữ màu tối tương phản */
            border: none !important;
            box-shadow: 0 0 15px rgba(0, 242, 195, 0.5); /* Neon Glow */
        }
        .stButton button[kind="primary"]:hover {
            box-shadow: 0 0 25px rgba(0, 242, 195, 0.8);
            transform: scale(1.02);
        }
        /* Nút phụ (Secondary - Xóa, Đăng xuất) */
        .stButton button[kind="secondary"] {
            background: transparent !important;
            border: 2px solid #ff4b4b !important;
            color: #ff4b4b !important;
        }
        .stButton button[kind="secondary"]:hover {
            background: #ff4b4b !important;
            color: white !important;
            box-shadow: 0 0 15px rgba(255, 75, 75, 0.5);
        }

        /* --- TABS (STYLE ARC BROWSER) --- */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 8px;
            border-radius: 20px;
            gap: 5px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 15px;
            border: none !important;
            color: #a0a0c0;
            padding: 8px 16px;
        }
        /* Tab đang chọn */
        .stTabs [aria-selected="true"] {
            background-color: rgba(0, 242, 195, 0.15) !important;
            color: #00f2c3 !important;
            font-weight: bold;
            box-shadow: 0 0 10px rgba(0, 242, 195, 0.2);
        }

        /* --- CÁC THÀNH PHẦN KHÁC --- */
        /* Tiêu đề */
        h1, h2, h3 {
            color: #ffffff !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        h1 span {
            background: linear-gradient(90deg, #00f2c3, #a700f2); /* Gradient chữ tiêu đề */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        /* Đường kẻ phân cách */
        hr { border-color: rgba(0, 242, 195, 0.2) !important; }
        /* Expander (Khung mở rộng) */
        .streamlit-expanderHeader {
            background-color: rgba(255,255,255,0.05) !important;
            color: #00f2c3 !important;
            border-radius: 10px;
        }
        /* Bảng dữ liệu */
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
        }
    </style>
    """, unsafe_allow_html=True)
load_css()

# --- 4. HÀM XỬ LÝ DỮ LIỆU (SUPABASE - GIỮ NGUYÊN) ---
# @st.cache_data(ttl=60)
def load_data():
    """Tải dữ liệu từ Supabase về DataFrame"""
    try:
        response = supabase.table('transactions').select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df['ngay'] = pd.to_datetime(df['ngay']).dt.date
            df['han_tra'] = pd.to_datetime(df['han_tra'], errors='coerce').dt.date
        else:
            df = pd.DataFrame(columns=['id', 'ngay', 'muc', 'so_tien', 'loai', 'phan_loai', 'han_tra', 'trang_thai', 'ghi_chu'])

        cat_res = supabase.table('categories').select("*").execute()
        cats_df = pd.DataFrame(cat_res.data)
        if not cats_df.empty:
            cats = cats_df['ten_danh_muc'].tolist()
        else:
            cats = ["Ăn uống", "Khác"]
        return df, cats
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame(), []

def add_transaction_db(row_dict):
    try:
        supabase.table('transactions').insert(row_dict).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi lưu: {e}")
        return False

def delete_transaction_db(ids_to_delete):
    try:
        for _id in ids_to_delete:
            supabase.table('transactions').delete().eq('id', _id).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi xóa: {e}")
        return False

def add_category_db(cat_name):
    try:
        supabase.table('categories').insert({"ten_danh_muc": cat_name}).execute()
        return True
    except:
        return False

def delete_category_db(cat_name):
    try:
        supabase.table('categories').delete().eq('ten_danh_muc', cat_name).execute()
        return True
    except:
        return False

# --- 5. HỆ THỐNG BẢO MẬT (V4 - CSS GRID PERFECT MOBILE) ---
def login_system():
    # CSS: Sử dụng GRID để căn chỉnh bàn phím hoàn hảo
    st.markdown("""
    <style>
        /* Bao bọc toàn bộ màn hình login để căn giữa */
        .login-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        /* Tiêu đề đẹp hơn */
        .login-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 30px;
            background: linear-gradient(90deg, #00f2c3, #a700f2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
        }

        /* Màn hình hiển thị chấm tròn PIN */
        .pin-screen {
            display: flex;
            justify-content: center;
            gap: 20px; /* Khoảng cách giữa các chấm */
            margin-bottom: 40px;
        }
        .dot {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid rgba(0, 242, 195, 0.5);
            transition: all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1);
        }
        /* Khi đã nhập số */
        .dot.filled {
            background-color: #00f2c3;
            border-color: #00f2c3;
            box-shadow: 0 0 15px rgba(0, 242, 195, 0.8);
            transform: scale(1.1);
        }

        /* --- CSS GRID KEYPAD (CHÌA KHÓA ĐỂ ĐẸP TRÊN MOBILE) --- */
        .keypad-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr); /* 3 cột đều nhau */
            gap: 25px; /* Khoảng cách giữa các nút */
            max-width: 320px; /* Chiều rộng tối đa trên mobile */
            margin: auto;
        }

        /* Style cứng cho nút bấm trong Grid này */
        .keypad-grid button {
            width: 80px !important;  /* Kích thước cố định */
            height: 80px !important; /* Tròn tuyệt đối */
            border-radius: 50% !important;
            
            font-size: 32px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            
            /* Màu sắc Neon Glass */
            background: rgba(255, 255, 255, 0.03) !important;
            border: 2px solid rgba(0, 242, 195, 0.3) !important;
            color: #00f2c3 !important; /* Chữ màu xanh neon */
            
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
            transition: all 0.15s ease !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            padding: 0 !important;
            margin: 0 !important; /* Loại bỏ margin mặc định của streamlit */
        }
        
        /* Hiệu ứng khi chạm vào */
        .keypad-grid button:active {
            background: rgba(0, 242, 195, 0.2) !important;
            border-color: #00f2c3 !important;
            transform: scale(0.95) !important;
            box-shadow: 0 2px 5px rgba(0, 242, 195, 0.4) !important;
        }
        
        /* Nút chức năng (C, Back) màu khác chút */
        .keypad-grid button.func-btn {
            color: rgba(255, 255, 255, 0.7) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
            font-size: 24px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: return True

    if "pin_buffer" not in st.session_state: st.session_state.pin_buffer = ""

    # Bắt đầu Wrapper
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    
    # Tiêu đề mới
    st.markdown('<div class="login-title">🔒 SmartWallet</div>', unsafe_allow_html=True)
    
    # Logic Supabase
    def get_pin_db():
        try:
            res = supabase.table('app_config').select("value").eq("key", "user_pin").execute()
            return res.data[0]['value'] if res.data else None
        except: return None

    def set_pin_db(val):
        supabase.table('app_config').upsert({"key": "user_pin", "value": val}).execute()

    stored_pin = get_pin_db()

    # Màn hình DOTS
    buffer_len = len(st.session_state.pin_buffer)
    dots_html = "".join([f'<div class="dot {"filled" if i < buffer_len else ""}"></div>' for i in range(4)])
    st.markdown(f'<div class="pin-screen">{dots_html}</div>', unsafe_allow_html=True)

    if stored_pin is None:
        st.info("🆕 Tạo mã PIN mới")
    
    # --- BÀN PHÍM SỐ (GRID LAYOUT) ---
    # Mở thẻ div grid
    st.markdown('<div class="keypad-grid">', unsafe_allow_html=True)
    
    # Logic bấm
    def add(d):
        if len(st.session_state.pin_buffer) < 4: st.session_state.pin_buffer += d
    def delete():
        st.session_state.pin_buffer = st.session_state.pin_buffer[:-1]
    def clear():
        st.session_state.pin_buffer = ""

    # Các nút bấm (Streamlit tự động xếp vào lưới 3 cột nhờ CSS)
    # Hàng 1
    st.button("1", on_click=add, args=("1",), key="k1")
    st.button("2", on_click=add, args=("2",), key="k2")
    st.button("3", on_click=add, args=("3",), key="k3")
    # Hàng 2
    st.button("4", on_click=add, args=("4",), key="k4")
    st.button("5", on_click=add, args=("5",), key="k5")
    st.button("6", on_click=add, args=("6",), key="k6")
    # Hàng 3
    st.button("7", on_click=add, args=("7",), key="k7")
    st.button("8", on_click=add, args=("8",), key="k8")
    st.button("9", on_click=add, args=("9",), key="k9")
    
    # Hàng 4 (Chức năng)
    # Dùng mẹo nhỏ: thêm class 'func-btn' vào nút C và Backspace (cần JS hoặc trick, ở đây ta dùng CSS selector dựa trên thứ tự hoặc chấp nhận màu giống nhau)
    # Để đơn giản và chắc chắn hoạt động, ta giữ màu giống nhau nhưng đổi icon
    st.button("C", on_click=clear, key="k_clr") # Clear
    st.button("0", on_click=add, args=("0",), key="k0")
    st.button("⌫", on_click=delete, key="k_del") # Backspace

    st.markdown('</div>', unsafe_allow_html=True) # Đóng div grid
    st.markdown('</div>', unsafe_allow_html=True) # Đóng div wrapper

    # --- TỰ ĐỘNG CHECK ---
    curr = st.session_state.pin_buffer
    if len(curr) == 4:
        if stored_pin is None:
            # Nút lưu pin mới (nằm ngoài grid để to rõ)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 LƯU PIN NÀY", type="primary", use_container_width=True):
                set_pin_db(curr)
                st.success("Đã tạo PIN!")
                time.sleep(1)
                st.session_state.logged_in = True
                st.session_state.pin_buffer = ""
                st.rerun()
        else:
            if curr == stored_pin:
                st.session_state.logged_in = True
                st.session_state.pin_buffer = ""
                st.rerun()
            else:
                st.toast("❌ Sai mã PIN", icon="⚠️")
                time.sleep(0.3)
                st.session_state.pin_buffer = ""
                st.rerun()

    st.stop()

# --- 6. APP CHÍNH (GIAO DIỆN MỚI) ---
import os

def main_app():
    # Sidebar
    with st.sidebar:
        st.title("⚡ SmartWallet '25")
        st.caption("Cyberpunk Finance Manager")
        st.divider()
        if st.button("🔄 TẢI LẠI DỮ LIỆU", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔒 KHÓA ỨNG DỤNG", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Load dữ liệu
    df, categories = load_data()
    st.session_state.categories = categories

   # --- CALLBACKS ---
    def save_callback():
        amt = st.session_state.get("w_amt", 0)
        desc_opt = st.session_state.get("w_opt", "")
        new_desc = st.session_state.get("w_desc", "")
        final_desc = new_desc if desc_opt == "➕ Mục mới..." else desc_opt

        if amt > 0 and final_desc:
            is_debt = st.session_state.get("w_debt", False)
            row_data = {
                "ngay": str(date.today()),
                "muc": final_desc,
                "so_tien": amt,
                "loai": "Thu" if "Thu" in st.session_state.get("w_type", "Chi") else "Chi",
                "phan_loai": st.session_state.get("w_cat", "Khác"),
                "han_tra": str(st.session_state.get("w_date", date.today())) if is_debt else None,
                "trang_thai": "Đang nợ" if is_debt else "Đã xong",
                "ghi_chu": st.session_state.get("w_note", "")
            }
            
            if add_transaction_db(row_data):
                st.toast("Đã lưu lên Cloud!", icon="☁️")
                
                # Reset Form
                st.session_state.w_amt = 0
                if "w_desc" in st.session_state: st.session_state.w_desc = ""
                st.session_state.w_opt = "➕ Mục mới..."
                
                # time.sleep(0.5)  <-- Có thể giữ hoặc bỏ tùy bạn
                # st.rerun()     <-- XÓA DÒNG NÀY ĐI
        else:
            st.toast("Thiếu thông tin!", icon="⚠️")

    # --- UI CHÍNH ---
    st.title("Tổng Quan")

    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "⏳ SỔ NỢ", "⚙️ CÀI ĐẶT"])

    with tab1:
        # Metrics
        if not df.empty:
            inc = df[df['loai']=='Thu']['so_tien'].sum()
            exp = df[df['loai']=='Chi']['so_tien'].sum()
            bal = inc - exp
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng Thu Nhập", f"{inc:,.0f}", delta="Tháng này")
            c2.metric("Tổng Chi Tiêu", f"{exp:,.0f}", delta="Tháng này", delta_color="inverse")
            c3.metric("Số Dư Khả Dụng", f"{bal:,.0f}", delta="Cashflow")
        
        st.divider()
        
        # Layout 2 cột: Nhập liệu & Biểu đồ
        # Sử dụng st.container() để áp dụng hiệu ứng kính mờ cho từng khối
        c_left, c_right = st.columns([1, 1.5], gap="medium")
        
        with c_left:
            with st.container(): # Khối kính mờ bên trái
                st.subheader("📝 Nhập Giao Dịch Mới")
                
                hist = df['muc'].unique().tolist() if not df.empty else []
                if hist: hist.reverse()
                st.selectbox("Nội dung", ["➕ Mục mới..."] + hist, key="w_opt")
                
                if st.session_state.w_opt == "➕ Mục mới...":
                    st.text_input("Tên mục chi tiêu:", key="w_desc", placeholder="VD: Trà sữa full topping...")
                
                st.number_input("Số tiền (VNĐ):", step=50000, key="w_amt")
                
                c1, c2 = st.columns(2)
                with c1: st.radio("Loại:", ["Chi tiền", "Thu tiền"], key="w_type")
                with c2: st.selectbox("Nhóm:", st.session_state.categories, key="w_cat")
                
                st.checkbox("Đánh dấu là Vay/Nợ?", key="w_debt")
                if st.session_state.get("w_debt"): st.date_input("Hạn xử lý:", key="w_date")
                st.text_input("Ghi chú:", key="w_note")
                
                st.button("LƯU LÊN CLOUD 🚀", type="primary", on_click=save_callback, use_container_width=True)

        with c_right:
            with st.container(): # Khối kính mờ bên phải
                st.subheader("📈 Phân Tích Chi Tiêu")
                if not df.empty:
                    exp_df = df[(df['loai']=='Chi') & (df['phan_loai']!='Cho vay')]
                    if not exp_df.empty:
                        chart_data = exp_df.groupby('phan_loai')['so_tien'].sum().reset_index()
                        
                        # Biểu đồ tròn Neon
                        base = alt.Chart(chart_data).encode(theta=alt.Theta("so_tien", stack=True))
                        pie = base.mark_arc(innerRadius=70, outerRadius=110, cornerRadius=8).encode(
                            color=alt.Color("phan_loai", scale=alt.Scale(scheme='turbo'), legend=None), # Dùng màu rực rỡ
                            order=alt.Order("so_tien", sort="descending"),
                            tooltip=["phan_loai", alt.Tooltip("so_tien", format=",.0f")]
                        )
                        text = base.mark_text(radius=130, fill="#00f2c3").encode(
                            text=alt.Text("so_tien", format=",.0f"),
                            order=alt.Order("so_tien", sort="descending")  
                        )
                        st.altair_chart(pie + text, use_container_width=True)
                        
                        # Legend tùy chỉnh bên dưới
                        st.write("Chi tiết nhóm:")
                        st.dataframe(chart_data.sort_values('so_tien', ascending=False).set_index('phan_loai'), use_container_width=True)

                    else:
                        st.info("Chưa có dữ liệu chi tiêu để phân tích.")
                else: st.info("Dữ liệu trống.")
        
        st.divider()
        
        with st.expander("📜 Lịch sử giao dịch gần đây (Nhấn để xem/xóa)"):
             if not df.empty:
                st.dataframe(
                    df[['id','ngay', 'muc', 'so_tien', 'loai', 'phan_loai']].sort_values(by='id', ascending=False).head(10),
                    use_container_width=True, hide_index=True
                )
                del_id = st.selectbox("Chọn ID để xóa vĩnh viễn:", ["--Chọn--"] + df.sort_values(by='id', ascending=False)['id'].astype(str).tolist(), key="del_select")
                if del_id != "--Chọn--" and st.button("Xác nhận xóa", type="secondary"):
                    if delete_transaction_db([int(del_id)]):
                        st.success(f"Đã xóa ID {del_id}!")
                        time.sleep(1)
                        st.rerun()

    with tab2:
        with st.container():
            st.subheader("Quản lý Vay & Nợ")
            if not df.empty:
                debt_df = df[df['trang_thai'] == 'Đang nợ']
                if not debt_df.empty:
                    # Hiển thị dạng thẻ bài (Cards) thay vì bảng
                    for i, row in debt_df.iterrows():
                        bg_color = "rgba(255, 75, 75, 0.1)" if row['loai'] == 'Thu' else "rgba(0, 242, 195, 0.1)"
                        border_color = "#ff4b4b" if row['loai'] == 'Thu' else "#00f2c3"
                        icon = "💸" if row['loai'] == 'Thu' else "💰"
                        title = "MÌNH NỢ HỌ (Phải trả)" if row['loai'] == 'Thu' else "HỌ NỢ MÌNH (Phải thu)"
                        
                        st.markdown(f"""
                        <div style="background: {bg_color}; border-left: 5px solid {border_color}; padding: 15px; border-radius: 12px; margin-bottom: 10px; backdrop-filter: blur(5px);">
                            <h4 style="margin: 0; color: {border_color};">{icon} {title}</h4>
                            <p style="font-size: 1.2em; font-weight: bold; margin: 5px 0;">{row['muc']} - {row['so_tien']:,} đ</p>
                            <p style="margin: 0; opacity: 0.8;">📅 Hạn: {row['han_tra']} | 📝 Note: {row['ghi_chu']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    st.divider()
                    st.write("Cập nhật trạng thái (Chọn dòng và sửa 'trang_thai' thành 'Đã xong'):")
                    edited_debt = st.data_editor(
                        debt_df[['id', 'ngay', 'muc', 'so_tien', 'loai', 'trang_thai']],
                        column_config={
                            "trang_thai": st.column_config.SelectboxColumn(options=["Đang nợ", "Đã xong"], required=True)
                        },
                        use_container_width=True, hide_index=True, key="debt_editor"
                    )
                    # Logic cập nhật trạng thái nợ (Cần viết thêm hàm update DB nếu muốn hoàn thiện phần này)
                    st.caption("Tính năng cập nhật trực tiếp trạng thái nợ trên DB đang được phát triển trong phiên bản tới.")

                else:
                    st.success("Tuyệt vời! Không có khoản nợ nào.")

    with tab3:
         with st.container():
            st.subheader("Cấu hình Danh mục")
            c1, c2 = st.columns(2, gap="large")
            with c1:
                st.write("Thêm danh mục mới:")
                new_c = st.text_input("Tên danh mục:", placeholder="VD: Đầu tư crypto...")
                if st.button("✅ Thêm", use_container_width=True):
                    if add_category_db(new_c): st.rerun()
            with c2:
                st.write("Xóa danh mục hiện có:")
                del_c = st.selectbox("Chọn để xóa:", st.session_state.categories)
                if st.button("🗑 Xóa bỏ", type="secondary", use_container_width=True):
                    if delete_category_db(del_c): st.rerun()
            
            st.divider()
            st.write("Danh sách hiện tại:")
            st.write(st.session_state.categories)

# Chạy App
login_system()
main_app()
