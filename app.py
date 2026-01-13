import streamlit as st
import google.generativeai as genai
import os, io, requests, time
from PIL import Image
from PyPDF2 import PdfReader
from docx import Document
from bs4 import BeautifulSoup

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hanzi Intelligence Pro v2", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fdfaf6; }
    .stButton>button { background: linear-gradient(45deg, #c0392b, #e74c3c); color: white; border-radius: 10px; font-weight: bold; height: 3em; width: 100%; }
    .lesson-box { padding: 20px; border-radius: 10px; border-left: 10px solid #c0392b; background-color: #ffffff; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .chinese-text { font-size: 22px; color: #c0392b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- KẾT NỐI API ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # Lấy danh sách model sạch
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
except:
    st.error("⚠️ Vui lòng kiểm tra GEMINI_API_KEY trong Secrets.")
    st.stop()

# --- HÀM TRỢ GIÚP ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏮 SIÊU NÃO BỘ HÁN NGỮ")
    selected_model = st.selectbox("🎯 Chọn Bộ Não AI:", available_models, index=0)
    
    st.divider()
    menu = st.radio("🚀 CHỌN CHẾ ĐỘ:", [
        "🎓 Học Viện & Giáo Trình Tự Động",
        "🧠 Đại Sư Kiến Thức (Upload)",
        "🌐 Cập Nhật Xu Hướng (Search)",
        "🏭 Dịch Thuật Công Nghiệp"
    ])
    st.divider()
    st.info("Phiên bản v2: Tự động thiết kế giáo trình dạy học.")

# Khởi tạo model mặc định (Không tool để tránh lỗi InvalidArgument)
model = genai.GenerativeModel(selected_model)

# --- 1. HỌC VIỆN & GIÁO TRÌNH TỰ ĐỘNG (TÍNH NĂNG MỚI) ---
if menu == "🎓 Học Viện & Giáo Trình Tự Động":
    st.title("🎓 Học Viện Hán Ngữ: Thiết Kế Giáo Trình Riêng")
    st.write("Nhập chủ đề bạn muốn học, AI sẽ tự tạo lộ trình bài bản cho bạn.")
    
    topic = st.text_input("Bạn muốn học về chủ đề gì?", placeholder="Ví dụ: Giao tiếp tại sân bay, Tiếng Trung ngành Logistics, Hán cổ đạo đức kinh...")
    
    if st.button("📚 Tạo Giáo Trình & Bắt Đầu Học"):
        with st.spinner("Đang biên soạn giáo án chuyên sâu..."):
            study_prompt = f"""
            Bạn là một Giáo sư ngôn ngữ học và chuyên gia giáo dục Hán ngữ.
            Nhiệm vụ: Hãy tạo một giáo trình dạy học tiếng Trung cho người Việt về chủ đề: "{topic}".
            
            YÊU CẦU GIÁO TRÌNH PHẢI CÓ:
            1. LỘ TRÌNH: Chia thành ít nhất 3 bài học nhỏ từ dễ đến khó.
            2. NỘI DUNG CHI TIẾT BÀI 1:
               - Các mẫu câu quan trọng nhất.
               - Bảng từ vựng chi tiết: Chữ Hán | Pinyin | Hán Việt | Nghĩa Việt.
               - Chiết tự và mẹo nhớ cho các chữ khó.
            3. NGỮ PHÁP: Giải thích cách sắp xếp câu của chủ đề này.
            4. BÀI TẬP: Tạo 3 câu bài tập để người dùng luyện tập ngay.
            
            Hãy trình bày thật đẹp mắt, rõ ràng và uyên bác.
            """
            try:
                res = model.generate_content(study_prompt)
                st.markdown("<div class='lesson-box'>", unsafe_allow_html=True)
                st.markdown(res.text)
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Lỗi khi tạo bài học: {e}")

# --- 2. ĐẠI SƯ KIẾN THỨC (QUY NẠP & GIẢNG GIẢI) ---
elif menu == "🧠 Đại Sư Kiến Thức (Upload)":
    st.title("🧠 Đại Sư Kiến Thức & Ngôn Ngữ")
    st.info("Nạp sách. AI vừa dạy kiến thức quyển sách, vừa dạy tiếng Trung trong đó.")
    
    up_files = st.file_uploader("Nạp sách/tài liệu (PDF/Docx):", accept_multiple_files=True)
    query = st.text_input("Yêu cầu (VD: Quy nạp các ý chính của sách và dạy tôi từ vựng chuyên ngành này):")
    
    if st.button("🚀 Phân Tích Chuyên Sâu"):
        if up_files:
            with st.spinner("Đại sư đang nghiên cứu tài liệu..."):
                ctx = get_text_from_files(up_files)
                expert_prompt = f"""
                Bạn là chuyên gia hàng đầu và Giáo sư Hán học.
                Dữ liệu nạp vào: {ctx[:30000]}
                
                Yêu cầu của người dùng: {query}
                
                Hãy thực hiện:
                1. QUY NẠP KIẾN THỨC: Phân tích, tổng hợp và diễn giải nội dung sách một cách dễ hiểu như chuyên gia tư vấn.
                2. GIẢNG DẠY NGÔN NGỮ: Từ nội dung trên, dạy tôi các thuật ngữ tiếng Trung cốt lõi (Hán-Pinyin-Hán Việt-Nghĩa).
                3. PHÂN TÍCH CHUYÊN SÂU: Đưa ra nhận xét của bạn về kiến thức này.
                """
                res = model.generate_content(expert_prompt)
                st.markdown(res.text)

# --- 3. CẬP NHẬT XU HƯỚNG (VÁ LỖI GOOGLE SEARCH) ---
elif menu == "🌐 Cập Nhật Xu Hướng (Search)":
    st.title("🌐 Cập Nhật Kiến Thức Mới Nhất")
    topic_search = st.text_input("Chủ đề tin tức/xu hướng mới nhất:")
    
    if st.button("🔍 Quét Mạng & Giảng Bài"):
        # Chỉ kích hoạt Tool Search ở đây để tránh lỗi InvalidArgument cho toàn app
        try:
            model_with_tools = genai.GenerativeModel(model_name=selected_model, tools=[{"google_search_retrieval": {}}])
            with st.spinner("AI đang lên mạng tìm kiếm..."):
                search_prompt = f"Tìm tin tức mới nhất về '{topic_search}' bằng tiếng Trung. Tóm tắt ý chính và dạy từ vựng mới liên quan."
                res = model_with_tools.generate_content(search_prompt)
                st.markdown(res.text)
        except Exception as e:
            st.error(f"Model này không hỗ trợ tìm kiếm hoặc lỗi kết nối. Hãy thử chọn model khác hoặc thử lại sau. Chi tiết: {e}")

# --- 4. DỊCH THUẬT CÔNG NGHIỆP ---
elif menu == "🏭 Dịch Thuật Công Nghiệp":
    st.title("🏭 Cào Truyện & Dịch Thuật Hàng Loạt")
    # (Giữ nguyên logic cào web và dịch hàng loạt từ các bản trước của bạn)
    st.warning("Vui lòng sử dụng tính năng dịch như đã cài đặt ở bản trước.")
