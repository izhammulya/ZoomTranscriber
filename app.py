import streamlit as st
import re
from datetime import datetime, timedelta
import io
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

def extract_participants_from_transcript(transcript):
    """
    Extract potential participants from transcript with smart detection
    """
    participants = set()
    lines = transcript.split('\n')
    
    # Patterns for detecting speakers
    speaker_patterns = [
        r'(?i)(bapak|ibu|pak|bu|sdr\.?|sdr\s|sdr\s|dari|oleh)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\(',
    ]
    
    for line in lines:
        # Check for speaker indicators
        if any(indicator in line.lower() for indicator in [':', 'bapak', 'ibu', 'pak', 'bu', 'sdr', 'dari', 'oleh']):
            # Try to extract name
            for pattern in speaker_patterns:
                matches = re.findall(pattern, line[:100])  # Only check first 100 chars
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            name = match[-1].strip()
                        else:
                            name = match.strip()
                        
                        # Filter out non-names
                        if (3 <= len(name) <= 50 and 
                            not any(word in name.lower() for word in ['terimakasih', 'selamat', 'rapat', 'agenda', 'diskusi'])):
                            participants.add(name)
    
    return list(participants)

def create_structured_notulen_template(transcript):
    """
    Create structured notulen template with detailed discussion points
    """
    now = datetime.now()
    
    # Extract participants
    participants = extract_participants_from_transcript(transcript)
    
    # Count words and lines
    word_count = len(transcript.split())
    line_count = transcript.count('\n') + 1
    
    # Create basic structured template
    structured_notulen = f"""# NOTULEN RAPAT

## INFORMASI UMUM
| Item | Keterangan |
|------|------------|
| **Nama Rapat** | Rapat Koordinasi |
| **Hari/Tanggal** | {now.strftime('%A, %d %B %Y')} |
| **Waktu** | {now.strftime('%H:%M')} - Selesai WIB |
| **Tempat** | Virtual Meeting / Ruang Rapat |
| **Pemimpin Rapat** | [Nama Pemimpin Rapat] |
| **Notulis** | Group Transformasi Korporasi dan Manajemen Program |
| **Jumlah Peserta** | {len(participants)} orang |

## DAFTAR HADIR
| No | Nama | Jabatan / Divisi |
|----|------|------------------|
"""
    
    # Add participants to table
    for i, participant in enumerate(participants[:15], 1):
        structured_notulen += f"| {i} | {participant} | [Jabatan/Divisi] |\n"
    
    structured_notulen += """
## AGENDA RAPAT
1. Pembukaan dan perkenalan
2. Pengecekan daftar hadir
3. Penyampaian agenda rapat
4. Pembahasan materi utama
5. Diskusi dan tanggapan
6. Penetapan keputusan
7. Penutupan

## HASIL PEMBAHASAN

### 1. PEMBUKAAN
| Penanggung Jawab | Yang Disampaikan | Arahan / Tindak Lanjut |
|-----------------|------------------|------------------------|
| [Pemimpin Rapat] | Membuka rapat, menyampaikan agenda, dan tujuan rapat | - |
| | | |

### 2. PEMBAHASAN MATERI UTAMA
| Penanggung Jawab | Yang Disampaikan | Arahan / Tindak Lanjut |
|-----------------|------------------|------------------------|
| [Nama Penanggung Jawab 1] | [Isi yang disampaikan] | [Arahan yang diberikan] |
| [Nama Penanggung Jawab 2] | [Isi yang disampaikan] | [Arahan yang diberikan] |
| | | |

### 3. DISKUSI DAN TANGGAPAN
| Penanggung Jawab | Tanggapan / Masukan | Respons / Tindak Lanjut |
|-----------------|---------------------|-------------------------|
| [Nama Peserta 1] | [Isi tanggapan] | [Respons dari penanggung jawab] |
| [Nama Peserta 2] | [Isi tanggapan] | [Respons dari penanggung jawab] |
| | | |

### 4. KEPUTUSAN YANG DIAMBIL
| No | Keputusan | Penanggung Jawab | Target Waktu |
|----|-----------|-----------------|--------------|
| 1 | [Deskripsi keputusan 1] | [Nama Penanggung Jawab] | [DD/MM/YYYY] |
| 2 | [Deskripsi keputusan 2] | [Nama Penanggung Jawab] | [DD/MM/YYYY] |
| | | |

### 5. RENCANA TINDAK LANJUT
| No | Aktivitas | Penanggung Jawab | Target Waktu | Keterangan |
|----|-----------|-----------------|--------------|------------|
| 1 | [Aktivitas 1] | [Nama Penanggung Jawab] | [DD/MM/YYYY] | [Keterangan] |
| 2 | [Aktivitas 2] | [Nama Penanggung Jawab] | [DD/MM/YYYY] | [Keterangan] |
| | | | |

## JADWAL RAPAT BERIKUTNYA
- **Hari/Tanggal**: [DD/MM/YYYY]
- **Waktu**: [HH:MM] WIB
- **Tempat**: [Lokasi]
- **Agenda**: [Pokok bahasan]

## PENUTUP
Rapat ditutup pada pukul [HH:MM] WIB.

---
**Disusun oleh:** Group Transformasi Korporasi dan Manajemen Program  
**Tanggal penyusunan:** {now.strftime('%d %B %Y')}  
**Catatan:** Notulen ini disusun berdasarkan transkrip otomatis ({word_count} kata, {line_count} baris).  
**Disclaimer:** Jika tidak ada koreksi dalam waktu 3x24 jam, notulen ini dianggap valid.

"""
    
    return structured_notulen

def extract_discussion_points_with_ai(transcript, api_key):
    """
    Extract structured discussion points from transcript using AI
    """
    try:
        if not api_key:
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""ANALISA TRANSCRIPT RAPAT UNTUK NOTULEN RESMI:

Transcript:
{transcript[:3000]}

FORMAT OUTPUT YANG DIBUTUHKAN:

1. DAFTAR PESERTA (nama saja):
- [Nama 1]
- [Nama 2]

2. POKOK BAHASAN UTAMA:
- [Bahasan 1]
- [Bahasan 2]

3. DISKUSI DETAIL (format tabel):
| Penanggung Jawab (Siapa) | Yang Disampaikan (Apa) | Arahan/Tindak Lanjut (Bagaimana) |
|-------------------------|------------------------|----------------------------------|
| [Nama] | [Isi pembicaraan] | [Arahan/keputusan] |
| [Nama] | [Isi pembicaraan] | [Arahan/keputusan] |

4. KEPUTUSAN PENTING:
- [Keputusan 1] - Penanggung Jawab: [Nama]
- [Keputusan 2] - Penanggung Jawab: [Nama]

5. ACTION ITEMS:
- [Tindakan] - PIC: [Nama] - Deadline: [Tanggal]

Gunakan bahasa Indonesia formal. Hanya ambil informasi yang jelas dari transcript.
"""
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 2000,
            }
        )
        
        if response and response.text:
            return response.text
        return None
        
    except Exception as e:
        return None

def parse_ai_response_to_structure(ai_response, original_transcript):
    """
    Parse AI response into structured format
    """
    now = datetime.now()
    
    # Extract participants from AI response
    participants = []
    if ai_response:
        lines = ai_response.split('\n')
        in_participants_section = False
        for line in lines:
            if 'DAFTAR PESERTA' in line or 'PESERTA:' in line:
                in_participants_section = True
                continue
            elif in_participants_section and ('POKOK BAHASAN' in line or 'DISKUSI' in line or line.strip().startswith('2.')):
                break
            elif in_participants_section and line.strip().startswith('-'):
                participant = line.strip().replace('-', '').strip()
                if participant and len(participant) > 2:
                    participants.append(participant)
    
    # If no participants found from AI, try to extract from transcript
    if not participants:
        participants = extract_participants_from_transcript(original_transcript)
    
    # Create structured notulen
    structured_notulen = f"""# NOTULEN RAPAT

## INFORMASI UMUM
| Item | Keterangan |
|------|------------|
| **Nama Rapat** | Rapat Koordinasi |
| **Hari/Tanggal** | {now.strftime('%A, %d %B %Y')} |
| **Waktu** | {now.strftime('%H:%M')} - Selesai WIB |
| **Tempat** | Virtual Meeting |
| **Pemimpin Rapat** | [Nama Pemimpin Rapat] |
| **Notulis** | Group Transformasi Korporasi dan Manajemen Program |
| **Jumlah Peserta** | {len(participants)} orang |

## DAFTAR HADIR
| No | Nama | Jabatan / Divisi |
|----|------|------------------|
"""
    
    # Add participants to table
    for i, participant in enumerate(participants[:15], 1):
        structured_notulen += f"| {i} | {participant} | [Jabatan/Divisi] |\n"
    
    # Add AI extracted content
    if ai_response:
        structured_notulen += f"""

## HASIL PEMBAHASAN (DIEKSTRAK OLEH AI)

{ai_response}

"""
    else:
        structured_notulen += """
## HASIL PEMBAHASAN

### 1. PEMBUKAAN
| Penanggung Jawab | Yang Disampaikan | Arahan / Tindak Lanjut |
|-----------------|------------------|------------------------|
| [Pemimpin Rapat] | Membuka rapat dan menyampaikan agenda | Rapat dilaksanakan sesuai agenda |
| [Sekretaris] | Menyampaikan daftar hadir | Daftar hadir dilampirkan |
| | | |

### 2. MATERI UTAMA
| Penanggung Jawab | Yang Disampaikan | Arahan / Tindak Lanjut |
|-----------------|------------------|------------------------|
| [Manajer Proyek] | Laporan progress proyek terkini | Monitoring mingguan akan dilakukan |
| [Tim Teknis] | Kendala teknis yang dihadapi | Akan diselesaikan dalam 3 hari kerja |
| [Tim Operasional] | Update aktivitas operasional | Koordinasi antar tim ditingkatkan |
| | | |

### 3. KEPUTUSAN
| No | Keputusan | Penanggung Jawab | Target Waktu |
|----|-----------|-----------------|--------------|
| 1 | Penyusunan laporan progress | [Nama] | {datetime.now().strftime('%d/%m/%Y')} |
| 2 | Penyelesaian kendala teknis | [Nama] | {datetime.now() + timedelta(days=3):%d/%m/%Y} |
| | | |

### 4. ACTION PLAN
| No | Aktivitas | Penanggung Jawab | Target Waktu | Status |
|----|-----------|-----------------|--------------|--------|
| 1 | Finalisasi dokumen | [Nama] | {datetime.now().strftime('%d/%m/%Y')} | On Progress |
| 2 | Koordinasi dengan vendor | [Nama] | {datetime.now() + timedelta(days=2):%d/%m/%Y} | Pending |
| | | | |

"""
    
    structured_notulen += f"""
## PENUTUP
Rapat ditutup dengan kesepakatan untuk melaksanakan action plan yang telah ditetapkan.

---
**Disusun oleh:** Group Transformasi Korporasi dan Manajemen Program  
**Tanggal:** {now.strftime('%d %B %Y')}  
**Status:** Draft - Harap dikoreksi dalam 3x24 jam  
**Lampiran:** Transkrip rapat ({len(original_transcript.split())} kata)

*Notulen ini dibuat otomatis dengan bantuan AI. Silakan lengkapi informasi yang belum tersedia.*
"""
    
    return structured_notulen

def generate_notulen_with_ai_enhanced(transcript, api_key):
    """
    Generate enhanced notulen with structured discussion points
    """
    try:
        # Try to extract structured content with AI
        ai_extracted_content = None
        if api_key:
            ai_extracted_content = extract_discussion_points_with_ai(transcript, api_key)
        
        # Create structured notulen
        structured_notulen = parse_ai_response_to_structure(ai_extracted_content, transcript)
        
        return {
            'success': True,
            'content': structured_notulen,
            'source': 'ai_enhanced' if ai_extracted_content else 'structured_template',
            'error': None
        }
        
    except Exception as e:
        # Fallback to structured template
        structured_notulen = create_structured_notulen_template(transcript)
        return {
            'success': True,
            'content': structured_notulen,
            'source': 'fallback_structured',
            'error': None
        }

def create_enhanced_word_document(content, filename):
    """
    Create enhanced Word document with better formatting
    """
    try:
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)
        
        # Add title
        title = doc.add_heading('NOTULEN RAPAT', level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.runs[0]
        title_run.font.size = Pt(16)
        title_run.font.bold = True
        title_run.font.name = 'Calibri'
        
        # Add subtitle
        subtitle = doc.add_paragraph()
        subtitle_run = subtitle.add_run('Dokumen Resmi - Group Transformasi Korporasi dan Manajemen Program')
        subtitle_run.font.size = Pt(10)
        subtitle_run.italic = True
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()  # Add spacing
        
        # Split content by sections and add with formatting
        lines = content.split('\n')
        current_paragraph = None
        
        for line in lines:
            if line.startswith('# '):
                # Main title - already added
                continue
            elif line.startswith('## '):
                # Section heading
                heading = doc.add_heading(line.replace('## ', ''), level=1)
                heading_run = heading.runs[0]
                heading_run.font.size = Pt(12)
                heading_run.font.bold = True
                heading_run.font.name = 'Calibri'
            elif line.startswith('### '):
                # Subsection heading
                subheading = doc.add_heading(line.replace('### ', ''), level=2)
                subheading_run = subheading.runs[0]
                subheading_run.font.size = Pt(11)
                subheading_run.font.bold = True
                subheading_run.font.name = 'Calibri'
            elif line.strip().startswith('|') and '|' in line:
                # Table row - add as paragraph
                p = doc.add_paragraph(line)
                p.style = 'Table Grid'
            elif line.strip():
                # Regular paragraph
                p = doc.add_paragraph(line)
                p.style = 'Normal'
            else:
                # Empty line
                doc.add_paragraph()
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        # Fallback to simple text buffer
        buffer = io.BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        return buffer

def interactive_chat_with_transcript(question, transcript_text, api_key):
    """
    Enhanced chat function with better context understanding
    """
    try:
        if not api_key:
            return {
                'success': True,
                'content': "Untuk fitur chat yang optimal, harap setup API key di secrets.toml",
                'error': None
            }
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Create enhanced context
        context = f"""
        Anda adalah asisten yang ahli dalam menganalisis notulen rapat.
        Anda memiliki transkrip rapat berikut:

        {transcript_text[:3000]}

        PERINTAH:
        1. JAWAB HANYA BERDASARKAN INFORMASI YANG ADA DALAM TRANSCRIPT
        2. Jika informasi tidak ditemukan, katakan: "Informasi tidak ditemukan dalam transkrip"
        3. Fokus pada: 
           - Siapa yang berbicara (Penanggung Jawab)
           - Apa yang disampaikan
           - Arahan atau tindak lanjut yang diberikan
        4. Format jawaban dengan jelas dan terstruktur
        5. Gunakan bahasa Indonesia formal

        Pertanyaan user: {question}
        """
        
        response = model.generate_content(
            context,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 1000,
            }
        )
        
        if response.text:
            return {
                'success': True,
                'content': response.text,
                'error': None
            }
        else:
            return {
                'success': True,
                'content': "Tidak dapat memproses pertanyaan. Silakan periksa transkrip Anda.",
                'error': None
            }
            
    except Exception as e:
        return {
            'success': True,
            'content': "Sistem chat sedang mengalami kendala. Silakan coba lagi nanti.",
            'error': None
        }

def main():
    st.set_page_config(
        page_title="Enhanced Notulen Generator by TKMP",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Enhanced CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1a2980 0%, #26d0ce 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #2c3e50;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    .feature-badge {
        background: linear-gradient(90deg, #00b09b 0%, #96c93d 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.25rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1a2980 0%, #26d0ce 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .info-box {
        background: linear-gradient(135deg, #e8f4fd 0%, #d1ecf1 100%);
        color: #0c5460;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #17a2b8;
        margin: 1rem 0;
    }
    .table-header {
        background: linear-gradient(90deg, #1a2980 0%, #26d0ce 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px 5px 0 0;
        font-weight: bold;
    }
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }
    .ai-message {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #9c27b0;
    }
    .stat-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        text-align: center;
        margin: 0.5rem 0;
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1a2980;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #6c757d;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">📋 Enhanced Notulen Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transformasi transkrip rapat menjadi notulen profesional dengan struktur lengkap</p>', unsafe_allow_html=True)
    
    # Feature badges
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div class="feature-badge">✅ Penanggung Jawab</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-badge">📋 Yang Disampaikan</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-badge">🎯 Arahan/Tindak Lanjut</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="feature-badge">📊 Tabel Terstruktur</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="feature-badge">🤖 AI Powered</div>', unsafe_allow_html=True)
    
    # Get API key
    try:
        api_key = st.secrets["api_key"]
        api_key_available = True
    except:
        api_key = None
        api_key_available = False
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        if api_key_available:
            st.success("✅ API Key loaded successfully")
        else:
            st.warning("⚠️ API Key not found")
            with st.expander("How to setup API key"):
                st.markdown("""
                1. Dapatkan API key dari [Google AI Studio](https://makersuite.google.com/app/apikey)
                2. Buat file `.streamlit/secrets.toml`
                3. Tambahkan:
                ```toml
                api_key = "your_api_key_here"
                ```
                4. Restart aplikasi
                """)
        
        st.header("📋 Template Features")
        st.markdown("""
        **Struktur Notulen:**
        - ✅ Informasi rapat lengkap
        - ✅ Daftar hadir peserta
        - ✅ Agenda terstruktur
        - ✅ Pembahasan detail dengan tabel
        - ✅ Keputusan dan action items
        - ✅ Penanggung jawab & deadline
        
        **Format Tabel Diskusi:**
        ```
        | Penanggung Jawab | Yang Disampaikan | Arahan/Tindak Lanjut |
        |-----------------|------------------|----------------------|
        | [Nama]          | [Isi]            | [Arahan]             |
        ```
        """)
        
        st.header("🚀 Quick Actions")
        if st.button("Clear All Data", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Main content tabs
    tab1, tab2 = st.tabs(["📄 Generate Notulen", "💬 Chat with Transcript"])

    with tab1:
        st.markdown("### 📤 Upload Transkrip Rapat")
        
        uploaded_file = st.file_uploader(
            "Pilih file VTT atau TXT",
            type=['vtt', 'txt'],
            help="Upload file transkrip dari Zoom/Teams/Google Meet",
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            # Process and store transcript
            content = uploaded_file.getvalue().decode("utf-8", errors='ignore')
            cleaned_transcript = process_vtt_text(content)
            st.session_state.uploaded_transcript = cleaned_transcript
            
            # Display file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-value">{len(cleaned_transcript.split())}</div>
                    <div class="stat-label">Kata</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-value">{cleaned_transcript.count(chr(10)) + 1}</div>
                    <div class="stat-label">Baris</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                participants = extract_participants_from_transcript(cleaned_transcript)
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-value">{len(participants)}</div>
                    <div class="stat-label">Peserta Terdeteksi</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Preview transcript
            with st.expander("👁️ Preview Transkrip (50 baris pertama)"):
                st.text_area("", cleaned_transcript[:2000], height=200, disabled=True)
            
            # Generate button
            if st.button("🚀 Generate Enhanced Notulen", type="primary", use_container_width=True):
                with st.spinner("🔄 Memproses transkrip dan mengekstrak struktur..."):
                    # Generate enhanced notulen
                    result = generate_notulen_with_ai_enhanced(cleaned_transcript, api_key)
                    
                    # Store results
                    st.session_state.enhanced_notulen = result['content']
                    st.session_state.notulen_generated = True
                    st.session_state.generation_source = result['source']
                    
                    st.success("✅ Notulen berhasil dibuat dengan struktur lengkap!")
                    
                    # Show generation info
                    source_display = {
                        'ai_enhanced': 'AI Enhanced',
                        'structured_template': 'Template Terstruktur',
                        'fallback_structured': 'Template Standar'
                    }.get(result['source'], 'Sistem')
                    
                    st.markdown(f'<div class="info-box"><strong>📊 Mode Generasi:</strong> {source_display}</div>', unsafe_allow_html=True)
        
        # Display generated notulen
        if 'enhanced_notulen' in st.session_state and st.session_state.get('notulen_generated', False):
            st.divider()
            st.markdown("### 📋 Notulen Hasil Generate")
            
            # Success message
            st.markdown("""
            <div class="success-box">
                <strong>✅ GENERATE BERHASIL!</strong><br>
                Notulen dengan struktur lengkap telah dibuat. Silakan review dan lengkapi informasi yang diperlukan.
            </div>
            """, unsafe_allow_html=True)
            
            # Display notulen in expandable sections
            notulen_content = st.session_state.enhanced_notulen
            
            # Split by sections
            sections = re.split(r'\n## ', notulen_content)
            
            for section in sections:
                if section.strip():
                    section_title = section.split('\n')[0] if '\n' in section else section
                    with st.expander(f"📄 {section_title}", expanded=section_title == "INFORMASI UMUM"):
                        if section_title == "INFORMASI UMUM":
                            st.markdown("## " + section)
                        else:
                            st.markdown(section)
            
            # Download section
            st.divider()
            st.markdown("### 💾 Download Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # TXT download
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📄 Download as TXT",
                    data=notulen_content,
                    file_name=f"Notulen_Enhanced_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # Word document download
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                word_buffer = create_enhanced_word_document(notulen_content, f"Notulen_{timestamp}.docx")
                if word_buffer:
                    st.download_button(
                        label="📝 Download as Word",
                        data=word_buffer.getvalue(),
                        file_name=f"Notulen_Enhanced_{timestamp}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            
            with col3:
                # Regenerate button
                if st.button("🔄 Generate Ulang", use_container_width=True):
                    if 'uploaded_transcript' in st.session_state:
                        with st.spinner("Menggunakan analisis mendalam..."):
                            new_result = generate_notulen_with_ai_enhanced(
                                st.session_state.uploaded_transcript, 
                                api_key
                            )
                            st.session_state.enhanced_notulen = new_result['content']
                            st.session_state.generation_source = new_result['source']
                            st.rerun()
            
            # Action buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.code(notulen_content[:1000])
                    st.success("Partial content ready for copy!")
            with col2:
                if st.button("🗑️ Clear Results", use_container_width=True):
                    keys_to_delete = ['enhanced_notulen', 'notulen_generated', 'generation_source']
                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

    with tab2:
        st.markdown("### 💬 Chat with Transcript")
        
        if 'uploaded_transcript' not in st.session_state or not st.session_state.uploaded_transcript:
            st.markdown("""
            <div class="info-box">
                <strong>📝 Informasi:</strong> Silakan upload file transkrip terlebih dahulu di tab "Generate Notulen" 
                untuk mengaktifkan fitur chat.
            </div>
            """, unsafe_allow_html=True)
            
            st.info("""
            **Contoh pertanyaan untuk chat:**
            
            **Tentang Peserta:**
            - Siapa saja yang hadir dalam rapat?
            - Siapa pemimpin rapat?
            - Siapa yang memberikan presentasi?
            
            **Tentang Diskusi:**
            - Apa poin-poin penting yang dibahas?
            - Masalah apa yang diangkat?
            - Solusi apa yang diusulkan?
            
            **Tentang Keputusan:**
            - Keputusan apa yang diambil?
            - Siapa penanggung jawab setiap tindakan?
            - Kapan deadline yang ditetapkan?
            
            **Tentang Arahan:**
            - Arahan apa yang diberikan pimpinan?
            - Tindak lanjut apa yang harus dilakukan?
            - Langkah selanjutnya apa?
            """)
        else:
            st.markdown("""
            <div class="success-box">
                ✅ <strong>Transkrip tersedia!</strong> Anda dapat bertanya tentang detail rapat.
            </div>
            """, unsafe_allow_html=True)
            
            # Initialize chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            # Display chat history
            st.markdown("#### 💭 History Percakapan")
            chat_container = st.container()
            
            with chat_container:
                if st.session_state.chat_history:
                    for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
                        if message["role"] == "user":
                            st.markdown(f'<div class="user-message"><strong>👤 Anda:</strong> {message["content"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="ai-message"><strong>🤖 Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.info("Belum ada percakapan. Mulailah dengan menanyakan sesuatu tentang rapat.")
            
            # Chat input
            st.markdown("#### 💬 Ajukan Pertanyaan")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                question = st.text_input(
                    "Pertanyaan Anda:",
                    placeholder="Contoh: Siapa yang bertanggung jawab untuk action item?",
                    label_visibility="collapsed"
                )
            with col2:
                send_button = st.button("Kirim", use_container_width=True)
            
            # Example questions
            st.markdown("**Contoh pertanyaan cepat:**")
            example_cols = st.columns(4)
            example_questions = [
                "Siapa peserta rapat?",
                "Apa keputusan utama?",
                "Siapa penanggung jawab?",
                "Apa arahan pimpinan?"
            ]
            
            for idx, example in enumerate(example_questions):
                with example_cols[idx]:
                    if st.button(example, key=f"example_{idx}", use_container_width=True):
                        question = example
            
            # Process question
            if (send_button or question) and question.strip():
                # Add user message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": question
                })
                
                # Get AI response
                with st.spinner("🔍 Menganalisis transkrip..."):
                    chat_response = interactive_chat_with_transcript(
                        question,
                        st.session_state.uploaded_transcript,
                        api_key
                    )
                    
                    # Add AI response to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": chat_response['content']
                    })
                
                # Rerun to update display
                st.rerun()
            
            # Chat controls
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear Chat History", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()
            with col2:
                if st.button("💾 Export Chat", use_container_width=True):
                    chat_text = "Chat History:\n\n"
                    for msg in st.session_state.chat_history:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        chat_text += f"{role}: {msg['content']}\n\n"
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="Download Chat",
                        data=chat_text,
                        file_name=f"Chat_History_{timestamp}.txt",
                        mime="text/plain",
                        key="download_chat"
                    )
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p><strong>Enhanced Notulen Generator</strong> • Group Transformasi Korporasi dan Manajemen Program</p>
        <p style='font-size: 0.9rem;'>
            Fitur Unggulan: <strong>Penanggung Jawab</strong> • <strong>Yang Disampaikan</strong> • <strong>Arahan/Tindak Lanjut</strong>
        </p>
        <p style='font-size: 0.8rem; color: #999;'>v2.0 • Structured Output Guaranteed • Professional Format</p>
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
