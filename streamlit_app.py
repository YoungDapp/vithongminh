import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import date
import os

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Ví Thông Thái Pro", layout="wide", page_icon="💎")
st.title("💎 Ví Thông Thái - Hệ thống Quản trị Tài chính")

# --- FILE DỮ LIỆU ---
TRANS_FILE = "dulieu_giaodich.csv"
CAT_FILE = "dulieu_danhmuc.csv"

# --- HÀM HỖ TRỢ ĐỌC/GHI FILE ---
def load_data():
    # 1. Tải Giao dịch
    if os.path.exists(TRANS_FILE):
        df = pd.read_csv(TRANS_FILE)
        df['Ngày'] = pd.to_datetime(df['Ngày']).dt.date
        df['Hạn trả'] = pd.to_datetime(df['Hạn trả'], errors='coerce').dt.date
    else:
        df = pd.DataFrame(columns=['Ngày', 'Mục', 'Số tiền', 'Loại', 'Phân loại', 'Hạn trả', 'Trạng thái', 'Ghi chú'])
    
    # 2. Tải Danh mục
    if os.path.exists(CAT_FILE):
        cats_df = pd.read_csv(CAT_FILE)
        cats = cats_df['Danh mục'].tolist()
    else:
        cats = ["Ăn uống", "Di chuyển", "Cố định", "Mua sắm", "Lương", "Đi vay", "Cho vay", "Khác"]
    
    return df, cats

def save_transactions():
    st.session_state.data.to_csv(TRANS_FILE, index=False)

def save_categories():
    pd.DataFrame(st.session_state.categories, columns=['Danh mục']).to_csv(CAT_FILE, index=False)

# --- KHỞI TẠO SESSION STATE ---
if 'data' not in st.session_state:
    df_loaded, cats_loaded = load_data()
    st.session_state.data = df_loaded
    st.session_state.categories = cats_loaded

# Khởi tạo các biến widget (để tránh lỗi Callback)
defaults = {
    'widget_new_desc': "",
    'widget_deadline': date.today(),
    'widget_amount': 0,
    'widget_note': "",
    'widget_is_debt': False
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- HÀM CALLBACK (LƯU & RESET) ---
def save_transaction_callback():
    # Lấy dữ liệu từ widget
    amount = st.session_state.widget_amount
    desc_option = st.session_state.widget_desc_select
    new_desc = st.session_state.get('widget_new_desc', "")
    trans_type = st.session_state.widget_type
    category = st.session_state.widget_category
    is_debt = st.session_state.widget_is_debt
    note = st.session_state.widget_note
    
    # Xử lý nội dung
    final_description = new_desc if desc_option == "➕ Nhập nội dung mới..." else desc_option

    if amount > 0 and final_description:
        real_type = "Chi" if "Chi" in trans_type else "Thu"
        
        deadline_val = st.session_state.get('widget_deadline', date.today())
        deadline = deadline_val if is_debt else None
        status = "Đang nợ" if is_debt else "Đã xong"
        
        # Thêm vào DataFrame
        new_row = [date.today(), final_description, amount, real_type, category, deadline, status, note]
        st.session_state.data.loc[len(st.session_state.data)] = new_row
        
        # ===> LƯU RA FILE <===
        save_transactions()
        
        st.toast(f"✅ Đã lưu: {final_description}", icon="💾")
        
        # Reset Widget
        st.session_state.widget_amount = 0
        st.session_state.widget_new_desc = ""
        st.session_state.widget_note = ""
        st.session_state.widget_is_debt = False
        # Reset dropdown về mục đầu
        st.session_state.widget_desc_select = "➕ Nhập nội dung mới..." 
    else:
        st.toast("⚠️ Thiếu nội dung hoặc số tiền!", icon="RW")

# --- GIAO DIỆN CHÍNH ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Tổng quan", "📒 Sổ Nợ & Cảnh báo", "📝 Dữ liệu chi tiết", "⚙️ Cấu hình"])

# ==========================================
# TAB 1: NHẬP LIỆU & DASHBOARD
# ==========================================
with tab1:
    col_input, col_dash = st.columns([1, 2])
    
    # --- PHẦN NHẬP LIỆU ---
    with col_input:
        st.markdown("### ➕ Nhập giao dịch")
        
        # Logic gợi ý lịch sử
        history = st.session_state.data['Mục'].unique().tolist() if not st.session_state.data.empty else []
        if history: history.reverse()
        opt_list = ["➕ Nhập nội dung mới..."] + history
        
        st.selectbox("Nội dung", opt_list, key="widget_desc_select")
        
        # Hiện ô nhập tay nếu chọn mục đầu
        if st.session_state.widget_desc_select == "➕ Nhập nội dung mới...":
            st.text_input("Gõ tên khoản mục:", key="widget_new_desc")
            
        st.number_input("Số tiền (VNĐ)", min_value=0, step=50000, key="widget_amount")
        
        c1, c2 = st.columns(2)
        with c1: st.radio("Loại", ["Chi (Tiền đi)", "Thu (Tiền về)"], key="widget_type")
        with c2: st.selectbox("Phân loại", st.session_state.categories, key="widget_category")
        
        st.checkbox("Theo dõi Vay/Nợ?", key="widget_is_debt")
        if st.session_state.widget_is_debt:
            st.date_input("Hạn xử lý", key="widget_deadline")
            
        st.text_input("Ghi chú", key="widget_note")
        
        st.button("Lưu Giao Dịch", type="primary", use_container_width=True, on_click=save_transaction_callback)

    # --- PHẦN DASHBOARD ---
    with col_dash:
        df = st.session_state.data
        if not df.empty:
            # 1. Metrics
            inc = df[df['Loại']=='Thu']['Số tiền'].sum()
            exp = df[df['Loại']=='Chi']['Số tiền'].sum()
            balance = inc - exp
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Tổng Thu", f"{inc:,.0f}")
            m2.metric("Tổng Chi", f"{exp:,.0f}", delta=f"-{exp:,.0f}", delta_color="inverse")
            m3.metric("Số Dư", f"{balance:,.0f}")
            
            st.divider()
            
            # 2. Biểu đồ (Khôi phục Altair chart)
            st.subheader("📈 Phân bổ chi tiêu")
            exp_df = df[(df['Loại'] == 'Chi') & (df['Phân loại'] != 'Cho vay')]
            
            if not exp_df.empty:
                chart_data = exp_df.groupby('Phân loại')['Số tiền'].sum().reset_index()
                
                c_chart1, c_chart2 = st.columns(2)
                with c_chart1:
                    # Biểu đồ tròn
                    pie = alt.Chart(chart_data).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta("Số tiền", stack=True),
                        color="Phân loại",
                        tooltip=["Phân loại", "Số tiền"]
                    ).properties(height=250)
                    st.altair_chart(pie, use_container_width=True)
                
                with c_chart2:
                    # Biểu đồ cột
                    bar = alt.Chart(exp_df).mark_bar().encode(
                        x='sum(Số tiền)',
                        y=alt.Y('Phân loại', sort='-x'),
                        color='Phân loại',
                        tooltip=['Phân loại', 'sum(Số tiền)']
                    ).properties(height=250)
                    st.altair_chart(bar, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu chi tiêu để vẽ biểu đồ.")
        else:
            st.info("👋 Chào mừng! Hãy nhập giao dịch đầu tiên bên tay trái.")

# ==========================================
# TAB 2: SỔ NỢ (LOGIC CẢNH BÁO MÀU SẮC)
# ==========================================
with tab2:
    st.header("⏳ Theo dõi Vay & Nợ")
    df = st.session_state.data
    
    if not df.empty:
        # Lọc các khoản đang nợ
        debt_df = df[df['Trạng thái'] == 'Đang nợ'].copy()
        
        # Tính tổng nợ
        my_debt = debt_df[debt_df['Loại'] == 'Thu']['Số tiền'].sum() # Mình vay người ta
        other_debt = debt_df[debt_df['Loại'] == 'Chi']['Số tiền'].sum() # Người ta vay mình
        
        col_d1, col_d2 = st.columns(2)
        col_d1.error(f"❌ Mình đang nợ: {my_debt:,.0f} đ")
        col_d2.success(f"✅ Người ta nợ mình: {other_debt:,.0f} đ")
        
        st.divider()
        
        if not debt_df.empty:
            today = date.today()
            st.subheader("⚠️ Cảnh báo hạn trả")
            
            for index, row in debt_df.iterrows():
                if pd.notnull(row['Hạn trả']):
                    days_left = (row['Hạn trả'] - today).days
                    msg = f"[{row['Loại']}] **{row['Mục']}**: {row['Số tiền']:,} đ (Hạn: {row['Hạn trả']})"
                    
                    if days_left < 0:
                        st.error(f"QUÁ HẠN {abs(days_left)} NGÀY: {msg}")
                    elif days_left <= 3:
                        st.warning(f"GẤP (Còn {days_left} ngày): {msg}")
                    else:
                        st.info(f"Sắp tới (Còn {days_left} ngày): {msg}")
        else:
            st.success("Tuyệt vời! Sổ nợ sạch sẽ.")

# ==========================================
# TAB 3: DATA EDITOR (EXCEL STYLE)
# ==========================================
with tab3:
    st.info("💡 Bạn có thể sửa xóa trực tiếp tại đây. Dữ liệu tự động lưu sau khi sửa.")
    
    # Editor cho phép sửa, xóa, thêm dòng
    edited_df = st.data_editor(
        st.session_state.data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Số tiền": st.column_config.NumberColumn(format="%d đ"),
            "Phân loại": st.column_config.SelectboxColumn(options=st.session_state.categories),
            "Loại": st.column_config.SelectboxColumn(options=["Thu", "Chi"]),
            "Trạng thái": st.column_config.SelectboxColumn(options=["Đang nợ", "Đã xong"]),
            "Ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Hạn trả": st.column_config.DateColumn(format="DD/MM/YYYY"),
        },
        key="main_editor"
    )
    
    # Logic lưu khi bảng thay đổi
    if not edited_df.equals(st.session_state.data):
        st.session_state.data = edited_df
        save_transactions()
        st.rerun()

# ==========================================
# TAB 4: CẤU HÌNH DANH MỤC
# ==========================================
with tab4:
    st.subheader("🛠 Quản lý Phân loại chi tiêu")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.write("**Danh sách hiện tại:**")
        st.write(st.session_state.categories)
        
        cat_to_del = st.selectbox("Chọn danh mục muốn xóa:", st.session_state.categories)
        if st.button("Xóa danh mục"):
            if len(st.session_state.categories) > 1:
                st.session_state.categories.remove(cat_to_del)
                save_categories() # Lưu file ngay
                st.success(f"Đã xóa {cat_to_del}")
                st.rerun()
            else:
                st.error("Không thể xóa hết danh mục!")

    with col_c2:
        st.write("**Thêm danh mục mới:**")
        new_cat = st.text_input("Nhập tên danh mục (VD: Đầu tư, Đám cưới...)")
        if st.button("Thêm ngay"):
            if new_cat and new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                save_categories() # Lưu file ngay
                st.success(f"Đã thêm {new_cat}")
                st.rerun()
            elif new_cat in st.session_state.categories:
                st.warning("Danh mục này đã có rồi!")
