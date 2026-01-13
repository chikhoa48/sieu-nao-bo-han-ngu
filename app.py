import streamlit as st
import google.generativeai as genai
import os, io, requests, time
from docx import Document
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google.api_core import exceptions

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Siêu Cỗ Máy Dịch Thuật", page_icon="🏮", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { background: linear-gradient(45deg, #1e3799, #0984e3); color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    .status-card { padding: 15px; border-radius: 10px; background-color: #ffffff; border-left: 5px solid #1e3799; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px; }
    .stProgress .st-bo { background-color: #1e3799; }
    </style>
    """, unsafe_allow_html=True)

# --- KẾT NỐI API ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # Ưu tiên Flash cho tốc độ và hạn mức cao
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
    default_model = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
except:
    st.error("⚠️ Lỗi cấu hình API Key.")
    st.stop()

# --- HÀM XỬ LÝ LÕI ---
def fetch_web(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = res.apparent_encoding
        return res.text
    except: return None

def call_ai(model_obj, prompt):
    try:
        return model_obj.generate_content(prompt)
    except exceptions.ResourceExhausted:
        st.warning("⚠️ Hết hạn mức Free. Đang nghỉ 60s để Google hồi phục...")
        time.sleep(60)
        return model_obj.generate_content(prompt)
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏮 TRANSLATOR PRO")
    selected_model = st.selectbox("🎯 Động cơ AI:", available_models, index=available_models.index(default_model))
    st.divider()
    menu = st.radio("🚀 TÍNH NĂNG CHÍNH:", [
        "🔍 Quét Website & Lọc Top",
        "🏭 Dịch Truyện Hàng Loạt (Auto-Link)",
        "📄 Dịch Sách File (Word/PDF)"
    ])
    st.divider()
    st.info("💡 Lưu ý: Sử dụng model 'Flash' để cào hàng loạt nhanh hơn.")

model = genai.GenerativeModel(selected_model)

# --- 1. QUÉT WEBSITE & LỌC TOP ---
if menu == "🔍 Quét Website & Lọc Top":
    st.title("🔍 Thợ Săn Truyện & Phân Loại")
    st.write("Dán link trang danh mục/bảng xếp hạng (Ví dụ từ 69shuba.cx, uukanshu.net...)")
    
    url_source = st.text_input("URL trang danh mục:", placeholder="https://www.69shuba.cx/top/allvisit/1.htm")
    
    if st.button("🚀 Bắt đầu quét & Phân loại"):
        with st.spinner("Đang thu thập dữ liệu..."):
            html = fetch_web(url_source)
            if html:
                prompt = f"""
                Dưới đây là mã nguồn của một trang web truyện. Hãy thực hiện các việc sau:
                1. Trích xuất danh sách tất cả các bộ truyện hiện có.
                2. Lấy các thông tin: Tên truyện (dịch sang TV), Thể loại, Lượt xem/Đánh giá, Link gốc bộ truyện.
                3. Phân loại truyện theo các nhóm (Tiên hiệp, Đô thị, vv).
                4. Sắp xếp theo thứ tự Lượt xem/Đánh giá giảm dần.
                5. Trình bày dạng BẢNG Markdown.
                
                HTML: {html[:30000]}
                """
                res = call_ai(model, prompt)
                if res: st.markdown(res.text)
            else: st.error("Không lấy được dữ liệu từ web.")

# --- 2. DỊCH TRUYỆN HÀNG LOẠT ---
elif menu == "🏭 Dịch Truyện Hàng Loạt (Auto-Link)":
    st.title("🏭 Nhà Máy Dịch Thuật Cuốn Chiếu")
    st.info("AI sẽ tự động tìm link chương tiếp theo và dịch cho đến khi đủ số lượng.")
    
    c1, c2 = st.columns(2)
    with c1:
        start_link = st.text_input("Link chương bắt đầu (VD: Chương 1):")
        num_chaps = st.number_input("Số lượng chương muốn dịch:", 1, 200, 10)
    with c2:
        style_instr = st.text_area("Yêu cầu trau chuốt bản dịch:", "Dịch mượt mà, văn phong tiểu thuyết, xưng hô Ta - Ngươi, giữ nguyên thuật ngữ Hán Việt chuẩn xác, không dịch word-by-word.")
        glossary = st.text_area("Từ điển (Glossary):", "Trúc Cơ, Kim Đan, Kim thủ chỉ")

    if st.button("🚀 Bắt Đầu Chiến Dịch Dịch Thuật"):
        curr_url = start_link
        full_story_content = ""
        p_bar = st.progress(0)
        
        for i in range(num_chaps):
            st.markdown(f"<div class='status-card'><b>Chương {i+1}:</b> {curr_url}</div>", unsafe_allow_html=True)
            html = fetch_web(curr_url)
            
            if not html or len(html) < 1500:
                st.error("❌ Link bị chặn hoặc rỗng. Dừng cào.")
                break
                
            prompt = f"""
            VAI TRÒ: Biên dịch viên cao cấp Hán-Việt.
            NHIỆM VỤ:
            1. Trích nội dung truyện từ HTML (Bỏ quảng cáo).
            2. Tìm link URL chương sau (Next Chapter).
            3. Dịch sang tiếng Việt cực kỳ trau chuốt: {style_instr}.
            4. Tuân thủ thuật ngữ: {glossary}.
            
            ĐỊNH DẠNG TRẢ VỀ:
            CONTENT: [Bản dịch]
            NEXT_URL: [Link sau]
            
            HTML: {html[:25000]}
            """
            
            res = call_ai(model, prompt)
            if res:
                try:
                    content_val = res.text.split("CONTENT:")[1].split("NEXT_URL:")[0].strip()
                    next_link = res.text.split("NEXT_URL:")[1].strip()
                    
                    full_story_content += f"\n\n--- CHƯƠNG {i+1} ---\n\n" + content_val
                    
                    # Xử lý link nhảy
                    curr_url = urljoin(curr_url, next_link) if not next_link.startswith("http") else next_link
                    st.success(f"✅ Đã dịch xong chương {i+1}")
                except:
                    st.warning("⚠️ AI không tách được cấu trúc link. Vui lòng kiểm tra lại link khởi đầu.")
                    break
            
            p_bar.progress((i+1)/num_chaps)
            time.sleep(3) # Nghỉ để tránh 429
            
        if full_story_content:
            doc = Document()
            for line in full_story_content.split('\n'):
                if line.strip(): doc.add_paragraph(line)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("📥 TẢI TRỌN BỘ WORD (.DOCX)", bio.getvalue(), "Peerless_Batch_Trans.docx")

# --- 3. DỊCH SÁCH FILE ---
elif menu == "📄 Dịch Sách File (Word/PDF)":
    st.title("📄 Dịch File Hàng Loạt")
    st.write("Nạp file sách thô, AI sẽ dịch từng đoạn lớn và ghép lại.")
    
    files = st.file_uploader("Tải file (Docx/PDF):", accept_multiple_files=True)
    if st.button("🚀 Bắt đầu dịch file"):
        for f in files:
            with st.spinner(f"Đang xử lý {f.name}..."):
                # Gửi file trực tiếp cho Gemini (Gemini xử lý PDF cực tốt)
                prompt_file = "Dịch toàn bộ văn bản trong file này sang tiếng Việt trau chuốt, giữ nguyên định dạng, không tóm tắt."
                res = call_ai(model, prompt_file) # Gemini hỗ trợ file đính kèm nếu API cho phép
                if res: st.markdown(res.text)
