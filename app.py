import streamlit as st
import re
from datetime import datetime
import io
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
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
    """
    try:
        # Configure API
        genai.configure(api_key=api_key)
        
        # Initialize model - Using gemini-1.5-flash which is more stable
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # IMPROVED PROMPT with clearer instructions and safety guidelines
        prompt = f"""
TUGAS: Buat notulen rapat formal dari transkrip rapat perusahaan berikut.

**TRANSCRIPT RAPAT:**
{sentences}

**INSTRUKSI KHUSUS:**
1. BUAT NOTULEN DALAM BAHASA INDONESIA YANG FORMAL DAN PROFESIONAL
2. FOKUS PADA INFORMASI BISNIS SAJA: agenda, diskusi, keputusan, dan tindak lanjut
3. HINDARI MENCANTUMKAN INFORMASI SENSITIF seperti data pribadi, konflik internal, atau informasi rahasia
4. Jika ada konten yang sensitif, ringkas dengan bahasa umum dan profesional
5. Gunakan format tabel seperti yang diminta

**FORMAT NOTULEN:**

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

**PANDUAN TAMBAHAN:**
- Jika informasi tidak ada dalam transkrip, tulis [Tidak disebutkan dalam transkrip]
- Identifikasi penanggung jawab berdasarkan diskusi
- Gunakan bahasa bisnis yang profesional
- Fokus pada fakta-fakta objektif dari rapat
- Ringkas diskusi panjang menjadi poin-poin penting
- Jika ada konten yang tidak jelas, tulis [Diskusi tidak spesifik] atau [Tidak diputuskan]
- Pastikan semua konten sesuai dengan etika bisnis dan profesional
"""
        
        # IMPROVED generation config with more conservative settings
        generation_config = {
            "temperature": 0.2,  # Lower temperature for more consistent results
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,  # Increased for complete response
        }
        
        # REVISED safety settings - less restrictive but still safe
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"  # Changed from BLOCK_NONE
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ]
        
        response = model.generate_content(
            prompt, 
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Check if response was blocked
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
            error_msg = f"Response blocked due to input content: {response.prompt_feedback.block_reason}"
            st.warning(f"⚠️ Safety block detected: {response.prompt_feedback.block_reason}")
            
            # Try alternative approach with more conservative settings
            return generate_notulen_fallback(sentences, api_key)
        
        # Check if response has candidates
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            # Check finish reason
            if hasattr(candidate, 'finish_reason'):
                if candidate.finish_reason == 2:  # SAFETY
                    st.warning("⚠️ Model output triggered safety filters. Trying fallback method...")
                    return generate_notulen_fallback(sentences, api_key)
                elif candidate.finish_reason == 1:  # STOP (normal completion)
                    # Get text from candidate
                    if candidate.content.parts:
                        content_text = candidate.content.parts[0].text
                        if content_text:
                            cleaned_response = content_text.strip()
                            
                            # Clean up the response
                            cleaned_response = cleaned_response.replace("**", "").replace("__", "")
                            
                            # Ensure the response starts with the correct header
                            if not cleaned_response.startswith("# Notulen Rapat"):
                                # Find the Notulen Rapat section
                                lines = cleaned_response.split('\n')
                                for i, line in enumerate(lines):
                                    if "Notulen Rapat" in line:
                                        # Take from this line to the end
                                        cleaned_response = '\n'.join(lines[i:])
                                        break
                                else:
                                    # If still not found, add the header
                                    cleaned_response = "# Notulen Rapat\n\n" + cleaned_response
                            
                            return {
                                'success': True,
                                'content': cleaned_response,
                                'error': None
                            }
        
        # If we reach here, try fallback
        return generate_notulen_fallback(sentences, api_key)
            
    except Exception as e:
        error_msg = f"API Error: {str(e)}"
        st.error(f"❌ Error: {error_msg}")
        return {
            'success': False,
            'content': None,
            'error': error_msg
        }

def generate_notulen_fallback(sentences, api_key):
    """
    Fallback method with simpler prompt if main method fails
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # SIMPLER PROMPT for fallback
        prompt = f"""
Buat notulen rapat profesional dari transkrip ini dengan format berikut:

{sentences}

FORMAT:
# Notulen Rapat
[Informasi dasar rapat]
**Agenda:** [daftar agenda]
**Peserta:** [daftar peserta]
**Diskusi:** [ringkasan diskusi dalam tabel]
**Keputusan:** [keputusan yang diambil]
**Tindak Lanjut:** [tindak lanjut dan penanggung jawab]

Instruksi:
1. Gunakan bahasa Indonesia formal
2. Fokus pada informasi bisnis saja
3. Hindari detail sensitif
4. Gunakan format tabel untuk diskusi
"""
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 2048,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
        )
        
        if response.text:
            return {
                'success': True,
                'content': response.text,
                'error': None
            }
        else:
            return {
                'success': False,
                'content': None,
                'error': 'Empty response from fallback model'
            }
            
    except Exception as e:
        return {
            'success': False,
            'content': None,
            'error': f"Fallback Error: {str(e)}"
        }

def create_word_document(content, filename):
    """
    Create a Word document from the generated content
    """
    try:
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Add title
        title = doc.add_heading('Notulen Rapat', level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.runs[0]
        title_run.font.size = Pt(16)
        title_run.font.bold = True
        
        # Add the content as simple text
        # Convert markdown-like formatting to Word formatting
        lines = content.split('\n')
        for line in lines:
            if line.startswith('#'):
                # This is a header
                level = line.count('#')
                heading_text = line.replace('#', '').strip()
                if heading_text:
                    doc.add_heading(heading_text, level=min(level, 2))
            elif '|' in line and line.count('|') > 2:
                # This is a table row - handle as plain text for now
                para = doc.add_paragraph(line)
            else:
                # Regular paragraph
                if line.strip():
                    para = doc.add_paragraph(line.strip())
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        st.error(f"Error creating Word document: {e}")
        return None

def chat_with_transcript(question, transcript_text, api_key, chat_history=None):
    """
    Function for interactive chat based on the uploaded transcript
    """
    try:
        # Configure API
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Create context from transcript
        context = f"""
        Berikut adalah transkrip rapat yang akan digunakan sebagai referensi untuk menjawab pertanyaan:

        {transcript_text}

        INSTRUKSI:
        1. JAWAB PERTANYAAN BERDASARKAN TRANSCRIPT DI ATAS SAJA
        2. Jika informasi tidak ada dalam transcript, katakan "Informasi tidak ditemukan dalam transkrip"
        3. Gunakan bahasa Indonesia yang formal dan profesional
        4. Berikan jawaban yang spesifik berdasarkan data yang ada dalam transkrip
        5. Jangan membuat informasi yang tidak ada dalam transkrip
        6. Hindari membahas konten sensitif atau pribadi
        7. Fokus pada informasi bisnis dan rapat

        Pertanyaan: {question}
        """
        
        # Generate content with safety settings
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ]
        
        response = model.generate_content(
            context, 
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        if response.text:
            return {
                'success': True,
                'content': response.text,
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
            'error': f"Chat Error: {str(e)}"
        }

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
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
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
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .info-box {
        background: #e8f4fd;
        color: #0c5460;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #b8daff;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">📝 Notulen Zoom Meeting Generator by TKMP</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate Notulen dengan praktis no ribet</p>', unsafe_allow_html=True)
    
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
        
        st.header("📋 Tips Mengatasi Error Safety")
        st.markdown("""
        **Jika muncul error safety filter:**
        1. **Review transkrip** - Hapus konten sensitif
        2. **Edit manual** - Hapus nama orang jika tidak penting
        3. **Redaksi ulang** - Ringkas diskusi panjang
        4. **Coba lagi** - Sistem akan otomatis mencoba metode alternatif
        """)
        
        st.header("📋 How to Use")
        st.markdown("""
        1. **Upload** transkrip Zoom Anda
        2. **Process** transkrip dengan tombol
        3. **Review** Notulen yang sudah jadi
        4. **Re-Generate** dengan klik tombol generate jika hasil kurang memuaskan
        5. **Chat** dengan konten transkrip apabila ingin menanyakan konten lebih spesifik
        6. **Chat** bisa digunakan jika ada file VTT yang diupload
        """)

    # Main content - Tabs for different functionalities
    tab1, tab2 = st.tabs(["📄 Generate Notulen", "💬 Chat dengan Transkrip"])

    with tab1:
        st.markdown("### 📁 Upload Transkrip")
        
        uploaded_file = st.file_uploader(
            "Pilih File",
            type=['vtt', 'txt'],
            help="Supported format: .vtt (Zoom transcript files) atau .txt",
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            # Store the uploaded file content in session state
            content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.uploaded_transcript = process_vtt_text(content)
            
            # File info
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**File:** {uploaded_file.name}")
            with col2:
                st.info(f"**Size:** {uploaded_file.size:,} bytes")
                st.info(f"**Characters:** {len(st.session_state.uploaded_transcript):,}")
            
            # Preview transcript
            with st.expander("📝 Preview Transkrip (50 baris pertama)"):
                preview_lines = st.session_state.uploaded_transcript.split('\n')[:50]
                st.text_area(
                    "Transkrip Preview",
                    value='\n'.join(preview_lines),
                    height=200,
                    disabled=True
                )
            
            # Process button
            if st.button("🚀 Generate Notulen", type="primary", use_container_width=True, key="generate_btn"):
                if not api_key_available:
                    st.error("Please configure your API key in secrets.toml first")
                    return
                    
                with st.spinner("🤖 AI sedang memproses transkrip..."):
                    try:
                        # Check if transcript has sufficient content
                        if len(st.session_state.uploaded_transcript.strip()) < 50:
                            st.error("❌ Transkrip terlalu pendek. Pastikan file berisi konten rapat yang cukup.")
                            return
                        
                        # Show warning about sensitive content
                        st.markdown("""
                        <div class="warning-box">
                            ⚠️ <strong>Perhatian:</strong> Sistem akan otomatis menghindari konten sensitif. 
                            Jika ada error, coba edit transkrip untuk menghapus informasi pribadi.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Generate AI content
                        ai_result = generate_notulen_with_ai(st.session_state.uploaded_transcript, api_key)
                        
                        if ai_result['success']:
                            st.session_state.ai_notulen = ai_result['content']
                            st.session_state.processed = True
                            st.success("✅ Generate Notulen berhasil!")
                            st.balloons()
                        else:
                            st.error(f"❌ Error: {ai_result['error']}")
                            if "safety" in ai_result['error'].lower() or "filter" in ai_result['error'].lower():
                                st.markdown("""
                                <div class="info-box">
                                    💡 **Solusi:**
                                    1. **Edit transkrip** untuk menghapus nama orang atau informasi sensitif
                                    2. **Ringkas diskusi** panjang menjadi poin-poin penting
                                    3. **Coba upload file yang berbeda**
                                    4. **Atau** - coba lagi dengan tombol di bawah:
                                </div>
                                """, unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"❌ Processing error: {str(e)}")
        
        # Display results
        if 'ai_notulen' in st.session_state and st.session_state.get('processed', False):
            st.divider()
            st.markdown("### 📋 Generated Notulen")
            
            # Success message
            st.markdown('<div class="success-box">✅ <strong>Notulen sukses dibuat!</strong> Silahkan review hasilnya.</div>', unsafe_allow_html=True)
            
            # Display the content with custom CSS for tables
            st.markdown("""
            <style>
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1rem 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            </style>
            """, unsafe_allow_html=True)
            
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
                    file_name=f"Notulen_meeting_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # Word document download
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                word_buffer = create_word_document(st.session_state.ai_notulen, f"Notulen_meeting_{timestamp}.docx")
                if word_buffer:
                    st.download_button(
                        label="📝 Download Word Document",
                        data=word_buffer.getvalue(),
                        file_name=f"Notulen_meeting_{timestamp}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            
            # Try again button
            st.divider()
            if st.button("🔄 Generate Ulang dengan Setting Berbeda", use_container_width=True, key="regenerate"):
                if 'ai_notulen' in st.session_state:
                    del st.session_state.ai_notulen
                if 'processed' in st.session_state:
                    del st.session_state.processed
                st.rerun()
            
            # Clear results button
            if st.button("🗑️ Clear Results", use_container_width=True, key="clear_results"):
                if 'ai_notulen' in st.session_state:
                    del st.session_state.ai_notulen
                if 'processed' in st.session_state:
                    del st.session_state.processed
                st.rerun()

    with tab2:
        st.markdown("### 💬 Chat dengan Transkrip")
        
        if 'uploaded_transcript' not in st.session_state or not st.session_state.uploaded_transcript:
            st.markdown("""
            <div class="info-box">
                <strong>📝 Informasi:</strong> Silakan upload file transkrip VTT terlebih dahulu di tab "Generate Notulen" 
                untuk mengaktifkan fitur chat.
            </div>
            """, unsafe_allow_html=True)
            
            st.info("""
            **Contoh pertanyaan yang bisa ditanyakan:**
            - Siapa saja yang hadir dalam rapat?
            - Apa agenda utama rapat ini?
            - Keputusan apa yang diambil dalam rapat?
            - Siapa yang bertanggung jawab untuk tindak lanjut?
            - Kapan deadline yang disepakati?
            """)
        else:
            st.markdown("""
            <div class="success-box">
                ✅ <strong>Transkrip tersedia!</strong> Anda dapat bertanya tentang konten rapat.
            </div>
            """, unsafe_allow_html=True)
            
            # Display transcript info
            with st.expander("📊 Info Transkrip"):
                st.text(f"Panjang transkrip: {len(st.session_state.uploaded_transcript)} karakter")
                st.text(f"Jumlah baris: {st.session_state.uploaded_transcript.count(chr(10)) + 1}")
            
            # Initialize chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            # Display chat history
            st.markdown("#### 💭 Percakapan")
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f'<div class="chat-message user-message"><strong>👤 Anda:</strong> {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message assistant-message"><strong>🤖 AI:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            
            # Chat input
            st.markdown("#### 💬 Tanya tentang rapat")
            user_input = st.text_area(
                "Pertanyaan Anda:",
                placeholder="Contoh: Siapa pemimpin rapat? Apa keputusan yang diambil? Siapa yang hadir?",
                key="chat_input",
                height=80
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("Kirim Pertanyaan", use_container_width=True, key="send_chat"):
                    if user_input.strip() and api_key_available:
                        with st.spinner("🔍 Mencari informasi dalam transkrip..."):
                            chat_result = chat_with_transcript(
                                user_input, 
                                st.session_state.uploaded_transcript, 
                                api_key
                            )
                            
                            if chat_result['success']:
                                # Add user message to history
                                st.session_state.chat_history.append({
                                    "role": "user", 
                                    "content": user_input
                                })
                                
                                # Add AI response to history
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": chat_result['content']
                                })
                                
                                # Clear input and rerun to update display
                                st.rerun()
                            else:
                                st.error(f"Error: {chat_result['error']}")
                    elif not api_key_available:
                        st.error("API Key tidak tersedia. Silakan konfigurasi di sidebar.")
                    elif not user_input.strip():
                        st.warning("Silakan ketik pertanyaan terlebih dahulu.")
            
            with col2:
                if st.button("Hapus Chat", use_container_width=True, key="clear_chat"):
                    st.session_state.chat_history = []
                    st.rerun()
            
            with col3:
                st.info("💡 Tanya tentang peserta, agenda, keputusan, atau hal spesifik dari rapat")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Dibuat dengan ❤️ oleh TKMP</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()


# import streamlit as st
# import re
# from datetime import datetime
# import io
# import google.generativeai as genai
# from docx import Document
# from docx.shared import Pt, Inches
# from docx.enum.text import WD_ALIGN_PARAGRAPH

# def process_vtt_text(vtt_text):
#     """
#     Process VTT text to clean timestamps and metadata
#     """
#     # Clean timestamp & metadata
#     cleaned_text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt_text)
#     cleaned_text = re.sub(r"WEBVTT.*\n", "", cleaned_text)
#     cleaned_text = "\n".join([line.strip() for line in cleaned_text.splitlines() if line.strip()])
#     return cleaned_text

# def generate_notulen_with_ai(sentences, api_key):
#     """
#     Generate formal meeting minutes using Google Gemini API
#     """
#     try:
#         # Configure API
#         genai.configure(api_key=api_key)
        
#         # Initialize model - CHANGED TO STANDARD FLASH MODEL
#         # model = genai.GenerativeModel("gemini-2.5-flash")

#         # model = genai.GenerativeModel("models/gemini-2.5-flash-lite") 
#         # model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-09-2025")
#         model = genai.GenerativeModel("models/gemini-flash-latest")
        
#         # REFINED PROMPT with strong emphasis on professional, non-sensitive content
#         prompt = f"""
# **INI ADALAH DATA RAPAT FORMAL PERUSAHAAN. BUATKAN NOTULEN RAPAT DENGAN BAHASA INDONESIA YANG FORMAL DAN PROFESIONAL. HANYA FOKUS PADA AGENDA, DISKUSI, DAN KEPUTUSAN SAJA.**

# Buatkan notulen rapat yang rapi dan formal dari transkrip rapat berikut:

# {sentences}

# FORMAT YANG DIHARAPKAN:

# # Notulen Rapat

# |Nama Rapat|[isi nama rapat berdasarkan transkrip]|
# |---|---|
# |Hari/Tanggal|[hari, tanggal berdasarkan transkrip]|
# |Waktu|[waktu rapat berdasarkan transkrip]|
# |Tempat|[lokasi rapat berdasarkan transkrip]|
# |Pemimpin Rapat|[nama pemimpin rapat berdasarkan transkrip]|
# |Dibuat oleh|[Group Transformasi Korporasi dan Manajemen Program]|

# **Agenda:**
# - [daftar agenda rapat berdasarkan transkrip]

# **Peserta Rapat:**
# |No||Nama/Jabatan|
# |---|---|---|
# |1|[nama dan jabatan peserta 1]|
# |2|[nama dan jabatan peserta 2]|
# |[dan seterusnya]|

# |Poin Diskusi dan Arahan|Penanggung Jawab|
# |---|---|
# |[Topik diskusi 1]||
# [Penjelasan Topik singkat]
# |Kesimpulan :||
# |• [kesimpulan point 1]|[penanggung jawab]|
# |[Topik diskusi 2]||
# [Penjelasan Topik singkat]
# |Kesimpulan :||
# |• [kesimpulan point 2]|[penanggung jawab]|
# |[dan seterusnya untuk semua topik]|

# **Disclaimer:**
# _Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final._

# INSTRUKSI KHUSUS:
# 1. Gunakan format tabel persis seperti contoh di atas
# 2. Ekstrak semua informasi dari transkrip yang diberikan
# 3. Untuk kolom "Penanggung Jawab", identifikasi pihak yang bertanggung jawab berdasarkan diskusi
# 4. Gunakan bahasa Indonesia yang formal dan profesional
# 5. Jika informasi tidak tersedia dalam transkrip, gunakan [Tidak disebutkan dalam transkrip]
# 6. Jangan tambahkan elemen format lain selain yang ditentukan

# Catatan: Jika informasi tertentu tidak tersedia dalam transkrip, beri tanda [Tidak disebutkan dalam transkrip].
# """
        
#         # Generate content with safety settings
#         generation_config = {
#             "temperature": 0.3,
#             "top_p": 0.8,
#             "top_k": 40,
#             "max_output_tokens": 2048,
#         }
        
#         # ADD SAFETY SETTINGS TO PREVENT INPUT BLOCKING
#         # You've already done this, which helps ensure the input transcript is not the issue.
#         safety_settings = [
#             {
#                 "category": "HARM_CATEGORY_HARASSMENT",
#                 "threshold": "BLOCK_NONE"
#             },
#             {
#                 "category": "HARM_CATEGORY_HATE_SPEECH", 
#                 "threshold": "BLOCK_NONE"
#             },
#             {
#                 "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
#                 "threshold": "BLOCK_NONE"
#             },
#             {
#                 "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
#                 "threshold": "BLOCK_NONE"
#             }
#         ]
        
#         response = model.generate_content(
#             prompt, 
#             generation_config=generation_config,
#             safety_settings=safety_settings
#         )
        
#         # Check if response was blocked (Input filtering)
#         if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
#             return {
#                 'success': False,
#                 'content': None,
#                 'error': f"Response blocked due to input content: {response.prompt_feedback.block_reason}"
#             }
        
#         # Check if response has candidates (Output filtering - Finish Reason 2)
#         if hasattr(response, 'candidates') and response.candidates:
#             candidate = response.candidates[0]
#             # This is the line that captures the OUTPUT safety filter
#             if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
#                 # Provide a more specific error message based on the safety filter.
#                 return {
#                     'success': False,
#                     'content': None,
#                     'error': "Response was filtered for safety reasons. The model's output likely contained sensitive content. Please review and edit your transcript."
#                 }
#             # Get text from candidate
#             if candidate.content.parts:
#                 content_text = candidate.content.parts[0].text
#                 if content_text:
#                     cleaned_response = content_text.strip()
                    
#                     # Ensure the response starts with the correct header
#                     if not cleaned_response.startswith("# Notulen Rapat"):
#                         lines = cleaned_response.split('\n')
#                         for i, line in enumerate(lines):
#                             if "Notulen Rapat" in line:
#                                 cleaned_response = '\n'.join(lines[i:])
#                                 break
                    
#                     return {
#                         'success': True,
#                         'content': cleaned_response,
#                         'error': None
#                     }
        
#         return {
#             'success': False,
#             'content': None,
#             'error': 'Empty response from model'
#         }
            
#     except Exception as e:
#         return {
#             'success': False,
#             'content': None,
#             'error': f"API Error: {str(e)}"
#         }

# def create_word_document(content, filename):
#     """
#     Create a Word document from the generated content
#     """
#     try:
#         doc = Document()
        
#         # Set document margins
#         sections = doc.sections
#         for section in sections:
#             section.top_margin = Inches(1)
#             section.bottom_margin = Inches(1)
#             section.left_margin = Inches(1)
#             section.right_margin = Inches(1)
        
#         # Add title
#         title = doc.add_heading('Notulen Rapat', level=0)
#         title.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         title_run = title.runs[0]
#         title_run.font.size = Pt(16)
#         title_run.font.bold = True
        
#         # Add the content as simple text
#         content_para = doc.add_paragraph(content)
        
#         # Save to bytes buffer
#         buffer = io.BytesIO()
#         doc.save(buffer)
#         buffer.seek(0)
        
#         return buffer
        
#     except Exception as e:
#         st.error(f"Error creating Word document: {e}")
#         return None

# def chat_with_transcript(question, transcript_text, api_key, chat_history=None):
#     """
#     Function for interactive chat based on the uploaded transcript
#     """
#     try:
#         # Configure API
#         genai.configure(api_key=api_key)
        
#         # Initialize model
#         model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-09-2025")
        
#         # Create context from transcript
#         context = f"""
#         Berikut adalah transkrip rapat yang akan digunakan sebagai referensi untuk menjawab pertanyaan:

#         {transcript_text}

#         INSTRUKSI:
#         1. JAWAB PERTANYAAN BERDASARKAN TRANSCRIPT DI ATAS SAJA
#         2. Jika informasi tidak ada dalam transcript, katakan "Informasi tidak ditemukan dalam transkrip"
#         3. Gunakan bahasa Indonesia yang formal dan profesional
#         4. Berikan jawaban yang spesifik berdasarkan data yang ada dalam transkrip
#         5. Jangan membuat informasi yang tidak ada dalam transkrip

#         Pertanyaan: {question}
#         """
        
#         # Generate content with safety settings
#         generation_config = {
#             "temperature": 0.3,
#             "top_p": 0.8,
#             "top_k": 40,
#             "max_output_tokens": 1024,
#         }
        
#         safety_settings = [
#             {
#                 "category": "HARM_CATEGORY_HARASSMENT",
#                 "threshold": "BLOCK_NONE"
#             },
#             {
#                 "category": "HARM_CATEGORY_HATE_SPEECH", 
#                 "threshold": "BLOCK_NONE"
#             },
#             {
#                 "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
#                 "threshold": "BLOCK_NONE"
#             },
#             {
#                 "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
#                 "threshold": "BLOCK_NONE"
#             }
#         ]
        
#         response = model.generate_content(
#             context, 
#             generation_config=generation_config,
#             safety_settings=safety_settings
#         )
        
#         if response.text:
#             return {
#                 'success': True,
#                 'content': response.text,
#                 'error': None
#             }
#         else:
#             return {
#                 'success': False,
#                 'content': None,
#                 'error': 'Empty response from model'
#             }
            
#     except Exception as e:
#         return {
#             'success': False,
#             'content': None,
#             'error': f"Chat Error: {str(e)}"
#         }

# def main():
#     st.set_page_config(
#         page_title="Notulen Zoom Meeting Generator by TKMP",
#         page_icon="📝",
#         layout="wide",
#         initial_sidebar_state="expanded"
#     )

#     # Custom CSS for better styling
#     st.markdown("""
#     <style>
#     .main-header {
#         text-align: center;
#         padding: 2rem 0;
#         background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         background-clip: text;
#         font-size: 2.5rem;
#         font-weight: bold;
#         margin-bottom: 1rem;
#     }
#     .sub-header {
#         text-align: center;
#         color: #666;
#         margin-bottom: 2rem;
#     }
#     .stButton>button {
#         background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         border: none;
#         border-radius: 8px;
#         padding: 0.75rem 1.5rem;
#         font-weight: 600;
#     }
#     .success-box {
#         background: #d4edda;
#         color: #155724;
#         padding: 1rem;
#         border-radius: 8px;
#         border: 1px solid #c3e6cb;
#         margin: 1rem 0;
#     }
#     .error-box {
#         background: #f8d7da;
#         color: #721c24;
#         padding: 1rem;
#         border-radius: 8px;
#         border: 1px solid #f5c6cb;
#         margin: 1rem 0;
#     }
#     .chat-message {
#         padding: 1rem;
#         border-radius: 8px;
#         margin: 0.5rem 0;
#     }
#     .user-message {
#         background: #e3f2fd;
#         border-left: 4px solid #2196f3;
#     }
#     .assistant-message {
#         background: #f3e5f5;
#         border-left: 4px solid #9c27b0;
#     }
#     .info-box {
#         background: #e8f4fd;
#         color: #0c5460;
#         padding: 1rem;
#         border-radius: 8px;
#         border: 1px solid #b8daff;
#         margin: 1rem 0;
#     }
#     </style>
#     """, unsafe_allow_html=True)

#     # Header
#     st.markdown('<h1 class="main-header">📝 Notulen Zoom Meeting Generator by TKMP</h1>', unsafe_allow_html=True)
#     st.markdown('<p class="sub-header">Generate Notulen dengan praktis no ribet</p>', unsafe_allow_html=True)
    
#     # Get API key from secrets.toml
#     try:
#         api_key = st.secrets["api_key"]
#         api_key_available = True
#     except (KeyError, FileNotFoundError):
#         api_key = None
#         api_key_available = False
    
#     # Sidebar
#     with st.sidebar:
#         st.header("⚙️ Configuration")
        
#         if api_key_available:
#             st.success("✅ API Key loaded successfully")
#         else:
#             st.error("❌ API Key not found")
#             st.info("""
#             **Setup Instructions:**
#             1. Create `.streamlit/secrets.toml`
#             2. Add your API key:
#             ```
#             api_key = "your_api_key_here"
#             ```
#             3. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
#             """)
        
#         st.header("📋 How to Use")
#         st.markdown("""
#         1. **Upload** transkrip Zoom Anda
#         2. **Process** transkrip dengan tombol
#         3. **Review** Notulen yang sudah jadi
#         4. **Re-Generate** dengan klik tombol generate jika hasil kurang memuaskan
#         5. **Chat** dengan konten transkrip apabila ingin menanyakan konten lebih spesifik
#         6. **Chat** bisa digunakan jika ada file VTT yang diupload
#         """)

#     # Main content - Tabs for different functionalities
#     tab1, tab2 = st.tabs(["📄 Generate Notulen", "💬 Chat dengan Transkrip"])

#     with tab1:
#         st.markdown("### 📁 Upload Transkrip")
        
#         uploaded_file = st.file_uploader(
#             "Pilih File",
#             type=['vtt', 'txt'],
#             help="Supported format: .vtt (Zoom transcript files) atau .txt",
#             key="file_uploader"
#         )
        
#         if uploaded_file is not None:
#             # Store the uploaded file content in session state
#             content = uploaded_file.getvalue().decode("utf-8")
#             st.session_state.uploaded_transcript = process_vtt_text(content)
            
#             # File info
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.info(f"**File:** {uploaded_file.name}")
#             with col2:
#                 st.info(f"**Size:** {uploaded_file.size:,} bytes")
#                 st.info(f"**Characters:** {len(st.session_state.uploaded_transcript):,}")
            
#             # Process button
#             if st.button("🚀 Generate Notulen", type="primary", use_container_width=True, key="generate_btn"):
#                 if not api_key_available:
#                     st.error("Please configure your API key in secrets.toml first")
#                     return
                    
#                 with st.spinner("🤖 AI sedang memproses transkrip..."):
#                     try:
#                         # Check if transcript has sufficient content
#                         if len(st.session_state.uploaded_transcript.strip()) < 50:
#                             st.error("❌ Transkrip terlalu pendek. Pastikan file berisi konten rapat yang cukup.")
#                             return
                        
#                         # Generate AI content
#                         ai_result = generate_notulen_with_ai(st.session_state.uploaded_transcript, api_key)
                        
#                         if ai_result['success']:
#                             st.session_state.ai_notulen = ai_result['content']
#                             st.session_state.processed = True
#                             st.success("✅ Generate Notulen berhasil!")
#                         else:
#                             st.error(f"❌ Error: {ai_result['error']}")
#                             if "safety" in ai_result['error'].lower() or "filter" in ai_result['error'].lower():
#                                 st.info("💡 **Tips**: Jika error ini berulang, coba **edit transkrip Anda** untuk menghapus konten yang mungkin sensitif atau coba **gunakan transkrip yang berbeda**.")
                            
#                     except Exception as e:
#                         st.error(f"❌ Processing error: {str(e)}")
        
#         # Display results
#         if 'ai_notulen' in st.session_state and st.session_state.get('processed', False):
#             st.divider()
#             st.markdown("### 📋 Generated Notulen")
            
#             # Success message
#             st.markdown('<div class="success-box">✅ <strong>Notulen sukses dibuat!</strong> Silahkan review hasilnya.</div>', unsafe_allow_html=True)
            
#             # Display the content
#             st.markdown(st.session_state.ai_notulen, unsafe_allow_html=True)
            
#             # Download section
#             st.divider()
#             st.markdown("### 📥 Download Options")
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 # Text download
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 st.download_button(
#                     label="📄 Download as TXT",
#                     data=st.session_state.ai_notulen,
#                     file_name=f"Notulen_meeting_{timestamp}.txt",
#                     mime="text/plain",
#                     use_container_width=True
#                 )
            
#             with col2:
#                 # Word document download
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 word_buffer = create_word_document(st.session_state.ai_notulen, f"Notulen_meeting_{timestamp}.docx")
#                 if word_buffer:
#                     st.download_button(
#                         label="📝 Download Word Document",
#                         data=word_buffer.getvalue(),
#                         file_name=f"Notulen_meeting_{timestamp}.docx",
#                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#                         use_container_width=True
#                     )
            
#             # Clear results button
#             if st.button("🗑️ Clear Results", use_container_width=True, key="clear_results"):
#                 if 'ai_notulen' in st.session_state:
#                     del st.session_state.ai_notulen
#                 if 'processed' in st.session_state:
#                     del st.session_state.processed
#                 st.rerun()

#     with tab2:
#         st.markdown("### 💬 Chat dengan Transkrip")
        
#         if 'uploaded_transcript' not in st.session_state or not st.session_state.uploaded_transcript:
#             st.markdown("""
#             <div class="info-box">
#                 <strong>📝 Informasi:</strong> Silakan upload file transkrip VTT terlebih dahulu di tab "Generate Notulen" 
#                 untuk mengaktifkan fitur chat.
#             </div>
#             """, unsafe_allow_html=True)
            
#             st.info("""
#             **Contoh pertanyaan yang bisa ditanyakan:**
#             - Siapa saja yang hadir dalam rapat?
#             - Apa agenda utama rapat ini?
#             - Keputusan apa yang diambil dalam rapat?
#             - Siapa yang bertanggung jawab untuk tindak lanjut?
#             - Kapan deadline yang disepakati?
#             """)
#         else:
#             st.markdown("""
#             <div class="success-box">
#                 ✅ <strong>Transkrip tersedia!</strong> Anda dapat bertanya tentang konten rapat.
#             </div>
#             """, unsafe_allow_html=True)
            
#             # Display transcript info
#             with st.expander("📊 Info Transkrip"):
#                 st.text(f"Panjang transkrip: {len(st.session_state.uploaded_transcript)} karakter")
#                 st.text(f"Jumlah baris: {st.session_state.uploaded_transcript.count(chr(10)) + 1}")
            
#             # Initialize chat history
#             if "chat_history" not in st.session_state:
#                 st.session_state.chat_history = []
            
#             # Display chat history
#             st.markdown("#### 💭 Percakapan")
#             for message in st.session_state.chat_history:
#                 if message["role"] == "user":
#                     st.markdown(f'<div class="chat-message user-message"><strong>👤 Anda:</strong> {message["content"]}</div>', unsafe_allow_html=True)
#                 else:
#                     st.markdown(f'<div class="chat-message assistant-message"><strong>🤖 AI:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            
#             # Chat input
#             st.markdown("#### 💬 Tanya tentang rapat")
#             user_input = st.text_area(
#                 "Pertanyaan Anda:",
#                 placeholder="Contoh: Siapa pemimpin rapat? Apa keputusan yang diambil? Siapa yang hadir?",
#                 key="chat_input",
#                 height=80
#             )
            
#             col1, col2, col3 = st.columns([1, 1, 2])
#             with col1:
#                 if st.button("Kirim Pertanyaan", use_container_width=True, key="send_chat"):
#                     if user_input.strip() and api_key_available:
#                         with st.spinner("🔍 Mencari informasi dalam transkrip..."):
#                             chat_result = chat_with_transcript(
#                                 user_input, 
#                                 st.session_state.uploaded_transcript, 
#                                 api_key
#                             )
                            
#                             if chat_result['success']:
#                                 # Add user message to history
#                                 st.session_state.chat_history.append({
#                                     "role": "user", 
#                                     "content": user_input
#                                 })
                                
#                                 # Add AI response to history
#                                 st.session_state.chat_history.append({
#                                     "role": "assistant",
#                                     "content": chat_result['content']
#                                 })
                                
#                                 # Clear input and rerun to update display
#                                 st.rerun()
#                             else:
#                                 st.error(f"Error: {chat_result['error']}")
#                     elif not api_key_available:
#                         st.error("API Key tidak tersedia. Silakan konfigurasi di sidebar.")
#                     elif not user_input.strip():
#                         st.warning("Silakan ketik pertanyaan terlebih dahulu.")
            
#             with col2:
#                 if st.button("Hapus Chat", use_container_width=True, key="clear_chat"):
#                     st.session_state.chat_history = []
#                     st.rerun()
            
#             with col3:
#                 st.info("💡 Tanya tentang peserta, agenda, keputusan, atau hal spesifik dari rapat")
    
#     # Footer
#     st.divider()
#     st.markdown("""
#     <div style='text-align: center; color: #666; padding: 2rem;'>
#         <p>Dibuat dengan ❤️ oleh TKMP</p>
#     </div>
#     """, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()
