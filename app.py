import streamlit as st
import pandas as pd
import re
import io

def process_text(full_text):
    """
    Xử lý văn bản thô, trích xuất các cặp task Tiếng Anh và Hướng dẫn Tiếng Việt.
    LOGIC MỚI (Validate):
    - Tách Anh/Việt bằng 'Hướng dẫn'.
    - Khối T.Anh PHẢI chứa 'Source:' VÀ 'deliverable(s)'.
    - Khối T.Việt PHẢI chứa 'Kết quả'.
    - Lấy TOÀN BỘ khối nếu hợp lệ.
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

        # 3. Tách Anh/Việt bằng "Hướng dẫn"
        parts = re.split(r'\n*(H[ưƯ]ớng dẫn[\s\S]*)', block, maxsplit=1, flags=re.IGNORECASE)
        
        english_text_full = ""
        vietnamese_text_full = ""
        
        if len(parts) > 1:
            # Tìm thấy "Hướng dẫn".
            english_text_full = parts[0].strip()
            vietnamese_text_full = parts[1].strip() # Bắt đầu bằng "Hướng dẫn"
        else:
            # Không tìm thấy "Hướng dẫn". Toàn bộ block là Tiếng Anh.
            english_text_full = parts[0].strip()
            vietnamese_text_full = ""

        extracted_english = ""
        extracted_vietnamese = ""

        # 4. TRÍCH XUẤT (Extract) khối Tiếng Anh
        if english_text_full:
            # [TRÍCH XUẤT] Tìm 'Source:' và lấy mọi thứ SAU nó
            en_match = re.search(r'(Source:[\s\S]*)', english_text_full, re.IGNORECASE)
            if en_match:
                # Tìm thấy 'Source:', lấy toàn bộ
                extracted_english = en_match.group(1).strip()
                
                # [VALIDATE] Kiểm tra 'deliverable(s)'
                # re.IGNORECASE không cần .lower()
                if not re.search(r'deliverables?:', extracted_english, re.IGNORECASE):
                    extracted_english = "ENGLISH_EXTRACT_FAIL (Không tìm thấy 'Deliverable:')"
            else:
                extracted_english = "ENGLISH_EXTRACT_FAIL (Không tìm thấy 'Source:')"
        else:
            extracted_english = "ENGLISH_EXTRACT_FAIL (Trống)"


        # 5. TRÍCH XUẤT (Extract) khối Tiếng Việt
        if vietnamese_text_full:
            # [TRÍCH XUẤT] Đã có 'Hướng dẫn' (từ bước 3), lấy toàn bộ
            extracted_vietnamese = vietnamese_text_full.strip()
            
            # [VALIDATE] Kiểm tra 'Kết quả'
            if not re.search(r'Kết quả', extracted_vietnamese, re.IGNORECASE):
                extracted_vietnamese = "VIETNAMESE_EXTRACT_FAIL (Không tìm thấy 'Kết quả')"
        else:
            # Không có 'Hướng dẫn'
            extracted_vietnamese = "" # Rỗng (bình thường)

        
        # 6. Dọn dẹp thẻ ``` ở cuối (nếu có)
        # (Văn bản của bạn có thẻ ``` ở đầu và cuối khối code)
        extracted_english = re.sub(r'\n```\n?$', '', extracted_english).strip()
        extracted_english = re.sub(r'^```\n?', '', extracted_english).strip()
        
        extracted_vietnamese = re.sub(r'\n```\n?$', '', extracted_vietnamese).strip()
        extracted_vietnamese = re.sub(r'^```\n?', '', extracted_vietnamese).strip()


        # 7. Chỉ thêm vào output nếu có gì đó
        if extracted_english or extracted_vietnamese:
             output_data.append([extracted_english, extracted_vietnamese])

    if not output_data:
        # Lỗi này xảy ra nếu input hoàn toàn rỗng hoặc chỉ có '-----'
        return None, "Không tìm thấy nội dung. Đảm bảo văn bản có chứa 'Source:' hoặc 'Hướng dẫn'."

    # 8. Tạo DataFrame
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
st.title("Công cụ Tách Task (Phiên bản Validate)")

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
