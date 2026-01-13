import streamlit as st
import google.generativeai as genai
import os, io, requests, time
from PIL import Image
from PyPDF2 import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Siêu AI Hán Ngữ Toàn Năng", page_icon="🧧", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fdfaf6; }
    .stButton>button { background: linear-gradient(45deg, #c0392b, #e74c3c); color: white; border-radius: 10px; font-weight: bold; height: 3em; }
    .lesson-box { padding: 20px; border-radius: 10px; border-left: 10px solid #c0392b; background-color: #ffffff; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .stProgress .st-bo { background-color: #c0392b; }
    </style>
    """, unsafe_allow_html=True)

# --- KẾT NỐI API ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
except:
    st.error("⚠️ Vui lòng kiểm tra GEMINI_API_KEY trong Secrets.")
    st.stop()

# --- HÀM HỖ TRỢ ---
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

def save_docx(content, title="Ban_Dich"):
    doc = Document()
    doc.add_heading(title, 0)
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
    st.title("🧧 SIÊU NÃO BỘ AI")
    selected_model = st.selectbox("🎯 Chọn Bộ Não AI:", available_models, index=0)
    st.divider()
    menu = st.radio("🚀 CHỌN CHẾ ĐỘ:", [
        "🎓 Học Viện & Giáo Trình Tự Động",
        "🏭 Cào Truyện & Dịch Hàng Loạt",
        "🧠 Đại Sư Kiến Thức (Upload)",
        "🌐 Cập Nhật Xu Hướng (Search)",
        "📸 Dịch Ảnh OCR"
    ])
    st.divider()
    st.info("Phiên bản v3: Full tính năng Cào & Học.")

model = genai.GenerativeModel(selected_model)

# --- 1. HỌC VIỆN & GIÁO TRÌNH TỰ ĐỘNG ---
if menu == "🎓 Học Viện & Giáo Trình Tự Động":
    st.title("🎓 Học Viện Hán Ngữ: Thiết Kế Giáo Trình Riêng")
    topic = st.text_input("Bạn muốn học về chủ đề gì?", placeholder="Ví dụ: Giao tiếp đàm phán, Tiếng Trung du lịch...")
    if st.button("📚 Tạo Giáo Trình"):
        with st.spinner("Đang biên soạn bài giảng..."):
            prompt = f"Bạn là giáo sư ngôn ngữ. Hãy tạo giáo trình tiếng Trung bài bản về '{topic}'. Bao gồm: Lộ trình bài học, Mẫu câu quan trọng, Bảng từ vựng (Hán-Pinyin-Hán Việt-Nghĩa), Chiết tự mẹo nhớ và Bài tập."
            res = model.generate_content(prompt)
            st.markdown("<div class='lesson-box'>", unsafe_allow_html=True)
            st.markdown(res.text)
            st.markdown("</div>", unsafe_allow_html=True)

# --- 2. CÀO TRUYỆN & DỊCH HÀNG LOẠT ---
elif menu == "🏭 Cào Truyện & Dịch Hàng Loạt":
    st.title("🏭 Cỗ Máy Dịch Thuật Công Nghiệp")
    tab1, tab2 = st.tabs(["🌐 Cào Web Cuốn Chiếu", "📄 Dịch File Hàng Loạt"])
    
    with tab1:
        st.subheader("Cào Truyện Từ Link")
        start_url = st.text_input("Link chương bắt đầu (URL):")
        num_chaps = st.number_input("Số chương cần dịch:", 1, 100, 5)
        instr = st.text_area("Yêu cầu văn phong:", "Dịch mượt mà, xưng hô phù hợp thể loại truyện.")
        
        if st.button("🚀 Khởi Động Cào Truyện"):
            current_url = start_url
            full_story = ""
            progress = st.progress(0)
            for i in range(num_chaps):
                html = get_web_content(current_url)
                if not html: break
                # AI trích xuất nội dung và link sau
                prompt = f"Từ HTML này: 1. Trích nội dung chương. 2. Tìm URL chương sau. 3. Dịch nội dung sang TV phong cách {instr}. Trả về dạng: CONTENT: [Nội dung dịch] | NEXT_URL: [Link sau]. HTML: {html[:20000]}"
                try:
                    res_raw = model.generate_content(prompt).text
                    chapter_text = res_raw.split("CONTENT:")[1].split("NEXT_URL:")[0].strip()
                    current_url = res_raw.split("NEXT_URL:")[1].strip()
                    full_story += f"\n\n--- CHƯƠNG {i+1} ---\n\n{chapter_text}"
                    st.success(f"✅ Đã xong chương {i+1}")
                except:
                    st.error(f"Lỗi cấu hình web tại chương {i+1}")
                    break
                progress.progress((i+1)/num_chaps)
                time.sleep(1)
            st.download_button("📥 Tải Word Trọn Bộ", save_docx(full_story).getvalue(), "Truyen_Full.docx")

    with tab2:
        st.subheader("Dịch File (Word/PDF)")
        up_files = st.file_uploader("Nạp nhiều file cùng lúc:", accept_multiple_files=True)
        if st.button("🚀 Dịch Tất Cả File"):
            for f in up_files:
                st.write(f"📄 Đang dịch: {f.name}")
                text = get_text_from_files([f])
                # Chia nhỏ dịch
                chunks = [text[i:i+6000] for i in range(0, len(text), 6000)]
                translated = ""
                for c in chunks:
                    translated += model.generate_content(f"Dịch sang tiếng Việt mượt mà: {c}").text + "\n"
                st.download_button(f"📥 Tải bản dịch {f.name}", save_docx(translated).getvalue(), f"VN_{f.name}.docx")

# --- 3. ĐẠI SƯ KIẾN THỨC ---
elif menu == "🧠 Đại Sư Kiến Thức (Upload)":
    st.title("🧠 Chuyên Gia Phân Tích & Quy Nạp")
    up_files = st.file_uploader("Nạp sách/tài liệu:", accept_multiple_files=True)
    query = st.text_input("Câu hỏi về kiến thức trong sách hoặc yêu cầu diễn giải:")
    if st.button("🚀 Nghiên Cứu & Giảng Giải"):
        if up_files:
            with st.spinner("AI đang nghiên cứu..."):
                ctx = get_text_from_files(up_files)
                prompt = f"Dựa vào nội dung này: {ctx[:30000]}. Hãy: 1. Quy nạp kiến thức quan trọng nhất. 2. Diễn giải dễ hiểu như chuyên gia. 3. Dạy 5 thuật ngữ tiếng Trung chuyên ngành từ sách này. Yêu cầu: {query}"
                res = model.generate_content(prompt)
                st.markdown(res.text)

# --- 4. CẬP NHẬT XU HƯỚNG ---
elif menu == "🌐 Cập Nhật Xu Hướng (Search)":
    st.title("🌐 Tin Tức & Xu Hướng Mới Nhất")
    topic_search = st.text_input("Chủ đề muốn search internet:")
    if st.button("🔍 Quét Mạng"):
        try:
            model_search = genai.GenerativeModel(model_name=selected_model, tools=[{"google_search_retrieval": {}}])
            res = model_search.generate_content(f"Tìm tin tức mới nhất bằng tiếng Trung về '{topic_search}', tóm tắt và dạy từ vựng mới liên quan.")
            st.markdown(res.text)
        except: st.error("Model này không hỗ trợ tìm kiếm.")

# --- 5. DỊCH ẢNH OCR ---
elif menu == "📸 Dịch Ảnh OCR":
    st.title("📸 Dịch Chữ Từ Hình Ảnh")
    imgs = st.file_uploader("Tải ảnh:", accept_multiple_files=True)
    if st.button("🚀 Bắt đầu dịch ảnh"):
        for im_f in imgs:
            img = Image.open(im_f)
            st.image(img, width=300)
            res = model.generate_content(["Dịch chữ trong ảnh này sang Tiếng Việt (chú ý chữ dọc nếu có):", img])
            st.write(res.text)
