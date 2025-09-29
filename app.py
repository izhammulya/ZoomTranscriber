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
        
#         # Initialize model
#         # model = genai.GenerativeModel("gemini-2.5-flash")

#         model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
#         # EXACT PROMPT - NOT CHANGED
#         prompt = f"""
# Buatkan notulen rapat yang rapi dan formal dari transkrip rapat berikut, sertakan konten sensitif:

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
        
#         # ADD SAFETY SETTINGS TO PREVENT BLOCKING
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
        
#         # Check if response was blocked
#         if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
#             return {
#                 'success': False,
#                 'content': None,
#                 'error': f"Response blocked: {response.prompt_feedback.block_reason}"
#             }
        
#         # Check if response has candidates
#         if hasattr(response, 'candidates') and response.candidates:
#             candidate = response.candidates[0]
#             if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
#                 return {
#                     'success': False,
#                     'content': None,
#                     'error': "Response was filtered for safety reasons. Please try with different content."
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
#         4. **Download** format yang diinginkan
#         """)

#     # Main content
#     st.markdown("### 📁 Upload Transkrip")
    
#     uploaded_file = st.file_uploader(
#         "Pilih File",
#         type=['vtt', 'txt'],
#         help="Supported format: .vtt (Zoom transcript files) atau .txt"
#     )
    
#     if uploaded_file is not None:
#         # File info
#         col1, col2 = st.columns(2)
#         with col1:
#             st.info(f"**File:** {uploaded_file.name}")
#         with col2:
#             st.info(f"**Size:** {uploaded_file.size:,} bytes")
        
#         # Process button
#         if st.button("🚀 Generate Notulen", type="primary", use_container_width=True):
#             if not api_key_available:
#                 st.error("Please configure your API key in secrets.toml first")
#                 return
                
#             with st.spinner("🤖 AI sedang memproses transkrip..."):
#                 try:
#                     # Read and process the file
#                     content = uploaded_file.getvalue().decode("utf-8")
#                     cleaned_text = process_vtt_text(content)
                    
#                     # Check if transcript has sufficient content
#                     if len(cleaned_text.strip()) < 50:
#                         st.error("❌ Transkrip terlalu pendek. Pastikan file berisi konten rapat yang cukup.")
#                         return
                    
#                     # Generate AI content
#                     ai_result = generate_notulen_with_ai(cleaned_text, api_key)
                    
#                     if ai_result['success']:
#                         st.session_state.ai_notulen = ai_result['content']
#                         st.session_state.processed = True
#                         st.success("✅ Generate Notulen berhasil!")
#                     else:
#                         st.error(f"❌ Error: {ai_result['error']}")
#                         if "safety" in ai_result['error'].lower() or "filter" in ai_result['error'].lower():
#                             st.info("💡 **Tips**: Coba dengan transkrip yang berbeda atau edit konten transkrip Anda.")
                        
#                 except Exception as e:
#                     st.error(f"❌ Processing error: {str(e)}")
    
#     # Display results
#     if 'ai_notulen' in st.session_state and st.session_state.get('processed', False):
#         st.divider()
#         st.markdown("### 📋 Generated Notulen")
        
#         # Success message
#         st.markdown('<div class="success-box">✅ <strong>Notulen sukses dibuat!</strong> Silahkan review hasilnya.</div>', unsafe_allow_html=True)
        
#         # Display the content
#         st.markdown(st.session_state.ai_notulen, unsafe_allow_html=True)
        
#         # Download section
#         st.divider()
#         st.markdown("### 📥 Download Options")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             # Text download
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             st.download_button(
#                 label="📄 Download as TXT",
#                 data=st.session_state.ai_notulen,
#                 file_name=f"Notulen_meeting_{timestamp}.txt",
#                 mime="text/plain",
#                 use_container_width=True
#             )
        
#         with col2:
#             # Word document download
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             word_buffer = create_word_document(st.session_state.ai_notulen, f"Notulen_meeting_{timestamp}.docx")
#             if word_buffer:
#                 st.download_button(
#                     label="📝 Download Word Document",
#                     data=word_buffer.getvalue(),
#                     file_name=f"Notulen_meeting_{timestamp}.docx",
#                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#                     use_container_width=True
#                 )
        
#         # Clear results button
#         if st.button("🗑️ Clear Results", use_container_width=True):
#             if 'ai_notulen' in st.session_state:
#                 del st.session_state.ai_notulen
#             if 'processed' in st.session_state:
#                 del st.session_state.processed
#             st.rerun()
    
#     # Footer
#     st.divider()
#     st.markdown("""
#     <div style='text-align: center; color: #666; padding: 2rem;'>
#         <p>Dibuat dengan ❤️ oleh TKMP</p>
#     </div>
#     """, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()


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
        
        # Initialize model - CHANGED TO STANDARD FLASH MODEL
        # model = genai.GenerativeModel("gemini-2.5-flash")

        # model = genai.GenerativeModel("models/gemini-2.5-flash-lite") 
        model = model.GenerativeModel("gemini-2.5-flash-lite-preview-09-2025")
        
        # REFINED PROMPT with strong emphasis on professional, non-sensitive content
        prompt = f"""
**INI ADALAH DATA RAPAT FORMAL PERUSAHAAN. BUATKAN NOTULEN RAPAT DENGAN BAHASA INDONESIA YANG FORMAL DAN PROFESIONAL. HANYA FOKUS PADA AGENDA, DISKUSI, DAN KEPUTUSAN SAJA.**

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
        
        # Generate content with safety settings
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # ADD SAFETY SETTINGS TO PREVENT INPUT BLOCKING
        # You've already done this, which helps ensure the input transcript is not the issue.
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        response = model.generate_content(
            prompt, 
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Check if response was blocked (Input filtering)
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
            return {
                'success': False,
                'content': None,
                'error': f"Response blocked due to input content: {response.prompt_feedback.block_reason}"
            }
        
        # Check if response has candidates (Output filtering - Finish Reason 2)
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            # This is the line that captures the OUTPUT safety filter
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                # Provide a more specific error message based on the safety filter.
                return {
                    'success': False,
                    'content': None,
                    'error': "Response was filtered for safety reasons. The model's output likely contained sensitive content. Please review and edit your transcript."
                }
            # Get text from candidate
            if candidate.content.parts:
                content_text = candidate.content.parts[0].text
                if content_text:
                    cleaned_response = content_text.strip()
                    
                    # Ensure the response starts with the correct header
                    if not cleaned_response.startswith("# Notulen Rapat"):
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
        
        return {
            'success': False,
            'content': None,
            'error': 'Empty response from model'
        }
            
    except Exception as e:
        return {
            'success': False,
            'content': None,
            'error': f"API Error: {str(e)}"
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
        content_para = doc.add_paragraph(content)
        
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
        
        st.header("📋 How to Use")
        st.markdown("""
        1. **Upload** transkrip Zoom Anda
        2. **Process** transkrip dengan tombol
        3. **Review** Notulen yang sudah jadi
        4. **Download** format yang diinginkan
        """)

    # Main content
    st.markdown("### 📁 Upload Transkrip")
    
    uploaded_file = st.file_uploader(
        "Pilih File",
        type=['vtt', 'txt'],
        help="Supported format: .vtt (Zoom transcript files) atau .txt"
    )
    
    if uploaded_file is not None:
        # File info
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**File:** {uploaded_file.name}")
        with col2:
            st.info(f"**Size:** {uploaded_file.size:,} bytes")
        
        # Process button
        if st.button("🚀 Generate Notulen", type="primary", use_container_width=True):
            if not api_key_available:
                st.error("Please configure your API key in secrets.toml first")
                return
                
            with st.spinner("🤖 AI sedang memproses transkrip..."):
                try:
                    # Read and process the file
                    content = uploaded_file.getvalue().decode("utf-8")
                    cleaned_text = process_vtt_text(content)
                    
                    # Check if transcript has sufficient content
                    if len(cleaned_text.strip()) < 50:
                        st.error("❌ Transkrip terlalu pendek. Pastikan file berisi konten rapat yang cukup.")
                        return
                    
                    # Generate AI content
                    ai_result = generate_notulen_with_ai(cleaned_text, api_key)
                    
                    if ai_result['success']:
                        st.session_state.ai_notulen = ai_result['content']
                        st.session_state.processed = True
                        st.success("✅ Generate Notulen berhasil!")
                    else:
                        st.error(f"❌ Error: {ai_result['error']}")
                        if "safety" in ai_result['error'].lower() or "filter" in ai_result['error'].lower():
                            st.info("💡 **Tips**: Jika error ini berulang, coba **edit transkrip Anda** untuk menghapus konten yang mungkin sensitif atau coba **gunakan transkrip yang berbeda**.")
                        
                except Exception as e:
                    st.error(f"❌ Processing error: {str(e)}")
    
    # Display results
    if 'ai_notulen' in st.session_state and st.session_state.get('processed', False):
        st.divider()
        st.markdown("### 📋 Generated Notulen")
        
        # Success message
        st.markdown('<div class="success-box">✅ <strong>Notulen sukses dibuat!</strong> Silahkan review hasilnya.</div>', unsafe_allow_html=True)
        
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
        <p>Dibuat dengan ❤️ oleh TKMP</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()


