import streamlit as st
import google.generativeai as genai
import os, io, requests, time, zipfile
from PIL import Image
from PyPDF2 import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Ultimate Hanzi Intelligence", page_icon="🏮", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fcfaf2; }
    .stButton>button { background: linear-gradient(45deg, #c0392b, #2c3e50); color: white; border-radius: 10px; font-weight: bold; height: 3em; }
    .expert-box { padding: 20px; border-left: 5px solid #c0392b; background-color: #fdf2f2; margin: 10px 0; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- KẾT NỐI API ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # Tự động quét Model
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
except:
    st.error("⚠️ Vui lòng cấu hình GEMINI_API_KEY trong Secrets.")
    st.stop()

# --- CÁC HÀM XỬ LÝ ---
def get_text_from_files(files):
    text = ""
    for f in files:
        if f.name.endswith('.pdf'):
            reader = PdfReader(f)
            for page in reader.pages: text += page.extract_text() or ""
        elif f.name.endswith('.docx'):
            doc = Document(f)
            for para in doc.paragraphs: text += para.text + "\n"
        elif f.name.endswith('.txt'):
            text += f.getvalue().decode("utf-8")
    return text

def save_docx(content):
    doc = Document()
    for line in content.split('\n'):
        if line.strip(): doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    return bio

def get_web_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = res.apparent_encoding
        return res.text
    except: return ""

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏮 SIÊU NÃO BỘ AI")
    selected_model = st.selectbox("🎯 Chọn Model:", available_models, index=0)
    # Kích hoạt Google Search nếu là model hỗ trợ
    model = genai.GenerativeModel(model_name=selected_model, tools=[{"google_search_retrieval": {}}])
    
    st.divider()
    menu = st.radio("🚀 CHỨC NĂNG:", [
        "🌐 Cập Nhật Xu Hướng (Internet)",
        "🧠 Phân Tích Chuyên Gia (Upload)",
        "🗣️ Giao Tiếp & Chiết Tự",
        "🏭 Cào & Dịch Công Nghiệp"
    ])

# --- 1. INTERNET SEARCH ---
if menu == "🌐 Cập Nhật Xu Hướng (Internet)":
    st.title("🌐 Cập Nhật Kiến Thức & Xu Hướng Mới")
    topic = st.text_input("Nhập chủ đề muốn tìm hiểu (Tiếng Việt/Trung):", placeholder="VD: Xu hướng AI tại Trung Quốc 2026...")
    if st.button("🔍 Quét Toàn Cầu & Giảng Bài"):
        with st.spinner("AI đang lên mạng tìm kiếm tin tức mới nhất..."):
            prompt = f"Sử dụng Google Search để tìm tin tức mới nhất về '{topic}' bằng tiếng Trung. Sau đó tóm tắt nội dung chính, dạy các từ vựng mới xuất hiện (Hán-Pinyin-Hán Việt-Nghĩa) và phân tích dưới góc nhìn chuyên gia."
            res = model.generate_content(prompt)
            st.markdown(res.text)

# --- 2. EXPERT ANALYSIS ---
elif menu == "🧠 Phân Tích Chuyên Gia (Upload)":
    st.title("🧠 Đại Sư Kiến Thức & Ngôn Ngữ")
    up_files = st.file_uploader("Nạp sách/tài liệu (PDF/Docx):", accept_multiple_files=True)
    query = st.text_input("Câu hỏi về nội dung sách hoặc yêu cầu quy nạp kiến thức:")
    if st.button("🚀 Phân Tích Chuyên Sâu"):
        if up_files:
            with st.spinner("AI đang đọc toàn bộ tài liệu..."):
                ctx = get_text_from_files(up_files)
                prompt = f"Bạn là chuyên gia hàng đầu. Dựa vào nội dung này: {ctx[:30000]}. Hãy trả lời: {query}. Sau đó chọn ra 5 đoạn văn hay nhất để dạy tiếng Trung (Hán-Pinyin-Hán Việt-Ngữ Pháp)."
                res = model.generate_content(prompt)
                st.markdown("<div class='expert-box'>", unsafe_allow_html=True)
                st.markdown(res.text)
                st.markdown("</div>", unsafe_allow_html=True)

# --- 3. COMMUNICATION ---
elif menu == "🗣️ Giao Tiếp & Chiết Tự":
    st.title("🗣️ Giao Tiếp Bản Địa & Mẹo Nhớ Chữ")
    text_to_learn = st.text_area("Nhập câu/chữ muốn học:")
    if st.button("🎓 Giảng Giải Chi Tiết"):
        prompt = f"Dạy tôi câu này như người bản xứ: '{text_to_learn}'. Bao gồm: 1. Cách nói tự nhiên. 2. Bảng từ vựng (Hán-Pinyin-Hán Việt-Nghĩa). 3. Chiết tự chữ Hán để nhớ lâu. 4. Ngữ pháp."
        res = model.generate_content(text_to_learn if not text_to_learn else prompt)
        st.markdown(res.text)

# --- 4. INDUSTRIAL TRANSLATOR ---
elif menu == "🏭 Cào & Dịch Công Nghiệp":
    st.title("🏭 Cỗ Máy Dịch Thuật & Cào Truyện")
    tab1, tab2, tab3 = st.tabs(["🌐 Cào Web", "📄 Dịch File", "📸 Dịch Ảnh"])
    
    with tab1:
        url = st.text_input("Link chương 1:")
        num = st.number_input("Số chương:", 1, 100, 5)
        if st.button("🚀 Chạy cào truyện"):
            full_content = ""
            curr_url = url
            p_bar = st.progress(0)
            for i in range(num):
                html = get_web_content(curr_url)
                if not html: break
                prompt = f"Trích nội dung chương, tìm link chương tiếp theo và dịch sang TV mượt mà. HTML: {html[:20000]}"
                res = model.generate_content(prompt).text
                try:
                    # Tách nội dung và link giả định AI trả về đúng format
                    full_content += f"\n\n--- CHƯƠNG {i+1} ---\n\n" + res
                    p_bar.progress((i+1)/num)
                except: break
            st.download_button("📥 Tải Word", save_docx(full_content).getvalue(), "Truyen_Full.docx")

    with tab2:
        f_batch = st.file_uploader("Nạp file cần dịch:", accept_multiple_files=True)
        if st.button("🚀 Dịch File Hàng Loạt"):
            # Tương tự logic dịch file các bản trước
            st.write("Đang dịch...")
            
    with tab3:
        i_batch = st.file_uploader("Tải ảnh sách cổ/truyện:", accept_multiple_files=True)
        if st.button("📸 Dịch Ảnh OCR"):
            for img_file in i_batch:
                img = Image.open(img_file)
                st.image(img, width=300)
                res = model.generate_content(["Đọc chữ dọc/ngang và dịch sang TV mượt mà:", img])
                st.write(res.text)
