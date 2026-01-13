import streamlit as st
import google.generativeai as genai
import os, io, requests, time
import pandas as pd
from PIL import Image
from PyPDF2 import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google.api_core import exceptions

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hán Ngữ Thông Tuệ v6", page_icon="🐲", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #fdfaf6; }
    .stButton>button { background: linear-gradient(45deg, #1e3799, #0984e3); color: white; border-radius: 10px; font-weight: bold; }
    .lesson-box { padding: 20px; border-radius: 10px; border: 1px solid #dcdde1; background-color: #ffffff; margin-bottom: 20px; }
    .chinese-text { font-family: 'Noto Sans SC', sans-serif; color: #c0392b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- KẾT NỐI API ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
except:
    st.error("⚠️ Vui lòng cấu hình GEMINI_API_KEY trong Secrets.")
    st.stop()

# --- HÀM GỌI AI AN TOÀN ---
def call_ai(model_obj, prompt, img=None):
    try:
        if img: return model_obj.generate_content([prompt, img])
        return model_obj.generate_content(prompt)
    except exceptions.ResourceExhausted:
        st.warning("Hệ thống đang nghỉ ngơi (Hạn mức Free)... Vui lòng chờ 60s.")
        time.sleep(60)
        return None
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- HÀM CÀO WEB ---
def fetch_html(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = res.apparent_encoding
        return res.text
    except: return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🐲 SIÊU NÃO BỘ v6")
    selected_model = st.selectbox("🎯 Chọn Bộ Não:", available_models, index=0)
    st.divider()
    menu = st.radio("🚀 MENU CHỨC NĂNG:", [
        "🔍 Thợ Săn Truyện & Lọc Top",
        "🏭 Cào & Dịch Tự Động",
        "📄 Dịch File (Word/PDF/Ảnh)",
        "🎓 Học Viện Hán Ngữ Toàn Diện"
    ])

model = genai.GenerativeModel(selected_model)

# --- 1. THỢ SĂN TRUYỆN (SỬA LỖI LỌC) ---
if menu == "🔍 Thợ Săn Truyện & Lọc Top":
    st.title("🔍 Lọc Truyện Top & Phân Loại")
    url_cat = st.text_input("Dán link trang danh mục (VD: https://www.69shuba.cx/top/allvisit/1.htm):")
    
    if st.button("🚀 Quét & Sắp Xếp"):
        html = fetch_html(url_cat)
        if html:
            prompt = f"""
            Dưới đây là mã nguồn HTML của một trang web truyện Trung Quốc.
            Nhiệm vụ:
            1. Lọc ra danh sách 10-20 bộ truyện có trong trang.
            2. Với mỗi bộ truyện hãy lấy: Tên truyện (Dịch sang Tiếng Việt), Link gốc, Thể loại, Lượt xem/Đánh giá (nếu có).
            3. Sắp xếp kết quả theo độ hot (lượt xem cao nhất lên đầu).
            4. Trình bày dưới dạng BẢNG (Markdown table) gồm các cột: STT, Tên Truyện (VN), Thể Loại, Đánh Giá, Link Truyện.
            
            HTML: {html[:30000]}
            """
            res = call_ai(model, prompt)
            if res: st.markdown(res.text)
        else: st.error("Không thể lấy dữ liệu từ URL này.")

# --- 2. CÀO & DỊCH TỰ ĐỘNG (SỬA LỖI CÀO) ---
elif menu == "🏭 Cào & Dịch Tự Động":
    st.title("🏭 Cào Truyện Cuốn Chiếu")
    col1, col2 = st.columns(2)
    with col1:
        start_url = st.text_input("Link chương 1:")
        num_chaps = st.number_input("Số chương:", 1, 100, 5)
    with col2:
        style = st.text_area("Yêu cầu bản dịch:", "Dịch tiên hiệp cổ phong, xưng hô Ta - Ngươi.")
    
    if st.button("🚀 Bắt Đầu Dịch Hàng Loạt"):
        curr_url = start_url
        full_text = ""
        p_bar = st.progress(0)
        
        for i in range(num_chaps):
            st.write(f"📂 Đang xử lý: {curr_url}")
            html = fetch_html(curr_url)
            if not html: break
            
            # AI nhặt nội dung và tìm nút "Next"
            prompt = f"""
            Từ HTML này, hãy lấy:
            1. Nội dung văn bản chương truyện (bỏ qua rác/quảng cáo).
            2. Tìm link URL chương sau.
            3. Dịch nội dung sang TV mượt mà (Yêu cầu: {style}).
            
            Trả về dạng:
            CONTENT: [Bản dịch]
            NEXT_URL: [Link sau]
            
            HTML: {html[:25000]}
            """
            res = call_ai(model, prompt)
            if res:
                try:
                    content = res.text.split("CONTENT:")[1].split("NEXT_URL:")[0].strip()
                    next_url = res.text.split("NEXT_URL:")[1].strip()
                    full_text += f"\n\n--- CHƯƠNG {i+1} ---\n\n{content}"
                    curr_url = urljoin(curr_url, next_url)
                    st.success(f"Xong chương {i+1}")
                except: break
            p_bar.progress((i+1)/num_chaps)
            time.sleep(2)
            
        st.download_button("📥 Tải Word Trọn Bộ", io.BytesIO(b'content').getvalue(), "Truyen_Full.docx") # Placeholder

# --- 3. DỊCH FILE (PDF TEXT/ẢNH, WORD) ---
elif menu == "📄 Dịch File (Word/PDF/Ảnh)":
    st.title("📄 Dịch Tài Liệu Đa Định Dạng")
    files = st.file_uploader("Tải lên PDF (Text/Ảnh), DOCX, hoặc JPG/PNG:", accept_multiple_files=True)
    
    if st.button("🚀 Dịch Hàng Loạt"):
        for f in files:
            st.write(f"📄 Đang xử lý: {f.name}")
            if f.name.endswith(".pdf"):
                # Gửi thẳng file cho Gemini (hỗ trợ cả PDF ảnh)
                res = call_ai(model, "Dịch toàn bộ file PDF này sang Tiếng Việt mượt mà:", img=f)
                if res: st.markdown(res.text)
            elif f.name.endswith(".docx"):
                # Đọc docx đơn giản
                doc = Document(f)
                text = "\n".join([p.text for p in doc.paragraphs])
                res = call_ai(model, f"Dịch đoạn này sang TV: {text[:15000]}")
                if res: st.markdown(res.text)
            else: # Ảnh
                img = Image.open(f)
                res = call_ai(model, "Dịch chữ trong ảnh này sang TV:", img=img)
                if res: st.markdown(res.text)

# --- 4. HỌC VIỆN HÁN NGỮ ---
elif menu == "🎓 Học Viện Hán Ngữ Toàn Diện":
    st.title("🎓 Giáo Trình Học Tiếng Trung Cá Nhân")
    topic = st.text_input("Bạn muốn học chủ đề gì?")
    
    if st.button("📚 Tạo Bài Học"):
        prompt = f"""
        Tạo bài giảng về '{topic}'. 
        Yêu cầu:
        1. Giao tiếp hiện đại (5 câu).
        2. Bảng từ vựng: Chữ Hán | Pinyin | Hán Việt | Nghĩa.
        3. Hướng dẫn viết: Chọn 2 chữ khó, mô tả bút thuận (nét nào trước nét nào sau) và chiết tự mẹo nhớ.
        4. Ngữ pháp & Bài tập.
        """
        res = call_ai(model, prompt)
        if res: st.markdown(res.text)
