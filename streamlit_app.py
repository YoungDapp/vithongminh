import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import date
import time
from supabase import create_client, Client

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="SmartWallet", layout="wide", page_icon="⚡")

# Kết nối Supabase
try:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("❌ Thiếu cấu hình Supabase!")
    st.stop()

# --- 2. CSS CYBERPUNK (ĐÃ FIX LỖI NÚT KHỔNG LỒ) ---
def load_css():
    st.markdown("""
    <style>
        /* Nền Deep Purple Gradient */
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #e0e0ff;
            font-family: 'Inter', sans-serif;
        }
        
        /* Ẩn Header & Padding */
        header {visibility: hidden;}
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 5rem !important;
        }

        /* Container Kính Mờ (Glassmorphism) */
        div[data-testid="stVerticalBlock"] > div.stContainer, 
        section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        }

        /* Style cho Metric (Thẻ số liệu) */
        div[data-testid="stMetric"] {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 242, 195, 0.3);
            border-radius: 12px;
            padding: 10px;
        }
        div[data-testid="stMetricLabel"] label { color: #aaa !important; }
        div[data-testid="stMetricValue"] { color: #00f2c3 !important; text-shadow: 0 0 10px rgba(0, 242, 195, 0.4); }

        /* --- STYLE NÚT BẤM (FIXED: KHÔNG ÉP HÌNH TRÒN) --- */
        div.stButton > button {
            width: 100%;
            border-radius: 12px; /* Bo góc vừa phải */
            font-weight: 700;
            border: 1px solid #00f2c3; /* Viền Neon */
            background: rgba(255, 255, 255, 0.05);
            color: #00f2c3;
            transition: all 0.2s;
            height: auto !important; /* Để nút tự co giãn chiều cao */
            padding: 0.5rem 1rem;
        }
        
        /* Hiệu ứng Hover/Active */
        div.stButton > button:hover {
            background: rgba(0, 242, 195, 0.1);
            box-shadow: 0 0 15px rgba(0, 242, 195, 0.3);
        }
        div.stButton > button:active {
            background: #00f2c3;
            color: #000;
        }

        /* --- INPUTS --- */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            background-color: rgba(0, 0, 0, 0.3) !important;
            color: #fff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
        }
        
        /* Chấm tròn PIN */
        .pin-area {
            display: flex; justify-content: center; gap: 15px; margin-bottom: 20px;
        }
        .dot {
            width: 15px; height: 15px; border-radius: 50%; border: 2px solid #555; transition: 0.2s;
        }
        .dot.active {
            background: #00f2c3; border-color: #00f2c3; box-shadow: 0 0 10px #00f2c3;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 5px; background: rgba(255,255,255,0.05); padding: 5px; border-radius: 10px; }
        .stTabs [aria-selected="true"] { background: rgba(0,242,195,0.2) !important; color: #00f2c3 !important; }
    </style>
    """, unsafe_allow_html=True)
load_css()

# --- 3. DATABASE ---
# @st.cache_data(ttl=60)
def load_data():
    try:
        t = supabase.table('transactions').select("*").execute()
        df = pd.DataFrame(t.data)
        if not df.empty:
            df['ngay'] = pd.to_datetime(df['ngay']).dt.date
            df['han_tra'] = pd.to_datetime(df['han_tra'], errors='coerce').dt.date
        else:
            df = pd.DataFrame(columns=['id', 'ngay', 'muc', 'so_tien', 'loai', 'phan_loai', 'han_tra', 'trang_thai', 'ghi_chu'])
        
        c = supabase.table('categories').select("*").execute()
        cats = [x['ten_danh_muc'] for x in c.data] if c.data else ["Ăn uống", "Khác"]
        return df, cats
    except: return pd.DataFrame(), []

def add_trans(row): supabase.table('transactions').insert(row).execute()
def del_trans(tid): supabase.table('transactions').delete().eq('id', tid).execute()
def add_cat(n): supabase.table('categories').insert({"ten_danh_muc": n}).execute()
def del_cat(n): supabase.table('categories').delete().eq('ten_danh_muc', n).execute()

# --- 4. HỆ THỐNG ĐĂNG NHẬP (Bàn phím 3 cột chuẩn Mobile) ---
def login_system():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: return True
    if "pin_buffer" not in st.session_state: st.session_state.pin_buffer = ""

    # CSS Riêng cho Login để căn giữa
    st.markdown("""
    <style>
        .login-box { max-width: 350px; margin: 0 auto; }
        [data-testid="column"] { min-width: 0 !important; } /* Fix mobile columns */
    </style>
    """, unsafe_allow_html=True)

    def get_pin():
        try:
            r = supabase.table('app_config').select("value").eq("key", "user_pin").execute()
            return r.data[0]['value'] if r.data else None
        except: return None
    
    def set_pin(v): supabase.table('app_config').upsert({"key": "user_pin", "value": v}).execute()

    stored = get_pin()

    # Layout căn giữa
    _, col_mid, _ = st.columns([1, 10, 1])
    with col_mid:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>🔒 SmartWallet</h1>", unsafe_allow_html=True)
        
        # Chấm tròn
        dots = '<div class="pin-area">'
        for i in range(4):
            state = "active" if i < len(st.session_state.pin_buffer) else ""
            dots += f'<div class="dot {state}"></div>'
        dots += '</div>'
        st.markdown(dots, unsafe_allow_html=True)

        if stored is None: st.info("🆕 Tạo PIN mới")

        # Keypad Logic
        def press(v): 
            if len(st.session_state.pin_buffer) < 4: st.session_state.pin_buffer += v
        def clr(): st.session_state.pin_buffer = ""
        def bck(): st.session_state.pin_buffer = st.session_state.pin_buffer[:-1]

        # Grid 3 Cột (Standard Keypad)
        c1, c2, c3 = st.columns(3)
        with c1: st.button("1", on_click=press, args="1", key="k1", use_container_width=True)
        with c2: st.button("2", on_click=press, args="2", key="k2", use_container_width=True)
        with c3: st.button("3", on_click=press, args="3", key="k3", use_container_width=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.button("4", on_click=press, args="4", key="k4", use_container_width=True)
        with c2: st.button("5", on_click=press, args="5", key="k5", use_container_width=True)
        with c3: st.button("6", on_click=press, args="6", key="k6", use_container_width=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.button("7", on_click=press, args="7", key="k7", use_container_width=True)
        with c2: st.button("8", on_click=press, args="8", key="k8", use_container_width=True)
        with c3: st.button("9", on_click=press, args="9", key="k9", use_container_width=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.button("C", on_click=clr, key="clr", use_container_width=True)
        with c2: st.button("0", on_click=press, args="0", key="k0", use_container_width=True)
        with c3: st.button("⌫", on_click=bck, key="del", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Check PIN
        curr = st.session_state.pin_buffer
        if len(curr) == 4:
            if stored is None:
                if st.button("💾 LƯU PIN", type="primary", use_container_width=True):
                    set_pin(curr)
                    st.success("Đã tạo!")
                    time.sleep(1)
                    st.session_state.logged_in = True
                    st.rerun()
            else:
                if curr == stored:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.toast("Sai PIN!", icon="⚠️")
                    time.sleep(0.3)
                    st.session_state.pin_buffer = ""
                    st.rerun()
    st.stop()

# --- 5. APP CHÍNH ---
def main_app():
    df, cats = load_data()
    st.session_state.categories = cats

    with st.sidebar:
        st.title("⚡ Menu")
        if st.button("🔄 Tải lại"): st.cache_data.clear(); st.rerun()
        if st.button("🔒 Đăng xuất"): st.session_state.logged_in = False; st.rerun()

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "⏳ SỔ NỢ", "⚙️ CÀI ĐẶT"])

    with tab1:
        if not df.empty:
            inc = df[df['loai']=='Thu']['so_tien'].sum()
            exp = df[df['loai']=='Chi']['so_tien'].sum()
            bal = inc - exp
            c1, c2, c3 = st.columns(3)
            c1.metric("Thu", f"{inc:,.0f}")
            c2.metric("Chi", f"{exp:,.0f}")
            c3.metric("Dư", f"{bal:,.0f}")
        
        st.divider()

        # Layout: Nhập liệu (Trái) - Biểu đồ (Phải)
        c_left, c_right = st.columns([1, 1.5], gap="medium")

        with c_left:
            with st.container():
                st.subheader("➕ Giao dịch")
                hist = df['muc'].unique().tolist() if not df.empty else []
                if hist: hist.reverse()
                opt = st.selectbox("Nội dung", ["➕ Mới..."] + hist, key="w_opt")
                desc = st.text_input("Tên mục:", key="w_desc") if opt == "➕ Mới..." else opt
                
                amt = st.number_input("Số tiền:", step=50000, key="w_amt")
                
                c1, c2 = st.columns(2)
                with c1: typ = st.radio("Loại:", ["Chi", "Thu"], key="w_type")
                with c2: cat = st.selectbox("Mục:", st.session_state.categories, key="w_cat")
                
                debt = st.checkbox("Vay/Nợ?", key="w_debt")
                ddl = st.date_input("Hạn:", key="w_date") if debt else None
                note = st.text_input("Note:", key="w_note")

                # Nút Lưu to rõ, style Neon nhưng hình chữ nhật
                if st.button("LƯU GIAO DỊCH 🚀", type="primary", use_container_width=True):
                    if amt > 0:
                        row = {
                            "ngay": str(date.today()), "muc": desc, "so_tien": amt,
                            "loai": typ, "phan_loai": cat,
                            "han_tra": str(ddl) if debt else None,
                            "trang_thai": "Đang nợ" if debt else "Đã xong",
                            "ghi_chu": note
                        }
                        add_trans(row)
                        st.toast("Đã lưu!")
                        time.sleep(1)
                        st.rerun()

        with c_right:
            with st.container():
                st.subheader("📈 Biểu đồ")
                if not df.empty:
                    exp_df = df[(df['loai']=='Chi') & (df['phan_loai']!='Cho vay')]
                    if not exp_df.empty:
                        # Biểu đồ tròn Altair (Đẹp như V6)
                        chart_data = exp_df.groupby('phan_loai')['so_tien'].sum().reset_index()
                        base = alt.Chart(chart_data).encode(theta=alt.Theta("so_tien", stack=True))
                        pie = base.mark_arc(innerRadius=60, outerRadius=100, cornerRadius=5).encode(
                            color=alt.Color("phan_loai", scale=alt.Scale(scheme='turbo'), legend=None),
                            order=alt.Order("so_tien", sort="descending"),
                            tooltip=["phan_loai", "so_tien"]
                        )
                        text = base.mark_text(radius=120, fill="#00f2c3").encode(
                            text=alt.Text("so_tien", format=",.0f"),
                            order=alt.Order("so_tien", sort="descending")
                        )
                        st.altair_chart(pie + text, use_container_width=True)
                        st.dataframe(chart_data.sort_values('so_tien', ascending=False).set_index('phan_loai'), use_container_width=True)
                    else: st.info("Chưa có chi tiêu")
                else: st.info("Trống")

        st.divider()
        with st.expander("📜 Lịch sử (Click để Xóa)"):
            if not df.empty:
                st.dataframe(df[['id', 'ngay', 'muc', 'so_tien', 'loai']].sort_values('id', ascending=False).head(5), use_container_width=True, hide_index=True)
                del_id = st.selectbox("ID Xóa:", df['id'].unique(), key="del_sel")
                if st.button("Xác nhận xóa"):
                    del_trans(int(del_id))
                    st.success("Xóa xong!")
                    time.sleep(1)
                    st.rerun()

    with tab2:
        st.subheader("Sổ Nợ")
        if not df.empty:
            d = df[df['trang_thai']=='Đang nợ']
            if not d.empty:
                for i, r in d.iterrows():
                    # Thẻ nợ màu sắc (Đã phục hồi từ V6)
                    clr = "#ff4b4b" if r['loai']=='Thu' else "#00f2c3"
                    st.markdown(f"""
                    <div style="border-left: 4px solid {clr}; background: rgba(255,255,255,0.05); padding: 15px; margin-bottom: 10px; border-radius: 8px;">
                        <b style="color:{clr}; font-size: 1.1em;">{r['muc']}</b> <br>
                        💰 {r['so_tien']:,} đ  |  📅 Hạn: {r['han_tra']} <br>
                        <small>Note: {r['ghi_chu']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.success("Sạch nợ!")

    with tab3:
        st.subheader("Danh mục")
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Thêm:")
            if st.button("Thêm mục"): add_cat(n); st.rerun()
        with c2:
            d = st.selectbox("Xóa:", st.session_state.categories)
            if st.button("Xóa mục"): del_cat(d); st.rerun()

# RUN
login_system()
main_app()
