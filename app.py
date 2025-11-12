import streamlit as st
import pandas as pd
import re
import io

def process_text(full_text):
    """
    Xử lý văn bản thô, trích xuất các cặp task Tiếng Anh và Hướng dẫn Tiếng Việt.
    Logic này được cập nhật để TRÍCH XUẤT (extract) thay vì DỌN DẸP (clean).
    - Cột 1: Bắt đầu từ 'Source:'
    - Cột 2: Bắt đầu từ 'Hướng dẫn'
    """
    if not full_text:
        return None, "Lỗi: Văn bản đầu vào trống."

    # 1. Tách các BLOCKS BIẾN THỂ bằng "-----"
    variation_blocks = re.split(r'\n*-----\n*', full_text)
    
    output_data = []

    # 2. Lặp qua TỪNG block
    for block in variation_blocks:
        block = block.strip()
        if not block:
            continue

        # 3. Tách Tiếng Anh và Tiếng Việt bằng "---"
        parts = re.split(r'\n---\n', block, maxsplit=1)
        
        if len(parts) == 2:
            english_text_full = parts[0]
            vietnamese_text_full = parts[1]

            # 4. TRÍCH XUẤT (Extract) khối Tiếng Anh
            # Tìm 'Source:' (không phân biệt hoa thường) và lấy mọi thứ sau nó.
            # Điều này tự động bỏ qua '### Biến thể...' và '```' ở đầu.
            en_match = re.search(r'(Source:[\s\S]*)', english_text_full, re.IGNORECASE)
            
            if en_match:
                extracted_english = en_match.group(1).strip()
                # Dọn dẹp thẻ ``` ở cuối nếu có
                extracted_english = re.sub(r'\n```\n?$', '', extracted_english).strip()
            else:
                extracted_english = "ENGLISH_EXTRACT_FAIL (Không tìm thấy 'Source:')"


            # 5. TRÍCH XUẤT (Extract) khối Tiếng Việt
            # Tìm 'Hướng dẫn' (không phân biệt hoa thường) và lấy mọi thứ sau nó.
            # Điều này tự động bỏ qua '```' ở đầu (nếu có).
            vi_match = re.search(r'(H[ưƯ]ớng dẫn[\s\S]*)', vietnamese_text_full, re.IGNORECASE)
            
            if vi_match:
                extracted_vietnamese = vi_match.group(1).strip()
                # Dọn dẹp thẻ ``` ở cuối nếu có
                extracted_vietnamese = re.sub(r'\n```\n?$', '', extracted_vietnamese).strip()
            else:
                extracted_vietnamese = "VIETNAMESE_EXTRACT_FAIL (Không tìm thấy 'Hướng dẫn')"

            
            output_data.append([extracted_english, extracted_vietnamese])

    if not output_data:
        return None, "Không tìm thấy task. Kiểm tra lại định dạng (----- và ---)."

    # 6. Tạo DataFrame
    df = pd.DataFrame(output_data, columns=['English Task', 'Vietnamese Guide'])
    return df, f"Xử lý thành công. Tìm thấy {len(df)} cặp task."

def to_excel(df):
    """
    Chuyển đổi DataFrame sang định dạng Excel (xlsx) trong bộ nhớ.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tasks')
    
    processed_data = output.getvalue()
    return processed_data

def to_csv(df):
    """
    Chuyển đổi DataFrame sang định dạng CSV (UTF-8) trong bộ nhớ.
    """
    return df.to_csv(index=False).encode('utf-8')

# ----- Giao diện ứng dụng Streamlit -----

st.set_page_config(layout="wide")
st.title("Công cụ Tách Task (Phiên bản Trích xuất)")

st.header("1. Dán nội dung (Paste Content)")
full_text = st.text_area(
    "Dán toàn bộ nội dung (bao gồm '### Biến thể 1...' và tất cả các biến thể) vào đây:", 
    height=350,
    label_visibility="collapsed"
)

if st.button("Xử lý (Process)", type="primary"):
    if full_text:
        # Xử lý văn bản
        df, message = process_text(full_text)
        
        if df is not None:
            st.success(message)
            
            st.header("2. Xem trước 5 hàng đầu tiên")
            st.dataframe(df.head())
            
            st.header("3. Tải về (Download)")
            
            col1, col2 = st.columns(2)
            
            # Tạo dữ liệu Excel
            excel_data = to_excel(df)
            col1.download_button(
                label="Tải về file Excel (.xlsx)",
                data=excel_data,
                file_name="extracted_tasks.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Tạo dữ liệu CSV
            csv_data = to_csv(df)
            col2.download_button(
                label="Tải về file CSV (.csv)",
                data=csv_data,
                file_name="extracted_tasks.csv",
                mime="text/csv"
            )
            
        else:
            # Hiển thị lỗi (ví dụ: không tìm thấy task)
            st.error(message)
    else:
        # Nếu người dùng chưa dán gì
        st.warning("Vui lòng dán nội dung vào ô bên trên.")