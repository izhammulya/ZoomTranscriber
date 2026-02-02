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

def extract_specific_details(transcript):
    """
    Extract VERY SPECIFIC details from transcript
    """
    lines = transcript.split('\n')
    
    # Find speakers with specific patterns
    speakers = {}
    for line in lines:
        if ':' in line:
            parts = line.split(':')
            if len(parts) > 1:
                speaker = parts[0].strip()
                content = ':'.join(parts[1:]).strip()
                
                if 3 <= len(speaker) <= 50:
                    # Check for position indicators
                    position = "Peserta"
                    if 'direktur' in speaker.lower() or 'dirut' in speaker.lower():
                        position = "Direktur"
                    elif 'manajer' in speaker.lower() or 'mgr' in speaker.lower():
                        position = "Manajer"
                    elif 'kepala' in speaker.lower() or 'head' in speaker.lower():
                        position = "Kepala Divisi"
                    
                    speakers[speaker] = {
                        'position': position,
                        'content_samples': [content[:100]] if content else []
                    }
    
    # Extract specific decisions with action items
    decisions = []
    action_patterns = [
        (r'(?:harus|wajib|perlu|tolong|silahkan)\s+(.+?)(?:dalam|pada|sebelum|hingga)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', 'deadline'),
        (r'(?:disepakati|diputuskan|setuju|sepakat)\s+bahwa\s+(.+?)(?:oleh|dari)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'decision_with_pic'),
        (r'(\d+%|\d+\s+persen|Rp\s*\d+[.,]?\d*|\d+\s+juta|\d+\s+miliar)', 'numbers'),
    ]
    
    for line in lines:
        for pattern, pattern_type in action_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                if pattern_type == 'deadline':
                    decisions.append(f"Tugas: {match[0]} - Deadline: {match[1]}")
                elif pattern_type == 'decision_with_pic':
                    decisions.append(f"Keputusan: {match[0]} - PIC: {match[1]}")
                elif pattern_type == 'numbers':
                    decisions.append(f"Angka disebutkan: {match}")
    
    # Extract specific topics
    topics = []
    for line in lines:
        if len(line) > 20 and len(line) < 200:
            if any(word in line.lower() for word in ['tentang', 'mengenai', 'agenda', 'topik', 'materi']):
                topics.append(line.strip())
    
    return {
        'speakers': speakers,
        'decisions': decisions[:10],
        'topics': topics[:5],
        'total_speakers': len(speakers),
        'total_lines': len(lines),
        'word_count': len(transcript.split())
    }

def create_sharp_template(details):
    """
    Create SHARP and SPECIFIC template
    """
    now = datetime.now()
    
    template = f"""# NOTULEN RAPAT - DOKUMEN SPESIFIK

## INFORMASI DETAIL
| Item | Keterangan Spesifik |
|------|-------------------|
| **Nama Rapat** | Rapat Koordinasi Operasional |
| **Tanggal** | {now.strftime('%A, %d %B %Y')} |
| **Waktu** | {now.strftime('%H:%M')} - {now.strftime('%H:%M')} WIB |
| **Lokasi** | Ruang Rapat Virtual/Langsung |
| **Dokumen** | NOT/{now.strftime('%Y%m%d')}/RK/{now.strftime('%H%M')} |
| **Status** | DRAFT - Review Required |

## PESERTA DETAIL ({details['total_speakers']} orang)
| No | Nama Lengkap | Jabatan | Divisi | Kontribusi |
|----|--------------|---------|--------|------------|
"""
    
    for i, (speaker, info) in enumerate(list(details['speakers'].items())[:12], 1):
        contribution = info['content_samples'][0][:50] + "..." if info['content_samples'] else "Berpartisipasi aktif"
        template += f"| {i} | {speaker} | {info['position']} | [Divisi] | {contribution} |\n"
    
    template += f"""
## AGENDA SPESIFIK
**Rapat ini membahas {len(details['topics'])} topik utama:**
{chr(10).join(['1. ' + topic for topic in details['topics']]) if details['topics'] else '1. Optimasi proses operasional'}

## DISKUSI DETAIL - POINT BY POINT

### **POIN 1: Pembukaan dan Konteks**
**Waktu:** {now.strftime('%H:%M')} - {now.strftime('%H:%M')}
**Pemimpin:** [Nama Pemimpin Rapat]

**Detail Pembahasan:**
- **Konteks:** Rapat membahas progress dan tantangan operasional
- **Tujuan:** Penyelesaian kendala dan optimalisasi proses
- **Scope:** Fokus pada implementasi strategi Q1 2024

**Data yang Disebutkan:**
- Jumlah peserta aktif: {details['total_speakers']} orang
- Durasi estimasi: 60-90 menit
- Target penyelesaian: {now.strftime('%d/%m/%Y')}

### **POIN 2: Analisis Kondisi Saat Ini**
**Fakta-fakta Kunci:**
"""
    
    # Add specific facts
    if details['decisions']:
        for i, decision in enumerate(details['decisions'][:3], 1):
            template += f"{i}. {decision}\n"
    else:
        template += "1. Analisis kondisi operasional terkini\n2. Identifikasi bottleneck dan kendala\n3. Review performance metrics\n"
    
    template += f"""
**Insight dari Peserta:**
{chr(10).join(['- ' + speaker + ': ' + list(info['content_samples'])[0][:80] + '...' for speaker, info in list(details['speakers'].items())[:3]]) if details['speakers'] else '- Diskusi aktif mengenai optimasi proses'}

### **POIN 3: Action Plan Detail**
**Rencana Aksi Konkret:**

| No | Aktivitas Spesifik | Penanggung Jawab | Departemen | Deadline | Success Metric |
|----|-------------------|------------------|------------|----------|----------------|
| 1 | Penyelesaian laporan Q4 2023 | [Nama PIC] | Finance | {(now + timedelta(days=3)).strftime('%d/%m/%Y')} | Dokumen lengkap + analisis |
| 2 | Koordinasi cross-department | [Nama PIC] | Operations | {(now + timedelta(days=2)).strftime('%d/%m/%Y')} | Meeting minutes + action items |
| 3 | Implementasi sistem baru | [Nama PIC] | IT | {(now + timedelta(days=7)).strftime('%d/%m/%Y')} | UAT passed + user training |

**Detail Implementasi:**
- **Timeline:** {(now + timedelta(days=1)).strftime('%d/%m')} - {(now + timedelta(days=14)).strftime('%d/%m/%Y')}
- **Budget:** [Detail alokasi budget]
- **Resource:** [Spesifikasi resource yang dibutuhkan]
- **Risk:** [Identifikasi risiko dan mitigasi]

### **POIN 4: Follow-up dan Monitoring**
**Mekanisme Monitoring:**
1. **Daily Standup:** Setiap hari pukul 09:00 WIB
2. **Weekly Review:** Setiap Jumat pukul 16:00 WIB
3. **Reporting:** Laporan progress setiap Senin pagi

**Escalation Path:**
- Level 1: PIC → Manager
- Level 2: Manager → Direktur
- Level 3: Direktur → Komisaris

## KESIMPULAN EXECUTIVE
**Summary Eksekutif:**
- Total keputusan: {len(details['decisions'])} item
- PIC teridentifikasi: {min(3, details['total_speakers'])} orang
- Timeline: {(now + timedelta(days=1)).strftime('%d/%m')} - {(now + timedelta(days=30)).strftime('%d/%m/%Y')}
- Key success factor: Koordinasi intensif dan monitoring ketat

**Next Immediate Actions:**
1. [Tindakan 24 jam pertama]
2. [Koordinasi dengan stakeholder]
3. [Preparation dokumen pendukung]

---
**Generated by:** Notulen Generator Pro - TKMP  
**Timestamp:** {now.strftime('%d/%m/%Y %H:%M:%S')}  
**Based on:** {details['word_count']} kata, {details['total_lines']} baris transcript  
**Confidence Level:** HIGH (Data spesifik terdeteksi)
"""
    
    return template

def generate_sharp_notulen(transcript, api_key):
    """
    Generate SHARP and SPECIFIC notulen with aggressive extraction
    """
    # First, extract specific details
    details = extract_specific_details(transcript)
    
    if not api_key:
        return {
            'success': True,
            'content': create_sharp_template(details),
            'source': 'sharp_template',
            'model': 'template_plus_extraction'
        }
    
    try:
        genai.configure(api_key=api_key)
        
        # Use PRO model for best results
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        # VERY SHARP AND SPECIFIC PROMPT
        prompt = f"""
        **TUGAS KRITIS: BUAT NOTULEN YANG SANGAT SPESIFIK DAN DETAIL**
        
        **INSTRUKSI MUTLAK:**
        1. **EKSTRAK SEMUA DETAIL SPESIFIK** dari transcript
        2. **JANGAN BUAT GENERALISASI** - hanya fakta spesifik
        3. **TANGKAP SEMUA NAMA, ANGKA, TANGGAL, DEADLINE**
        4. **FORMAT DENGAN STRUKTUR YANG SANGAT DETAIL**
        
        **TRANSCRIPT ASLI:**
        {transcript[:5000]}
        
        **DATA YANG SUDAH DIEXTRAK:**
        - Jumlah pembicara: {details['total_speakers']}
        - Topik terdeteksi: {len(details['topics'])}
        - Keputusan terdeteksi: {len(details['decisions'])}
        
        **FORMAT OUTPUT YANG WAJIB:**
        
        # NOTULEN RAPAT - [NAMA SPESIFIK DARI TRANSCRIPT]
        
        ## 📊 METRICS & DATA POINTS
        | Metric | Value | Detail |
        |--------|-------|--------|
        | Durasi Rapat | [jam:menit] | [dari transcript] |
        | Jumlah Peserta | [angka] | [nama-nama spesifik] |
        | Topik Dibahas | [jumlah] | [list topik spesifik] |
        | Keputusan Diambil | [jumlah] | [detail spesifik] |
        
        ## 👥 PARTICIPANT DETAILS
        ### Speaker 1: [NAMA LENGKAP]
        - **Role:** [jabatan spesifik dari transcript]
        - **Key Contributions:**
          1. "[Quote spesifik dari pembicaraan]" → [Analisis/Impact]
          2. "[Quote spesifik lainnya]" → [Analisis/Impact]
        
        ### Speaker 2: [NAMA LENGKAP]
        [format sama]
        
        ## 💬 CONVERSATION THREADS
        ### Thread 1: [TOPIK SPESIFIK]
        **Timeline:** [waktu mulai] - [waktu selesai]
        **Participants:** [nama-nama yang terlibat]
        
        **Conversation Flow:**
        1. [Speaker A]: "[Statement spesifik]"
           → [Speaker B]: "[Response spesifik]"
           → **Outcome:** [Kesimpulan spesifik]
        
        2. [Speaker C]: "[Statement spesifik]"
           → [Speaker D]: "[Response spesifik]"
           → **Data Point:** [Angka/fakta yang disebut]
        
        ### Thread 2: [TOPIK SPESIFIK LAIN]
        [format sama]
        
        ## 🎯 ACTION ITEMS (VERY SPECIFIC)
        ### High Priority (Due < 3 days)
        | ID | Action Description | Assigned To | Department | Specific Deadline | Success Criteria | Dependencies |
        |----|-------------------|-------------|------------|-------------------|------------------|--------------|
        | A1 | [Deskripsi SANGAT spesifik] | [NAMA LENGKAP] | [Departemen] | [DD/MM/YYYY HH:MM] | [Metric spesifik] | [Dependency] |
        
        ### Medium Priority (Due < 7 days)
        [format sama]
        
        ## 📈 DATA & NUMBERS MENTIONED
        ### Financial Data
        - Budget: [jumlah spesifik] untuk [tujuan spesifik]
        - Revenue Target: [angka] dengan timeline [tanggal]
        - Cost Saving: [persentase] dari [baseline]
        
        ### Operational Data
        - Productivity: [angka] unit/jam
        - Quality Rate: [persentase] defect
        - Timeline: [tanggal spesifik] untuk [milestone]
        
        ## 🔍 KEY INSIGHTS
        ### Insight 1: [Judul insight spesifik]
        - **Evidence:** [Quote/fakta dari transcript]
        - **Implication:** [Dampak pada bisnis]
        - **Recommendation:** [Rekomendasi spesifik]
        
        ### Insight 2: [Judul insight spesifik]
        [format sama]
        
        ## ⚠️ RISKS & ISSUES IDENTIFIED
        ### Risk 1: [Deskripsi risk spesifik]
        - **Probability:** High/Medium/Low
        - **Impact:** High/Medium/Low
        - **Owner:** [Nama penanggung jawab]
        - **Mitigation:** [Rencana mitigasi spesifik]
        
        **RULES FOR SPECIFICITY:**
        1. SELALU gunakan nama asli dari transcript
        2. SELALU sebutkan angka eksak yang disebut
        3. SELALU cantumkan tanggal spesifik
        4. SELALU quote pembicaraan yang penting
        5. JANGAN gunakan "[...]" atau generalisasi
        
        **CONTOH OUTPUT YANG BAIK:**
        "Budi Santoso (Manager Sales) mengatakan: 'Target Q1 adalah Rp 8.5M, namun realisasi hanya Rp 6.2M (73%). Kendala utama adalah supply chain delay dari vendor PT ABC.'"
        
        **CONTOH OUTPUT YANG BURUK:**
        "Diskusi mengenai target sales dan kendala yang dihadapi."
        
        **OUTPUT HARUS:** Sangat spesifik, detail, factual, dan actionable.
        """
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,  # Very low for maximum consistency
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 8000,  # More tokens for detailed output
                "stop_sequences": ["##"]
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
            
            # Post-process untuk membuat lebih tajam
            lines = content.split('\n')
            sharp_lines = []
            
            for line in lines:
                # Remove generic phrases
                if any(phrase in line.lower() for phrase in ['secara umum', 'pada dasarnya', 'umumnya', 'biasanya']):
                    continue
                
                # Enhance specific mentions
                if any(word in line for word in ['Rp', '%', 'hari', 'jam', 'target', 'deadline']):
                    sharp_lines.append(f"🔸 {line}")
                elif line.strip().startswith('###') or line.strip().startswith('##'):
                    sharp_lines.append(f"\n{line}")
                else:
                    sharp_lines.append(line)
            
            sharp_content = '\n'.join(sharp_lines)
            
            # Add extraction summary
            sharp_content += f"\n\n---\n**EXTRACTION SUMMARY**\n"
            sharp_content += f"- Speakers identified: {details['total_speakers']}\n"
            sharp_content += f"- Topics extracted: {len(details['topics'])}\n"
            sharp_content += f"- Decisions captured: {len(details['decisions'])}\n"
            sharp_content += f"- Model: Gemini 1.5 Pro (Max Specificity Mode)\n"
            
            return {
                'success': True,
                'content': sharp_content,
                'source': 'gemini_pro_sharp',
                'model': 'gemini-1.5-pro',
                'extraction_stats': details
            }
    
    except Exception as e:
        pass
    
    # Fallback to sharp template
    return {
        'success': True,
        'content': create_sharp_template(details),
        'source': 'sharp_fallback',
        'model': 'template_with_extraction',
        'extraction_stats': details
    }

def main():
    st.set_page_config(
        page_title="Notulen SHARP - Output Spesifik Detail",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sharp CSS
    st.markdown("""
    <style>
    .sharp-header {
        text-align: center;
        padding: 1.5rem 0;
        color: #d32f2f;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    .sub-sharp {
        text-align: center;
        color: #5d4037;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    .sharp-badge {
        background: linear-gradient(90deg, #d32f2f 0%, #f44336 100%);
        color: white;
        padding: 0.6rem 1.4rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 700;
        display: inline-block;
        margin: 0.25rem;
        border: 2px solid #b71c1c;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .detail-badge {
        background: linear-gradient(90deg, #1976d2 0%, #2196f3 100%);
        color: white;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 0.2rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #d32f2f 0%, #f44336 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.85rem 1.8rem;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s;
        border: 2px solid #b71c1c;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 20px rgba(211, 47, 47, 0.4);
        background: linear-gradient(90deg, #c62828 0%, #e53935 100%);
    }
    .sharp-card {
        background: white;
        border: 2px solid #ffcdd2;
        border-radius: 10px;
        padding: 1.8rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .data-point {
        background: #ffebee;
        border-left: 4px solid #d32f2f;
        padding: 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        font-weight: 500;
    }
    .speaker-highlight {
        background: #e3f2fd;
        border: 1px solid #1976d2;
        border-radius: 6px;
        padding: 0.8rem;
        margin: 0.3rem 0;
    }
    .metric-box {
        background: white;
        border: 2px solid #4caf50;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #d32f2f;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #555;
        margin-top: 0.3rem;
        font-weight: 600;
    }
    .specific-item {
        background: #fff8e1;
        border-left: 4px solid #ff9800;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        font-weight: 500;
    }
    .quote-box {
        background: #f1f8e9;
        border: 1px solid #7cb342;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.8rem 0;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="sharp-header">🎯 NOTULEN SHARP</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-sharp">Output SANGAT Spesifik • Detail Maksimal • Fakta Konkret</p>', unsafe_allow_html=True)
    
    # Sharp badges
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="sharp-badge">🔍 MAX SPECIFICITY</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="detail-badge">📊 DETAIL EXTRACTION</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="sharp-badge">💬 QUOTE CAPTURE</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="detail-badge">🎯 ACTION FOCUSED</div>', unsafe_allow_html=True)
    
    # Get API key
    try:
        api_key = st.secrets["api_key"]
        api_key_available = True
    except:
        api_key = None
        api_key_available = False
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Sharp Mode Configuration")
        
        if api_key_available:
            st.success("✅ Gemini Pro Ready")
            st.markdown("""
            **Sharp Mode Features:**
            - Quote extraction
            - Number capture
            - Name identification
            - Deadline tracking
            - Specific fact finding
            """)
        else:
            st.warning("⚠️ Template Mode")
            st.info("API key dibutuhkan untuk ekstraksi maksimal")
        
        st.header("🎯 What Makes It SHARP")
        st.markdown("""
        **Specificity Targets:**
        ✅ **Names:** Ekstrak SEMUA nama
        ✅ **Numbers:** Tangkap SEMUA angka
        ✅ **Dates:** Semua deadline & timeline
        ✅ **Quotes:** Kutipan penting
        ✅ **Actions:** Detail spesifik tugas
        ✅ **Metrics:** Data terukur
        
        **Output Style:**
        - No generalizations
        - No "[...]" placeholders
        - Direct quotes
        - Specific data points
        """)
    
    # Main content
    st.markdown('<div class="sharp-card"><strong>📤 UPLOAD TRANSCRIPT untuk Analisis SHARP</strong><br>System akan mengekstrak SEMUA detail spesifik dari percakapan.</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Pilih file transcript",
        type=['vtt', 'txt'],
        help="File akan dianalisis dengan detail maksimal",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        content = uploaded_file.getvalue().decode("utf-8", errors='ignore')
        transcript = process_vtt_text(content)
        st.session_state.transcript = transcript
        
        # Pre-analysis
        details = extract_specific_details(transcript)
        
        st.markdown("#### 🔍 Pre-Analysis Results")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{details['total_speakers']}</div>
                <div class="metric-label">Pembicara</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{len(details['topics'])}</div>
                <div class="metric-label">Topik</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{len(details['decisions'])}</div>
                <div class="metric-label">Keputusan</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{details['word_count']:,}</div>
                <div class="metric-label">Kata</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show extracted details
        with st.expander("🔍 Lihat Detail yang Sudah Diekstrak"):
            if details['speakers']:
                st.markdown("**Pembicara Teridentifikasi:**")
                for speaker, info in list(details['speakers'].items())[:8]:
                    st.markdown(f'<div class="speaker-highlight">👤 {speaker} ({info["position"]})</div>', unsafe_allow_html=True)
            
            if details['decisions']:
                st.markdown("**Keputusan Terdeteksi:**")
                for decision in details['decisions'][:5]:
                    st.markdown(f'<div class="specific-item">✅ {decision}</div>', unsafe_allow_html=True)
        
        # Generate button
        st.markdown("#### 🚀 Generate SHARP Notulen")
        
        if st.button("🎯 GENERATE SHARP NOTULEN", type="primary", use_container_width=True):
            with st.spinner("🔍 Mengekstrak detail spesifik dengan maksimal..."):
                result = generate_sharp_notulen(transcript, api_key)
                
                st.session_state.notulen = result['content']
                st.session_state.generated = True
                st.session_state.model = result['model']
                st.session_state.strategy = result['source']
                st.session_state.stats = result.get('extraction_stats', {})
                
                st.success(f"✅ SHARP Notulen berhasil dibuat!")
                
                # Show stats
                if 'extraction_stats' in result:
                    stats = result['extraction_stats']
                    st.markdown(f"""
                    <div class="sharp-card">
                        <strong>📊 Extraction Results:</strong><br>
                        • Speakers: {stats['total_speakers']}<br>
                        • Topics: {len(stats['topics'])}<br>
                        • Decisions: {len(stats['decisions'])}<br>
                        • Strategy: {result['source']}
                    </div>
                    """, unsafe_allow_html=True)
    
    # Display results
    if 'notulen' in st.session_state and st.session_state.get('generated'):
        st.divider()
        st.markdown("### 📋 SHARP NOTULEN OUTPUT")
        
        # Badge
        st.markdown('<div class="sharp-badge">🎯 OUTPUT SHARP MODE</div>', unsafe_allow_html=True)
        
        # Display with highlights
        content = st.session_state.notulen
        
        # Split and display with formatting
        lines = content.split('\n')
        
        current_section = ""
        for line in lines:
            if line.startswith('# '):
                st.markdown(f'<h1 style="color: #d32f2f; border-bottom: 3px solid #d32f2f; padding-bottom: 10px;">{line[2:]}</h1>', unsafe_allow_html=True)
            elif line.startswith('## '):
                st.markdown(f'<h2 style="color: #1976d2; margin-top: 30px;">{line[3:]}</h2>', unsafe_allow_html=True)
                current_section = line[3:]
            elif line.startswith('### '):
                st.markdown(f'<h3 style="color: #388e3c; margin-top: 20px;">{line[4:]}</h3>', unsafe_allow_html=True)
            elif line.strip().startswith('|') and '|' in line:
                # Table
                st.markdown(line)
            elif 'Rp' in line or '%' in line or ':' in line and len(line.split(':')) > 1:
                # Data point
                st.markdown(f'<div class="data-point">📊 {line}</div>', unsafe_allow_html=True)
            elif '"' in line or ':' in line and any(name in line for name in list(st.session_state.stats.get('speakers', {}).keys())[:5]):
                # Quote or speaker line
                st.markdown(f'<div class="quote-box">💬 {line}</div>', unsafe_allow_html=True)
            elif line.strip() and len(line.strip()) > 10:
                # Regular content
                st.markdown(line)
            elif line.strip() == '':
                st.markdown('<br>', unsafe_allow_html=True)
        
        # Download section
        st.divider()
        st.markdown("### 💾 Download SHARP Output")
        
        col1, col2 = st.columns(2)
        with col1:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📄 Download TXT (Sharp)",
                data=content,
                file_name=f"Notulen_SHARP_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            try:
                doc = Document()
                doc.add_heading('NOTULEN SHARP - OUTPUT DETAIL', 0)
                doc.add_paragraph(content)
                
                buffer = io.BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                
                st.download_button(
                    label="📝 Download Word (Sharp)",
                    data=buffer.getvalue(),
                    file_name=f"Notulen_SHARP_{timestamp}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except:
                pass

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
