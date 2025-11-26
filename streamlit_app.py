import streamlit as st
import pandas as pd
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

# --- 2. CSS CƠ BẢN (CHỈ MÀU SẮC, KHÔNG CAN THIỆP HÌNH DÁNG) ---
def load_css():
    st.markdown("""
    <style>
        /* Nền tối dễ chịu */
        .stApp {
            background-color: #0e1117;
            color: #fff;
        }
        /* Ẩn Header mặc định */
        header {visibility: hidden;}
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
        }
        
        /* Tùy chỉnh nhẹ cho Metric */
        div[data-testid="stMetric"] {
            background-color: #262730;
            border: 1px solid #464b5f;
            border-radius: 8px;
            padding: 10px;
        }
        
        /* --- KHÔNG CÓ CSS CAN THIỆP VÀO BUTTON --- */
        /* Để nút bấm hiển thị mặc định của Streamlit (Hình chữ nhật bo góc) */
    </style>
    """, unsafe_allow_html=True)
load_css()

# --- 3. LOGIC DATABASE ---
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
        cats = [x['ten_danh_muc'] for x in cat_res.data] if cat_res.data else ["Ăn uống", "Khác"]
        return df, cats
    except: return pd.DataFrame(), []

def add_trans(row): supabase.table('transactions').insert(row).execute()
def del_trans(tid): supabase.table('transactions').delete().eq('id', tid).execute()
def add_cat(name): supabase.table('categories').insert({"ten_danh_muc": name}).execute()
def del_cat(name): supabase.table('categories').delete().eq('ten_danh_muc', name).execute()

# --- 4. HỆ THỐNG ĐĂNG NHẬP (ĐƠN GIẢN HÓA) ---
def login_system():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: return True
    if "pin_buffer" not in st.session_state: st.session_state.pin_buffer = ""

    # Lấy PIN từ DB
    def get_pin_db():
        try:
            res = supabase.table('app_config').select("value").eq("key", "user_pin").execute()
            return res.data[0]['value'] if res.data else None
        except: return None
    
    def set_pin_db(val):
        supabase.table('app_config').upsert({"key": "user_pin", "value": val}).execute()

    stored_pin = get_pin_db()

    # Giao diện Login căn giữa
    _, col_main, _ = st.columns([1, 5, 1])
    with col_main:
        st.markdown("<h1 style='text-align: center;'>🔐 SmartWallet</h1>", unsafe_allow_html=True)
        
        # Hiển thị số đang nhập (Dạng text đơn giản)
        curr = st.session_state.pin_buffer
        mask = "● " * len(curr) + "_ " * (4 - len(curr))
        st.markdown(f"<h2 style='text-align: center; color: #00f2c3; letter-spacing: 5px;'>{mask}</h2>", unsafe_allow_html=True)

        if stored_pin is None:
            st.info("🆕 Nhập 4 số để tạo PIN mới")

        st.markdown("---")

        # --- BÀN PHÍM SỐ (2 Hàng x 5 Cột) ---
        # Cách này đảm bảo hiển thị tốt nhất trên mobile
        
        def press(num):
            if len(st.session_state.pin_buffer) < 4:
                st.session_state.pin_buffer += num
        
        def clear(): st.session_state.pin_buffer = ""
        def back(): st.session_state.pin_buffer = st.session_state.pin_buffer[:-1]

        # Hàng 1: Từ 0 đến 4
        c0, c1, c2, c3, c4 = st.columns(5)
        with c0: st.button("0", on_click=press, args="0", use_container_width=True)
        with c1: st.button("1", on_click=press, args="1", use_container_width=True)
        with c2: st.button("2", on_click=press, args="2", use_container_width=True)
        with c3: st.button("3", on_click=press, args="3", use_container_width=True)
        with c4: st.button("4", on_click=press, args="4", use_container_width=True)

        # Hàng 2: Từ 5 đến 9
        c5, c6, c7, c8, c9 = st.columns(5)
        with c5: st.button("5", on_click=press, args="5", use_container_width=True)
        with c6: st.button("6", on_click=press, args="6", use_container_width=True)
        with c7: st.button("7", on_click=press, args="7", use_container_width=True)
        with c8: st.button("8", on_click=press, args="8", use_container_width=True)
        with c9: st.button("9", on_click=press, args="9", use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Hàng chức năng: Xóa - Backspace - OK
        b1, b2, b3 = st.columns(3)
        with b1: st.button("❌ Xóa hết", on_click=clear, use_container_width=True)
        with b2: st.button("⬅️ Xóa 1", on_click=back, use_container_width=True)
        
        # Logic Kiểm tra
        if len(curr) == 4:
            with b3:
                if stored_pin is None:
                    if st.button("💾 Lưu PIN", type="primary", use_container_width=True):
                        set_pin_db(curr)
                        st.success("Đã tạo PIN!")
                        time.sleep(1)
                        st.session_state.logged_in = True
                        st.rerun()
                else:
                    if curr == stored_pin:
                         # Tự động login nếu đúng (Hoặc bấm nút này)
                        if st.button("🚀 Vào App", type="primary", use_container_width=True):
                            st.session_state.logged_in = True
                            st.rerun()
                    else:
                        st.error("Sai PIN")
                        if st.button("Thử lại"):
                            st.session_state.pin_buffer = ""
                            st.rerun()

    st.stop()

# --- 5. APP CHÍNH ---
def main_app():
    df, cats = load_data()
    st.session_state.categories = cats

    # Sidebar
    with st.sidebar:
        st.header("SmartWallet")
        if st.button("🔄 Tải lại dữ liệu"): st.cache_data.clear(); st.rerun()
        if st.button("🔒 Đăng xuất"): st.session_state.logged_in = False; st.rerun()

    # Tab
    tab1, tab2, tab3 = st.tabs(["DASHBOARD", "SỔ NỢ", "CẤU HÌNH"])

    # --- TAB 1: NHẬP LIỆU & BÁO CÁO ---
    with tab1:
        if not df.empty:
            inc = df[df['loai']=='Thu']['so_tien'].sum()
            exp = df[df['loai']=='Chi']['so_tien'].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng Thu", f"{inc:,.0f}")
            c2.metric("Tổng Chi", f"{exp:,.0f}")
            c3.metric("Số Dư", f"{inc-exp:,.0f}")
        
        st.divider()
        
        # Form nhập liệu (Dùng st.container để gom nhóm)
        with st.container(border=True):
            st.subheader("Nhập giao dịch")
            
            # Gợi ý lịch sử
            hist = df['muc'].unique().tolist() if not df.empty else []
            if hist: hist.reverse()
            opt = st.selectbox("Nội dung", ["➕ Mới..."] + hist, key="w_opt")
            desc = st.text_input("Tên mục:", key="w_desc") if opt == "➕ Mới..." else opt
            
            amount = st.number_input("Số tiền:", step=50000, key="w_amt")
            
            c1, c2 = st.columns(2)
            with c1: type_ = st.radio("Loại:", ["Chi", "Thu"], horizontal=True, key="w_type")
            with c2: cat = st.selectbox("Mục:", st.session_state.categories, key="w_cat")
            
            is_debt = st.checkbox("Vay/Nợ?", key="w_debt")
            ddl = st.date_input("Hạn:", key="w_date") if is_debt else None
            note = st.text_input("Ghi chú:", key="w_note")

            # Nút Lưu Bình Thường (Không còn bị tròn nữa)
            if st.button("Lưu Giao Dịch", type="primary", use_container_width=True):
                if amount > 0:
                    row = {
                        "ngay": str(date.today()), "muc": desc, "so_tien": amount,
                        "loai": type_, "phan_loai": cat,
                        "han_tra": str(ddl) if is_debt else None,
                        "trang_thai": "Đang nợ" if is_debt else "Đã xong",
                        "ghi_chu": note
                    }
                    add_trans(row)
                    st.toast("Đã lưu!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Nhập số tiền > 0")

        st.divider()
        st.subheader("Lịch sử")
        if not df.empty:
            st.dataframe(df[['id', 'ngay', 'muc', 'so_tien', 'loai']].sort_values('id', ascending=False).head(5), use_container_width=True, hide_index=True)
            
            with st.expander("Xóa giao dịch"):
                del_id = st.selectbox("Chọn ID:", df.sort_values('id', ascending=False)['id'].unique())
                if st.button("Xóa ngay"):
                    del_trans(int(del_id))
                    st.success("Đã xóa")
                    time.sleep(1)
                    st.rerun()

    # --- TAB 2: SỔ NỢ ---
    with tab2:
        if not df.empty:
            debt = df[df['trang_thai']=='Đang nợ']
            if not debt.empty:
                st.dataframe(debt, use_container_width=True)
            else: st.success("Không có nợ!")

    # --- TAB 3: CẤU HÌNH ---
    with tab3:
        st.subheader("Danh mục chi tiêu")
        col_new, col_del = st.columns(2)
        with col_new:
            new_c = st.text_input("Thêm mục:")
            if st.button("Thêm"):
                add_cat(new_c); st.rerun()
        with col_del:
            del_c = st.selectbox("Xóa mục:", st.session_state.categories)
            if st.button("Xóa"):
                del_cat(del_c); st.rerun()

# Chạy App
login_system()
main_app()
