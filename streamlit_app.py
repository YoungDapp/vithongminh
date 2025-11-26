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

# --- 2. CSS CAO CẤP (V19 NEON PRO - FULL) ---
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
        section[data-testid="stSidebar"],
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
            color: #fff;
        }

        /* --- CUSTOM METRIC CARDS --- */
        .metric-card {
            background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px);
            border-radius: 16px; padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform 0.2s;
            margin-bottom: 10px;
        }
        .metric-card:hover { transform: translateY(-3px); }
        
        .card-income { border-bottom: 3px solid #00f2c3; box-shadow: 0 5px 20px -10px rgba(0, 242, 195, 0.2); }
        .card-expense { border-bottom: 3px solid #ff4b4b; box-shadow: 0 5px 20px -10px rgba(255, 75, 75, 0.2); }
        .card-balance { border-bottom: 3px solid #7000ff; box-shadow: 0 5px 20px -10px rgba(112, 0, 255, 0.2); }

        .metric-label { font-size: 0.85rem; color: #ccc; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .metric-value { font-size: 1.8rem; font-weight: 700; margin-bottom: 5px; }
        .metric-delta { font-size: 0.8rem; font-weight: 500; padding: 2px 8px; border-radius: 8px; display: inline-block; }
        
        /* Text Colors */
        .text-green { color: #00f2c3 !important; text-shadow: 0 0 15px rgba(0, 242, 195, 0.3); }
        .text-red { color: #ff4b4b !important; text-shadow: 0 0 15px rgba(255, 75, 75, 0.3); }
        .text-purple { color: #a742ff !important; text-shadow: 0 0 15px rgba(167, 66, 255, 0.3); }
        .bg-green-soft { background: rgba(0, 242, 195, 0.15); color: #00f2c3; }
        .bg-red-soft { background: rgba(255, 75, 75, 0.15); color: #ff4b4b; }

        /* Button Style */
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
        
        /* Tabs */
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
COLOR_PALETTE = [
    "#00f2c3", "#ff4b4b", "#f7b731", "#a55eea", "#4b7bec", 
    "#fa8231", "#2bcbba", "#eb3b5a", "#3867d6", "#8854d0",
    "#20bf6b", "#0fb9b1", "#45aaf2", "#fd9644", "#fc5c65"
]

# @st.cache_data(ttl=30)
def load_data():
    try:
        # 1. Load Transactions
        t = supabase.table('transactions').select("*").execute()
        df = pd.DataFrame(t.data)
        if not df.empty:
            df['ngay'] = pd.to_datetime(df['ngay'])
            df['han_tra'] = pd.to_datetime(df['han_tra'], errors='coerce').dt.date
            if 'phuong_thuc' not in df.columns:
                df['phuong_thuc'] = "Ví tiền mặt"
        else:
            df = pd.DataFrame(columns=['id', 'ngay', 'muc', 'so_tien', 'loai', 'phan_loai', 'phuong_thuc', 'han_tra', 'trang_thai', 'ghi_chu'])
        
        # 2. Load Categories
        c = supabase.table('categories').select("*").execute()
        cats = [x['ten_danh_muc'] for x in c.data] if c.data else ["Ăn uống", "Khác"]

        # 3. Load Payment Methods
        m = supabase.table('payment_methods').select("*").execute()
        methods = [x['ten_phuong_thuc'] for x in m.data] if m.data else ["Ví tiền mặt", "Tài khoản ngân hàng", "Thẻ"]

        return df, cats, methods
    except Exception as e:
        return pd.DataFrame(), [], []

def add_trans(row): supabase.table('transactions').insert(row).execute()
def update_trans(tid, row): supabase.table('transactions').update(row).eq('id', tid).execute()
def del_trans_list(ids): supabase.table('transactions').delete().in_('id', ids).execute()

def add_cat(n): supabase.table('categories').insert({"ten_danh_muc": n}).execute()
def del_cat(n): supabase.table('categories').delete().eq('ten_danh_muc', n).execute()

def add_method(n): supabase.table('payment_methods').insert({"ten_phuong_thuc": n}).execute()
def del_method(n): supabase.table('payment_methods').delete().eq('ten_phuong_thuc', n).execute()

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
    df, cats, methods = load_data()
    st.session_state.categories = cats
    st.session_state.methods = methods
    
    if 'w_opt' not in st.session_state: st.session_state.w_opt = "➕ Mới..."
    if 'w_desc' not in st.session_state: st.session_state.w_desc = ""
    if 'w_amt' not in st.session_state: st.session_state.w_amt = 0
    if 'w_note' not in st.session_state: st.session_state.w_note = ""
    if 'w_debt' not in st.session_state: st.session_state.w_debt = False
    
    # Ghi nhớ phương thức (Last used method)
    if 'last_method' not in st.session_state:
        st.session_state.last_method = methods[0] if methods else "Ví tiền mặt"

    def save_callback():
        opt = st.session_state.get("w_opt", "")
        desc = st.session_state.get("w_desc", "")
        amt = st.session_state.get("w_amt", 0)
        
        final = desc if opt == "➕ Mới..." else opt
        
        w_type = st.session_state.get("w_type", "Chi")
        w_cat = st.session_state.get("w_cat", "Khác")
        w_method = st.session_state.get("w_method", "Ví tiền mặt")
        w_debt = st.session_state.get("w_debt", False)
        w_date = st.session_state.get("w_date", None)
        w_note = st.session_state.get("w_note", "")

        if amt > 0 and final:
            row = {
                "ngay": str(datetime.datetime.now()), "muc": final, "so_tien": amt,
                "loai": "Thu" if "Thu" in w_type else "Chi",
                "phan_loai": w_cat,
                "phuong_thuc": w_method,
                "han_tra": str(w_date) if w_debt else None,
                "trang_thai": "Đang nợ" if w_debt else "Đã xong",
                "ghi_chu": w_note
            }
            add_trans(row)
            
            # Cập nhật last_method
            st.session_state.last_method = w_method
            
            st.toast("Đã lưu!", icon="✨")
            
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
        # KPI
        inc, exp, bal, pi, pe = calculate_kpis(df)
        ci = "text-green" if pi>=0 else "text-red"
        icon_i = "↗" if pi>=0 else "↘"
        ce = "text-red" if pe>=0 else "text-green"
        icon_e = "↗" if pe>=0 else "↘"
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card card-income"><div class="metric-label">Thu Nhập</div><div class="metric-value text-green">{inc:,.0f}</div><div class="metric-delta bg-green-soft">{icon_i} {abs(pi):.1f}%</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card card-expense"><div class="metric-label">Chi Tiêu</div><div class="metric-value text-red">{exp:,.0f}</div><div class="metric-delta bg-red-soft">{icon_e} {abs(pe):.1f}%</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card card-balance"><div class="metric-label">Số Dư</div><div class="metric-value text-purple">{bal:,.0f}</div><div class="metric-delta" style="color:#aaa">Cashflow</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # --- NHẬP & CHART ---
        c_left, c_right = st.columns([1, 1.6], gap="large")
        with c_left:
            with st.container():
                st.subheader("📝 Nhập Mới")
                hist = df['muc'].unique().tolist() if not df.empty else []
                if hist: hist.reverse()
                st.selectbox("Nội dung", ["➕ Mới..."] + hist, key="w_opt")
                if st.session_state.w_opt == "➕ Mới...": st.text_input("Tên mục:", key="w_desc")
                
                # --- SỐ TIỀN VỚI FORMATTING PREVIEW ---
                st.number_input("Số tiền:", step=50000, key="w_amt")
                if st.session_state.w_amt > 0:
                    st.caption(f"💡 {st.session_state.w_amt:,.0f} VNĐ") # Preview định dạng số
                
                c1, c2 = st.columns(2)
                with c1: st.radio("Loại:", ["Chi tiền", "Thu tiền"], key="w_type")
                with c2: st.selectbox("Nhóm:", st.session_state.categories, key="w_cat")
                
                # Selectbox Phương Thức (Nhớ giá trị cũ)
                try:
                    idx = st.session_state.methods.index(st.session_state.last_method)
                except: idx = 0
                st.selectbox("Phương thức:", st.session_state.methods, index=idx, key="w_method")

                st.checkbox("Vay/Nợ?", key="w_debt")
                if st.session_state.w_debt: st.date_input("Hạn:", key="w_date")
                st.text_input("Ghi chú:", key="w_note")
                st.button("LƯU NGAY ✨", type="primary", on_click=save_callback, use_container_width=True)

        with c_right:
            with st.container():
                st.subheader("📊 Phân Tích")
                if not df.empty:
                    # Tab Nguồn Tiền Theo Phương Án 1 (Tách dòng tiền vào/ra)
                    tab_chi, tab_thu, tab_nguon = st.tabs(["📉 Chi Tiêu", "📈 Thu Nhập", "💳 Nguồn Tiền"])
                    
                    # Hàm vẽ biểu đồ đồng bộ màu sắc
                    def draw_chart(sub_df, group_col, color_scheme):
                        if not sub_df.empty:
                            chart_data = sub_df.groupby(group_col)['so_tien'].sum().reset_index()
                            
                            unique_cats = chart_data[group_col].unique()
                            # Color matching
                            color_map = {cat: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, cat in enumerate(unique_cats)}
                            
                            base = alt.Chart(chart_data).encode(theta=alt.Theta("so_tien", stack=True))
                            pie = base.mark_arc(innerRadius=65, outerRadius=100, cornerRadius=5).encode(
                                color=alt.Color(group_col, scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None),
                                order=alt.Order("so_tien", sort="descending"), tooltip=[group_col, "so_tien"]
                            )
                            text = base.mark_text(radius=120, fill="#fff").encode(text=alt.Text("so_tien", format=",.0f"), order=alt.Order("so_tien", sort="descending"))
                            st.altair_chart((pie + text).properties(background='transparent'), use_container_width=True)
                            
                            for _, row in chart_data.sort_values('so_tien', ascending=False).iterrows():
                                cat_color = color_map[row[group_col]]
                                st.markdown(f"""
                                <div style="display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid rgba(255,255,255,0.05)">
                                    <span style="color:{cat_color}; font-weight:500">▫️ {row[group_col]}</span>
                                    <span style="color:#fff; font-weight:bold">{row['so_tien']:,.0f}</span>
                                </div>
                                """, unsafe_allow_html=True)
                        else: st.info("Chưa có dữ liệu.")

                    with tab_chi: draw_chart(df[df['loai']=='Chi'], 'phan_loai', 'turbo')
                    with tab_thu: draw_chart(df[df['loai']=='Thu'], 'phan_loai', 'greens')
                    
                    # TAB NGUỒN TIỀN (Phương án 1 - Tách biệt)
                    with tab_nguon:
                        col_in, col_out = st.columns(2)
                        with col_in:
                            st.markdown("##### 📥 Tiền Vào (Thu)")
                            draw_chart(df[df['loai']=='Thu'], 'phuong_thuc', 'greens')
                        with col_out:
                            st.markdown("##### 📤 Tiền Ra (Chi)")
                            draw_chart(df[df['loai']=='Chi'], 'phuong_thuc', 'reds')

                else: st.info("Trống.")

        st.divider()
        
        # --- SMART HISTORY (EXPANDER) ---
        with st.expander("📅 Lịch sử & Chỉnh sửa (Click để xem)", expanded=False):
            if not df.empty:
                c_d, c_v = st.columns([1,2])
                with c_d: f_date = st.date_input("Chọn ngày:", date.today())
                with c_v: view = st.radio("Chế độ xem:", ["Chỉ ngày này", "Tất cả"], horizontal=True)
                
                df_show = df[df['ngay'].dt.date == f_date].copy() if view == "Chỉ ngày này" else df.copy()
                
                if not df_show.empty:
                    df_show['Xóa'] = False 
                    edited = st.data_editor(
                        df_show,
                        column_config={
                            "id": None,
                            "ngay": st.column_config.DatetimeColumn("Thời gian", format="DD/MM/YYYY HH:mm"),
                            "muc": "Mục",
                            "so_tien": st.column_config.NumberColumn("Số tiền", format="%d"),
                            "loai": st.column_config.SelectboxColumn("Loại", options=["Thu", "Chi"]),
                            "phan_loai": st.column_config.SelectboxColumn("Nhóm", options=st.session_state.categories),
                            "phuong_thuc": st.column_config.SelectboxColumn("Ví/Thẻ", options=st.session_state.methods),
                            "trang_thai": st.column_config.SelectboxColumn("Status", options=["Đã xong", "Đang nợ"]),
                            "Xóa": st.column_config.CheckboxColumn("❌ Xóa", default=False)
                        },
                        use_container_width=True, hide_index=True, key="history_edit"
                    )
                    
                    if st.button("💾 CẬP NHẬT THAY ĐỔI", type="primary", use_container_width=True):
                        to_del = edited[edited['Xóa']==True]['id'].tolist()
                        if to_del: del_trans_list(to_del); st.toast(f"Đã xóa {len(to_del)} dòng")
                        
                        to_upd = edited[edited['Xóa']==False]
                        cnt = 0
                        for i, r in to_upd.iterrows():
                            org = df[df['id']==r['id']].iloc[0]
                            if (str(r['ngay']) != str(org['ngay']) or r['muc'] != org['muc'] or 
                                r['so_tien'] != org['so_tien'] or r['loai'] != org['loai'] or 
                                r['phan_loai'] != org['phan_loai'] or r['phuong_thuc'] != org.get('phuong_thuc', '') or
                                r['trang_thai'] != org['trang_thai'] or r['ghi_chu'] != org['ghi_chu']):
                                
                                update_trans(r['id'], {
                                    "ngay": str(r['ngay']), "muc": r['muc'], "so_tien": r['so_tien'],
                                    "loai": r['loai'], "phan_loai": r['phan_loai'], 
                                    "phuong_thuc": r['phuong_thuc'],
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
            n = st.text_input("Thêm danh mục:")
            if st.button("Thêm"): add_cat(n); st.rerun()
        with c2: 
            d = st.selectbox("Xóa danh mục:", st.session_state.categories)
            if st.button("Xóa"): del_cat(d); st.rerun()
            
        st.divider()
        st.markdown("### 💳 Quản lý Phương Thức Thanh Toán")
        c3, c4 = st.columns(2)
        with c3: 
            nm = st.text_input("Thêm phương thức (Ví, Thẻ...):")
            if st.button("Thêm PT"): add_method(nm); st.rerun()
        with c4: 
            dm = st.selectbox("Xóa phương thức:", st.session_state.methods)
            if st.button("Xóa PT"): del_method(dm); st.rerun()
        
        st.divider()
        if st.button("🔒 ĐĂNG XUẤT KHỎI THIẾT BỊ", type="primary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

login_system()
main_app()
