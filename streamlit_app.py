import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import date
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

# --- 2. CSS CAO CẤP (V13 NEON PRO) ---
def load_css():
    st.markdown("""
    <style>
        /* Font & Nền */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
        .stApp {
            background: radial-gradient(circle at 10% 20%, #1a1c29 0%, #0f0c29 90%);
            color: #e0e0ff; font-family: 'Outfit', sans-serif;
        }
        header {visibility: hidden;}
        .block-container { padding-top: 1.5rem !important; padding-bottom: 5rem !important; }

        /* Container Kính Mờ */
        div[data-testid="stVerticalBlock"] > div.stContainer, 
        section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        }

        /* --- CUSTOM METRIC CARDS (THẺ CHỈ SỐ PRO) --- */
        .metric-card {
            background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px);
            border-radius: 16px; padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform 0.2s;
        }
        .metric-card:hover { transform: translateY(-3px); }
        
        .card-income { border-bottom: 3px solid #00f2c3; box-shadow: 0 5px 20px -10px rgba(0, 242, 195, 0.2); }
        .card-expense { border-bottom: 3px solid #ff4b4b; box-shadow: 0 5px 20px -10px rgba(255, 75, 75, 0.2); }
        .card-balance { border-bottom: 3px solid #7000ff; box-shadow: 0 5px 20px -10px rgba(112, 0, 255, 0.2); }

        .metric-label { font-size: 0.85rem; color: #ccc; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .metric-value { font-size: 1.8rem; font-weight: 700; margin-bottom: 5px; }
        .metric-delta { font-size: 0.8rem; font-weight: 500; padding: 2px 8px; border-radius: 8px; display: inline-block; }
        
        .text-green { color: #00f2c3; text-shadow: 0 0 15px rgba(0, 242, 195, 0.3); }
        .text-red { color: #ff4b4b; text-shadow: 0 0 15px rgba(255, 75, 75, 0.3); }
        .text-purple { color: #a742ff; text-shadow: 0 0 15px rgba(167, 66, 255, 0.3); }
        .bg-green-soft { background: rgba(0, 242, 195, 0.15); color: #00f2c3; }
        .bg-red-soft { background: rgba(255, 75, 75, 0.15); color: #ff4b4b; }

        /* Button Style (Pill Shape) */
        div.stButton > button {
            width: 100%; border-radius: 12px; font-weight: 600;
            border: 1px solid #00f2c3; background: rgba(255, 255, 255, 0.05);
            color: #00f2c3; transition: all 0.2s; padding: 0.5rem 1rem;
        }
        div.stButton > button:hover {
            background: rgba(0, 242, 195, 0.1); box-shadow: 0 0 15px rgba(0, 242, 195, 0.3);
        }
        div.stButton > button:active { background: #00f2c3; color: #000; }
        
        /* Logout Button */
        div.stButton > button.logout-btn { border-color: #ff4b4b !important; color: #ff4b4b !important; }

        /* Inputs & Editor */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, [data-testid="stDataEditor"] {
            background-color: rgba(0, 0, 0, 0.3) !important; color: #fff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 8px !important;
        }
        
        /* Tabs (Pill Shape) */
        .stTabs [data-baseweb="tab-list"] { 
            gap: 8px; background: rgba(255,255,255,0.05); padding: 6px; border-radius: 30px; justify-content: center; 
        }
        .stTabs [data-baseweb="tab"] { border-radius: 20px; border: none; color: #aaa; }
        .stTabs [aria-selected="true"] { 
            background: linear-gradient(90deg, #00f2c3, #0098f0); color: #fff !important; font-weight: bold;
            box-shadow: 0 4px 10px rgba(0, 242, 195, 0.3);
        }
        
        /* Login Dots */
        .pin-area { display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; }
        .dot { width: 15px; height: 15px; border-radius: 50%; border: 2px solid #555; transition: 0.2s; }
        .dot.active { background: #00f2c3; border-color: #00f2c3; box-shadow: 0 0 10px #00f2c3; }
    </style>
    """, unsafe_allow_html=True)
load_css()

# --- 3. DATABASE & LOGIC ---
# @st.cache_data(ttl=30)
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
def del_trans_list(ids): supabase.table('transactions').delete().in_('id', ids).execute()
def add_cat(n): supabase.table('categories').insert({"ten_danh_muc": n}).execute()
def del_cat(n): supabase.table('categories').delete().eq('ten_danh_muc', n).execute()

# Hàm tính toán KPI (% Tăng trưởng)
def calculate_kpis(df):
    if df.empty: return 0, 0, 0, 0, 0
    today = pd.Timestamp.now()
    curr_m = df[(df['ngay'].dt.month == today.month) & (df['ngay'].dt.year == today.year)]
    last_m_date = today - pd.DateOffset(months=1)
    last_m = df[(df['ngay'].dt.month == last_m_date.month) & (df['ngay'].dt.year == last_m_date.year)]
    
    inc = curr_m[curr_m['loai']=='Thu']['so_tien'].sum()
    exp = curr_m[curr_m['loai']=='Chi']['so_tien'].sum()
    bal = inc - exp
    
    last_inc = last_m[last_m['loai']=='Thu']['so_tien'].sum()
    last_exp = last_m[last_m['loai']=='Chi']['so_tien'].sum()
    
    # Tránh chia cho 0
    pct_inc = ((inc - last_inc)/last_inc)*100 if last_inc > 0 else (100 if inc > 0 else 0)
    pct_exp = ((exp - last_exp)/last_exp)*100 if last_exp > 0 else (100 if exp > 0 else 0)
    return inc, exp, bal, pct_inc, pct_exp

# --- 4. HỆ THỐNG ĐĂNG NHẬP ---
def login_system():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: return True
    if "pin_buffer" not in st.session_state: st.session_state.pin_buffer = ""

    st.markdown("""<style>.login-box { max-width: 350px; margin: 0 auto; } [data-testid="column"] { min-width: 0 !important; }</style>""", unsafe_allow_html=True)
    def get_pin():
        try:
            r = supabase.table('app_config').select("value").eq("key", "user_pin").execute()
            return r.data[0]['value'] if r.data else None
        except: return None
    def set_pin(v): supabase.table('app_config').upsert({"key": "user_pin", "value": v}).execute()
    stored = get_pin()

    _, col_mid, _ = st.columns([1, 10, 1])
    with col_mid:
        st.markdown("<div class='login-box'><br><h1 style='text-align: center;'>🔒 SmartWallet Pro</h1>", unsafe_allow_html=True)
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

        if len(st.session_state.pin_buffer) == 4:
            curr = st.session_state.pin_buffer
            if stored is None:
                if st.button("💾 LƯU PIN", type="primary", use_container_width=True):
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
        # Lấy dữ liệu an toàn bằng .get() để tránh lỗi widget bị ẩn
        opt = st.session_state.get("w_opt", "")
        desc = st.session_state.get("w_desc", "")
        amt = st.session_state.get("w_amt", 0)
        
        final = desc if opt == "➕ Mới..." else opt
        
        # Lấy các giá trị khác (an toàn)
        w_type = st.session_state.get("w_type", "Chi")
        w_cat = st.session_state.get("w_cat", "Khác")
        w_debt = st.session_state.get("w_debt", False)
        w_date = st.session_state.get("w_date", None)
        w_note = st.session_state.get("w_note", "")

        if amt > 0 and final:
            row = {
                "ngay": str(datetime.datetime.now()), "muc": final, "so_tien": amt,
                "loai": "Thu" if "Thu" in w_type else "Chi",
                "phan_loai": w_cat,
                "han_tra": str(w_date) if w_debt else None,
                "trang_thai": "Đang nợ" if w_debt else "Đã xong",
                "ghi_chu": w_note
            }
            add_trans(row)
            st.toast("Đã lưu!", icon="✨")
            
            # Reset Form an toàn
            st.session_state.w_amt = 0
            if "w_desc" in st.session_state: st.session_state.w_desc = ""
            if "w_note" in st.session_state: st.session_state.w_note = ""
            if "w_debt" in st.session_state: st.session_state.w_debt = False
            st.session_state.w_opt = "➕ Mới..."
        else: st.toast("Thiếu thông tin!", icon="⚠️")

    with st.sidebar:
        st.title("⚡ Menu")
        if st.button("🔄 Tải lại"): st.cache_data.clear(); st.rerun()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 TỔNG QUAN", "⏳ SỔ NỢ", "⚙️ CÀI ĐẶT"])

    with tab1:
        # --- PHẦN 1: THẺ CHỈ SỐ CUSTOM (V13) ---
        inc, exp, bal, pi, pe = calculate_kpis(df)
        
        ci = "text-green" if pi>=0 else "text-red"
        icon_i = "↗" if pi>=0 else "↘"
        
        ce = "text-red" if pe>=0 else "text-green" # Chi tăng là xấu (Đỏ)
        icon_e = "↗" if pe>=0 else "↘"
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card card-income"><div class="metric-label">Thu Nhập</div><div class="metric-value text-green">{inc:,.0f}</div><div class="metric-delta bg-green-soft">{icon_i} {abs(pi):.1f}%</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card card-expense"><div class="metric-label">Chi Tiêu</div><div class="metric-value text-red">{exp:,.0f}</div><div class="metric-delta bg-red-soft">{icon_e} {abs(pe):.1f}%</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card card-balance"><div class="metric-label">Số Dư</div><div class="metric-value text-purple">{bal:,.0f}</div><div class="metric-delta" style="color:#aaa">Cashflow</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- PHẦN 2: NHẬP & CHART ---
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
                        
                        # Chart trong suốt (V13)
                        base = alt.Chart(chart_data).encode(theta=alt.Theta("so_tien", stack=True))
                        pie = base.mark_arc(innerRadius=65, outerRadius=100, cornerRadius=5).encode(
                            color=alt.Color("phan_loai", scale=alt.Scale(scheme='turbo'), legend=None),
                            order=alt.Order("so_tien", sort="descending"), tooltip=["phan_loai", "so_tien"]
                        )
                        text = base.mark_text(radius=120, fill="#00f2c3").encode(text=alt.Text("so_tien", format=",.0f"), order=alt.Order("so_tien", sort="descending"))
                        st.altair_chart((pie + text).properties(background='transparent'), use_container_width=True)
                        
                        # List chi tiết
                        for _, row in chart_data.sort_values('so_tien', ascending=False).iterrows():
                            st.markdown(f"<div style='display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid rgba(255,255,255,0.05)'><span style='color:#ddd'>▫️ {row['phan_loai']}</span><span style='color:#00f2c3; font-weight:bold'>{row['so_tien']:,.0f}</span></div>", unsafe_allow_html=True)
                    else: st.info("Chưa có dữ liệu chi.")
                else: st.info("Trống.")

        st.divider()
        
        # --- PHẦN 3: SMART HISTORY (V14) ---
        with st.container():
            st.subheader("📅 Lịch sử & Chỉnh sửa")
            if not df.empty:
                c_d, c_v = st.columns([1,2])
                with c_d: f_date = st.date_input("Chọn ngày:", date.today())
                with c_v: view = st.radio("Chế độ xem:", ["Chỉ ngày này", "Tất cả"], horizontal=True)
                
                # Lọc
                df_show = df[df['ngay'].dt.date == f_date].copy() if view == "Chỉ ngày này" else df.copy()
                
                if not df_show.empty:
                    df_show['Xóa'] = False 
                    
                    # Bảng Edit
                    edited = st.data_editor(
                        df_show,
                        column_config={
                            "id": None,
                            "ngay": st.column_config.DatetimeColumn("Thời gian", format="DD/MM/YYYY HH:mm"),
                            "muc": "Mục",
                            "so_tien": st.column_config.NumberColumn("Số tiền", format="%d"),
                            "loai": st.column_config.SelectboxColumn("Loại", options=["Thu", "Chi"]),
                            "phan_loai": st.column_config.SelectboxColumn("Nhóm", options=st.session_state.categories),
                            "trang_thai": st.column_config.SelectboxColumn("Status", options=["Đã xong", "Đang nợ"]),
                            "Xóa": st.column_config.CheckboxColumn("❌ Xóa", default=False)
                        },
                        use_container_width=True, hide_index=True, key="history_edit"
                    )
                    
                    # Nút Lưu Thay Đổi
                    if st.button("💾 CẬP NHẬT THAY ĐỔI", type="primary", use_container_width=True):
                        # Xóa
                        to_del = edited[edited['Xóa']==True]['id'].tolist()
                        if to_del: del_trans_list(to_del); st.toast(f"Đã xóa {len(to_del)} dòng")
                        
                        # Sửa
                        to_upd = edited[edited['Xóa']==False]
                        cnt = 0
                        for i, r in to_upd.iterrows():
                            org = df[df['id']==r['id']].iloc[0]
                            if (str(r['ngay']) != str(org['ngay']) or r['muc'] != org['muc'] or 
                                r['so_tien'] != org['so_tien'] or r['loai'] != org['loai'] or 
                                r['phan_loai'] != org['phan_loai'] or r['trang_thai'] != org['trang_thai'] or 
                                r['ghi_chu'] != org['ghi_chu']):
                                
                                update_trans(r['id'], {
                                    "ngay": str(r['ngay']), "muc": r['muc'], "so_tien": r['so_tien'],
                                    "loai": r['loai'], "phan_loai": r['phan_loai'], 
                                    "trang_thai": r['trang_thai'], "ghi_chu": r['ghi_chu']
                                })
                                cnt += 1
                        
                        if cnt > 0: st.toast(f"Đã sửa {cnt} dòng")
                        time.sleep(1); st.rerun()
                else: st.info("Không có giao dịch.")
            else: st.info("Chưa có dữ liệu.")

    with tab2:
        st.subheader("Sổ Nợ")
        if not df.empty:
            d = df[df['trang_thai']=='Đang nợ']
            if not d.empty:
                for i, r in d.iterrows():
                    clr = "#ff4b4b" if r['loai']=='Thu' else "#00f2c3"
                    tit = f"🔴 BẠN NỢ: {r['muc']}" if r['loai']=='Thu' else f"🟢 HỌ NỢ BẠN: {r['muc']}"
                    st.markdown(f"<div style='border-left: 4px solid {clr}; background: rgba(255,255,255,0.03); padding: 15px; margin-bottom: 10px; border-radius: 10px;'><div style='font-weight:bold; color:{clr}; font-size:1.1em; margin-bottom:5px;'>{tit}</div><div style='font-size:1.5em; font-weight:bold;'>{r['so_tien']:,} đ</div><div style='color:#aaa; font-size:0.9em; margin-top:5px;'>📅 Hạn: {r['han_tra']} &nbsp;|&nbsp; 📝 {r['ghi_chu']}</div></div>", unsafe_allow_html=True)
            else: st.success("Sạch nợ!")

    with tab3:
        st.subheader("Cài đặt")
        c1, c2 = st.columns(2)
        with c1: 
            n = st.text_input("Thêm mục:")
            if st.button("Thêm mục"): add_cat(n); st.rerun()
        with c2: 
            d = st.selectbox("Xóa mục:", st.session_state.categories)
            if st.button("Xóa mục"): del_cat(d); st.rerun()
        
        st.divider()
        if st.button("🔒 ĐĂNG XUẤT KHỎI THIẾT BỊ", type="primary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

login_system()
main_app()
