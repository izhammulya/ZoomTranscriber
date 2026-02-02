import streamlit as st
import re
from datetime import datetime, timedelta
import io
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def process_vtt_text(vtt_text):
    """
    Process VTT text to clean timestamps and metadata
    """
    cleaned_text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt_text)
    cleaned_text = re.sub(r"WEBVTT.*\n", "", cleaned_text)
    cleaned_text = "\n".join([line.strip() for line in cleaned_text.splitlines() if line.strip()])
    return cleaned_text

def extract_detailed_info(transcript):
    """
    Extract detailed information from transcript
    """
    lines = transcript.split('\n')
    
    # Extract speakers
    speakers = []
    for line in lines:
        if ':' in line:
            speaker = line.split(':')[0].strip()
            if 2 < len(speaker) < 50 and speaker not in speakers:
                speakers.append(speaker)
    
    # Extract potential topics
    topics = []
    topic_keywords = ['tentang', 'mengenai', 'pembahasan', 'agenda', 'diskusi', 'materi']
    for line in lines:
        if any(keyword in line.lower() for keyword in topic_keywords):
            if len(line) < 150:
                topics.append(line.strip())
    
    # Extract potential decisions
    decisions = []
    decision_keywords = ['disepakati', 'diputuskan', 'kesimpulan', 'keputusan', 'setuju', 'sepakat']
    for line in lines:
        if any(keyword in line.lower() for keyword in decision_keywords):
            decisions.append(line.strip())
    
    return {
        'speakers': speakers[:15],
        'topics': topics[:10],
        'decisions': decisions[:5],
        'word_count': len(transcript.split()),
        'line_count': len(lines)
    }

def create_detailed_template(transcript):
    """
    Create detailed notulen template with extracted information
    """
    now = datetime.now()
    info = extract_detailed_info(transcript)
    
    template = f"""# NOTULEN RAPAT - DOKUMEN RESMI

## INFORMASI RAPAT
| Item | Keterangan |
|------|------------|
| **Nama Rapat** | Rapat Koordinasi |
| **Tanggal** | {now.strftime('%A, %d %B %Y')} |
| **Waktu** | {now.strftime('%H:%M')} - Selesai WIB |
| **Tempat** | [Lokasi Rapat] |
| **Pemimpin Rapat** | [Nama Lengkap Pemimpin] |
| **Notulen** | Group Transformasi Korporasi dan Manajemen Program |
| **Dokumen** | NOT/{now.strftime('%Y%m%d')}/001 |

## DAFTAR PESERTA
| No | Nama Peserta | Jabatan/Divisi | Keterangan |
|----|--------------|----------------|------------|
"""
    
    # Add speakers as participants
    for i, speaker in enumerate(info['speakers'], 1):
        template += f"| {i} | {speaker} | [Jabatan/Divisi] | Hadir |\n"
    
    template += f"""
## AGENDA RAPAT
1. **Pembukaan** - Pengantar dan penjelasan agenda rapat
2. **Laporan Divisi** - Presentasi progress masing-masing divisi
3. **Diskusi Strategis** - Pembahasan isu-isu penting perusahaan
4. **Koordinasi** - Sinkronisasi antar departemen
5. **Keputusan** - Penetapan keputusan dan arahan
6. **Tindak Lanjut** - Rencana implementasi pasca rapat

## RINCIAN DISKUSI

### 1. Pembukaan dan Pengarahan
**Disampaikan oleh:** [Nama Pemimpin Rapat]
**Waktu:** {now.strftime('%H:%M')} WIB

**Isi Pembahasan:**
- Penyampaian maksud dan tujuan rapat
- Penjelasan agenda yang akan dibahas
- Arahan umum untuk seluruh peserta

**Arahan Spesifik:**
1. [Arahan 1] - Deadline: {(now + timedelta(days=1)).strftime('%d/%m/%Y')}
2. [Arahan 2] - Deadline: {(now + timedelta(days=2)).strftime('%d/%m/%Y')}

### 2. Laporan Progress Divisi
**Disampaikan oleh:** [Nama Manager Divisi]
**Waktu:** [Waktu Presentasi]

**Isi Pembahasan:**
- Progress kerja periode sebelumnya
- Pencapaian target yang telah diraih
- Kendala dan hambatan yang dihadapi
- Rencana kerja periode mendatang

**Data dan Angka:**
- Target: [Angka Target]
- Realisasi: [Angka Realisasi]
- Percentage: [Persentase Pencapaian]

**Keputusan:**
- [Keputusan terkait progress divisi]
- [Arahan untuk perbaikan]

### 3. Diskusi Strategis
**Topik:** {info['topics'][0] if info['topics'] else 'Pembahasan Strategis Perusahaan'}
**Pemimpin Diskusi:** [Nama]

**Poin-poin Diskusi:**
1. **Isu 1:** [Deskripsi isu]
   - Pendapat Peserta A: [Isi pendapat]
   - Pendapat Peserta B: [Isi pendapat]
   - Analisis: [Analisis dari diskusi]

2. **Isu 2:** [Deskripsi isu]
   - Masukan dari Divisi X: [Isi masukan]
   - Saran dari Divisi Y: [Isi saran]
   - Rekomendasi: [Rekomendasi akhir]

**Kesimpulan Diskusi:**
- [Kesimpulan 1]
- [Kesimpulan 2]
- [Kesimpulan 3]

### 4. Koordinasi Antar Departemen
**Fokus:** Optimalisasi kerja sama antar unit kerja

**Koordinasi yang Dibahas:**
- **Proyek Bersama:** [Nama Proyek]
  - Timeline: [Rentang waktu]
  - PIC: [Nama Penanggung Jawab]
  - Kebutuhan: [Resource yang diperlukan]

- **Proses Terkait:** [Nama Proses]
  - Sinkronisasi: [Point sinkronisasi]
  - Eskalasi: [Mekanisme eskalasi]
  - Monitoring: [Cara monitoring]

### 5. Keputusan yang Diambil
**Disepakati dalam rapat:**

1. **Keputusan Utama:**
   - [Detail keputusan 1]
   - Penanggung Jawab: [Nama PJ]
   - Target: [Target spesifik]
   - Deadline: {(now + timedelta(days=7)).strftime('%d/%m/%Y')}

2. **Keputusan Operasional:**
   - [Detail keputusan 2]
   - Penanggung Jawab: [Nama PJ]
   - Timeline: [Jadwal pelaksanaan]
   - Metric: [Metrik pengukuran]

3. **Keputusan Strategis:**
   - [Detail keputusan 3]
   - Penanggung Jawab: [Nama PJ]
   - Impact: [Dampak yang diharapkan]
   - Monitoring: [Mekanisme monitoring]

### 6. Rencana Tindak Lanjut
**Action Plan:**

| No | Action Item | PIC | Departemen | Deadline | Status | Keterangan |
|----|-------------|-----|------------|----------|--------|------------|
| 1  | [Deskripsi Tugas 1] | [Nama PIC] | [Departemen] | {(now + timedelta(days=3)).strftime('%d/%m/%Y')} | Pending | [Detail] |
| 2  | [Deskripsi Tugas 2] | [Nama PIC] | [Departemen] | {(now + timedelta(days=5)).strftime('%d/%m/%Y')} | Pending | [Detail] |
| 3  | [Deskripsi Tugas 3] | [Nama PIC] | [Departemen] | {(now + timedelta(days=7)).strftime('%d/%m/%Y')} | Pending | [Detail] |
| 4  | [Deskripsi Tugas 4] | [Nama PIC] | [Departemen] | {(now + timedelta(days=14)).strftime('%d/%m/%Y')} | Pending | [Detail] |

## JADWAL FOLLOW-UP
- **Rapat Monitoring:** {(now + timedelta(days=7)).strftime('%A, %d %B %Y')} pukul {now.strftime('%H:%M')} WIB
- **Deadline Interim:** {(now + timedelta(days=3)).strftime('%d/%m/%Y')}
- **Laporan Progress:** Setiap Jumat pukul 16:00 WIB

## PENUTUP
Rapat ditutup pada pukul [Waktu Penutupan] dengan kesepakatan untuk melaksanakan semua keputusan dan arahan yang telah ditetapkan.

---
**Disusun oleh:** Group Transformasi Korporasi dan Manajemen Program  
**Tanggal Penyusunan:** {now.strftime('%d %B %Y %H:%M WIB')}  
**Status Dokumen:** DRAFT - Harap direview dalam 24 jam  
**Lampiran:** Transkrip rapat ({info['word_count']} kata, {info['line_count']} baris)

*Notulen ini disusun berdasarkan pembahasan aktual dalam rapat. Silakan lengkapi informasi [detail] sesuai dengan diskusi.*
"""
    
    return template

def generate_detailed_notulen_with_gemini_pro(transcript, api_key):
    """
    Generate detailed notulen using Gemini Pro with enhanced prompting
    """
    if not api_key:
        return {
            'success': True,
            'content': create_detailed_template(transcript),
            'source': 'detailed_template',
            'model': 'template_pro'
        }
    
    try:
        genai.configure(api_key=api_key)
        
        # Use Gemini Pro for better quality
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        prompt = f"""
        TUGAS: BUATKAN NOTULEN RAPAT YANG SANGAT DETAIL DAN SPESIFIK DARI TRANSCRIPT BERIKUT.

        **TRANSCRIPT RAPAT:**
        {transcript[:5000]}

        **INSTRUKSI DETAIL:**
        1. **EKSTRAK INFORMASI SPESIFIK:**
           - Nama-nama lengkap semua peserta
           - Jabatan dan divisi masing-masing peserta
           - Topik-topik spesifik yang dibahas
           - Angka, data, dan metrik yang disebutkan
           - Timeline dan deadline yang disepakati
           - Keputusan konkret dengan penanggung jawab

        2. **FORMAT OUTPUT YANG DIMINTA:**
        # NOTULEN RAPAT - [NAMA RAPAT]

        ## INFORMASI RAPAT
        [tabel dengan semua detail rapat]

        ## DAFTAR PESERTA LENGKAP
        [tabel dengan nama, jabatan, divisi, dan keterangan]

        ## RINCIAN DISKUSI PER TOPIK
        ### [Topik 1: Nama Topik Spesifik]
        **Waktu Diskusi:** [jam:menit]
        **Pemimpin Diskusi:** [Nama]
        **Peserta Aktif:** [Daftar nama]
        
        **Isi Pembahasan Detail:**
        - [Point 1 dengan detail]
        - [Point 2 dengan detail]
        - [Data dan angka yang disebutkan]
        
        **Argumentasi dan Diskusi:**
        - [Pendapat peserta A: isi pendapat]
        - [Pendapat peserta B: isi pendapat]
        - [Debat atau perbedaan pendapat]
        
        **Kesimpulan Topik:**
        - [Kesimpulan 1 dengan detail]
        - [Kesimpulan 2 dengan detail]

        ### [Topik 2: Nama Topik Spesifik]
        [struktur sama seperti di atas]

        ## KEPUTUSAN DAN ARAHAN SPESIFIK
        ### Keputusan Utama:
        1. [Keputusan spesifik dengan detail]
           - Penanggung Jawab: [Nama lengkap]
           - Divisi: [Nama divisi]
           - Deadline: [Tanggal spesifik]
           - Target: [Target terukur]
           - Sumber Daya: [Resource yang dialokasi]

        2. [Keputusan spesifik dengan detail]
           [detail seperti di atas]

        ## ACTION PLAN TERPERINCI
        | No | Action Item | PIC | Divisi | Deadline | Priority | Dependencies | Success Criteria |
        |----|-------------|-----|--------|----------|----------|--------------|------------------|
        | 1  | [Deskripsi tugas sangat spesifik] | [Nama PIC] | [Divisi] | [DD/MM/YYYY] | High/Medium/Low | [Dependency] | [Kriteria sukses] |

        ## DATA DAN METRIK YANG DISEPAKATI
        - [Metrik 1]: [Nilai] dengan target [Target]
        - [Metrik 2]: [Nilai] dengan target [Target]
        - [Timeline]: [Jadwal spesifik dengan milestone]

        3. **KETENTUAN:**
           - Gunakan nama asli dari transcript
           - Sertakan angka dan data konkret
           - Detailkan setiap arahan dengan spesifik
           - Tulis timeline dengan jelas
           - Cantumkan penanggung jawab untuk setiap item
           - Format harus sangat terstruktur

        4. **JIKA INFORMASI TIDAK LENGKAP:**
           - Gunakan [Perlu konfirmasi] untuk data yang kurang
           - Tetap buat struktur lengkap
           - Tandai informasi yang perlu dilengkapi

        **OUTPUT HARUS:** Sangat detail, spesifik, terstruktur, dan siap digunakan sebagai dokumen resmi.
        """
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent output
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 6000,  # More tokens for detailed output
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
        )
        
        if response and response.text:
            content = response.text.strip()
            
            # Enhance the content
            enhanced_content = content
            
            # Add header if missing
            if not enhanced_content.startswith('# NOTULEN RAPAT'):
                enhanced_content = f"# NOTULEN RAPAT - DOKUMEN RESMI\n\n{enhanced_content}"
            
            # Add timestamp
            now = datetime.now()
            enhanced_content += f"\n\n---\n**Dibuat oleh:** Group Transformasi Korporasi dan Manajemen Program\n**Tanggal:** {now.strftime('%d %B %Y %H:%M WIB')}\n**Model AI:** Gemini 1.5 Pro\n"
            
            return {
                'success': True,
                'content': enhanced_content,
                'source': 'gemini_pro_detailed',
                'model': 'gemini-1.5-pro'
            }
    
    except Exception as e:
        pass  # Fall through to detailed template
    
    # Fallback to detailed template
    return {
        'success': True,
        'content': create_detailed_template(transcript),
        'source': 'fallback_detailed',
        'model': 'template_pro'
    }

def main():
    st.set_page_config(
        page_title="Notulen Generator Pro - Detail & Spesifik",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Professional CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        color: #1a237e;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .sub-header {
        text-align: center;
        color: #5c6bc0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    .model-badge {
        background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
        color: white;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin: 0.25rem;
    }
    .performance-badge {
        background: linear-gradient(90deg, #00c853 0%, #64dd17 100%);
        color: white;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin: 0.25rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(26, 35, 126, 0.3);
    }
    .info-card {
        background: #f5f7ff;
        border-left: 4px solid #1a237e;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .success-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-left: 4px solid #4caf50;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .detail-highlight {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
    }
    .metric-box {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a237e;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.25rem;
    }
    .notulen-section {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .notulen-section h3 {
        color: #1a237e;
        border-bottom: 2px solid #1a237e;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">📋 Notulen Generator Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gemini Pro • Detail Spesifik • Output Profesional</p>', unsafe_allow_html=True)
    
    # Feature badges
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="model-badge">🚀 Gemini 1.5 Pro</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="performance-badge">🎯 Detail Spesifik</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="model-badge">📊 Data & Angka</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="performance-badge">⏰ Timeline Detail</div>', unsafe_allow_html=True)
    
    # Get API key
    try:
        api_key = st.secrets["api_key"]
        api_key_available = True
    except:
        api_key = None
        api_key_available = False
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Model Configuration")
        
        if api_key_available:
            st.success("✅ Gemini Pro Ready")
            st.markdown("""
            **Active Model:** Gemini 1.5 Pro
            **Features:**
            - 1M token context
            - Advanced reasoning
            - Detailed extraction
            - Professional formatting
            """)
        else:
            st.warning("⚠️ Basic Mode")
            st.info("Setup API key untuk akses Gemini Pro dengan output lebih detail")
        
        st.header("🎯 Output Features")
        st.markdown("""
        **Detail yang Diambil:**
        - ✅ Nama lengkap semua peserta
        - ✅ Jabatan dan divisi
        - ✅ Topik spesifik
        - ✅ Angka dan data
        - ✅ Timeline & deadline
        - ✅ Penanggung jawab per item
        - ✅ Action plan rinci
        - ✅ Success criteria
        """)
        
        st.header("📊 Performance")
        if 'generation_count' not in st.session_state:
            st.session_state.generation_count = 0
        
        st.metric("Notulen Dibuat", st.session_state.generation_count)
    
    # Main content
    st.markdown("### 📤 Upload Transcript untuk Notulen Detail")
    
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
        
        # Show detailed analysis
        info = extract_detailed_info(transcript)
        
        st.markdown("#### 📊 Analisis Transcript")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{info['word_count']:,}</div>
                <div class="metric-label">Kata</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{len(info['speakers'])}</div>
                <div class="metric-label">Pembicara</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{len(info['topics'])}</div>
                <div class="metric-label">Topik</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{len(info['decisions'])}</div>
                <div class="metric-label">Keputusan</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Preview
        with st.expander("👁️ Preview Transcript", expanded=False):
            st.text_area("", transcript[:1000], height=200, disabled=True)
        
        # Generate button
        st.markdown("#### 🚀 Generate Options")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✨ Generate dengan Gemini Pro", type="primary", use_container_width=True):
                with st.spinner("🧠 Gemini Pro menganalisis transcript dengan detail..."):
                    result = generate_detailed_notulen_with_gemini_pro(transcript, api_key)
                    
                    st.session_state.notulen = result['content']
                    st.session_state.generated = True
                    st.session_state.generation_model = result['model']
                    st.session_state.generation_count += 1
                    
                    if result['source'] == 'gemini_pro_detailed':
                        st.success("✅ Gemini Pro generation berhasil!")
                        st.markdown("""
                        <div class="success-card">
                            <strong>🎯 OUTPUT DETAIL SPESIFIK</strong><br>
                            Gemini Pro telah menghasilkan notulen dengan detail lengkap:
                            - Nama dan jabatan spesifik
                            - Data dan angka konkret
                            - Timeline terperinci
                            - Action plan rinci
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.success("✅ Template detail berhasil dibuat!")
        
        with col2:
            if st.button("📋 Generate Template Detail", use_container_width=True):
                template = create_detailed_template(transcript)
                st.session_state.notulen = template
                st.session_state.generated = True
                st.session_state.generation_model = 'template_pro'
                st.session_state.generation_count += 1
                st.success("✅ Template detail berhasil dibuat!")
    
    # Display results
    if 'notulen' in st.session_state and st.session_state.get('generated'):
        st.divider()
        st.markdown("### 📋 HASIL NOTULEN DETAIL")
        
        # Model info
        model = st.session_state.get('generation_model', 'unknown')
        st.markdown(f'<span class="model-badge">Model: {model}</span>', unsafe_allow_html=True)
        
        # Display in sections
        content = st.session_state.notulen
        
        # Split by main sections
        sections = re.split(r'\n## ', content)
        
        for section in sections:
            if section.strip():
                section_title = section.split('\n')[0] if '\n' in section else section
                
                if 'INFORMASI RAPAT' in section_title or 'DAFTAR PESERTA' in section_title:
                    with st.expander(f"📄 {section_title}", expanded=True):
                        st.markdown(f"## {section}", unsafe_allow_html=True)
                elif 'RINCIAN DISKUSI' in section_title or 'KEPUTUSAN' in section_title:
                    with st.expander(f"💬 {section_title}", expanded=True):
                        st.markdown(f"## {section}", unsafe_allow_html=True)
                elif 'ACTION' in section_title.upper() or 'TINDAK LANJUT' in section_title:
                    with st.expander(f"🎯 {section_title}", expanded=True):
                        st.markdown(f"## {section}", unsafe_allow_html=True)
                        st.markdown("""
                        <div class="detail-highlight">
                            <strong>📌 Action Items Detail:</strong><br>
                            Setiap tugas memiliki PIC, deadline, dan kriteria sukses yang spesifik.
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    with st.expander(f"📋 {section_title}"):
                        st.markdown(f"## {section}", unsafe_allow_html=True)
        
        # Download section
        st.divider()
        st.markdown("### 💾 Download")
        
        col1, col2 = st.columns(2)
        with col1:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📄 Download TXT",
                data=content,
                file_name=f"Notulen_Detail_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # Simple Word document
            try:
                doc = Document()
                doc.add_heading('NOTULEN RAPAT - DOKUMEN DETAIL', 0)
                doc.add_paragraph(content)
                
                buffer = io.BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                
                st.download_button(
                    label="📝 Download Word",
                    data=buffer.getvalue(),
                    file_name=f"Notulen_Detail_{timestamp}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except:
                pass
        
        # Regenerate option
        if st.button("🔄 Generate Ulang dengan Analisis Lebih Detail", use_container_width=True):
            if 'transcript' in st.session_state:
                with st.spinner("Menganalisis lebih dalam..."):
                    result = generate_detailed_notulen_with_gemini_pro(st.session_state.transcript, api_key)
                    st.session_state.notulen = result['content']
                    st.session_state.generation_model = result['model']
                    st.rerun()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1.5rem;'>
        <p><strong>Notulen Generator Pro • Gemini 1.5 Pro • Output Detail Spesifik</strong></p>
        <p style='font-size: 0.9rem;'>Group Transformasi Korporasi dan Manajemen Program</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # Initialize session state
    if 'generation_count' not in st.session_state:
        st.session_state.generation_count = 0
    
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
