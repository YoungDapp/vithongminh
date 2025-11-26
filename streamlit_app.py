import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import date
import json
import time
from supabase import create_client, Client

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="SmartWallet Cloud", layout="wide", page_icon="☁️")

# --- 2. KẾT NỐI SUPABASE ---
# Lấy key từ Streamlit Secrets
try:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("❌ Chưa cấu hình Supabase Secret! Vào Settings trên Streamlit Cloud để thêm.")
    st.stop()

# --- 3. CSS UI (GIỮ NGUYÊN) ---
def load_css():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        div[data-testid="stMetric"] {
            background-color: #ffffff; border-left: 5px solid #4CAF50;
            padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton button { border-radius: 20px; font-weight: 600; }
        .stButton button[kind="primary"] {
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%); border: none;
        }
    </style>
    """, unsafe_allow_html=True)
load_css()

# --- 4. HÀM XỬ LÝ DỮ LIỆU (SUPABASE) ---

# @st.cache_data(ttl=60) # Cache 60s để đỡ load lại liên tục, bỏ comment nếu muốn nhanh hơn
def load_data():
    """Tải dữ liệu từ Supabase về DataFrame"""
    try:
        # 1. Lấy Giao dịch
        response = supabase.table('transactions').select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            df['ngay'] = pd.to_datetime(df['ngay']).dt.date
            df['han_tra'] = pd.to_datetime(df['han_tra'], errors='coerce').dt.date
        else:
            # Tạo khung rỗng nếu chưa có dữ liệu
            df = pd.DataFrame(columns=['id', 'ngay', 'muc', 'so_tien', 'loai', 'phan_loai', 'han_tra', 'trang_thai', 'ghi_chu'])

        # 2. Lấy Danh mục
        cat_res = supabase.table('categories').select("*").execute()
        cats_df = pd.DataFrame(cat_res.data)
        if not cats_df.empty:
            cats = cats_df['ten_danh_muc'].tolist()
        else:
            cats = ["Ăn uống", "Khác"] # Mặc định
            
        return df, cats
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame(), []

def add_transaction_db(row_dict):
    """Thêm giao dịch mới vào Supabase"""
    try:
        supabase.table('transactions').insert(row_dict).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi lưu: {e}")
        return False

def delete_transaction_db(ids_to_delete):
    """Xóa giao dịch theo ID"""
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

# --- 5. HỆ THỐNG BẢO MẬT (MÃ PIN LOCAL) ---
# Mã PIN này vẫn lưu Local Storage của trình duyệt/file tạm. 
# Để bảo mật tuyệt đối, bạn có thể lưu mã PIN lên Supabase luôn, nhưng ở đây ta giữ đơn giản.
CONFIG_FILE = "config.json"
def login_system():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: return True

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<br><h2 style='text-align: center;'>🔐 Ví Cloud</h2>", unsafe_allow_html=True)
        if not os.path.exists(CONFIG_FILE):
            st.warning("Thiết lập mã PIN lần đầu.")
            with st.form("setup"):
                p1 = st.text_input("PIN mới", type="password", max_chars=4)
                if st.form_submit_button("Lưu"):
                    with open(CONFIG_FILE, "w") as f: json.dump({"pin": p1}, f)
                    st.rerun()
        else:
            with st.form("login"):
                pin = st.text_input("Nhập PIN", type="password", max_chars=4)
                if st.form_submit_button("Mở khóa", type="primary"):
                    with open(CONFIG_FILE, "r") as f: stored = json.load(f).get("pin")
                    if pin == stored:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Sai mã PIN")
    st.stop()

# --- 6. APP CHÍNH ---
import os # Import lại để tránh lỗi

def main_app():
    # Sidebar
    with st.sidebar:
        st.title("☁️ Quản lý Ví")
        if st.button("🔄 Tải lại dữ liệu"):
            st.cache_data.clear() # Xóa cache để load mới
            st.rerun()
        if st.button("🔒 Đăng xuất"):
            st.session_state.logged_in = False
            st.rerun()

    # Load dữ liệu (Chạy mỗi khi reload trang)
    df, categories = load_data()
    st.session_state.categories = categories # Lưu vào session để dùng ở selectbox

    # --- CALLBACKS ---
    def save_callback():
        # Lấy an toàn
        amt = st.session_state.get("w_amt", 0)
        desc_opt = st.session_state.get("w_opt", "")
        new_desc = st.session_state.get("w_desc", "")
        final_desc = new_desc if desc_opt == "➕ Mục mới..." else desc_opt

        if amt > 0 and final_desc:
            # Chuẩn bị dữ liệu gửi lên Supabase
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
                # Reset form
                st.session_state.w_amt = 0
                if "w_desc" in st.session_state: st.session_state.w_desc = ""
                st.session_state.w_opt = "➕ Mục mới..."
                time.sleep(1)
                st.rerun() # Reload để bảng cập nhật dòng mới
        else:
            st.toast("Thiếu thông tin!", icon="⚠️")

    # --- UI ---
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "⏳ SỔ NỢ", "⚙️ CÀI ĐẶT"])

    with tab1:
        # Metrics
        if not df.empty:
            inc = df[df['loai']=='Thu']['so_tien'].sum()
            exp = df[df['loai']=='Chi']['so_tien'].sum()
            bal = inc - exp
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng Thu", f"{inc:,.0f}")
            c2.metric("Tổng Chi", f"{exp:,.0f}")
            c3.metric("Số Dư", f"{bal:,.0f}")
        
        st.divider()
        c_left, c_right = st.columns([1, 1.5], gap="medium")
        
        with c_left:
            with st.container(border=True):
                st.subheader("📝 Nhập liệu")
                
                # Logic chọn
                hist = df['muc'].unique().tolist() if not df.empty else []
                if hist: hist.reverse()
                st.selectbox("Nội dung", ["➕ Mục mới..."] + hist, key="w_opt")
                
                if st.session_state.w_opt == "➕ Mục mới...":
                    st.text_input("Tên mục:", key="w_desc")
                
                st.number_input("Số tiền:", step=50000, key="w_amt")
                
                c1, c2 = st.columns(2)
                with c1: st.radio("Loại:", ["Chi tiền", "Thu tiền"], key="w_type")
                with c2: st.selectbox("Nhóm:", st.session_state.categories, key="w_cat")
                
                st.checkbox("Vay/Nợ?", key="w_debt")
                if st.session_state.get("w_debt"): st.date_input("Hạn:", key="w_date")
                st.text_input("Ghi chú:", key="w_note")
                
                st.button("LƯU LÊN CLOUD", type="primary", on_click=save_callback, use_container_width=True)

        with c_right:
            st.subheader("📜 Lịch sử gần đây")
            if not df.empty:
                # Hiển thị bảng rút gọn
                st.dataframe(
                    df[['ngay', 'muc', 'so_tien', 'loai', 'phan_loai']].sort_values(by='ngay', ascending=False).head(10),
                    use_container_width=True, hide_index=True
                )
                
                # Nút xóa
                with st.expander("🗑 Xóa giao dịch"):
                    del_id = st.selectbox("Chọn giao dịch để xóa:", df.sort_values(by='id', ascending=False)['id'].astype(str) + " - " + df['muc'], key="del_select")
                    if st.button("Xóa vĩnh viễn"):
                        real_id = int(del_id.split(" - ")[0])
                        if delete_transaction_db([real_id]):
                            st.success("Đã xóa!")
                            time.sleep(1)
                            st.rerun()

    with tab2:
        st.subheader("Quản lý Nợ")
        if not df.empty:
            debt_df = df[df['trang_thai'] == 'Đang nợ']
            if not debt_df.empty:
                st.dataframe(debt_df, use_container_width=True)
            else:
                st.success("Không có khoản nợ nào.")

    with tab3:
        st.write("Quản lý Danh mục (Lưu trên Server)")
        c1, c2 = st.columns(2)
        with c1:
            new_c = st.text_input("Thêm danh mục:")
            if st.button("Thêm"):
                if add_category_db(new_c): st.rerun()
        with c2:
            del_c = st.selectbox("Xóa danh mục:", st.session_state.categories)
            if st.button("Xóa"):
                if delete_category_db(del_c): st.rerun()

# Chạy App
login_system()
main_app()
