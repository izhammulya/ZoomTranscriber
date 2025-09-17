import streamlit as st
import re
from datetime import datetime
import io
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def process_vtt_text(vtt_text):
    """
    Process VTT text to clean timestamps and metadata
    """
    # Clean timestamp & metadata
    cleaned_text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt_text)
    cleaned_text = re.sub(r"WEBVTT.*\n", "", cleaned_text)
    cleaned_text = "\n".join([line.strip() for line in cleaned_text.splitlines() if line.strip()])
    return cleaned_text

def generate_notulen_with_ai(sentences, api_key):
    """
    Generate formal meeting minutes using Google Gemini API
    Uses the exact prompt provided by the user
    """
    try:
        # Configure API
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
        
        # EXACT PROMPT - DO NOT CHANGE
        prompt = f"""
Buatkan notulen rapat yang rapi dan formal dari transkrip rapat berikut:

{sentences}

FORMAT YANG DIHARAPKAN:

# Notulen Rapat

|Nama Rapat|[isi nama rapat berdasarkan transkrip]|
|---|---|
|Hari/Tanggal|[hari, tanggal berdasarkan transkrip]|
|Waktu|[waktu rapat berdasarkan transkrip]|
|Tempat|[lokasi rapat berdasarkan transkrip]|
|Pemimpin Rapat|[nama pemimpin rapat berdasarkan transkrip]|
|Dibuat oleh|[Group Transformasi Korporasi dan Manajemen Program]|

**Agenda:**
- [daftar agenda rapat berdasarkan transkrip]

**Peserta Rapat:**
|No||Nama/Jabatan|
|---|---|---|
|1|[nama dan jabatan peserta 1]|
|2|[nama dan jabatan peserta 2]|
|[dan seterusnya]|

|Poin Diskusi dan Arahan|Penanggung Jawab|
|---|---|
|[Topik diskusi 1]||
[Penjelasan Topik singkat]
|Kesimpulan :||
|• [kesimpulan point 1]|[penanggung jawab]|
|[Topik diskusi 2]||
[Penjelasan Topik singkat]
|Kesimpulan :||
|• [kesimpulan point 2]|[penanggung jawab]|
|[dan seterusnya untuk semua topik]|

**Disclaimer:**
_Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final._

INSTRUKSI KHUSUS:
1. Gunakan format tabel persis seperti contoh di atas
2. Ekstrak semua informasi dari transkrip yang diberikan
3. Untuk kolom "Penanggung Jawab", identifikasi pihak yang bertanggung jawab berdasarkan diskusi
4. Gunakan bahasa Indonesia yang formal dan profesional
5. Jika informasi tidak tersedia dalam transkrip, gunakan [Tidak disebutkan dalam transkrip]
6. Jangan tambahkan elemen format lain selain yang ditentukan

Catatan: Jika informasi tertentu tidak tersedia dalam transkrip, beri tanda [Tidak disebutkan dalam transkrip].
"""
        
        # Generate content with specific configuration
        generation_config = {
            "temperature": 0.5,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        
        if response and response.text:
            # Clean up the response to ensure proper table formatting
            cleaned_response = response.text.strip()
            
            # Ensure the response starts with the correct header
            if not cleaned_response.startswith("# Notulen Rapat"):
                # Try to find the start of the actual content
                lines = cleaned_response.split('\n')
                for i, line in enumerate(lines):
                    if "Notulen Rapat" in line:
                        cleaned_response = '\n'.join(lines[i:])
                        break
            
            return {
                'success': True,
                'content': cleaned_response,
                'error': None
            }
        else:
            return {
                'success': False,
                'content': None,
                'error': 'Empty response from model'
            }
            
    except Exception as e:
        return {
            'success': False,
            'content': None,
            'error': str(e)
        }

def create_word_document(content, filename):
    """
    Create a Word document from the generated content
    """
    try:
        doc = Document()
        title = doc.add_heading('Notulen Rapat', level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add the content as plain text
        doc.add_paragraph(content)
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        st.error(f"Error creating Word document: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Notulen Zoom Meeting Generator by TKMP",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .upload-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #ddd;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">📝 Notulen Zoom Meeting Generator by TKMP</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate Notulen dengan praktis no ribet </p>', unsafe_allow_html=True)
    
    # Get API key from secrets.toml
    try:
        api_key = st.secrets["api_key"]
        api_key_available = True
    except (KeyError, FileNotFoundError):
        api_key = None
        api_key_available = False
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        if api_key_available:
            st.success("✅ API Key loaded successfully")
        else:
            st.error("❌ API Key not found")
            st.info("""
            **Setup Instructions:**
            1. Create `.streamlit/secrets.toml`
            2. Add your API key:
            ```
            api_key = "your_api_key_here"
            ```
            3. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
            """)
        
        st.header("📋 How to Use")
        st.markdown("""
        1. **Upload** transkrip Zoom Anda
        2. **Process** transkrip nya by button
        3. **Review** Notulen yang sudah jadi
        """)
        
        st.header("📊 Kelebihannya cuy")
        st.markdown("""
        - ✅ Sudah disesuaikan dengan format notulen
        - ✅ Ekstraksi agenda
        - ✅ Mengidentifikasi peserta (speaker)
        - ✅ Menggunakan bahasa Indonesia yang baik
        - ✅ Downloadable
        """)

    # Main content
    st.markdown("### 📁 Upload Transkripmu disini")
    
    uploaded_file = st.file_uploader(
        "Pilih File",
        type=['vtt'],
        help="Supported format: .vtt (Zoom transcript files)"
    )
    
    if uploaded_file is not None:
        # File info
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**File name:** {uploaded_file.name}")
        with col2:
            st.info(f"**File size:** {uploaded_file.size:,} bytes")
        
        # Process button
        if st.button("🚀 Generate Notulen", type="primary", use_container_width=True):
            if not api_key_available:
                st.error("Please configure your API key in secrets.toml first")
                return
                
            with st.spinner("🤖 AI is processing your transcript..."):
                try:
                    # Read and process the file
                    content = uploaded_file.getvalue().decode("utf-8")
                    cleaned_text = process_vtt_text(content)
                    
                    # Generate AI content
                    ai_result = generate_notulen_with_ai(cleaned_text, api_key)
                    
                    if ai_result['success']:
                        st.session_state.ai_notulen = ai_result['content']
                        st.session_state.processed = True
                        st.success("✅ Meeting minutes generated successfully!")
                    else:
                        st.error(f"❌ Error: {ai_result['error']}")
                        
                except Exception as e:
                    st.error(f"❌ Processing error: {str(e)}")
    
    # Display results
    if 'ai_notulen' in st.session_state and st.session_state.get('processed', False):
        st.divider()
        st.markdown("### 📋 Generated Notulen")
        
        # Success message
        st.markdown('<div class="success-box">✅ <strong>Notulen sukses dibuat!</strong>  Silahkan review hasilnya.</div>', unsafe_allow_html=True)
        
        # Display the content
        st.markdown(st.session_state.ai_notulen, unsafe_allow_html=True)
        
        # Download section
        st.divider()
        st.markdown("### 📥 Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Text download
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📄 Download as TXT",
                data=st.session_state.ai_notulen,
                file_name=f"meeting_minutes_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # Word document download
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            word_buffer = create_word_document(st.session_state.ai_notulen, f"meeting_minutes_{timestamp}.docx")
            if word_buffer:
                st.download_button(
                    label="📝 Download Word Document",
                    data=word_buffer.getvalue(),
                    file_name=f"meeting_minutes_{timestamp}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        
        # Clear results button
        if st.button("🗑️ Clear Results", use_container_width=True):
            if 'ai_notulen' in st.session_state:
                del st.session_state.ai_notulen
            if 'processed' in st.session_state:
                del st.session_state.processed
            st.rerun()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Di buat dengan penuh ❤️</p>
        <p>Summary rapat Anda disini</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
