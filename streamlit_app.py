import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import datetime as dt_class # Đổi tên để tránh trùng
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

# --- 2. CSS ---
def load_css():
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #e0e0ff;
            font-family: 'Inter', sans-serif;
        }
        header {visibility: hidden;}
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
        div[data-testid="stVerticalBlock"] > div.stContainer, section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stMetric"] {
            background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(0, 242, 195, 0.3);
            border-radius: 12px; padding: 10px;
        }
        div[data-testid="stMetricLabel"] label { color: #aaa !important; }
        div[data-testid="stMetricValue"] { color: #00f2c3 !important; text-shadow: 0 0 10px rgba(0, 242, 195, 0.4); }
        div.stButton > button {
            width: 100%; border-radius: 12px; font-weight: 700; border: 1px solid #00f2c3;
            background: rgba(255, 255, 255, 0.05); color: #00f2c3; transition: all 0.2s;
        }
        div.stButton > button:hover { background: rgba(0, 242, 195, 0.1); box-shadow: 0 0 15px rgba(0, 242, 195, 0.3); }
        div.stButton > button:active { background: #00f2c3; color: #000; }
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, [data-testid="stDataEditor"] {
            background-color: rgba(0, 0, 0, 0.3) !important; color: #fff !important; border-radius: 8px !important;
        }
        .pin-area { display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; }
        .dot { width: 15px; height: 15px; border-radius: 50%; border: 2px solid #555; transition: 0.2s; }
        .dot.active { background: #00f2c3; border-color: #00f2c3; box-shadow: 0 0 10px #00f2c3; }
        .stTabs [data-baseweb="tab-list"] { gap: 5px; background: rgba(255,255,255,0.05); padding: 5px; border-radius: 10px; }
        .stTabs [aria-selected="true"] { background: rgba(0,242,195,0.2) !important; color: #00f2c3 !important; }
    </style>
    """, unsafe_allow_html=True)
load_css()

# --- 3. DATABASE (FIX TIMEZONE) ---
# @st.cache_data(ttl=60)
def load_data():
    try:
        t = supabase.table('transactions').select("*").execute()
        df = pd.DataFrame(t.data)
        if not df.empty:
            # Chuyển đổi cột 'ngay' sang Datetime và chỉnh múi giờ
            df['ngay'] = pd.to_datetime(df['ngay'])
            
            # Xử lý cột Hạn trả (chỉ cần ngày)
            df['han_tra'] = pd.to_datetime(df['han_tra'], errors='coerce').dt.date
        else:
            df = pd.DataFrame(columns=['id', 'ngay', 'muc', 'so_tien', 'loai', 'phan_loai', 'han_tra', 'trang_thai', 'ghi_chu'])
        
        c = supabase.table('categories').select("*").execute()
        cats = [x['ten_danh_muc'] for x in c.data] if c.data else ["Ăn uống", "Khác"]
        return df, cats
    except: return pd.DataFrame(), []

def add_trans(row): supabase.table('transactions').insert(row).execute()
def update_trans(tid, row): supabase.table('transactions').update(row).eq('id', tid).execute()
def del_trans_list(id_list): 
    if id_list: supabase.table('transactions').delete().in_('id', id_list).execute()

def add_cat(n): supabase.table('categories').insert({"ten_danh_muc": n}).execute()
def del_cat(n): supabase.table('categories').delete().eq('ten_danh_muc', n).execute()

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
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>🔒 SmartWallet</h1>", unsafe_allow_html=True)
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
        curr = st.session_state.pin_buffer
        if len(curr) == 4:
            if stored is None:
                if st.button("💾 LƯU PIN", type="primary", use_container_width=True):
                    set_pin(curr); st.success("Đã tạo!"); time.sleep(1); st.session_state.logged_in = True; st.rerun()
            else:
                if curr == stored: st.session_state.logged_in = True; st.rerun()
                else: st.toast("Sai PIN!", icon="⚠️"); time.sleep(0.3); st.session_state.pin_buffer = ""; st.rerun()
    st.stop()

# --- 5. APP CHÍNH ---
def main_app():
    df, cats = load_data()
    st.session_state.categories = cats
    if 'w_opt' not in st.session_state: st.session_state.w_opt = "➕ Mới..."
    if 'w_desc' not in st.session_state: st.session_state.w_desc = ""
    if 'w_amt' not in st.session_state: st.session_state.w_amt = 0
    if 'w_note' not in st.session_state: st.session_state.w_note = ""
    if 'w_debt' not in st.session_state: st.session_state.w_debt = False

    def save_callback():
        opt = st.session_state.w_opt
        desc_input = st.session_state.w_desc
        amt = st.session_state.w_amt
        typ = st.session_state.w_type
        cat = st.session_state.w_cat
        debt = st.session_state.w_debt
        ddl = st.session_state.w_date if debt else None
        note = st.session_state.w_note
        final_desc = desc_input if opt == "➕ Mới..." else opt

        if amt > 0 and final_desc:
            # LƯU THỜI GIAN HIỆN TẠI (Full datetime)
            now = dt_class.now() # Lấy ngày giờ hiện tại
            
            row = {
                "ngay": str(now), # Lưu chuỗi ISO đầy đủ
                "muc": final_desc, "so_tien": amt,
                "loai": typ, "phan_loai": cat,
                "han_tra": str(ddl) if debt else None,
                "trang_thai": "Đang nợ" if debt else "Đã xong",
                "ghi_chu": note
            }
            add_trans(row)
            st.toast("Đã lưu thành công!", icon="✅")
            st.session_state.w_amt = 0; st.session_state.w_desc = ""; st.session_state.w_note = ""
            st.session_state.w_debt = False; st.session_state.w_opt = "➕ Mới..."
        else: st.toast("Thiếu thông tin!", icon="⚠️")

    with st.sidebar:
        st.title("⚡ Menu")
        if st.button("🔄 Tải lại"): st.cache_data.clear(); st.rerun()
        if st.button("🔒 Đăng xuất"): st.session_state.logged_in = False; st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "⏳ SỔ NỢ", "⚙️ CÀI ĐẶT"])

    with tab1:
        if not df.empty:
            inc = df[df['loai']=='Thu']['so_tien'].sum(); exp = df[df['loai']=='Chi']['so_tien'].sum(); bal = inc - exp
            c1, c2, c3 = st.columns(3)
            c1.metric("Thu", f"{inc:,.0f}"); c2.metric("Chi", f"{exp:,.0f}"); c3.metric("Dư", f"{bal:,.0f}")
        st.divider()
        c_left, c_right = st.columns([1, 1.5], gap="medium")
        with c_left:
            with st.container():
                st.subheader("➕ Giao dịch")
                hist = df['muc'].unique().tolist() if not df.empty else []
                if hist: hist.reverse()
                st.selectbox("Nội dung", ["➕ Mới..."] + hist, key="w_opt")
                if st.session_state.w_opt == "➕ Mới...": st.text_input("Tên mục:", key="w_desc")
                st.number_input("Số tiền:", step=50000, key="w_amt")
                c1, c2 = st.columns(2)
                with c1: st.radio("Loại:", ["Chi", "Thu"], key="w_type")
                with c2: st.selectbox("Mục:", st.session_state.categories, key="w_cat")
                st.checkbox("Vay/Nợ?", key="w_debt")
                if st.session_state.w_debt: st.date_input("Hạn:", key="w_date")
                st.text_input("Note:", key="w_note")
                st.button("LƯU GIAO DỊCH 🚀", type="primary", on_click=save_callback, use_container_width=True)

        with c_right:
            with st.container():
                st.subheader("📈 Phân tích")
                if not df.empty:
                    exp_df = df[(df['loai']=='Chi') & (df['phan_loai']!='Cho vay')]
                    if not exp_df.empty:
                        chart_data = exp_df.groupby('phan_loai')['so_tien'].sum().reset_index()
                        base = alt.Chart(chart_data).encode(theta=alt.Theta("so_tien", stack=True))
                        pie = base.mark_arc(innerRadius=60, outerRadius=100, cornerRadius=5).encode(
                            color=alt.Color("phan_loai", scale=alt.Scale(scheme='turbo'), legend=None),
                            order=alt.Order("so_tien", sort="descending"), tooltip=["phan_loai", "so_tien"]
                        )
                        text = base.mark_text(radius=120, fill="#00f2c3").encode(text=alt.Text("so_tien", format=",.0f"), order=alt.Order("so_tien", sort="descending"))
                        final_chart = (pie + text).properties(background='transparent').configure_view(strokeWidth=0)
                        st.altair_chart(final_chart, use_container_width=True)
                        st.write("---")
                        for idx, row in chart_data.sort_values('so_tien', ascending=False).iterrows():
                            st.markdown(f"<div style='display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 5px 0;'><span style='color: #ccc;'>{row['phan_loai']}</span><span style='color: #00f2c3; font-weight: bold;'>{row['so_tien']:,.0f} đ</span></div>", unsafe_allow_html=True)
                    else: st.info("Chưa có dữ liệu chi tiêu.")
                else: st.info("Dữ liệu trống.")

        st.divider()
        with st.container():
            st.subheader("📅 Lịch sử & Chỉnh sửa")
            if not df.empty:
                col_date, col_view = st.columns([1, 2])
                with col_date: filter_date = st.date_input("Xem ngày:", date.today())
                with col_view: view_mode = st.radio("Chế độ:", ["Chỉ ngày này", "Tất cả"], horizontal=True)
                
                # Lọc dữ liệu
                if view_mode == "Chỉ ngày này":
                    # Lọc theo ngày (so sánh phần date của cột 'ngay')
                    df_filtered = df[df['ngay'].dt.date == filter_date].copy()
                else:
                    df_filtered = df.copy()

                if not df_filtered.empty:
                    df_filtered['Xóa?'] = False
                    
                    # --- CẤU HÌNH HIỂN THỊ ĐẸP (FORMAT DD-MM-YY | HH:MM) ---
                    edited_df = st.data_editor(
                        df_filtered,
                        column_config={
                            "id": None,
                            # FORMAT QUAN TRỌNG Ở ĐÂY:
                            "ngay": st.column_config.DatetimeColumn(
                                "Thời gian",
                                format="DD-MM-YY | HH:mm",
                                step=60
                            ),
                            "muc": "Mục",
                            "so_tien": st.column_config.NumberColumn("Số tiền", format="%d đ"),
                            "loai": st.column_config.SelectboxColumn("Loại", options=["Thu", "Chi"]),
                            "phan_loai": st.column_config.SelectboxColumn("Nhóm", options=st.session_state.categories),
                            "trang_thai": st.column_config.SelectboxColumn("Status", options=["Đã xong", "Đang nợ"]),
                            "Xóa?": st.column_config.CheckboxColumn("❌ Xóa?")
                        },
                        use_container_width=True, hide_index=True, key="history_editor"
                    )

                    if st.button("💾 CẬP NHẬT THAY ĐỔI", type="primary", use_container_width=True):
                        to_delete = edited_df[edited_df['Xóa?'] == True]['id'].tolist()
                        if to_delete: del_trans_list(to_delete); st.toast(f"Đã xóa {len(to_delete)} dòng!")
                        
                        rows_to_update = edited_df[edited_df['Xóa?'] == False]
                        count_update = 0
                        for index, row in rows_to_update.iterrows():
                            original_row = df[df['id'] == row['id']].iloc[0]
                            # So sánh nếu có thay đổi
                            if (str(row['ngay']) != str(original_row['ngay']) or row['muc'] != original_row['muc'] or
                                row['so_tien'] != original_row['so_tien'] or row['loai'] != original_row['loai'] or
                                row['phan_loai'] != original_row['phan_loai'] or row['trang_thai'] != original_row['trang_thai'] or
                                row['ghi_chu'] != original_row['ghi_chu']):
                                
                                update_data = {
                                    "ngay": str(row['ngay']), "muc": row['muc'], "so_tien": row['so_tien'],
                                    "loai": row['loai'], "phan_loai": row['phan_loai'],
                                    "trang_thai": row['trang_thai'], "ghi_chu": row['ghi_chu']
                                }
                                update_trans(row['id'], update_data)
                                count_update += 1
                        
                        if count_update > 0: st.toast(f"Đã cập nhật {count_update} dòng!")
                        time.sleep(1); st.rerun()
                else: st.info(f"Không có giao dịch ngày {filter_date}")
            else: st.info("Chưa có dữ liệu.")

    with tab2:
        st.subheader("Sổ Nợ")
        if not df.empty:
            d = df[df['trang_thai']=='Đang nợ']
            if not d.empty:
                for i, r in d.iterrows():
                    clr = "#ff4b4b" if r['loai']=='Thu' else "#00f2c3"
                    t = f"🔴 BẠN NỢ: {r['muc']}" if r['loai']=='Thu' else f"🟢 HỌ NỢ BẠN: {r['muc']}"
                    st.markdown(f"<div style='border-left: 4px solid {clr}; background: rgba(255,255,255,0.05); padding: 15px; margin-bottom: 10px; border-radius: 8px;'><b style='color:{clr}; font-size: 1.1em;'>{t}</b> <br>💰 <span style='color: #fff; font-weight: bold;'>{r['so_tien']:,} đ</span> <br>📅 Hạn: {r['han_tra']} <br><i style='color: #aaa; font-size: 0.9em;'>Note: {r['ghi_chu']}</i></div>", unsafe_allow_html=True)
            else: st.success("Sạch nợ!")

    with tab3:
        st.subheader("Danh mục")
        c1, c2 = st.columns(2)
        with c1: 
            n = st.text_input("Thêm:"); 
            if st.button("Thêm mục"): add_cat(n); st.rerun()
        with c2: 
            d = st.selectbox("Xóa:", st.session_state.categories); 
            if st.button("Xóa mục"): del_cat(d); st.rerun()

login_system()
main_app()
