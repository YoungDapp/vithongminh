import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import date, timedelta
import time
from supabase import create_client, Client

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="SmartWallet Pro", layout="wide", page_icon="💎")

# Kết nối Supabase
try:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("❌ Thiếu cấu hình Supabase!")
    st.stop()

# --- 2. CSS CAO CẤP (CUSTOM CARDS & ANIMATION) ---
def load_css():
    st.markdown("""
    <style>
        /* Font & Nền */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
        .stApp {
            background: radial-gradient(circle at 10% 20%, #1a1c29 0%, #0f0c29 90%);
            font-family: 'Outfit', sans-serif;
            color: #fff;
        }
        header {visibility: hidden;}
        .block-container { padding-top: 1.5rem !important; }

        /* --- CUSTOM TABS (Mượt mà hơn) --- */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 8px;
            border-radius: 50px;
            display: flex;
            gap: 10px;
            justify-content: center;
        }
        .stTabs [data-baseweb="tab"] {
            border: none !important;
            background-color: transparent;
            color: #aaa;
            border-radius: 30px;
            padding: 8px 24px;
            transition: all 0.3s ease;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, #00f2c3, #0098f0);
            color: #fff !important;
            font-weight: 700;
            box-shadow: 0 4px 15px rgba(0, 242, 195, 0.4);
        }

        /* --- CUSTOM METRIC CARDS (Thẻ số liệu Pro) --- */
        .metric-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.06);
        }
        
        /* Màu sắc riêng biệt cho từng loại */
        .card-income { border-bottom: 4px solid #00f2c3; box-shadow: 0 10px 30px -10px rgba(0, 242, 195, 0.1); }
        .card-expense { border-bottom: 4px solid #ff4b4b; box-shadow: 0 10px 30px -10px rgba(255, 75, 75, 0.1); }
        .card-balance { border-bottom: 4px solid #7000ff; box-shadow: 0 10px 30px -10px rgba(112, 0, 255, 0.1); }

        .metric-label { font-size: 0.9rem; color: #ccc; text-transform: uppercase; letter-spacing: 1px; }
        .metric-value { font-size: 2rem; font-weight: 700; margin: 5px 0; }
        .metric-delta { font-size: 0.85rem; font-weight: 500; display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; border-radius: 10px; }
        
        .text-green { color: #00f2c3; text-shadow: 0 0 20px rgba(0, 242, 195, 0.4); }
        .text-red { color: #ff4b4b; text-shadow: 0 0 20px rgba(255, 75, 75, 0.4); }
        .text-purple { color: #a742ff; text-shadow: 0 0 20px rgba(167, 66, 255, 0.4); }
        
        .bg-green-soft { background: rgba(0, 242, 195, 0.15); color: #00f2c3; }
        .bg-red-soft { background: rgba(255, 75, 75, 0.15); color: #ff4b4b; }
        .bg-gray-soft { background: rgba(255, 255, 255, 0.1); color: #aaa; }

        /* --- BUTTONS & INPUTS --- */
        div.stButton > button {
            width: 100%; border-radius: 12px; font-weight: 600; border: none;
            background: linear-gradient(135deg, #2a2d3a, #1f212b);
            color: #fff; border: 1px solid rgba(255,255,255,0.1);
            transition: 0.2s; padding: 0.6rem 1rem;
        }
        div.stButton > button:hover {
            border-color: #00f2c3; color: #00f2c3; box-shadow: 0 0 15px rgba(0,242,195,0.2);
        }
        /* Nút Primary (Lưu) */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #00f2c3, #00b894);
            color: #000; border: none;
        }
        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 0 20px rgba(0, 242, 195, 0.6); transform: scale(1.02);
        }

        /* Input styling */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            background-color: rgba(0, 0, 0, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important; color: white !important;
        }
        
        /* Keypad & Dots */
        .login-box { max-width: 360px; margin: 0 auto; }
        [data-testid="column"] { min-width: 0 !important; }
        .pin-area { display: flex; justify-content: center; gap: 15px; margin-bottom: 25px; }
        .dot { width: 14px; height: 14px; border-radius: 50%; border: 2px solid #444; transition: 0.2s; }
        .dot.active { background: #00f2c3; border-color: #00f2c3; box-shadow: 0 0 10px #00f2c3; }

    </style>
    """, unsafe_allow_html=True)
load_css()

# --- 3. DATABASE & LOGIC ---
# @st.cache_data(ttl=30) # Cache ngắn để cập nhật nhanh
def load_data():
    try:
        t = supabase.table('transactions').select("*").execute()
        df = pd.DataFrame(t.data)
        if not df.empty:
            df['ngay'] = pd.to_datetime(df['ngay'])
            df['han_tra'] = pd.to_datetime(df['han_tra'], errors='coerce').dt.date
        else:
            df = pd.DataFrame(columns=['id', 'ngay', 'muc', 'so_tien', 'loai', 'phan_loai', 'han_tra', 'trang_thai', 'ghi_chu'])
        
        c = supabase.table('categories').select("*").execute()
        cats = [x['ten_danh_muc'] for x in c.data] if c.data else ["Ăn uống", "Khác"]
        return df, cats
    except: return pd.DataFrame(), []

def add_trans(row): supabase.table('transactions').insert(row).execute()
def update_trans(tid, row): supabase.table('transactions').update(row).eq('id', tid).execute()
def del_trans(tid): supabase.table('transactions').delete().eq('id', tid).execute()
def add_cat(n): supabase.table('categories').insert({"ten_danh_muc": n}).execute()
def del_cat(n): supabase.table('categories').delete().eq('ten_danh_muc', n).execute()

# Hàm tính toán chỉ số so sánh tháng trước
def calculate_kpis(df):
    if df.empty: return 0, 0, 0, 0, 0, 0
    
    today = pd.Timestamp.now()
    current_month = today.month
    current_year = today.year
    
    # Tính tháng trước
    last_month_date = today - pd.DateOffset(months=1)
    last_month = last_month_date.month
    last_month_year = last_month_date.year

    # Lọc dữ liệu
    df_curr = df[(df['ngay'].dt.month == current_month) & (df['ngay'].dt.year == current_year)]
    df_last = df[(df['ngay'].dt.month == last_month) & (df['ngay'].dt.year == last_month_year)]

    # Tính tổng
    inc_curr = df_curr[df_curr['loai']=='Thu']['so_tien'].sum()
    exp_curr = df_curr[df_curr['loai']=='Chi']['so_tien'].sum()
    bal_curr = inc_curr - exp_curr

    inc_last = df_last[df_last['loai']=='Thu']['so_tien'].sum()
    exp_last = df_last[df_last['loai']=='Chi']['so_tien'].sum()
    
    # Tính % thay đổi (Tránh chia cho 0)
    def calc_pct(curr, last):
        if last == 0: return 100 if curr > 0 else 0
        return ((curr - last) / last) * 100

    pct_inc = calc_pct(inc_curr, inc_last)
    pct_exp = calc_pct(exp_curr, exp_last)
    # pct_bal không quan trọng lắm, ta dùng 2 cái kia
    
    return inc_curr, exp_curr, bal_curr, pct_inc, pct_exp

# --- 4. HỆ THỐNG ĐĂNG NHẬP ---
def login_system():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: return True
    if "pin_buffer" not in st.session_state: st.session_state.pin_buffer = ""

    def get_pin():
        try:
            r = supabase.table('app_config').select("value").eq("key", "user_pin").execute()
            return r.data[0]['value'] if r.data else None
        except: return None
    def set_pin(v): supabase.table('app_config').upsert({"key": "user_pin", "value": v}).execute()
    stored = get_pin()

    _, col_mid, _ = st.columns([1, 10, 1])
    with col_mid:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<br><h1 style='text-align: center;'>🔐 SmartWallet Pro</h1>", unsafe_allow_html=True)
        dots = '<div class="pin-area">'
        for i in range(4):
            state = "active" if i < len(st.session_state.pin_buffer) else ""
            dots += f'<div class="dot {state}"></div>'
        dots += '</div>'
        st.markdown(dots, unsafe_allow_html=True)

        if stored is None: st.info("🆕 Tạo PIN mới")

        def press(v): 
            if len(st.session_state.pin_buffer) < 4: st.session_state.pin_buffer += v
        def clr(): st.session_state.pin_buffer = ""
        def bck(): st.session_state.pin_buffer = st.session_state.pin_buffer[:-1]

        c1, c2, c3 = st.columns(3)
        with c1: st.button("1", on_click=press, args="1", key="k1")
        with c2: st.button("2", on_click=press, args="2", key="k2")
        with c3: st.button("3", on_click=press, args="3", key="k3")
        c1, c2, c3 = st.columns(3)
        with c1: st.button("4", on_click=press, args="4", key="k4")
        with c2: st.button("5", on_click=press, args="5", key="k5")
        with c3: st.button("6", on_click=press, args="6", key="k6")
        c1, c2, c3 = st.columns(3)
        with c1: st.button("7", on_click=press, args="7", key="k7")
        with c2: st.button("8", on_click=press, args="8", key="k8")
        with c3: st.button("9", on_click=press, args="9", key="k9")
        c1, c2, c3 = st.columns(3)
        with c1: st.button("C", on_click=clr, key="clr")
        with c2: st.button("0", on_click=press, args="0", key="k0")
        with c3: st.button("⌫", on_click=bck, key="del")
        st.markdown("</div>", unsafe_allow_html=True)

        curr = st.session_state.pin_buffer
        if len(curr) == 4:
            if stored is None:
                if st.button("💾 LƯU PIN", type="primary"):
                    set_pin(curr); st.success("OK"); time.sleep(1); st.session_state.logged_in = True; st.rerun()
            else:
                if curr == stored: st.session_state.logged_in = True; st.rerun()
                else: st.toast("Sai PIN!", icon="⚠️"); time.sleep(0.3); st.session_state.pin_buffer = ""; st.rerun()
    st.stop()

# --- 5. APP CHÍNH ---
def main_app():
    df, cats = load_data()
    st.session_state.categories = cats
    
    # Init keys
    if 'w_opt' not in st.session_state: st.session_state.w_opt = "➕ Mới..."
    if 'w_desc' not in st.session_state: st.session_state.w_desc = ""
    if 'w_amt' not in st.session_state: st.session_state.w_amt = 0
    if 'w_note' not in st.session_state: st.session_state.w_note = ""
    if 'w_debt' not in st.session_state: st.session_state.w_debt = False

    def save_callback():
        opt = st.session_state.w_opt
        desc = st.session_state.w_desc
        final = desc if opt == "➕ Mới..." else opt
        amt = st.session_state.w_amt
        
        if amt > 0 and final:
            row = {
                "ngay": str(datetime.datetime.now()), "muc": final, "so_tien": amt,
                "loai": "Thu" if "Thu" in st.session_state.w_type else "Chi", 
                "phan_loai": st.session_state.w_cat,
                "han_tra": str(st.session_state.w_date) if st.session_state.w_debt else None,
                "trang_thai": "Đang nợ" if st.session_state.w_debt else "Đã xong",
                "ghi_chu": st.session_state.w_note
            }
            add_trans(row)
            st.toast("Đã lưu!", icon="✨")
            # Reset
            st.session_state.w_amt = 0
            st.session_state.w_desc = ""
            st.session_state.w_note = ""
            st.session_state.w_debt = False
            st.session_state.w_opt = "➕ Mới..."
        else: st.toast("Nhập thiếu!", icon="⚠️")

    with st.sidebar:
        st.markdown("## ⚡ Menu")
        if st.button("🔄 Reload Data"): st.cache_data.clear(); st.rerun()
        if st.button("🔒 Logout"): st.session_state.logged_in = False; st.rerun()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 TỔNG QUAN", "⏳ SỔ NỢ", "⚙️ CÀI ĐẶT"])

    with tab1:
        # --- PHẦN HIỂN THỊ CHỈ SỐ (CUSTOM HTML CARDS) ---
        inc, exp, bal, pct_inc, pct_exp = calculate_kpis(df)
        
        # Format dấu mũi tên
        icon_inc = "↗" if pct_inc >= 0 else "↘"
        class_inc = "bg-green-soft" if pct_inc >= 0 else "bg-red-soft"
        
        icon_exp = "↗" if pct_exp >= 0 else "↘"
        class_exp = "bg-red-soft" if pct_exp >= 0 else "bg-green-soft" # Chi tăng là xấu (Đỏ)

        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        
        with col_kpi1:
            st.markdown(f"""
            <div class="metric-card card-income">
                <div class="metric-label">Thu Nhập (Tháng này)</div>
                <div class="metric-value text-green">{inc:,.0f}</div>
                <div class="metric-delta {class_inc}">{icon_inc} {abs(pct_inc):.1f}% vs tháng trước</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_kpi2:
            st.markdown(f"""
            <div class="metric-card card-expense">
                <div class="metric-label">Chi Tiêu (Tháng này)</div>
                <div class="metric-value text-red">{exp:,.0f}</div>
                <div class="metric-delta {class_exp}">{icon_exp} {abs(pct_exp):.1f}% vs tháng trước</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_kpi3:
            st.markdown(f"""
            <div class="metric-card card-balance">
                <div class="metric-label">Số Dư Thực Tế</div>
                <div class="metric-value text-purple">{bal:,.0f}</div>
                <div class="metric-delta bg-gray-soft">Cashflow</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True) # Khoảng cách

        # --- PHẦN NHẬP & BIỂU ĐỒ ---
        c_left, c_right = st.columns([1, 1.6], gap="large")
        
        with c_left:
            with st.container():
                st.subheader("📝 Nhập Mới")
                hist = df['muc'].unique().tolist() if not df.empty else []
                if hist: hist.reverse()
                
                st.selectbox("Nội dung", ["➕ Mới..."] + hist, key="w_opt")
                if st.session_state.w_opt == "➕ Mới...": st.text_input("Tên mục:", key="w_desc")
                st.number_input("Số tiền:", step=50000, key="w_amt")
                
                c1, c2 = st.columns(2)
                with c1: st.radio("Loại:", ["Chi tiền", "Thu tiền"], key="w_type")
                with c2: st.selectbox("Nhóm:", st.session_state.categories, key="w_cat")
                
                st.checkbox("Vay/Nợ?", key="w_debt")
                if st.session_state.w_debt: st.date_input("Hạn:", key="w_date")
                st.text_input("Ghi chú:", key="w_note")
                
                st.button("LƯU NGAY ✨", type="primary", on_click=save_callback, use_container_width=True)

        with c_right:
            with st.container():
                st.subheader("📊 Phân Tích")
                if not df.empty:
                    exp_df = df[(df['loai']=='Chi') & (df['phan_loai']!='Cho vay')]
                    if not exp_df.empty:
                        chart_data = exp_df.groupby('phan_loai')['so_tien'].sum().reset_index()
                        
                        base = alt.Chart(chart_data).encode(theta=alt.Theta("so_tien", stack=True))
                        pie = base.mark_arc(innerRadius=65, outerRadius=100, cornerRadius=5).encode(
                            color=alt.Color("phan_loai", scale=alt.Scale(scheme='turbo'), legend=None),
                            order=alt.Order("so_tien", sort="descending"),
                            tooltip=["phan_loai", alt.Tooltip("so_tien", format=",.0f")]
                        )
                        text = base.mark_text(radius=120, fill="#00f2c3").encode(
                            text=alt.Text("so_tien", format=",.0f"),
                            order=alt.Order("so_tien", sort="descending")
                        )
                        st.altair_chart((pie + text).properties(background='transparent'), use_container_width=True)
                        
                        # Danh sách chi tiết đẹp
                        for _, row in chart_data.sort_values('so_tien', ascending=False).iterrows():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05)">
                                <span style="color:#ddd">▫️ {row['phan_loai']}</span>
                                <span style="color:#00f2c3; font-weight:bold">{row['so_tien']:,.0f}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else: st.info("Chưa có dữ liệu chi.")
                else: st.info("Trống")

        st.divider()
        with st.expander("📅 Lịch sử chi tiết"):
            if not df.empty:
                st.dataframe(df[['ngay', 'muc', 'so_tien', 'loai', 'phan_loai']].sort_values('ngay', ascending=False), use_container_width=True)
                # Logic xóa đơn giản
                did = st.selectbox("Chọn ID xóa:", df['id'].unique(), key='del_main')
                if st.button("Xóa ID này"): del_trans(did); time.sleep(0.5); st.rerun()

    with tab2:
        st.subheader("Sổ Nợ")
        if not df.empty:
            d = df[df['trang_thai']=='Đang nợ']
            if not d.empty:
                for i, r in d.iterrows():
                    clr = "#ff4b4b" if r['loai']=='Thu' else "#00f2c3"
                    tit = f"🔴 BẠN ĐANG NỢ: {r['muc']}" if r['loai']=='Thu' else f"🟢 HỌ NỢ BẠN: {r['muc']}"
                    st.markdown(f"""
                    <div style="border-left: 4px solid {clr}; background: rgba(255,255,255,0.03); padding: 15px; margin-bottom: 10px; border-radius: 10px;">
                        <div style="font-weight:bold; color:{clr}; font-size:1.1em; margin-bottom:5px;">{tit}</div>
                        <div style="font-size:1.5em; font-weight:bold;">{r['so_tien']:,} đ</div>
                        <div style="color:#aaa; font-size:0.9em; margin-top:5px;">📅 Hạn: {r['han_tra']} &nbsp;|&nbsp; 📝 {r['ghi_chu']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.success("Sạch nợ!")

    with tab3:
        c1, c2 = st.columns(2)
        with c1: 
            n = st.text_input("Thêm mục:")
            if st.button("Thêm"): add_cat(n); st.rerun()
        with c2:
            d = st.selectbox("Xóa mục:", st.session_state.categories)
            if st.button("Xóa"): del_cat(d); st.rerun()

login_system()
main_app()
