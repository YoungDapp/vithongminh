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
st.set_page_config(page_title="SmartWallet", layout="wide", page_icon="⚡")

# --- 2. KẾT NỐI SUPABASE ---
try:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("❌ Chưa cấu hình Supabase Secret! Vào Settings trên Streamlit Cloud để thêm.")
    st.stop()

# --- 3. CSS GLOBAL (CHO CẢ APP) ---
def load_css():
    st.markdown("""
    <style>
        /* Nền chung */
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #fff;
        }
        /* Ẩn Header */
        header {visibility: hidden;}
        /* Ẩn Padding thừa để giao diện sát viền hơn trên mobile */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
        }
        /* Style Metric */
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 242, 195, 0.2);
            border-radius: 10px;
            padding: 10px;
        }
        div[data-testid="stMetricLabel"] label { color: #aaa !important; }
        div[data-testid="stMetricValue"] { color: #00f2c3 !important; }
    </style>
    """, unsafe_allow_html=True)
load_css()

# --- 4. HÀM XỬ LÝ DỮ LIỆU (SUPABASE) ---
# @st.cache_data(ttl=60)
def load_data():
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
    except: return False

def delete_category_db(cat_name):
    try:
        supabase.table('categories').delete().eq('ten_danh_muc', cat_name).execute()
        return True
    except: return False

# --- 5. HỆ THỐNG BẢO MẬT (FINAL MOBILE FIX) ---
def login_system():
    # CSS: FIX CỨNG CHO MOBILE
    st.markdown("""
    <style>
        /* 1. Ép các cột KHÔNG ĐƯỢC xuống dòng trên mobile */
        div[data-testid="column"] {
            width: 33.33% !important;
            flex: 1 1 33.33% !important;
            min-width: 0px !important;
        }
        
        /* 2. Style nút bấm: TARGET SÂU ĐỂ GHI ĐÈ MÀU ĐỎ */
        div.stButton > button {
            width: 100% !important;
            aspect-ratio: 1 / 1 !important;
            border-radius: 50% !important;
            margin: 0 !important;
            padding: 0 !important;
            
            /* Màu nền và viền Neon */
            background: rgba(255, 255, 255, 0.05) !important;
            border: 2px solid #00f2c3 !important; 
            box-shadow: 0 0 10px rgba(0, 242, 195, 0.1) !important;
        }

        /* 3. Style CHỮ bên trong nút (Quan trọng để xóa màu đỏ của text) */
        div.stButton > button p {
            font-size: 24px !important;
            font-weight: 700 !important;
            color: #00f2c3 !important; /* Ép chữ màu xanh */
        }

        /* Hiệu ứng bấm */
        div.stButton > button:active {
            background-color: #00f2c3 !important;
            transform: scale(0.95);
        }
        div.stButton > button:active p {
            color: #000 !important; /* Chữ chuyển đen khi bấm */
        }

        /* Wrapper căn giữa */
        .keypad-wrapper {
            max-width: 350px;
            margin: 0 auto;
            padding: 10px;
        }
        
        /* Chấm tròn PIN */
        .pin-display-area {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
            margin-top: 10px;
        }
        .pin-dot {
            width: 16px; height: 16px;
            border-radius: 50%;
            border: 2px solid #555;
            transition: 0.2s;
        }
        .pin-dot.active {
            background-color: #00f2c3;
            border-color: #00f2c3;
            box-shadow: 0 0 10px #00f2c3;
        }
    </style>
    """, unsafe_allow_html=True)

    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: return True

    if "pin_buffer" not in st.session_state: st.session_state.pin_buffer = ""

    # GIAO DIỆN LOGIN
    st.markdown('<div class="keypad-wrapper">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #fff; margin-bottom: 0;'>🔒 SmartWallet</h1>", unsafe_allow_html=True)
    
    # Hiển thị chấm tròn
    dots_html = '<div class="pin-display-area">'
    for i in range(4):
        state = "active" if i < len(st.session_state.pin_buffer) else ""
        dots_html += f'<div class="pin-dot {state}"></div>'
    dots_html += '</div>'
    st.markdown(dots_html, unsafe_allow_html=True)

    # Logic Database
    def get_pin_db():
        try:
            res = supabase.table('app_config').select("value").eq("key", "user_pin").execute()
            return res.data[0]['value'] if res.data else None
        except: return None

    def set_pin_db(val):
        supabase.table('app_config').upsert({"key": "user_pin", "value": val}).execute()

    stored_pin = get_pin_db()

    if stored_pin is None:
        st.info("🆕 Tạo PIN mới")

    # BÀN PHÍM SỐ
    def press(val):
        if len(st.session_state.pin_buffer) < 4:
            st.session_state.pin_buffer += val
    def clear(): st.session_state.pin_buffer = ""
    def back(): st.session_state.pin_buffer = st.session_state.pin_buffer[:-1]

    # GRID 3 CỘT (Đã fix CSS)
    c1, c2, c3 = st.columns(3)
    with c1: st.button("1", on_click=press, args=("1",), key="k1", use_container_width=True)
    with c2: st.button("2", on_click=press, args=("2",), key="k2", use_container_width=True)
    with c3: st.button("3", on_click=press, args=("3",), key="k3", use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.button("4", on_click=press, args=("4",), key="k4", use_container_width=True)
    with c2: st.button("5", on_click=press, args=("5",), key="k5", use_container_width=True)
    with c3: st.button("6", on_click=press, args=("6",), key="k6", use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.button("7", on_click=press, args=("7",), key="k7", use_container_width=True)
    with c2: st.button("8", on_click=press, args=("8",), key="k8", use_container_width=True)
    with c3: st.button("9", on_click=press, args=("9",), key="k9", use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.button("C", on_click=clear, key="k_clr", use_container_width=True)
    with c2: st.button("0", on_click=press, args=("0",), key="k0", use_container_width=True)
    with c3: st.button("⌫", on_click=back, key="k_del", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True) # Đóng wrapper

    # CHECK PIN
    curr = st.session_state.pin_buffer
    if len(curr) == 4:
        if stored_pin is None:
            if st.button("💾 LƯU PIN", type="primary", use_container_width=True):
                set_pin_db(curr)
                st.success("OK!")
                time.sleep(1)
                st.session_state.logged_in = True
                st.rerun()
        else:
            if curr == stored_pin:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.toast("Sai PIN!", icon="⚠️")
                time.sleep(0.3)
                st.session_state.pin_buffer = ""
                st.rerun()
    
    st.stop()

# --- 6. APP CHÍNH ---
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

    # Callback lưu
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
                st.session_state.w_amt = 0
                if "w_desc" in st.session_state: st.session_state.w_desc = ""
                st.session_state.w_opt = "➕ Mục mới..."
        else:
            st.toast("Thiếu thông tin!", icon="⚠️")

    # UI CHÍNH
    st.title("Tổng Quan")
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "⏳ SỔ NỢ", "⚙️ CÀI ĐẶT"])

    with tab1:
        if not df.empty:
            inc = df[df['loai']=='Thu']['so_tien'].sum()
            exp = df[df['loai']=='Chi']['so_tien'].sum()
            bal = inc - exp
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng Thu", f"{inc:,.0f}", delta="Tháng này")
            c2.metric("Tổng Chi", f"{exp:,.0f}", delta="Tháng này", delta_color="inverse")
            c3.metric("Số Dư", f"{bal:,.0f}", delta="Cashflow")
        
        st.divider()
        
        c_left, c_right = st.columns([1, 1.5], gap="medium")
        with c_left:
            with st.container():
                st.subheader("📝 Nhập Giao Dịch")
                hist = df['muc'].unique().tolist() if not df.empty else []
                if hist: hist.reverse()
                st.selectbox("Nội dung", ["➕ Mục mới..."] + hist, key="w_opt")
                
                if st.session_state.w_opt == "➕ Mục mới...":
                    st.text_input("Tên mục:", key="w_desc", placeholder="VD: Trà sữa...")
                
                st.number_input("Số tiền:", step=50000, key="w_amt")
                c1, c2 = st.columns(2)
                with c1: st.radio("Loại:", ["Chi", "Thu"], key="w_type")
                with c2: st.selectbox("Nhóm:", st.session_state.categories, key="w_cat")
                
                st.checkbox("Vay/Nợ?", key="w_debt")
                if st.session_state.get("w_debt"): st.date_input("Hạn:", key="w_date")
                st.text_input("Note:", key="w_note")
                
                st.button("LƯU CLOUD 🚀", type="primary", on_click=save_callback, use_container_width=True)

        with c_right:
            with st.container():
                st.subheader("📈 Biểu đồ")
                if not df.empty:
                    exp_df = df[(df['loai']=='Chi') & (df['phan_loai']!='Cho vay')]
                    if not exp_df.empty:
                        chart_data = exp_df.groupby('phan_loai')['so_tien'].sum().reset_index()
                        base = alt.Chart(chart_data).encode(theta=alt.Theta("so_tien", stack=True))
                        pie = base.mark_arc(innerRadius=70, outerRadius=110, cornerRadius=8).encode(
                            color=alt.Color("phan_loai", scale=alt.Scale(scheme='turbo'), legend=None),
                            order=alt.Order("so_tien", sort="descending"),
                            tooltip=["phan_loai", alt.Tooltip("so_tien", format=",.0f")]
                        )
                        text = base.mark_text(radius=130, fill="#00f2c3").encode(
                            text=alt.Text("so_tien", format=",.0f"),
                            order=alt.Order("so_tien", sort="descending")  
                        )
                        st.altair_chart(pie + text, use_container_width=True)
                        st.dataframe(chart_data.sort_values('so_tien', ascending=False).set_index('phan_loai'), use_container_width=True)
                    else: st.info("Chưa có dữ liệu chi tiêu.")
                else: st.info("Dữ liệu trống.")
        
        st.divider()
        with st.expander("📜 Lịch sử (Xem/Xóa)"):
             if not df.empty:
                st.dataframe(df[['id','ngay', 'muc', 'so_tien', 'loai']].sort_values(by='id', ascending=False).head(10), use_container_width=True, hide_index=True)
                del_id = st.selectbox("Chọn ID xóa:", ["--Chọn--"] + df.sort_values(by='id', ascending=False)['id'].astype(str).tolist(), key="del_select")
                if del_id != "--Chọn--" and st.button("Xóa ngay", type="secondary"):
                    if delete_transaction_db([int(del_id)]):
                        st.success("Đã xóa!")
                        time.sleep(1)
                        st.rerun()

    with tab2:
        with st.container():
            st.subheader("Sổ Nợ")
            if not df.empty:
                debt_df = df[df['trang_thai'] == 'Đang nợ']
                if not debt_df.empty:
                    for i, row in debt_df.iterrows():
                        color = "#ff4b4b" if row['loai'] == 'Thu' else "#00f2c3"
                        st.markdown(f"<div style='border-left: 4px solid {color}; padding: 10px; background: rgba(255,255,255,0.05); margin-bottom: 5px;'>"
                                    f"<b>{row['muc']}</b> - {row['so_tien']:,} đ<br><small>Hạn: {row['han_tra']}</small></div>", unsafe_allow_html=True)
                    
                    st.divider()
                    st.caption("Để xóa nợ: Vào tab Dashboard, tìm ID và xóa giao dịch.")
                else: st.success("Sạch nợ!")

    with tab3:
        with st.container():
            st.subheader("Cấu hình")
            c1, c2 = st.columns(2)
            with c1:
                new_c = st.text_input("Thêm mục:")
                if st.button("Thêm"): 
                    add_category_db(new_c); st.rerun()
            with c2:
                del_c = st.selectbox("Xóa mục:", st.session_state.categories)
                if st.button("Xóa"): 
                    delete_category_db(del_c); st.rerun()

# Chạy App
login_system()
main_app()
