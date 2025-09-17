import streamlit as st
import re
from datetime import datetime
import io
import os
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def process_vtt_text(vtt_text):
    """
    Process VTT text exactly like the original Python code
    """
    # Clean timestamp & metadata
    cleaned_text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt_text)
    cleaned_text = re.sub(r"WEBVTT.*\n", "", cleaned_text)
    cleaned_text = "\n".join([line.strip() for line in cleaned_text.splitlines() if line.strip()])

    # Split into sentences
    sentences = cleaned_text.split(". ")
    sentences = [s.strip() for s in sentences if s.strip()]

    # Take key sentence every 5 sentences (exactly like original)
    summary = []
    for i in range(0, len(sentences), 5):
        if i < len(sentences):
            summary.append(sentences[i])

    return {
        'summary': summary,
        'full_text': cleaned_text,
        'original_length': len(sentences),
        'summary_length': len(summary),
        'sentences': sentences
    }

def generate_notulen(summary):
    """
    Generate meeting notes exactly like the original code
    """
    notulen = "📌 Notulen Rapat\n\n"
    notulen += "Ringkasan:\n" + "\n".join(f"- {s.strip()}" for s in summary if s.strip())
    return notulen

def generate_notulen_with_ai(sentences, api_key):
    """
    Generate formal meeting minutes using Google Gemini API
    Uses the exact backend code provided
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
|Kesimpulan :||
|• [kesimpulan point 1]|[penanggung jawab]|
|[Topik diskusi 2]||
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
        
        # Generate content exactly as in the backend code
        response = model.generate_content(prompt)
        
        if response and response.text:
            # Clean up the response
            cleaned_response = response.text.strip()
            
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
        page_title="Meeting Transcript Processor",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    table, th, td {
        border: 1px solid #ddd;
        padding: 8px;
    }
    th {
        background-color: #f2f2f2;
        text-align: left;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">📝 Meeting Transcript Processor</h1>', unsafe_allow_html=True)
    st.markdown("Transform your Zoom meeting transcripts into concise summaries")
    
    # Get API key from secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        api_key_available = True
    except (KeyError, FileNotFoundError):
        api_key = None
        api_key_available = False
    
    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ How to Use")
        st.markdown("""
        1. **Upload VTT File**: Select your Zoom transcript file
        2. **Process**: Click to analyze the transcript
        3. **Review**: Check the generated summary
        4. **Download**: Save your meeting notes
        """)
        
        st.header("🤖 AI-Powered Processing")
        
        if api_key_available:
            st.success("✅ API Key loaded from secrets")
            st.markdown("""
            **Gemini API Integration:**
            - Formal Indonesian meeting minutes
            - Professional table formatting
            - Structured agenda extraction
            - Participant identification
            """)
        else:
            st.warning("⚠️ API Key not found in secrets")
            st.markdown("""
            **To enable AI features:**
            1. Create a `.streamlit/secrets.toml` file
            2. Add your Gemini API key:
            ```
            GEMINI_API_KEY = "your_api_key_here"
            ```
            3. Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
            """)
        
        st.header("🚀 Deploy for Free")
        st.markdown("""
        **Hosting Options:**
        - Streamlit Community Cloud
        - Hugging Face Spaces
        - Railway
        - Render
        """)

    # Main content
    tab1, tab2, tab3 = st.tabs(["📁 Upload File", "🤖 AI Processing", "🔗 Zoom URL (Coming Soon)"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Upload VTT Transcript")
            uploaded_file = st.file_uploader(
                "Choose a VTT file",
                type=['vtt'],
                help="Upload the VTT transcript file from your Zoom recording"
            )
            
            if uploaded_file is not None:
                st.success(f"File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
                
                if st.button("🔄 Process Transcript", type="primary", key="process_btn"):
                    with st.spinner("Processing transcript..."):
                        # Read and process the file
                        content = uploaded_file.getvalue().decode("utf-8")
                        result = process_vtt_text(content)
                        
                        # Store in session state
                        st.session_state.result = result
                        st.session_state.notulen = generate_notulen(result['summary'])
                        st.success("✅ Transcript processed successfully!")
    
    with tab2:
        st.subheader("🤖 AI-Powered Formal Minutes Generation")
        
        if 'result' not in st.session_state:
            st.info("📁 Please upload and process a VTT file first in the 'Upload File' tab")
        else:
            if api_key_available:
                st.success("✅ API Key loaded from secrets.toml")
                
                if st.button("🚀 Generate Formal Meeting Minutes", type="primary", key="ai_btn"):
                    with st.spinner("🤖 Generating formal notulen with AI..."):
                        result = st.session_state.result
                        full_text = result['full_text']
                        
                        # Generate AI content
                        ai_result = generate_notulen_with_ai(full_text, api_key)
                        
                        if ai_result['success']:
                            st.session_state.ai_notulen = ai_result['content']
                            st.success("✅ Formal meeting minutes generated successfully!")
                        else:
                            st.error(f"❌ Error generating AI content: {ai_result['error']}")
            else:
                st.error("❌ API Key not available")
                st.info("""
                **To enable AI features:**
                1. Create a `.streamlit/secrets.toml` file in your project directory
                2. Add your Gemini API key:
                ```
                GEMINI_API_KEY = "your_actual_api_key_here"
                ```
                3. Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
                4. Restart the application
                """)
                
                # Fallback: Allow manual API key input
                manual_api_key = st.text_input(
                    "Or enter API key manually:",
                    type="password",
                    help="Get your free API key from https://makersuite.google.com/app/apikey",
                    key="manual_api_key"
                )
                
                if manual_api_key:
                    if st.button("🚀 Generate with Manual API Key", key="manual_ai_btn"):
                        with st.spinner("🤖 Generating formal notulen with AI..."):
                            result = st.session_state.result
                            full_text = result['full_text']
                            
                            # Generate AI content
                            ai_result = generate_notulen_with_ai(full_text, manual_api_key)
                            
                            if ai_result['success']:
                                st.session_state.ai_notulen = ai_result['content']
                                st.success("✅ Formal meeting minutes generated successfully!")
                            else:
                                st.error(f"❌ Error generating AI content: {ai_result['error']}")

    with tab3:
        st.subheader("🔗 Zoom Recording URL")
        st.info("This feature requires backend integration and will be available in future updates.")
        
        zoom_url = st.text_input("Zoom Recording URL", placeholder="https://zoom.us/rec/share/...")
        passcode = st.text_input("Passcode (if required)", type="password")
        st.button("Process URL", disabled=True, help="Coming soon!")

    # Results section - Basic Summary
    if 'result' in st.session_state and 'notulen' in st.session_state:
        st.divider()
        st.subheader("📋 Basic Summary Results")
        
        result = st.session_state.result
        notulen = st.session_state.notulen
        
        # Display the basic summary
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.text_area(
                "Basic Summary (Every 5th Sentence)",
                value=notulen,
                height=300,
                help="Your basic processed meeting summary"
            )
        
        with col2:
            st.subheader("📥 Download Options")
            
            # Prepare download content
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            download_content = f"""Meeting Summary - {timestamp}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{notulen}

Statistics:
- Original sentences: {result['original_length']}
- Summary points: {result['summary_length']}
- Compression ratio: {((result['summary_length'] / result['original_length']) * 100):.1f}%

Full processed text:
{result['full_text'][:500]}{'...' if len(result['full_text']) > 500 else ''}
"""
            
            st.download_button(
                label="📄 Download as TXT",
                data=download_content,
                file_name=f"meeting_summary_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            # Additional download format
            csv_content = "Point,Summary\n" + "\n".join([f"{i+1},\"{point}\"" for i, point in enumerate(result['summary'])])
            st.download_button(
                label="📊 Download as CSV",
                data=csv_content,
                file_name=f"meeting_summary_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            if st.button("🗑️ Clear Basic Results", key="clear_basic"):
                if 'result' in st.session_state:
                    del st.session_state.result
                if 'notulen' in st.session_state:
                    del st.session_state.notulen
                st.rerun()

    # AI Results section - Formal Meeting Minutes
    if 'ai_notulen' in st.session_state:
        st.divider()
        st.subheader("🤖 AI-Generated Formal Meeting Minutes")
        
        ai_content = st.session_state.ai_notulen
        
        # Display AI-generated content
        st.markdown(ai_content, unsafe_allow_html=True)
        
        # Download section
        st.subheader("📥 Download AI Results")
        col1, col2 = st.columns(2)
        
        with col1:
            # Prepare download content
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Text download
            st.download_button(
                label="📄 Download as TXT",
                data=ai_content,
                file_name=f"formal_notulen_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # Word document download
            if st.button("📄 Generate Word Document", use_container_width=True, key="word_btn"):
                with st.spinner("Creating Word document..."):
                    word_buffer = create_word_document(ai_content, f"notulen_{timestamp}.docx")
                    if word_buffer:
                        st.download_button(
                            label="📄 Download Word Document",
                            data=word_buffer.getvalue(),
                            file_name=f"Notulen_Rapat_{timestamp}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
            
            if st.button("🗑️ Clear AI Results", key="clear_ai"):
                if 'ai_notulen' in st.session_state:
                    del st.session_state.ai_notulen
                st.rerun()

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        Built with ❤️ using Streamlit | Process Zoom transcripts efficiently
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
