import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import date
import os
import json
import time

# --- 1. CẤU HÌNH TRANG (PHẢI Ở DÒNG ĐẦU TIÊN) ---
st.set_page_config(page_title="SmartWallet Pro", layout="wide", page_icon="💳")

# --- FILE DỮ LIỆU ---
TRANS_FILE = "dulieu_giaodich.csv"
CAT_FILE = "dulieu_danhmuc.csv"
CONFIG_FILE = "config.json"

# --- 2. CSS CAO CẤP (GLASSMORPHISM UI) ---
def load_css():
    st.markdown("""
    <style>
        /* Nền Gradient toàn trang */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        /* Ẩn Header mặc định của Streamlit */
        header[data-testid="stHeader"] {
            visibility: hidden;
        }
        
        /* Hiệu ứng kính (Glassmorphism) cho các Container */
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
            /* background: rgba(255, 255, 255, 0.7); */
            /* backdrop-filter: blur(10px); */
            /* border-radius: 15px; */
            /* padding: 20px; */
            /* box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15); */
        }

        /* Style cho Metric (Thẻ số) */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border-left: 5px solid #4CAF50;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* Nút bấm (Button) đẹp hơn */
        .stButton button {
            border-radius: 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        /* Nút Primary (Lưu) */
        .stButton button[kind="primary"] {
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            border: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .stButton button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }

        /* Nút Đăng xuất (Màu đỏ) */
        button[data-testid="baseButton-secondary"] {
            border-color: #ff4b4b;
            color: #ff4b4b;
        }
        button[data-testid="baseButton-secondary"]:hover {
            background-color: #ff4b4b;
            color: white;
        }

        /* Tab Menu */
        .stTabs [data-baseweb="tab-list"] {
            background-color: white;
            padding: 10px;
            border-radius: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 20px;
            padding: 8px 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #e8f5e9;
            color: #2e7d32;
            font-weight: bold;
        }
        
        /* Form Login đẹp */
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- 3. HỆ THỐNG BẢO MẬT (ĐÃ FIX LỖI) ---
def login_system():
    # Kiểm tra Session State
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Nếu ĐÃ đăng nhập -> Trả về True để chạy App
    if st.session_state.logged_in:
        return True

    # Nếu CHƯA đăng nhập -> Hiện Form
    col_spacer1, col_login, col_spacer2 = st.columns([1, 1, 1]) # Căn giữa
    
    with col_login:
        st.markdown("<br><br><br>", unsafe_allow_html=True) # Khoảng trống
        st.markdown("<h1 style='text-align: center; color: #333;'>🔐 Ví Thông Thái</h1>", unsafe_allow_html=True)
        
        # Kiểm tra xem đã có file Config chưa
        if not os.path.exists(CONFIG_FILE):
            st.warning("⚠️ Lần đầu sử dụng: Hãy tạo mã PIN mới.")
            with st.form("setup_form"):
                pin1 = st.text_input("Tạo mã PIN (4 số)", type="password", max_chars=4)
                pin2 = st.text_input("Nhập lại mã PIN", type="password", max_chars=4)
                submit_setup = st.form_submit_button("Lưu & Vào App", use_container_width=True)
                
                if submit_setup:
                    if len(pin1) == 4 and pin1.isdigit() and pin1 == pin2:
                        with open(CONFIG_FILE, "w") as f:
                            json.dump({"pin": pin1}, f)
                        st.session_state.logged_in = True
                        st.success("Tạo PIN thành công!")
                        st.rerun()
                    else:
                        st.error("Mã PIN không khớp hoặc không đủ 4 số!")
        else:
            # ĐÃ CÓ PIN -> ĐĂNG NHẬP
            with st.form("login_form"):
                st.write("Nhập mã PIN để mở khóa:")
                input_pin = st.text_input("Mã PIN", type="password", max_chars=4)
                submit_login = st.form_submit_button("🔓 MỞ KHÓA", type="primary", use_container_width=True)
                
                if submit_login:
                    with open(CONFIG_FILE, "r") as f:
                        stored_pin = json.load(f).get("pin")
                    
                    if input_pin == stored_pin:
                        st.session_state.logged_in = True
                        st.toast("Đăng nhập thành công!", icon="🎉")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ SAI MÃ PIN! Vui lòng thử lại.")
    
    # Dừng chương trình tại đây nếu chưa đăng nhập
    st.stop() 

# --- 4. HÀM XỬ LÝ DỮ LIỆU ---
def load_data():
    if os.path.exists(TRANS_FILE):
        df = pd.read_csv(TRANS_FILE)
        df['Ngày'] = pd.to_datetime(df['Ngày']).dt.date
        df['Hạn trả'] = pd.to_datetime(df['Hạn trả'], errors='coerce').dt.date
    else:
        # Dữ liệu mẫu
        data_mau = [
            [date.today(), "Lương tháng", 20000000, "Thu", "Lương", None, "Đã xong", "Demo"],
            [date.today(), "Tiền nhà", 5000000, "Chi", "Cố định", None, "Đã xong", "Demo"],
        ]
        df = pd.DataFrame(data_mau, columns=['Ngày', 'Mục', 'Số tiền', 'Loại', 'Phân loại', 'Hạn trả', 'Trạng thái', 'Ghi chú'])
        df.to_csv(TRANS_FILE, index=False)
    
    if os.path.exists(CAT_FILE):
        cats = pd.read_csv(CAT_FILE)['Danh mục'].tolist()
    else:
        cats = ["Ăn uống", "Di chuyển", "Cố định", "Mua sắm", "Lương", "Đi vay", "Cho vay", "Khác"]
        pd.DataFrame(cats, columns=['Danh mục']).to_csv(CAT_FILE, index=False)
    return df, cats

def save_data():
    st.session_state.data.to_csv(TRANS_FILE, index=False)
    pd.DataFrame(st.session_state.categories, columns=['Danh mục']).to_csv(CAT_FILE, index=False)

# --- 5. GIAO DIỆN CHÍNH (APP) ---
def main_app():
    # --- SIDEBAR (THANH BÊN TRÁI) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1077/1077114.png", width=80) # Icon ví tiền
        st.title("Smart Wallet")
        st.caption("Quản lý tài chính cá nhân")
        
        st.divider()
        
        # Nút ĐĂNG XUẤT TO VÀ RÕ RÀNG
        if st.button("🔒 KHÓA ỨNG DỤNG NGAY", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
        st.info("💡 Mẹo: Nhập liệu đều đặn để quản lý tốt hơn.")

    # --- KHỞI TẠO DỮ LIỆU ---
    if 'data' not in st.session_state:
        df_l, cat_l = load_data()
        st.session_state.data = df_l
        st.session_state.categories = cat_l

    # Init Widgets
    defaults = {'w_desc': "", 'w_amt': 0, 'w_note': "", 'w_debt': False, 'w_date': date.today()}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

   # --- CALLBACK LƯU (ĐÃ SỬA LỖI ATTRIBUTE ERROR) ---
    def save_cb():
        # Lấy giá trị an toàn bằng .get() để tránh lỗi khi ô nhập bị ẩn
        amt = st.session_state.get("w_amt", 0)
        desc_opt = st.session_state.get("w_opt", "")
        
        # DÒNG QUAN TRỌNG ĐÃ SỬA: Dùng .get() thay vì gọi trực tiếp
        new_desc = st.session_state.get("w_desc", "")
        
        final = new_desc if desc_opt == "➕ Mục mới..." else desc_opt
        
        if amt > 0 and final:
            # Lấy các thông số khác
            w_type = st.session_state.get("w_type", "Chi")
            w_cat = st.session_state.get("w_cat", "Khác")
            w_debt = st.session_state.get("w_debt", False)
            w_date = st.session_state.get("w_date", date.today())
            w_note = st.session_state.get("w_note", "")

            row = [
                date.today(), final, amt,
                "Thu" if "Thu" in w_type else "Chi",
                w_cat,
                w_date if w_debt else None,
                "Đang nợ" if w_debt else "Đã xong",
                w_note
            ]
            st.session_state.data.loc[len(st.session_state.data)] = row
            save_data()
            st.toast("Đã lưu thành công!", icon="✅")
            
            # Reset Form (Dùng safe reset)
            st.session_state.w_amt = 0
            if "w_desc" in st.session_state: st.session_state.w_desc = "" # Chỉ xóa nếu nó đang hiện
            if "w_note" in st.session_state: st.session_state.w_note = ""
            if "w_debt" in st.session_state: st.session_state.w_debt = False
            st.session_state.w_opt = "➕ Mục mới..."
        else:
            st.toast("Thiếu thông tin!", icon="⚠️")

    # --- TABS GIAO DIỆN ---
    tab1, tab2, tab3 = st.tabs(["📊 TỔNG QUAN", "📒 SỔ NỢ", "⚙️ CÀI ĐẶT"])

    # TAB 1: DASHBOARD
    with tab1:
        # 1. Thẻ số liệu (Cards)
        df = st.session_state.data
        inc = df[df['Loại']=='Thu']['Số tiền'].sum()
        exp = df[df['Loại']=='Chi']['Số tiền'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng Thu Nhập", f"{inc:,.0f} đ")
        c2.metric("Tổng Chi Tiêu", f"{exp:,.0f} đ", delta=f"-{exp:,.0f}", delta_color="inverse")
        c3.metric("Số Dư Hiện Tại", f"{(inc-exp):,.0f} đ")

        st.markdown("---")
        
        # 2. Layout Nhập & Biểu đồ
        col_left, col_right = st.columns([1, 1.5], gap="medium")
        
        with col_left:
            with st.container(border=True):
                st.subheader("📝 Nhập Giao Dịch")
                
                # Logic chọn lịch sử
                hist = df['Mục'].unique().tolist() if not df.empty else []
                if hist: hist.reverse()
                
                st.selectbox("Nội dung", ["➕ Mục mới..."] + hist, key="w_opt")
                if st.session_state.w_opt == "➕ Mục mới...":
                    st.text_input("Tên mục chi tiêu:", key="w_desc", placeholder="VD: Ăn trưa...")
                
                st.number_input("Số tiền (VNĐ):", min_value=0, step=50000, key="w_amt")
                
                cc1, cc2 = st.columns(2)
                with cc1: st.radio("Loại giao dịch:", ["Chi tiền", "Thu tiền"], key="w_type")
                with cc2: st.selectbox("Danh mục:", st.session_state.categories, key="w_cat")
                
                st.checkbox("Theo dõi nợ?", key="w_debt")
                if st.session_state.w_debt:
                    st.date_input("Hạn xử lý:", key="w_date")
                
                st.text_input("Ghi chú:", key="w_note")
                
                st.button("LƯU NGAY", type="primary", use_container_width=True, on_click=save_cb)

        with col_right:
            with st.container(border=True):
                st.subheader("📈 Biểu đồ Chi Tiêu")
                exp_df = df[(df['Loại']=='Chi') & (df['Phân loại']!='Cho vay')]
                if not exp_df.empty:
                    chart_data = exp_df.groupby('Phân loại')['Số tiền'].sum().reset_index()
                    
                    # Biểu đồ tròn đẹp hơn
                    base = alt.Chart(chart_data).encode(theta=alt.Theta("Số tiền", stack=True))
                    pie = base.mark_arc(innerRadius=60, outerRadius=100, cornerRadius=5).encode(
                        color=alt.Color("Phân loại", scale=alt.Scale(scheme='tableau10')),
                        order=alt.Order("Số tiền", sort="descending"),
                        tooltip=["Phân loại", "Số tiền"]
                    )
                    text = base.mark_text(radius=120).encode(
                        text=alt.Text("Số tiền", format=",.0f"),
                        order=alt.Order("Số tiền", sort="descending")  
                    )
                    st.altair_chart(pie + text, use_container_width=True)
                else:
                    st.info("Chưa có dữ liệu chi tiêu.")

    # TAB 2: SỔ NỢ & DATA
    with tab2:
        st.subheader("Quản lý Vay & Nợ")
        debt_df = df[df['Trạng thái'] == 'Đang nợ']
        if not debt_df.empty:
            for i, row in debt_df.iterrows():
                # Card nợ tùy chỉnh
                color = "#ffebee" if row['Loại'] == 'Thu' else "#e8f5e9" # Đỏ nhạt nếu mình nợ, Xanh nhạt nếu nợ mình
                icon = "💸" if row['Loại'] == 'Thu' else "💰"
                txt = "Mình nợ" if row['Loại'] == 'Thu' else "Nợ mình"
                
                st.markdown(f"""
                <div style="background-color: {color}; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {'red' if row['Loại'] == 'Thu' else 'green'}">
                    <b>{icon} {txt}: {row['Mục']}</b> - {row['Số tiền']:,} đ <br>
                    <small>Hạn: {row['Hạn trả']} | Ghi chú: {row['Ghi chú']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Hiện tại không có khoản nợ nào!")

        st.divider()
        st.subheader("Dữ liệu chi tiết (Sửa trực tiếp)")
        edited = st.data_editor(
            df, 
            column_config={
                "Số tiền": st.column_config.NumberColumn(format="%d đ"),
                "Trạng thái": st.column_config.SelectboxColumn(options=["Đang nợ", "Đã xong"])
            },
            use_container_width=True, num_rows="dynamic"
        )
        if not edited.equals(df):
            st.session_state.data = edited
            save_data()
            st.rerun()

    # TAB 3: CÀI ĐẶT
    with tab3:
        st.write("Cấu hình danh mục")
        new_cat = st.text_input("Thêm danh mục mới:")
        if st.button("Thêm"):
            if new_cat and new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                save_data()
                st.rerun()
        
        st.write("Danh sách hiện tại (Chọn để xóa):")
        st.multiselect("Danh mục", st.session_state.categories, st.session_state.categories, disabled=True)

# --- CHẠY CHƯƠNG TRÌNH ---
# Gọi hàm login_system() trước. Chỉ khi hàm này trả về True thì main_app() mới được chạy.
login_system()
main_app()
