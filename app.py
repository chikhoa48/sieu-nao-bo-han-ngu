import streamlit as st
import google.generativeai as genai
import os, io, requests, time
from PIL import Image
from docx import Document
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google.api_core import exceptions

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Peerless God-Mode Translator", page_icon="🏛️", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { background: linear-gradient(45deg, #b33939, #212121); color: white; border: none; height: 3em; border-radius: 10px; font-weight: bold; }
    .status-box { padding: 15px; border-radius: 10px; background-color: #1e272e; border-left: 5px solid #ff5252; margin-bottom: 10px; }
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

# --- HÀM XỬ LÝ LÕI ---

def call_ai_ultimate(model_obj, prompt, file_data=None, mime_type=None):
    try:
        if file_data and mime_type:
            content = [{"mime_type": mime_type, "data": file_data}, prompt]
            return model_obj.generate_content(content)
        return model_obj.generate_content(prompt)
    except exceptions.ResourceExhausted:
        st.warning("⚠️ Hạn mức API bản Free đang đầy. Tự động nghỉ 60s...")
        time.sleep(60)
        return call_ai_ultimate(model_obj, prompt, file_data, mime_type)
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return None

def fetch_web_raw(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=20)
        res.encoding = res.apparent_encoding
        return res.text
    except: return None

def save_docx(content):
    doc = Document()
    for line in content.split('\n'):
        if line.strip(): doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    return bio

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ BỘ ĐIỀU KHIỂN")
    selected_model = st.selectbox("🎯 Chọn Động Cơ AI:", available_models, index=0)
    st.warning("💡 Dùng 'Pro' cho file Scan/Hán cổ dọc. Dùng 'Flash' cho Web hàng loạt.")
    
    st.divider()
    is_ancient = st.checkbox("📜 Chế độ Hán cổ (Chữ dọc, Phải qua Trái)", value=False)
    
    st.divider()
    style_req = st.text_area("✍️ Yêu cầu trau chuốt bản dịch:", "Dịch trau chuốt, trung thành với nguyên tác, ưu tiên từ Hán Việt chuyên ngành, xưng hô phù hợp bối cảnh cổ đại/hiện đại.")
    glossary = st.text_area("📖 Từ điển bắt buộc:", "Trúc Cơ, Nguyên Anh, Long Mạch")

model = genai.GenerativeModel(selected_model)

# --- GIAO DIỆN CHÍNH ---
tabs = st.tabs(["🌐 Quét & Dịch Website", "📄 Dịch File Scan/PDF/Sách Cổ", "📝 Dịch Văn Bản Thô"])

# --- TAB 1: WEBSITE ---
with tabs[0]:
    st.subheader("🌐 Cào Website & Dịch Hàng Loạt")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        web_url = st.text_input("Link chương bắt đầu (hoặc link danh mục):")
    with col_b:
        task = st.radio("Nhiệm vụ:", ["Quét danh mục & Lọc Top", "Dịch hàng loạt chương"])
        num_chaps = st.number_input("Số chương:", 1, 500, 10) if task == "Dịch hàng loạt chương" else 0

    if st.button("🚀 THỰC THI"):
        html = fetch_web_raw(web_url)
        if html:
            if task == "Quét danh mục & Lọc Top":
                prompt = f"Lọc danh sách truyện từ HTML này: Tên truyện, Thể loại, Lượt xem/Đánh giá, Link. Sắp xếp theo độ hot. Trình bày dạng bảng Markdown. HTML: {html[:30000]}"
                res = call_ai_ultimate(model, prompt)
                if res: st.markdown(res.text)
            else:
                curr_url = web_url
                full_book = ""
                p_bar = st.progress(0)
                for i in range(num_chaps):
                    st.markdown(f"<div class='status-box'>Đang xử lý chương {i+1}: {curr_url}</div>", unsafe_allow_html=True)
                    h = fetch_web_raw(curr_url)
                    if not h: break
                    
                    prompt = f"""
                    Nhiệm vụ: 1. Trích nội dung. 2. Tìm URL chương tiếp. 3. Dịch sang TV: {style_req}.
                    Thuật ngữ: {glossary}.
                    Trả về dạng: CONTENT: [Bản dịch] | NEXT_URL: [Link sau]
                    HTML: {h[:25000]}
                    """
                    res = call_ai_ultimate(model, prompt)
                    if res:
                        try:
                            content = res.text.split("CONTENT:")[1].split("NEXT_URL:")[0].strip()
                            next_l = res.text.split("NEXT_URL:")[1].strip()
                            full_book += f"\n\n--- CHƯƠNG {i+1} ---\n\n{content}"
                            curr_url = urljoin(curr_url, next_l)
                            st.success(f"✅ Xong chương {i+1}")
                        except: break
                    p_bar.progress((i+1)/num_chaps)
                    time.sleep(2)
                st.download_button("📥 Tải bản dịch (.docx)", save_docx(full_book).getvalue(), "Web_Dich.docx")

# --- TAB 2: FILE SCAN & SÁCH CỔ ---
with tabs[1]:
    st.subheader("📄 Dịch Sách PDF Scan / Ảnh Chữ Hán Cổ")
    st.info("Hệ thống sử dụng Vision AI để đọc file scan. Hỗ trợ chữ dọc từ phải sang trái.")
    
    files = st.file_uploader("Tải lên PDF Scan hoặc Ảnh:", accept_multiple_files=True, type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if st.button("🚀 BẮT ĐẦU DỊCH FILE SCAN"):
        all_res = ""
        for f in files:
            with st.spinner(f"AI đang 'nhìn' và dịch: {f.name}..."):
                f_bytes = f.read()
                m_type = "application/pdf" if f.name.endswith(".pdf") else "image/jpeg"
                
                # PROMPT ĐẶC BIỆT CHO HÁN CỔ DỌC
                layout_instr = ""
                if is_ancient:
                    layout_instr = "LƯU Ý CỰC QUAN TRỌNG: Đây là sách cổ. Chữ được viết theo CỘT DỌC, thứ tự đọc là từ PHẢI SANG TRÁI. Hãy nhận diện đúng thứ tự câu trước khi dịch."
                
                prompt_ocr = f"""
                Bạn là một đại sư ngôn ngữ chuyên về Hán học và dịch thuật cao cấp.
                {layout_instr}
                Nhiệm vụ: Nhận diện toàn bộ chữ trong file này và dịch sang tiếng Việt trau chuốt.
                Yêu cầu văn phong: {style_req}.
                Thuật ngữ: {glossary}.
                """
                
                res = call_ai_ultimate(model, prompt_ocr, file_data=f_bytes, mime_type=m_type)
                if res:
                    st.markdown(f"### Kết quả: {f.name}")
                    st.write(res.text)
                    all_res += f"\n\n--- FILE: {f.name} ---\n\n" + res.text
        
        if all_res:
            st.download_button("📥 Tải Kết Quả (.docx)", save_docx(all_res).getvalue(), "Scan_Dich.docx")

# --- TAB 3: VĂN BẢN THÔ ---
with tabs[2]:
    st.subheader("📝 Dịch văn bản copy-paste")
    raw_in = st.text_area("Dán tiếng Trung vào đây:", height=300)
    if st.button("🚀 Dịch Ngay"):
        p = f"Dịch văn bản sau sang tiếng Việt trau chuốt: {style_req}. Thuật ngữ: {glossary}.\n\nNội dung: {raw_in}"
        res = call_ai_ultimate(model, p)
        if res: st.write(res.text)
