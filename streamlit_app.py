import streamlit as st
import pandas as pd
import altair as alt
import datetime
from datetime import date, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Ví Thông Thái Ultimate", layout="wide", page_icon="💰")
st.title("💰 Ví Thông Thái - Quản lý Chi tiêu & Sổ nợ")

# --- 1. KHỞI TẠO DỮ LIỆU ---
# Cấu trúc dữ liệu mới: Thêm 'Hạn trả' và 'Trạng thái'
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'Ngày', 'Mục', 'Số tiền', 'Loại', 'Phân loại', 'Hạn trả', 'Trạng thái', 'Ghi chú'
    ])
    
    # Dữ liệu mẫu (Có cả chi tiêu thường và nợ)
    sample_data = [
        [date.today(), "Lương tháng", 15000000, "Thu", "Lương", None, "Đã xong", "Nhận qua Bank"],
        [date.today(), "Tiền nhà", 3500000, "Chi", "Cố định", None, "Đã xong", ""],
        [date.today(), "Vay tiền bạn Tuấn", 2000000, "Thu", "Đi vay", date.today() + timedelta(days=5), "Đang nợ", "Hứa trả cuối tuần"],
        [date.today(), "Cho Lan mượn", 500000, "Chi", "Cho vay", date.today() + timedelta(days=3), "Đang nợ", "Mua mỹ phẩm"],
    ]
    for row in sample_data:
        st.session_state.data.loc[len(st.session_state.data)] = row

# Danh mục mặc định
if 'categories' not in st.session_state:
    st.session_state.categories = ["Ăn uống", "Di chuyển", "Cố định", "Mua sắm", "Lương", "Đi vay", "Cho vay", "Khác"]

# --- TẠO CÁC TAB CHỨC NĂNG ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Nhập liệu & Báo cáo", "📒 Sổ Nợ & Cảnh báo", "📝 Quản lý Chung", "⚙️ Cài đặt"])

# ==================================================
# TAB 1: NHẬP LIỆU & BÁO CÁO (ĐÃ FIX LỖI KHỞI TẠO)
# ==================================================
with tab1:
    col1, col2 = st.columns([1, 2])

    # --- 1. KHỞI TẠO BIẾN TRƯỚC (QUAN TRỌNG ĐỂ TRÁNH LỖI) ---
    # Phải đảm bảo các key này luôn tồn tại dù widget có hiện hay không
    if 'widget_new_desc' not in st.session_state:
        st.session_state.widget_new_desc = ""
    if 'widget_deadline' not in st.session_state:
        st.session_state.widget_deadline = date.today()
    
    # Chuẩn bị danh sách
    history_items = st.session_state.data['Mục'].unique().tolist()
    if history_items:
        history_items.reverse()
    option_list = ["➕ Nhập nội dung mới..."] + history_items

    # --- 2. HÀM CALLBACK (XỬ LÝ LƯU & RESET) ---
    def save_transaction_callback():
        # Lấy giá trị an toàn bằng .get() để tránh lỗi nếu key chưa kịp cập nhật
        amount = st.session_state.widget_amount
        desc_option = st.session_state.widget_desc_select
        
        # Lấy nội dung nhập tay (nếu có)
        new_desc = st.session_state.get('widget_new_desc', "")
        
        trans_type = st.session_state.widget_type
        category = st.session_state.widget_category
        is_debt = st.session_state.widget_is_debt
        note = st.session_state.widget_note
        
        # Xác định nội dung cuối cùng
        if desc_option == "➕ Nhập nội dung mới...":
            final_description = new_desc
        else:
            final_description = desc_option

        # Kiểm tra và Lưu
        if amount > 0 and final_description:
            real_type = "Chi" if "Chi" in trans_type else "Thu"
            
            # Lấy hạn trả (chỉ quan tâm nếu là nợ)
            # Dùng .get() cho deadline phòng trường hợp widget chưa hiện
            deadline_val = st.session_state.get('widget_deadline', date.today())
            deadline = deadline_val if is_debt else None
            status = "Đang nợ" if is_debt else "Đã xong"
            
            # Lưu vào DataFrame
            new_row = [date.today(), final_description, amount, real_type, category, deadline, status, note]
            st.session_state.data.loc[len(st.session_state.data)] = new_row
            
            st.toast(f"✅ Đã lưu: {final_description} - {amount:,} đ", icon="🎉")
            
            # RESET FORM
            st.session_state.widget_amount = 0
            st.session_state.widget_new_desc = ""
            st.session_state.widget_note = ""
            st.session_state.widget_is_debt = False
            # Reset dropdown về mục đầu tiên
            st.session_state.widget_desc_select = option_list[0] 
            
        else:
            st.toast("⚠️ Vui lòng nhập đủ Nội dung và Số tiền!", icon="RW")

    # --- 3. GIAO DIỆN NHẬP LIỆU ---
    with col1:
        st.markdown("### ➕ Nhập giao dịch mới")
        
        # Selectbox chọn nội dung
        st.selectbox("Nội dung", option_list, key="widget_desc_select")
        
        # Logic hiển thị ô nhập tay
        if st.session_state.widget_desc_select == "➕ Nhập nội dung mới...":
            st.text_input("Gõ nội dung:", placeholder="VD: Bún bò...", key="widget_new_desc")
        
        st.number_input("Số tiền", min_value=0, step=50000, key="widget_amount")
        
        c_type1, c_type2 = st.columns(2)
        with c_type1:
            st.radio("Loại", ["Chi (Tiền đi)", "Thu (Tiền về)"], key="widget_type")
        with c_type2:
            st.selectbox("Phân loại", st.session_state.categories, key="widget_category")
        
        # Checkbox Nợ
        st.checkbox("Đây là khoản vay/nợ?", key="widget_is_debt")
        
        # Logic hiển thị ngày hạn
        if st.session_state.widget_is_debt:
            st.date_input("Hạn cần trả/thu tiền", min_value=date.today(), key="widget_deadline")
        
        st.text_input("Ghi chú", key="widget_note")
        
        # Nút Lưu gọi Callback
        st.button("Lưu Giao Dịch", type="primary", use_container_width=True, on_click=save_transaction_callback)

    # --- 4. DASHBOARD (GIỮ NGUYÊN) ---
    with col2:
        df = st.session_state.data
        if not df.empty:
            total_thu = df[df['Loại'] == 'Thu']['Số tiền'].sum()
            total_chi = df[df['Loại'] == 'Chi']['Số tiền'].sum()
            
            my_debt = df[(df['Loại'] == 'Thu') & (df['Trạng thái'] == 'Đang nợ')]['Số tiền'].sum()
            others_debt = df[(df['Loại'] == 'Chi') & (df['Trạng thái'] == 'Đang nợ')]['Số tiền'].sum()

            m1, m2, m3 = st.columns(3)
            m1.metric("Số Dư Thực Tế", f"{(total_thu - total_chi):,.0f} đ")
            m2.metric("Đang Nợ (Phải trả)", f"{my_debt:,.0f} đ", delta="-Nợ", delta_color="inverse")
            m3.metric("Cho Vay (Phải thu)", f"{others_debt:,.0f} đ", delta="+Chờ thu")
            
            st.divider()
            st.caption("Biểu đồ chi tiêu (Không tính các khoản cho vay)")
            expense_df = df[(df['Loại'] == 'Chi') & (df['Phân loại'] != 'Cho vay')]
            if not expense_df.empty:
                chart = alt.Chart(expense_df).mark_bar().encode(
                    x='Số tiền',
                    y=alt.Y('Phân loại', sort='-x'),
                    color='Phân loại',
                    tooltip=['Ngày', 'Mục', 'Số tiền']
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu. Hãy nhập giao dịch đầu tiên!")
# ==================================================
# TAB 2: SỔ NỢ & CẢNH BÁO (TÍNH NĂNG MỚI)
# ==================================================
with tab2:
    st.header("⏳ Theo dõi Vay & Nợ")
    
    # Lọc ra các khoản đang nợ (chưa xong)
    debt_df = df[df['Trạng thái'] == 'Đang nợ'].copy()
    
    if debt_df.empty:
        st.success("Tuyệt vời! Hiện tại bạn không có khoản nợ nào cần xử lý.")
    else:
        # Cảnh báo hạn nợ
        st.subheader("⚠️ Cảnh báo hạn trả")
        today = date.today()
        
        for index, row in debt_df.iterrows():
            if row['Hạn trả']: # Nếu có set ngày hạn
                days_left = (row['Hạn trả'] - today).days
                msg = f"{row['Mục']} ({row['Số tiền']:,} đ)"
                
                if days_left < 0:
                    st.error(f"QUÁ HẠN: {msg} - Trễ {abs(days_left)} ngày!")
                elif days_left <= 3:
                    st.warning(f"SẮP ĐẾN HẠN: {msg} - Còn {days_left} ngày.")
                else:
                    st.info(f"Sắp tới: {msg} - Hạn: {row['Hạn trả']}")

        st.divider()
        st.subheader("Danh sách chi tiết")
        # Hiển thị bảng riêng cho nợ để dễ nhìn
        st.dataframe(
            debt_df[['Ngày', 'Mục', 'Số tiền', 'Loại', 'Hạn trả', 'Ghi chú']], 
            use_container_width=True
        )
        st.caption("💡 Để đánh dấu đã trả nợ, hãy sang Tab 'Quản lý Chung' và đổi Trạng thái thành 'Đã xong'.")

# ==================================================
# TAB 3: QUẢN LÝ CHUNG (SỬA/XÓA/CẬP NHẬT TRẠNG THÁI)
# ==================================================
with tab3:
    st.info("💡 Click đúp vào ô 'Trạng thái' để đổi từ 'Đang nợ' sang 'Đã xong' khi bạn đã trả/thu tiền.")
    
    edited_df = st.data_editor(
        st.session_state.data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Số tiền": st.column_config.NumberColumn(format="%d đ"),
            "Ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Hạn trả": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Loại": st.column_config.SelectboxColumn(options=["Thu", "Chi"]),
            "Trạng thái": st.column_config.SelectboxColumn(
                options=["Đang nợ", "Đã xong"],
                help="Chọn 'Đã xong' khi khoản nợ đã được thanh toán"
            ),
            "Phân loại": st.column_config.SelectboxColumn(options=st.session_state.categories),
        },
        key="main_editor"
    )
    
    if not edited_df.equals(st.session_state.data):
        st.session_state.data = edited_df
        st.rerun()

# ==================================================
# TAB 4: CÀI ĐẶT
# ==================================================
with tab4:
    st.write("Quản lý danh mục chi tiêu")
    current_cats = st.session_state.categories
    
    c1, c2 = st.columns(2)
    with c1:
        new_cat = st.text_input("Thêm danh mục mới")
        if st.button("Thêm"):
            if new_cat and new_cat not in current_cats:
                st.session_state.categories.append(new_cat)
                st.rerun()
    with c2:
        del_cat = st.selectbox("Xóa danh mục", current_cats)
        if st.button("Xóa"):
            if len(current_cats) > 1:
                st.session_state.categories.remove(del_cat)
                st.rerun()
