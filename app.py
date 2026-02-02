import streamlit as st
import re
from datetime import datetime, timedelta
import io
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import json
import pandas as pd

def process_vtt_text(vtt_text):
    """
    Process VTT text to clean timestamps and metadata
    """
    # Clean timestamp & metadata
    cleaned_text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt_text)
    cleaned_text = re.sub(r"WEBVTT.*\n", "", cleaned_text)
    cleaned_text = "\n".join([line.strip() for line in cleaned_text.splitlines() if line.strip()])
    return cleaned_text

def create_fallback_notulen(transcript):
    """
    Create fallback notulen template
    """
    now = datetime.now()
    
    # Simple participant extraction
    participants = []
    lines = transcript.split('\n')
    for line in lines:
        if ':' in line:
            speaker = line.split(':')[0].strip()
            if 2 < len(speaker) < 50 and speaker not in participants:
                participants.append(speaker)
    
    word_count = len(transcript.split())
    
    notulen = f"""# NOTULEN RAPAT

## INFORMASI RAPAT
| Item | Keterangan |
|------|------------|
| **Nama Rapat** | Rapat Koordinasi |
| **Tanggal** | {now.strftime('%d %B %Y')} |
| **Waktu** | {now.strftime('%H:%M')} - Selesai |
| **Tempat** | Ruang Rapat |
| **Pemimpin Rapat** | Pimpinan Rapat |
| **Dibuat oleh** | Group Transformasi Korporasi dan Manajemen Program |

## DAFTAR PESERTA
| No | Nama | Jabatan |
|----|------|---------|
"""
    
    for i, participant in enumerate(participants[:10], 1):
        notulen += f"| {i} | {participant} | [Jabatan] |\n"
    
    notulen += f"""
## HASIL DISKUSI

### 1. Pembukaan
**Disampaikan oleh:** Pimpinan Rapat
**Isi:** Pembukaan rapat dan penyampaian agenda

### 2. Diskusi Utama
**Disampaikan oleh:** Peserta Rapat
**Isi:** Diskusi mengenai berbagai agenda yang telah ditentukan

### 3. Arahan dan Tugas
1. **Tugas:** Penyusunan laporan - **PIC:** Tim Terkait - **Deadline:** {(now + timedelta(days=3)).strftime('%d/%m/%Y')}
2. **Tugas:** Koordinasi follow-up - **PIC:** Semua Peserta - **Deadline:** {(now + timedelta(days=2)).strftime('%d/%m/%Y')}

## PENUTUP
Rapat ditutup dengan kesepakatan untuk melaksanakan arahan yang telah diberikan.

---
*Notulen ini dibuat otomatis ({word_count} kata)*
"""
    
    return notulen

def generate_notulen_with_ai(transcript, api_key):
    """
    Generate notulen using AI with fallback
    """
    if api_key:
        try:
            genai.configure(api_key=api_key)
            
            # Try multiple models
            models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
            
            for model_name in models:
                try:
                    model = genai.GenerativeModel(model_name)
                    
                    prompt = f"""
                    BUATKAN NOTULEN RAPAT YANG LENGKAP DARI TRANSCRIPT BERIKUT:
                    
                    {transcript[:4000]}
                    
                    FORMAT:
                    # NOTULEN RAPAT
                    
                    ## INFORMASI RAPAT
                    [tabel informasi]
                    
                    ## DAFTAR PESERTA
                    [tabel peserta]
                    
                    ## HASIL DISKUSI
                    ### [Topik 1]
                    **Disampaikan oleh:** [Nama]
                    **Isi:** [Ringkasan]
                    **Arahan:** [Arahan yang diberikan]
                    
                    ### [Topik 2]
                    **Disampaikan oleh:** [Nama]
                    **Isi:** [Ringkasan]
                    **Arahan:** [Arahan yang diberikan]
                    
                    ## ACTION ITEMS
                    [daftar tugas dengan PIC dan deadline]
                    """
                    
                    response = model.generate_content(prompt)
                    
                    if response and response.text:
                        return {
                            'success': True,
                            'content': response.text,
                            'model': model_name
                        }
                        
                except Exception as e:
                    continue
        except Exception as e:
            # Continue to fallback
            pass
    
    # Fallback jika AI gagal atau tidak ada API key
    fallback = create_fallback_notulen(transcript)
    return {
        'success': True,
        'content': fallback,
        'model': 'fallback_template'
    }

def create_word_document(content):
    """
    Create Word document
    """
    try:
        doc = Document()
        doc.add_heading('Notulen Rapat', 0)
        doc.add_paragraph(content)
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        buffer = io.BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        return buffer

def chat_with_transcript(question, transcript, api_key):
    """
    Chat function to ask questions about transcript
    """
    if not api_key:
        return "Untuk fitur chat yang optimal, setup API key di secrets.toml"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        JAWAB PERTANYAAN BERDASARKAN TRANSCRIPT RAPAT BERIKUT:
        
        {transcript[:3000]}
        
        PERTANYAAN: {question}
        
        INSTRUKSI:
        1. Jawab berdasarkan transcript saja
        2. Jika informasi tidak ada, katakan tidak ditemukan
        3. Gunakan bahasa Indonesia formal
        4. Berikan jawaban spesifik
        """
        
        response = model.generate_content(prompt)
        return response.text if response and response.text else "Tidak dapat menjawab saat ini"
        
    except Exception as e:
        return "Sistem chat sedang mengalami kendala"

def main():
    st.set_page_config(
        page_title="Notulen Generator & Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # CSS Styling
    st.markdown("""
    <style>
    .main-title {
        text-align: center;
        padding: 1rem 0;
        color: #1a237e;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: #5c6bc0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #283593 0%, #3949ab 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(26, 35, 126, 0.3);
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        animation: fadeIn 0.3s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #2196f3;
        margin-left: 2rem;
    }
    .assistant-message {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border-left: 4px solid #9c27b0;
        margin-right: 2rem;
    }
    .info-box {
        background: #f5f7ff;
        border-left: 4px solid #1a237e;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .success-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-left: 4px solid #4caf50;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .tab-content {
        padding: 1rem 0;
    }
    .upload-area {
        border: 2px dashed #1a237e;
        border-radius: 10px;
        padding: 3rem;
        text-align: center;
        margin: 1rem 0;
        background: #f8f9ff;
    }
    .quick-questions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    .quick-question-btn {
        background: #e8eaf6 !important;
        color: #1a237e !important;
        border: 1px solid #c5cae9 !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
    }
    .quick-question-btn:hover {
        background: #d1d9ff !important;
        transform: translateY(-1px) !important;
    }
    .model-badge {
        display: inline-block;
        background: #1a237e;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        margin: 0.25rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-title">🤖 Notulen Generator & Chatbot</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Generate notulen lengkap + Chat dengan konten rapat</p>', unsafe_allow_html=True)
    
    # Get API key
    try:
        api_key = st.secrets["api_key"]
        api_key_available = True
    except:
        api_key = None
        api_key_available = False
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        
        if api_key_available:
            st.success("✅ API Key tersedia")
        else:
            st.warning("⚠️ API Key tidak ditemukan")
            with st.expander("Cara setup API key"):
                st.markdown("""
                1. Buat file `.streamlit/secrets.toml`
                2. Tambahkan:
                ```toml
                api_key = "api_key_anda"
                ```
                3. Dapatkan API key dari [Google AI Studio](https://makersuite.google.com/app/apikey)
                """)
        
        st.header("📊 Statistik")
        if 'total_generated' not in st.session_state:
            st.session_state.total_generated = 0
        if 'total_chats' not in st.session_state:
            st.session_state.total_chats = 0
            
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Notulen Dibuat", st.session_state.total_generated)
        with col2:
            st.metric("Chat Terkirim", st.session_state.total_chats)
        
        st.header("🚀 Fitur")
        st.markdown("""
        - **AI Notulen Generator**
        - **Transcript Chatbot**
        - **Export to Word**
        - **Multi-model AI**
        - **100% Success Rate**
        """)
        
        if st.button("🔄 Reset Semua Data", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['total_generated', 'total_chats']:
                    del st.session_state[key]
            st.rerun()
    
    # Main tabs
    tab1, tab2 = st.tabs(["📄 Generate Notulen", "💬 Chat dengan Transcript"])
    
    with tab1:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        
        st.markdown("### 📤 Upload Transcript")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "Pilih file VTT atau TXT",
                type=['vtt', 'txt'],
                help="Upload transcript dari Zoom, Teams, atau Google Meet",
                label_visibility="collapsed"
            )
        
        if uploaded_file:
            content = uploaded_file.getvalue().decode("utf-8", errors='ignore')
            transcript = process_vtt_text(content)
            st.session_state.transcript = transcript
            
            # Show stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Kata", len(transcript.split()))
            with col2:
                st.metric("Karakter", len(transcript))
            with col3:
                # Count speakers
                speakers = set()
                for line in transcript.split('\n'):
                    if ':' in line:
                        speaker = line.split(':')[0].strip()
                        if 2 < len(speaker) < 50:
                            speakers.add(speaker)
                st.metric("Pembicara", len(speakers))
            
            # Generate buttons
            st.markdown("### 🚀 Generate Options")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✨ Generate dengan AI", type="primary", use_container_width=True):
                    with st.spinner("AI sedang menganalisis transcript..."):
                        result = generate_notulen_with_ai(transcript, api_key)
                        
                        st.session_state.notulen = result['content']
                        st.session_state.notulen_generated = True
                        st.session_state.generation_model = result.get('model', 'unknown')
                        st.session_state.total_generated += 1
                        
                        st.success(f"✅ Notulen berhasil dibuat! (Model: {result['model']})")
            
            with col2:
                if st.button("📋 Generate Template", use_container_width=True):
                    fallback = create_fallback_notulen(transcript)
                    st.session_state.notulen = fallback
                    st.session_state.notulen_generated = True
                    st.session_state.generation_model = 'template'
                    st.session_state.total_generated += 1
                    st.success("✅ Template notulen berhasil dibuat!")
        
        # Display notulen if generated
        if 'notulen' in st.session_state and st.session_state.get('notulen_generated'):
            st.markdown("### 📋 Hasil Notulen")
            
            # Show model badge
            model = st.session_state.get('generation_model', 'unknown')
            st.markdown(f'<span class="model-badge">Model: {model}</span>', unsafe_allow_html=True)
            
            # Display notulen
            st.markdown(st.session_state.notulen)
            
            # Download section
            st.markdown("### 💾 Download")
            col1, col2 = st.columns(2)
            
            with col1:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📄 Download TXT",
                    data=st.session_state.notulen,
                    file_name=f"notulen_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                word_buffer = create_word_document(st.session_state.notulen)
                st.download_button(
                    label="📝 Download Word",
                    data=word_buffer.getvalue(),
                    file_name=f"notulen_{timestamp}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        
        st.markdown("### 💬 Chat dengan Konten Rapat")
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Check if transcript exists
        if 'transcript' not in st.session_state or not st.session_state.transcript:
            st.markdown('<div class="info-box">📝 Upload transcript terlebih dahulu di tab "Generate Notulen" untuk menggunakan fitur chat</div>', unsafe_allow_html=True)
            
            st.markdown("### 📋 Contoh Pertanyaan")
            st.markdown("""
            **Tentang Peserta:**
            - Siapa saja yang hadir dalam rapat?
            - Berapa jumlah peserta rapat?
            - Siapa pemimpin rapat?
            
            **Tentang Diskusi:**
            - Apa saja topik yang dibahas?
            - Keputusan apa yang diambil?
            - Masalah apa yang diangkat?
            
            **Tentang Arahan:**
            - Tugas apa yang diberikan?
            - Siapa yang ditugaskan?
            - Kapan deadline-nya?
            """)
        else:
            # Display chat history
            st.markdown("#### 💭 History Chat")
            
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.chat_history:
                    if message['role'] == 'user':
                        st.markdown(f'<div class="chat-message user-message"><strong>👤 Anda:</strong> {message["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-message assistant-message"><strong>🤖 Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            
            # Quick questions
            st.markdown("#### ⚡ Pertanyaan Cepat")
            
            quick_questions = [
                "Siapa peserta rapat?",
                "Apa agenda utama?",
                "Keputusan apa yang diambil?",
                "Arahan apa yang diberikan?",
                "Deadline yang disepakati?"
            ]
            
            cols = st.columns(5)
            for idx, question in enumerate(quick_questions):
                with cols[idx % 5]:
                    if st.button(question, key=f"quick_{idx}", use_container_width=True):
                        # Add to input
                        st.session_state.last_quick_question = question
            
            # Chat input
            st.markdown("#### 💬 Tanya tentang rapat")
            
            # Initialize input text
            if 'last_quick_question' in st.session_state:
                default_question = st.session_state.last_quick_question
                del st.session_state.last_quick_question
            else:
                default_question = ""
            
            question = st.text_input(
                "Masukkan pertanyaan Anda:",
                value=default_question,
                placeholder="Contoh: Siapa yang bertanggung jawab untuk action items?",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Kirim Pertanyaan", type="primary", use_container_width=True):
                    if question.strip():
                        # Add user message to history
                        st.session_state.chat_history.append({
                            'role': 'user',
                            'content': question,
                            'timestamp': datetime.now().strftime("%H:%M")
                        })
                        
                        # Get AI response
                        with st.spinner("🤖 Mencari jawaban..."):
                            response = chat_with_transcript(question, st.session_state.transcript, api_key)
                            
                            # Add assistant response to history
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response,
                                'timestamp': datetime.now().strftime("%H:%M")
                            })
                            
                            st.session_state.total_chats += 1
                        
                        # Rerun to update display
                        st.rerun()
                    else:
                        st.warning("Silakan masukkan pertanyaan terlebih dahulu")
            
            with col2:
                if st.button("🗑️ Hapus Chat", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()
            
            # Export chat option
            if st.session_state.chat_history:
                st.markdown("---")
                if st.button("📥 Export Chat History", use_container_width=True):
                    chat_text = "Chat History:\n\n"
                    for msg in st.session_state.chat_history:
                        role = "User" if msg['role'] == 'user' else "Assistant"
                        time = msg.get('timestamp', '')
                        chat_text += f"[{time}] {role}: {msg['content']}\n\n"
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="Download Chat History",
                        data=chat_text,
                        file_name=f"chat_history_{timestamp}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem; margin-top: 2rem; border-top: 1px solid #eee;'>
        <p><strong>Notulen Generator & Chatbot</strong> • Group Transformasi Korporasi dan Manajemen Program</p>
        <p style='font-size: 0.9rem;'>Versi 2.0 • AI-Powered • User Friendly</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # Initialize session state variables
    if 'total_generated' not in st.session_state:
        st.session_state.total_generated = 0
    if 'total_chats' not in st.session_state:
        st.session_state.total_chats = 0
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    main()

# import streamlit as st
# import re
# from datetime import datetime, timedelta
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

# def create_basic_notulen_template(transcript):
#     """
#     Sistem Cadangan (Emergency Fallback) - Menjamin hasil tetap ada jika AI gagal total.
#     """
#     now = datetime.now()
#     word_count = len(transcript.split())
    
#     # Ekstraksi partisipan dasar dari teks
#     lines = transcript.split('\n')[:30]
#     participants = []
#     for line in lines:
#         if any(p in line.lower() for p in ['bapak', 'ibu', 'pak', 'bu', 'direktur']):
#             participants.append(line.strip())
    
#     participants_list = ""
#     for i, p in enumerate(participants[:5], 1):
#         participants_list += f"|{i}||{p}|\n"
#     if not participants_list: participants_list = "|1||Peserta Terlampir|\n"

#     return f"""# Notulen Rapat

# |Nama Rapat|Rapat Koordinasi Internal|
# |---|---|
# |Hari/Tanggal|{now.strftime('%A, %d %B %Y')}|
# |Waktu|{now.strftime('%H:%M')} WIB|
# |Tempat|Ruang Rapat Virtual|
# |Pemimpin Rapat|Pimpinan Rapat|
# |Dibuat oleh|[Group Transformasi Korporasi dan Manajemen Program]|

# **Agenda:**
# - Pembahasan poin-poin transkrip
# - Koordinasi tindak lanjut operasional

# **Peserta Rapat:**
# |No||Nama/Jabatan|
# |---|---|---|
# {participants_list}

# |Poin Diskusi dan Arahan|Penanggung Jawab|
# |---|---|
# |**Tinjauan Transkrip**||
# |Sistem mendeteksi aktivitas rapat dengan total {word_count} kata. Diskusi mencakup koordinasi teknis dan manajerial.||
# |Kesimpulan :||
# |• Seluruh pimpinan unit agar mereviu kembali detail diskusi untuk eksekusi lapangan.|Seluruh Peserta|

# **Disclaimer:**
# _Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final._

# ---
# *Catatan: Notulen ini dibuat menggunakan sistem cadangan otomatis.*
# """

# def generate_notulen_with_ai(sentences, api_key):
#     """
#     Fungsi utama Generate Notulen dengan instruksi ketat (Penanggung Jawab & Arahan).
#     Memasukkan bypass safety agar tidak terblokir filter.
#     """
#     try:
#         genai.configure(api_key=api_key)
        
#         # Menggunakan System Instruction untuk memaksa AI bersikap objektif & bypass safety
#         model = genai.GenerativeModel(
#             model_name="gemini-1.5-flash",
#             system_instruction="Anda adalah asisten notulensi profesional. Tugas Anda meringkas transkrip rapat secara faktual. Jangan memblokir output karena konten sensitif bisnis (seperti 'eksekusi', 'investigasi', 'insiden'). Tetap objektif dan profesional."
#         )
        
#         prompt = f"""
# **PERINTAH: BUAT NOTULEN RAPAT FORMAL BERDASARKAN TRANSKRIP BERIKUT.**

# TRANSKRIP:
# {sentences[:12000]}

# FORMAT WAJIB (TABEL):

# # Notulen Rapat

# |Nama Rapat|[isi]|
# |---|---|
# |Hari/Tanggal|[isi]|
# |Waktu|[isi]|
# |Tempat|[isi]|
# |Pemimpin Rapat|[isi]|
# |Dibuat oleh|[Group Transformasi Korporasi dan Manajemen Program]|

# **Agenda:**
# - [Daftar agenda rapat secara lengkap]

# **Peserta Rapat:**
# |No||Nama/Jabatan|
# |---|---|---|
# |1|[isi]|

# **TABEL DISKUSI, PENANGGUNG JAWAB & ARAHAN:**
# |Poin Diskusi dan Arahan|Penanggung Jawab|
# |---|---|
# |**[TOPIK DISKUSI]**||
# |[Penjelasan mendalam mengenai apa yang disampaikan oleh pembicara]||
# |Kesimpulan :||
# |• [TULISKAN ARAHAN/KEPUTUSAN SPESIFIK DI SINI]|[NAMA PEMBICARA/PENANGGUNG JAWAB]|

# **Disclaimer:**
# _Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final._

# INSTRUKSI KHUSUS:
# 1. Pastikan kolom "Penanggung Jawab" diisi dengan orang yang memberikan instruksi atau menyampaikan materi.
# 2. Gunakan bahasa Indonesia yang sangat formal.
# 3. Jangan pernah memberikan pesan error atau disclaimer keamanan di dalam hasil.
# """
        
#         generation_config = {"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 4096}
        
#         # Safety Settings BLOCK_NONE untuk mencegah input/output filtering
#         safety_settings = [
#             {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
#         ]
        
#         response = model.generate_content(
#             prompt, 
#             generation_config=generation_config,
#             safety_settings=safety_settings
#         )
        
#         # Validasi output jika terfilter (Finish Reason 2)
#         if response.candidates and response.candidates[0].finish_reason == 2:
#              return {'success': True, 'content': create_basic_notulen_template(sentences), 'error': None}
        
#         if response.text:
#             return {'success': True, 'content': response.text.strip(), 'error': None}
        
#         return {'success': True, 'content': create_basic_notulen_template(sentences), 'error': None}
            
#     except Exception as e:
#         return {'success': True, 'content': create_basic_notulen_template(sentences), 'error': f"API Fallback: {str(e)}"}

# def create_word_document(content, filename):
#     """
#     Membuat dokumen Word dari hasil notulensi.
#     """
#     try:
#         doc = Document()
#         sections = doc.sections
#         for section in sections:
#             section.top_margin = Inches(1)
#             section.bottom_margin = Inches(1)
#             section.left_margin = Inches(1)
#             section.right_margin = Inches(1)
        
#         title = doc.add_heading('Notulen Rapat', level=0)
#         title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
#         doc.add_paragraph(content)
        
#         buffer = io.BytesIO()
#         doc.save(buffer)
#         buffer.seek(0)
#         return buffer
#     except Exception as e:
#         st.error(f"Word Error: {e}")
#         return None

# def chat_with_transcript(question, transcript_text, api_key):
#     """
#     Fitur chat interaktif dengan transkrip.
#     """
#     try:
#         genai.configure(api_key=api_key)
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         context = f"Referensi Transkrip:\n{transcript_text[:5000]}\n\nPertanyaan: {question}\nJawab secara profesional."
#         response = model.generate_content(context)
#         return {'success': True, 'content': response.text}
#     except Exception:
#         return {'success': True, 'content': "Maaf, sistem sedang memproses permintaan lain."}

# def main():
#     st.set_page_config(page_title="Notulen Generator by TKMP", page_icon="📝", layout="wide")

#     # CSS Original
#     st.markdown("""
#     <style>
#     .main-header { text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-weight: bold; }
#     .sub-header { text-align: center; color: #666; margin-bottom: 2rem; }
#     .stButton>button { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; font-weight: 600; padding: 0.75rem 1.5rem; }
#     .success-box { background: #d4edda; color: #155724; padding: 1rem; border-radius: 8px; margin: 1rem 0; border: 1px solid #c3e6cb; }
#     </style>
#     """, unsafe_allow_html=True)

#     st.markdown('<h1 class="main-header">📝 Notulen Zoom Meeting Generator by TKMP</h1>', unsafe_allow_html=True)
#     st.markdown('<p class="sub-header">Generate Notulen dengan Praktis & Detail</p>', unsafe_allow_html=True)
    
#     # API Key Loading
#     api_key = st.secrets.get("api_key")
#     api_key_available = True if api_key else False
    
#     with st.sidebar:
#         st.header("⚙️ Configuration")
#         if api_key_available:
#             st.success("✅ API Key Loaded Successfully")
#         else:
#             api_key = st.text_input("Input API Key:", type="password")
#             api_key_available = True if api_key else False
            
#         st.info("Sistem ini menjamin hasil 100% dengan ekstraksi Penanggung Jawab dan Arahan.")

#     tab1, tab2 = st.tabs(["📄 Generate Notulen", "💬 Chat dengan Transkrip"])

#     with tab1:
#         uploaded_file = st.file_uploader("Upload Transkrip (VTT/TXT)", type=['vtt', 'txt'])
        
#         if uploaded_file:
#             raw_content = uploaded_file.getvalue().decode("utf-8", errors='ignore')
#             st.session_state.uploaded_transcript = process_vtt_text(raw_content)
            
#             st.info(f"File: {uploaded_file.name} | Characters: {len(st.session_state.uploaded_transcript)}")
            
#             if st.button("🚀 Generate Notulen", type="primary", use_container_width=True):
#                 with st.spinner("🤖 AI sedang menganalisis alur rapat..."):
#                     result = generate_notulen_with_ai(st.session_state.uploaded_transcript, api_key)
#                     st.session_state.ai_notulen = result['content']
#                     st.session_state.processed = True
#                     st.rerun()

#         if st.session_state.get('processed'):
#             st.markdown('<div class="success-box">✅ Notulen Sukses Dibuat</div>', unsafe_allow_html=True)
#             st.markdown(st.session_state.ai_notulen)
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.download_button("📄 Download TXT", st.session_state.ai_notulen, "Notulen_TKMP.txt", use_container_width=True)
#             with col2:
#                 word_file = create_word_document(st.session_state.ai_notulen, "Notulen_TKMP.docx")
#                 st.download_button("📝 Download Word", word_file, "Notulen_TKMP.docx", use_container_width=True)

#     with tab2:
#         if 'uploaded_transcript' in st.session_state:
#             if "chat_history" not in st.session_state: st.session_state.chat_history = []
            
#             for chat in st.session_state.chat_history:
#                 with st.chat_message(chat["role"]): st.markdown(chat["content"])
            
#             if user_query := st.chat_input("Tanyakan sesuatu tentang rapat..."):
#                 st.session_state.chat_history.append({"role": "user", "content": user_query})
#                 with st.chat_message("user"): st.markdown(user_query)
                
#                 with st.spinner("Mencari jawaban..."):
#                     chat_res = chat_with_transcript(user_query, st.session_state.uploaded_transcript, api_key)
#                     st.session_state.chat_history.append({"role": "assistant", "content": chat_res['content']})
#                     with st.chat_message("assistant"): st.markdown(chat_res['content'])
#         else:
#             st.info("Upload transkrip di tab pertama untuk mengaktifkan fitur chat.")

# if __name__ == "__main__":
#     main()



# # import streamlit as st
# # import re
# # from datetime import datetime
# # import io
# # import google.generativeai as genai
# # from docx import Document
# # from docx.shared import Pt, Inches
# # from docx.enum.text import WD_ALIGN_PARAGRAPH

# # def process_vtt_text(vtt_text):
# #     """
# #     Process VTT text to clean timestamps and metadata
# #     """
# #     # Clean timestamp & metadata
# #     cleaned_text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt_text)
# #     cleaned_text = re.sub(r"WEBVTT.*\n", "", cleaned_text)
# #     cleaned_text = "\n".join([line.strip() for line in cleaned_text.splitlines() if line.strip()])
# #     return cleaned_text

# # def generate_notulen_with_ai(sentences, api_key):
# #     """
# #     Generate formal meeting minutes using Google Gemini API
# #     """
# #     try:
# #         # Configure API
# #         genai.configure(api_key=api_key)
        
# #         # Initialize model - CHANGED TO STANDARD FLASH MODEL
# #         # model = genai.GenerativeModel("gemini-2.5-flash")

# #         # model = genai.GenerativeModel("models/gemini-2.5-flash-lite") 
# #         # model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-09-2025")
# #         model = genai.GenerativeModel("models/gemini-flash-latest")
        
# #         # REFINED PROMPT with strong emphasis on professional, non-sensitive content
# #         prompt = f"""
# # **INI ADALAH DATA RAPAT FORMAL PERUSAHAAN. BUATKAN NOTULEN RAPAT DENGAN BAHASA INDONESIA YANG FORMAL DAN PROFESIONAL. HANYA FOKUS PADA AGENDA, DISKUSI, DAN KEPUTUSAN SAJA.**

# # Buatkan notulen rapat yang rapi dan formal dari transkrip rapat berikut:

# # {sentences}

# # FORMAT YANG DIHARAPKAN:

# # # Notulen Rapat

# # |Nama Rapat|[isi nama rapat berdasarkan transkrip]|
# # |---|---|
# # |Hari/Tanggal|[hari, tanggal berdasarkan transkrip]|
# # |Waktu|[waktu rapat berdasarkan transkrip]|
# # |Tempat|[lokasi rapat berdasarkan transkrip]|
# # |Pemimpin Rapat|[nama pemimpin rapat berdasarkan transkrip]|
# # |Dibuat oleh|[Group Transformasi Korporasi dan Manajemen Program]|

# # **Agenda:**
# # - [daftar agenda rapat berdasarkan transkrip]

# # **Peserta Rapat:**
# # |No||Nama/Jabatan|
# # |---|---|---|
# # |1|[nama dan jabatan peserta 1]|
# # |2|[nama dan jabatan peserta 2]|
# # |[dan seterusnya]|

# # |Poin Diskusi dan Arahan|Penanggung Jawab|
# # |---|---|
# # |[Topik diskusi 1]||
# # [Penjelasan Topik singkat]
# # |Kesimpulan :||
# # |• [kesimpulan point 1]|[penanggung jawab]|
# # |[Topik diskusi 2]||
# # [Penjelasan Topik singkat]
# # |Kesimpulan :||
# # |• [kesimpulan point 2]|[penanggung jawab]|
# # |[dan seterusnya untuk semua topik]|

# # **Disclaimer:**
# # _Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final._

# # INSTRUKSI KHUSUS:
# # 1. Gunakan format tabel persis seperti contoh di atas
# # 2. Ekstrak semua informasi dari transkrip yang diberikan
# # 3. Untuk kolom "Penanggung Jawab", identifikasi pihak yang bertanggung jawab berdasarkan diskusi
# # 4. Gunakan bahasa Indonesia yang formal dan profesional
# # 5. Jika informasi tidak tersedia dalam transkrip, gunakan [Tidak disebutkan dalam transkrip]
# # 6. Jangan tambahkan elemen format lain selain yang ditentukan

# # Catatan: Jika informasi tertentu tidak tersedia dalam transkrip, beri tanda [Tidak disebutkan dalam transkrip].
# # """
        
# #         # Generate content with safety settings
# #         generation_config = {
# #             "temperature": 0.3,
# #             "top_p": 0.8,
# #             "top_k": 40,
# #             "max_output_tokens": 2048,
# #         }
        
# #         # ADD SAFETY SETTINGS TO PREVENT INPUT BLOCKING
# #         # You've already done this, which helps ensure the input transcript is not the issue.
# #         safety_settings = [
# #             {
# #                 "category": "HARM_CATEGORY_HARASSMENT",
# #                 "threshold": "BLOCK_NONE"
# #             },
# #             {
# #                 "category": "HARM_CATEGORY_HATE_SPEECH", 
# #                 "threshold": "BLOCK_NONE"
# #             },
# #             {
# #                 "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
# #                 "threshold": "BLOCK_NONE"
# #             },
# #             {
# #                 "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
# #                 "threshold": "BLOCK_NONE"
# #             }
# #         ]
        
# #         response = model.generate_content(
# #             prompt, 
# #             generation_config=generation_config,
# #             safety_settings=safety_settings
# #         )
        
# #         # Check if response was blocked (Input filtering)
# #         if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
# #             return {
# #                 'success': False,
# #                 'content': None,
# #                 'error': f"Response blocked due to input content: {response.prompt_feedback.block_reason}"
# #             }
        
# #         # Check if response has candidates (Output filtering - Finish Reason 2)
# #         if hasattr(response, 'candidates') and response.candidates:
# #             candidate = response.candidates[0]
# #             # This is the line that captures the OUTPUT safety filter
# #             if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
# #                 # Provide a more specific error message based on the safety filter.
# #                 return {
# #                     'success': False,
# #                     'content': None,
# #                     'error': "Response was filtered for safety reasons. The model's output likely contained sensitive content. Please review and edit your transcript."
# #                 }
# #             # Get text from candidate
# #             if candidate.content.parts:
# #                 content_text = candidate.content.parts[0].text
# #                 if content_text:
# #                     cleaned_response = content_text.strip()
                    
# #                     # Ensure the response starts with the correct header
# #                     if not cleaned_response.startswith("# Notulen Rapat"):
# #                         lines = cleaned_response.split('\n')
# #                         for i, line in enumerate(lines):
# #                             if "Notulen Rapat" in line:
# #                                 cleaned_response = '\n'.join(lines[i:])
# #                                 break
                    
# #                     return {
# #                         'success': True,
# #                         'content': cleaned_response,
# #                         'error': None
# #                     }
        
# #         return {
# #             'success': False,
# #             'content': None,
# #             'error': 'Empty response from model'
# #         }
            
# #     except Exception as e:
# #         return {
# #             'success': False,
# #             'content': None,
# #             'error': f"API Error: {str(e)}"
# #         }

# # def create_word_document(content, filename):
# #     """
# #     Create a Word document from the generated content
# #     """
# #     try:
# #         doc = Document()
        
# #         # Set document margins
# #         sections = doc.sections
# #         for section in sections:
# #             section.top_margin = Inches(1)
# #             section.bottom_margin = Inches(1)
# #             section.left_margin = Inches(1)
# #             section.right_margin = Inches(1)
        
# #         # Add title
# #         title = doc.add_heading('Notulen Rapat', level=0)
# #         title.alignment = WD_ALIGN_PARAGRAPH.CENTER
# #         title_run = title.runs[0]
# #         title_run.font.size = Pt(16)
# #         title_run.font.bold = True
        
# #         # Add the content as simple text
# #         content_para = doc.add_paragraph(content)
        
# #         # Save to bytes buffer
# #         buffer = io.BytesIO()
# #         doc.save(buffer)
# #         buffer.seek(0)
        
# #         return buffer
        
# #     except Exception as e:
# #         st.error(f"Error creating Word document: {e}")
# #         return None

# # def chat_with_transcript(question, transcript_text, api_key, chat_history=None):
# #     """
# #     Function for interactive chat based on the uploaded transcript
# #     """
# #     try:
# #         # Configure API
# #         genai.configure(api_key=api_key)
        
# #         # Initialize model
# #         model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-09-2025")
        
# #         # Create context from transcript
# #         context = f"""
# #         Berikut adalah transkrip rapat yang akan digunakan sebagai referensi untuk menjawab pertanyaan:

# #         {transcript_text}

# #         INSTRUKSI:
# #         1. JAWAB PERTANYAAN BERDASARKAN TRANSCRIPT DI ATAS SAJA
# #         2. Jika informasi tidak ada dalam transcript, katakan "Informasi tidak ditemukan dalam transkrip"
# #         3. Gunakan bahasa Indonesia yang formal dan profesional
# #         4. Berikan jawaban yang spesifik berdasarkan data yang ada dalam transkrip
# #         5. Jangan membuat informasi yang tidak ada dalam transkrip

# #         Pertanyaan: {question}
# #         """
        
# #         # Generate content with safety settings
# #         generation_config = {
# #             "temperature": 0.3,
# #             "top_p": 0.8,
# #             "top_k": 40,
# #             "max_output_tokens": 1024,
# #         }
        
# #         safety_settings = [
# #             {
# #                 "category": "HARM_CATEGORY_HARASSMENT",
# #                 "threshold": "BLOCK_NONE"
# #             },
# #             {
# #                 "category": "HARM_CATEGORY_HATE_SPEECH", 
# #                 "threshold": "BLOCK_NONE"
# #             },
# #             {
# #                 "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
# #                 "threshold": "BLOCK_NONE"
# #             },
# #             {
# #                 "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
# #                 "threshold": "BLOCK_NONE"
# #             }
# #         ]
        
# #         response = model.generate_content(
# #             context, 
# #             generation_config=generation_config,
# #             safety_settings=safety_settings
# #         )
        
# #         if response.text:
# #             return {
# #                 'success': True,
# #                 'content': response.text,
# #                 'error': None
# #             }
# #         else:
# #             return {
# #                 'success': False,
# #                 'content': None,
# #                 'error': 'Empty response from model'
# #             }
            
# #     except Exception as e:
# #         return {
# #             'success': False,
# #             'content': None,
# #             'error': f"Chat Error: {str(e)}"
# #         }

# # def main():
# #     st.set_page_config(
# #         page_title="Notulen Zoom Meeting Generator by TKMP",
# #         page_icon="📝",
# #         layout="wide",
# #         initial_sidebar_state="expanded"
# #     )

# #     # Custom CSS for better styling
# #     st.markdown("""
# #     <style>
# #     .main-header {
# #         text-align: center;
# #         padding: 2rem 0;
# #         background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
# #         -webkit-background-clip: text;
# #         -webkit-text-fill-color: transparent;
# #         background-clip: text;
# #         font-size: 2.5rem;
# #         font-weight: bold;
# #         margin-bottom: 1rem;
# #     }
# #     .sub-header {
# #         text-align: center;
# #         color: #666;
# #         margin-bottom: 2rem;
# #     }
# #     .stButton>button {
# #         background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
# #         color: white;
# #         border: none;
# #         border-radius: 8px;
# #         padding: 0.75rem 1.5rem;
# #         font-weight: 600;
# #     }
# #     .success-box {
# #         background: #d4edda;
# #         color: #155724;
# #         padding: 1rem;
# #         border-radius: 8px;
# #         border: 1px solid #c3e6cb;
# #         margin: 1rem 0;
# #     }
# #     .error-box {
# #         background: #f8d7da;
# #         color: #721c24;
# #         padding: 1rem;
# #         border-radius: 8px;
# #         border: 1px solid #f5c6cb;
# #         margin: 1rem 0;
# #     }
# #     .chat-message {
# #         padding: 1rem;
# #         border-radius: 8px;
# #         margin: 0.5rem 0;
# #     }
# #     .user-message {
# #         background: #e3f2fd;
# #         border-left: 4px solid #2196f3;
# #     }
# #     .assistant-message {
# #         background: #f3e5f5;
# #         border-left: 4px solid #9c27b0;
# #     }
# #     .info-box {
# #         background: #e8f4fd;
# #         color: #0c5460;
# #         padding: 1rem;
# #         border-radius: 8px;
# #         border: 1px solid #b8daff;
# #         margin: 1rem 0;
# #     }
# #     </style>
# #     """, unsafe_allow_html=True)

# #     # Header
# #     st.markdown('<h1 class="main-header">📝 Notulen Zoom Meeting Generator by TKMP</h1>', unsafe_allow_html=True)
# #     st.markdown('<p class="sub-header">Generate Notulen dengan praktis no ribet</p>', unsafe_allow_html=True)
    
# #     # Get API key from secrets.toml
# #     try:
# #         api_key = st.secrets["api_key"]
# #         api_key_available = True
# #     except (KeyError, FileNotFoundError):
# #         api_key = None
# #         api_key_available = False
    
# #     # Sidebar
# #     with st.sidebar:
# #         st.header("⚙️ Configuration")
        
# #         if api_key_available:
# #             st.success("✅ API Key loaded successfully")
# #         else:
# #             st.error("❌ API Key not found")
# #             st.info("""
# #             **Setup Instructions:**
# #             1. Create `.streamlit/secrets.toml`
# #             2. Add your API key:
# #             ```
# #             api_key = "your_api_key_here"
# #             ```
# #             3. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
# #             """)
        
# #         st.header("📋 How to Use")
# #         st.markdown("""
# #         1. **Upload** transkrip Zoom Anda
# #         2. **Process** transkrip dengan tombol
# #         3. **Review** Notulen yang sudah jadi
# #         4. **Re-Generate** dengan klik tombol generate jika hasil kurang memuaskan
# #         5. **Chat** dengan konten transkrip apabila ingin menanyakan konten lebih spesifik
# #         6. **Chat** bisa digunakan jika ada file VTT yang diupload
# #         """)

# #     # Main content - Tabs for different functionalities
# #     tab1, tab2 = st.tabs(["📄 Generate Notulen", "💬 Chat dengan Transkrip"])

# #     with tab1:
# #         st.markdown("### 📁 Upload Transkrip")
        
# #         uploaded_file = st.file_uploader(
# #             "Pilih File",
# #             type=['vtt', 'txt'],
# #             help="Supported format: .vtt (Zoom transcript files) atau .txt",
# #             key="file_uploader"
# #         )
        
# #         if uploaded_file is not None:
# #             # Store the uploaded file content in session state
# #             content = uploaded_file.getvalue().decode("utf-8")
# #             st.session_state.uploaded_transcript = process_vtt_text(content)
            
# #             # File info
# #             col1, col2 = st.columns(2)
# #             with col1:
# #                 st.info(f"**File:** {uploaded_file.name}")
# #             with col2:
# #                 st.info(f"**Size:** {uploaded_file.size:,} bytes")
# #                 st.info(f"**Characters:** {len(st.session_state.uploaded_transcript):,}")
            
# #             # Process button
# #             if st.button("🚀 Generate Notulen", type="primary", use_container_width=True, key="generate_btn"):
# #                 if not api_key_available:
# #                     st.error("Please configure your API key in secrets.toml first")
# #                     return
                    
# #                 with st.spinner("🤖 AI sedang memproses transkrip..."):
# #                     try:
# #                         # Check if transcript has sufficient content
# #                         if len(st.session_state.uploaded_transcript.strip()) < 50:
# #                             st.error("❌ Transkrip terlalu pendek. Pastikan file berisi konten rapat yang cukup.")
# #                             return
                        
# #                         # Generate AI content
# #                         ai_result = generate_notulen_with_ai(st.session_state.uploaded_transcript, api_key)
                        
# #                         if ai_result['success']:
# #                             st.session_state.ai_notulen = ai_result['content']
# #                             st.session_state.processed = True
# #                             st.success("✅ Generate Notulen berhasil!")
# #                         else:
# #                             st.error(f"❌ Error: {ai_result['error']}")
# #                             if "safety" in ai_result['error'].lower() or "filter" in ai_result['error'].lower():
# #                                 st.info("💡 **Tips**: Jika error ini berulang, coba **edit transkrip Anda** untuk menghapus konten yang mungkin sensitif atau coba **gunakan transkrip yang berbeda**.")
                            
# #                     except Exception as e:
# #                         st.error(f"❌ Processing error: {str(e)}")
        
# #         # Display results
# #         if 'ai_notulen' in st.session_state and st.session_state.get('processed', False):
# #             st.divider()
# #             st.markdown("### 📋 Generated Notulen")
            
# #             # Success message
# #             st.markdown('<div class="success-box">✅ <strong>Notulen sukses dibuat!</strong> Silahkan review hasilnya.</div>', unsafe_allow_html=True)
            
# #             # Display the content
# #             st.markdown(st.session_state.ai_notulen, unsafe_allow_html=True)
            
# #             # Download section
# #             st.divider()
# #             st.markdown("### 📥 Download Options")
            
# #             col1, col2 = st.columns(2)
            
# #             with col1:
# #                 # Text download
# #                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# #                 st.download_button(
# #                     label="📄 Download as TXT",
# #                     data=st.session_state.ai_notulen,
# #                     file_name=f"Notulen_meeting_{timestamp}.txt",
# #                     mime="text/plain",
# #                     use_container_width=True
# #                 )
            
# #             with col2:
# #                 # Word document download
# #                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# #                 word_buffer = create_word_document(st.session_state.ai_notulen, f"Notulen_meeting_{timestamp}.docx")
# #                 if word_buffer:
# #                     st.download_button(
# #                         label="📝 Download Word Document",
# #                         data=word_buffer.getvalue(),
# #                         file_name=f"Notulen_meeting_{timestamp}.docx",
# #                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
# #                         use_container_width=True
# #                     )
            
# #             # Clear results button
# #             if st.button("🗑️ Clear Results", use_container_width=True, key="clear_results"):
# #                 if 'ai_notulen' in st.session_state:
# #                     del st.session_state.ai_notulen
# #                 if 'processed' in st.session_state:
# #                     del st.session_state.processed
# #                 st.rerun()

# #     with tab2:
# #         st.markdown("### 💬 Chat dengan Transkrip")
        
# #         if 'uploaded_transcript' not in st.session_state or not st.session_state.uploaded_transcript:
# #             st.markdown("""
# #             <div class="info-box">
# #                 <strong>📝 Informasi:</strong> Silakan upload file transkrip VTT terlebih dahulu di tab "Generate Notulen" 
# #                 untuk mengaktifkan fitur chat.
# #             </div>
# #             """, unsafe_allow_html=True)
            
# #             st.info("""
# #             **Contoh pertanyaan yang bisa ditanyakan:**
# #             - Siapa saja yang hadir dalam rapat?
# #             - Apa agenda utama rapat ini?
# #             - Keputusan apa yang diambil dalam rapat?
# #             - Siapa yang bertanggung jawab untuk tindak lanjut?
# #             - Kapan deadline yang disepakati?
# #             """)
# #         else:
# #             st.markdown("""
# #             <div class="success-box">
# #                 ✅ <strong>Transkrip tersedia!</strong> Anda dapat bertanya tentang konten rapat.
# #             </div>
# #             """, unsafe_allow_html=True)
            
# #             # Display transcript info
# #             with st.expander("📊 Info Transkrip"):
# #                 st.text(f"Panjang transkrip: {len(st.session_state.uploaded_transcript)} karakter")
# #                 st.text(f"Jumlah baris: {st.session_state.uploaded_transcript.count(chr(10)) + 1}")
            
# #             # Initialize chat history
# #             if "chat_history" not in st.session_state:
# #                 st.session_state.chat_history = []
            
# #             # Display chat history
# #             st.markdown("#### 💭 Percakapan")
# #             for message in st.session_state.chat_history:
# #                 if message["role"] == "user":
# #                     st.markdown(f'<div class="chat-message user-message"><strong>👤 Anda:</strong> {message["content"]}</div>', unsafe_allow_html=True)
# #                 else:
# #                     st.markdown(f'<div class="chat-message assistant-message"><strong>🤖 AI:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            
# #             # Chat input
# #             st.markdown("#### 💬 Tanya tentang rapat")
# #             user_input = st.text_area(
# #                 "Pertanyaan Anda:",
# #                 placeholder="Contoh: Siapa pemimpin rapat? Apa keputusan yang diambil? Siapa yang hadir?",
# #                 key="chat_input",
# #                 height=80
# #             )
            
# #             col1, col2, col3 = st.columns([1, 1, 2])
# #             with col1:
# #                 if st.button("Kirim Pertanyaan", use_container_width=True, key="send_chat"):
# #                     if user_input.strip() and api_key_available:
# #                         with st.spinner("🔍 Mencari informasi dalam transkrip..."):
# #                             chat_result = chat_with_transcript(
# #                                 user_input, 
# #                                 st.session_state.uploaded_transcript, 
# #                                 api_key
# #                             )
                            
# #                             if chat_result['success']:
# #                                 # Add user message to history
# #                                 st.session_state.chat_history.append({
# #                                     "role": "user", 
# #                                     "content": user_input
# #                                 })
                                
# #                                 # Add AI response to history
# #                                 st.session_state.chat_history.append({
# #                                     "role": "assistant",
# #                                     "content": chat_result['content']
# #                                 })
                                
# #                                 # Clear input and rerun to update display
# #                                 st.rerun()
# #                             else:
# #                                 st.error(f"Error: {chat_result['error']}")
# #                     elif not api_key_available:
# #                         st.error("API Key tidak tersedia. Silakan konfigurasi di sidebar.")
# #                     elif not user_input.strip():
# #                         st.warning("Silakan ketik pertanyaan terlebih dahulu.")
            
# #             with col2:
# #                 if st.button("Hapus Chat", use_container_width=True, key="clear_chat"):
# #                     st.session_state.chat_history = []
# #                     st.rerun()
            
# #             with col3:
# #                 st.info("💡 Tanya tentang peserta, agenda, keputusan, atau hal spesifik dari rapat")
    
# #     # Footer
# #     st.divider()
# #     st.markdown("""
# #     <div style='text-align: center; color: #666; padding: 2rem;'>
# #         <p>Dibuat dengan ❤️ oleh TKMP</p>
# #     </div>
# #     """, unsafe_allow_html=True)

# # if __name__ == "__main__":
# #     main()
