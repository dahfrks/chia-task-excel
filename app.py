import streamlit as st
import pandas as pd
import re
import io

def process_text(full_text):
    """
    Xử lý văn bản thô, trích xuất (CẮT) các phần cụ thể.
    LOGIC MỚI (v8 - Lấy hết, Dừng ở Separator):
    - Tách Biến thể (Variant) bằng '---' HOẶC '-----'.
    - T.Anh: Lấy TẤT CẢ từ 'Source:' DỪNG LẠI TRƯỚC 'Hướng dẫn'.
    - T.Việt: Lấy TẤT CẢ từ 'Hướng dẫn'
    - Dọn dẹp các dấu '---' hoặc '-----' ở cuối.
    """
    if not full_text:
        return None, "Lỗi: Văn bản đầu vào trống."

    # 1. Tách các BLOCKS BIẾN THỂ (Thử cả hai kiểu)
    # Tách bằng ----- (dùng cho 10-variant data)
    variation_blocks = re.split(r'\n*-----\n*', full_text)
    
    # Nếu không tách được (chỉ có 1 block), thử tách bằng '---' (dùng cho 5-variant data)
    if len(variation_blocks) == 1:
        # (?=...) là positive lookahead, nó đảm bảo '---' được theo sau bởi 'Source:'
        variation_blocks = re.split(r'\n---\n*(?=(?:###\s*)?Source:)', full_text, flags=re.IGNORECASE)

    output_data = []

    # 2. Lặp qua TỪNG block (mỗi block là 1 variant)
    for block in variation_blocks:
        block = block.strip()
        if not block:
            continue
            
        # 3. [LOGIC MỚI] Tách Anh/Việt
        # Tách block này thành 2 phần: Tiếng Anh và Tiếng Việt
        # Điểm tách là 'Hướng dẫn'
        parts = re.split(r'\n*(H[ưƯ]ớng dẫn[\s\S]*)', block, maxsplit=1, flags=re.IGNORECASE)
        
        english_text_full = ""
        vietnamese_text_full = ""
        
        if len(parts) > 1:
            english_text_full = parts[0].strip() # Phần trước 'Hướng dẫn'
            vietnamese_text_full = parts[1].strip() # Phần từ 'Hướng dẫn'
        else:
            english_text_full = parts[0].strip() # Không có 'Hướng dẫn'
            vietnamese_text_full = ""

        extracted_english = ""
        extracted_vietnamese = ""

        # 4. [LOGIC MỚI] Trích xuất Tiếng Anh
        # Lấy TẤT CẢ từ 'Source:'
        if english_text_full:
            # 'english_text_full' là mọi thứ TRƯỚC 'Hướng dẫn'
            # Chúng ta chỉ cần tìm 'Source:'
            
            en_match = re.search(r'(Source:[\s\S]*)', english_text_full, re.IGNORECASE)
            
            if en_match:
                extracted_english = en_match.group(1).strip()
                # Dọn dẹp dấu tách '---' (của 5-variant) nếu nó nằm TRƯỚC 'Hướng dẫn'
                extracted_english = re.split(r'\n---', extracted_english, maxsplit=1)[0].strip()
            else:
                extracted_english = "ENGLISH_FAIL (Không tìm thấy 'Source:')"
        else:
            # Trường hợp block bắt đầu bằng '### Hướng dẫn'
            if vietnamese_text_full: # Chỉ báo lỗi nếu có T.Việt
                extracted_english = "ENGLISH_FAIL (Trống)"
            else:
                extracted_english = "" # Block rỗng

        # 5. [LOGIC MỚI] Trích xuất Tiếng Việt
        # Lấy TẤT CẢ từ 'Hướng dẫn'
        if vietnamese_text_full:
            # 'vietnamese_text_full' đã bắt đầu bằng 'Hướng dẫn'
            # Chúng ta không cần search, chỉ cần dọn dẹp dấu tách (nếu có) ở cuối
            
            # Dọn dẹp dấu tách thừa (--- hoặc -----) ở cuối
            extracted_vietnamese = re.split(r'\n---|\n-----', vietnamese_text_full, maxsplit=1)[0].strip()
        else:
            extracted_vietnamese = "" # Rỗng (bình thường)

        
        # 6. Dọn dẹp thẻ ``` (nếu có)
        extracted_english = re.sub(r'(^```\n?|\n```\n?$)', '', extracted_english).strip()
        extracted_vietnamese = re.sub(r'(^```\n?|\n```\n?$)', '', extracted_vietnamese).strip()

        # 7. Chỉ thêm vào output nếu có gì đó
        if extracted_english or extracted_vietnamese:
             # Bỏ qua các Fails rỗng
             if extracted_english.startswith("ENGLISH_FAIL") and not extracted_vietnamese:
                 continue # Bỏ qua nếu T.Anh lỗi VÀ T.Việt rỗng
             else:
                output_data.append([extracted_english, extracted_vietnamese])


    if not output_data:
        # Nếu block đầu vào có 'Source:' nhưng TÁCH sai, output_data sẽ rỗng.
        if re.search(r'Source:', full_text, re.IGNORECASE):
             return None, "Lỗi Tách Biến Thể (Variant Split). Kiểm tra dấu '---' hoặc '-----' của bạn."
        return None, "Không tìm thấy nội dung. Đảm bảo văn bản có 'Source:'."

    # 8. Tạo DataFrame
    df = pd.DataFrame(output_data, columns=['English Task', 'Vietnamese Guide'])
    return df, f"Xử lý thành công. Tìm thấy {len(df)} cặp task."

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tasks')
    processed_data = output.getvalue()
    return processed_data

def to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# ----- Giao diện ứng dụng Streamlit -----

st.set_page_config(layout="wide")
st.title("Công cụ Tách Task (v8 - Lấy Hết / Dừng ở Separator)")

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
            excel_data = to_excel(df)
            col1.download_button(
                label="Tải về file Excel (.xlsx)",
                data=excel_data,
                file_name="extracted_tasks.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            csv_data = to_csv(df)
            col2.download_button(
                label="Tải về file CSV (.csv)",
                data=csv_data,
                file_name="extracted_tasks.csv",
                mime="text/csv"
            )
        else:
            st.error(message)
    else:
        st.warning("Vui lòng dán nội dung vào ô bên trên.")
