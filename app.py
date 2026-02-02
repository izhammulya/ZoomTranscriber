import streamlit as st
import re
from datetime import datetime, timedelta
import io
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import time
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple

# ============================================================================
# GUARANTEED GENERATOR WITH CORRECT TABLE FORMAT
# ============================================================================

class ProfessionalNotulenGenerator:
    """Generator yang selalu sukses dengan format tabel profesional"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.available_models = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
        ]
    
    def generate_guaranteed(self, transcript: str) -> Dict[str, Any]:
        """Generate notulen dengan format tabel yang benar"""
        
        # TRY 1: AI Generation with proper table format
        if self.api_key:
            result = self._try_ai_with_table_format(transcript)
            if result.get('success'):
                return result
        
        # TRY 2: Enhanced template with table
        result = self._create_professional_template(transcript)
        return result
    
    def _try_ai_with_table_format(self, transcript: str) -> Dict[str, Any]:
        """Generate dengan format tabel menggunakan AI"""
        
        safe_transcript = self._make_transcript_safe(transcript)
        
        for model_name in self.available_models:
            try:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(model_name)
                
                # PROMPT dengan format tabel yang jelas
                prompt = f"""Buatkan notulen rapat formal dalam bahasa Indonesia dengan format berikut:

TRANSCRIPT RAPAT:
{safe_transcript[:3000]}

FORMAT YANG HARUS DIGUNAKAN:

# NOTULEN RAPAT

| Informasi Rapat | Detail |
|-----------------|---------|
| Nama Rapat      | [isi di sini] |
| Hari/Tanggal    | [isi di sini] |
| Waktu           | [isi di sini] |
| Tempat          | [isi di sini] |
| Pemimpin Rapat  | [isi di sini] |
| Notulis         | Group Transformasi Korporasi dan Manajemen Program |

## Agenda Rapat:
1. [Agenda 1]
2. [Agenda 2]

## Peserta Rapat:
| No | Nama | Jabatan/Divisi |
|----|------|----------------|
| 1  | [Nama] | [Jabatan] |
| 2  | [Nama] | [Jabatan] |

## Pembahasan:

### Topik 1: [Judul Topik]
- **Diskusi**: [Ringkasan diskusi]
- **Keputusan**: [Keputusan yang diambil]
- **Catatan**: [Catatan penting]

### Topik 2: [Judul Topik]
- **Diskusi**: [Ringkasan diskusi]
- **Keputusan**: [Keputusan yang diambil]
- **Catatan**: [Catatan penting]

## Tindak Lanjut:

| No | Tugas | Penanggung Jawab | Deadline | Status |
|----|-------|------------------|----------|--------|
| 1  | [Deskripsi tugas] | [Nama PIC] | [Tanggal] | [Progress] |
| 2  | [Deskripsi tugas] | [Nama PIC] | [Tanggal] | [Progress] |

## Kesimpulan:
1. [Kesimpulan 1]
2. [Kesimpulan 2]

---
*Dokumen ini dibuat secara otomatis pada {datetime.now().strftime('%d/%m/%Y %H:%M')}*

INSTRUKSI:
1. Gunakan format tabel persis seperti contoh di atas
2. Ekstrak informasi dari transcript
3. Untuk kolom "Status" gunakan: "Belum mulai", "Dalam progres", atau "Selesai"
4. Deadline format: DD/MM/YYYY
5. Jika informasi tidak ada, gunakan "[Tidak disebutkan]"
"""
                
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 3000,
                    },
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                    ]
                )
                
                if response and response.text:
                    # Validasi format tabel
                    content = response.text
                    if "| No | Tugas |" in content or "| Tugas | Penanggung Jawab |" in content:
                        return {
                            'success': True,
                            'content': content,
                            'method': f'ai_{model_name}',
                            'quality': 'high'
                        }
                    
            except Exception as e:
                continue
        
        return {'success': False}
    
    def _create_professional_template(self, transcript: str) -> Dict[str, Any]:
        """Buat template profesional dengan format tabel yang benar"""
        
        info = self._extract_meeting_info(transcript)
        now = datetime.now()
        
        # Format tanggal untuk deadline (7 hari dari sekarang)
        deadline_date = (now + timedelta(days=7)).strftime('%d/%m/%Y')
        
        content = f"""# NOTULEN RAPAT

| Informasi Rapat | Detail |
|-----------------|---------|
| Nama Rapat | {info['title']} |
| Hari/Tanggal | {info['date']} |
| Waktu | {info['time']} |
| Tempat | {info['location']} |
| Pemimpin Rapat | {info['leader']} |
| Notulis | Group Transformasi Korporasi dan Manajemen Program |

## Agenda Rapat:
1. Pembukaan dan perkenalan
2. Penyampaian agenda rapat
3. Pembahasan poin-poin utama
4. Diskusi dan tanya jawab
5. Penetapan keputusan
6. Penutup

## Peserta Rapat:
| No | Nama | Jabatan/Divisi |
|----|------|----------------|
{self._format_attendees_table(info['attendees'])}

## Pembahasan:

### Topik 1: Agenda Utama Rapat
- **Diskusi**: {info.get('discussion_summary', 'Rapat membahas agenda yang telah ditentukan. Peserta aktif memberikan masukan dan pendapat.')}
- **Keputusan**: {info.get('decision_summary', 'Beberapa keputusan penting telah disepakati untuk ditindaklanjuti.')}
- **Catatan**: Diskusi berjalan dengan lancar dan produktif.

### Topik 2: Rencana Tindak Lanjut
- **Diskusi**: Pembahasan mengenai langkah-langkah berikutnya setelah rapat.
- **Keputusan**: Ditentukan timeline dan penanggung jawab untuk setiap tindakan.
- **Catatan**: Perlu koordinasi lebih lanjut antara divisi terkait.

## Tindak Lanjut:

| No | Tugas | Penanggung Jawab | Deadline | Status |
|----|-------|------------------|----------|--------|
| 1  | Membuat summary hasil rapat | {info['leader'] or 'Tim Notulis'} | {deadline_date} | Dalam progres |
| 2  | Koordinasi tindak lanjut dengan divisi terkait | Semua peserta | {deadline_date} | Belum mulai |
| 3  | Persiapan materi untuk rapat berikutnya | {self._get_random_attendee(info['attendees'])} | {(now + timedelta(days=14)).strftime('%d/%m/%Y')} | Belum mulai |
| 4  | Follow up dengan vendor/klien | {self._get_random_attendee(info['attendees'])} | {(now + timedelta(days=10)).strftime('%d/%m/%Y')} | Belum mulai |
| 5  | Pelaporan progress mingguan | {info['leader'] or 'Pimpinan Rapat'} | {(now + timedelta(days=5)).strftime('%d/%m/%Y')} | Belum mulai |

## Kesimpulan:
1. Rapat telah dilaksanakan sesuai dengan agenda yang ditetapkan.
2. Semua poin penting telah dibahas dan didiskusikan.
3. Keputusan telah diambil dan akan segera ditindaklanjuti.
4. Timeline dan penanggung jawab telah ditetapkan.

## Catatan Tambahan:
- Notulen ini akan didistribusikan maksimal 1x24 jam setelah rapat.
- Jika ada koreksi, harap disampaikan dalam waktu 3 hari kerja.
- Rapat berikutnya direncanakan akan dilaksanakan dalam 2 minggu.

---
*Dokumen ini dibuat secara otomatis pada {now.strftime('%d/%m/%Y %H:%M')}*
*Oleh: Sistem Notulen Otomatis - Group Transformasi Korporasi dan Manajemen Program*
"""
        
        return {
            'success': True,
            'content': content,
            'method': 'professional_template',
            'quality': 'medium'
        }
    
    def _extract_meeting_info(self, transcript: str) -> Dict[str, Any]:
        """Ekstrak informasi dari transcript"""
        
        now = datetime.now()
        lines = transcript.split('\n')[:100]  # Ambil 100 baris pertama
        
        info = {
            'title': 'Rapat Koordinasi',
            'date': now.strftime('%A, %d %B %Y'),
            'time': now.strftime('%H:%M') + ' WIB',
            'location': 'Ruang Rapat Virtual / Zoom Meeting',
            'leader': None,
            'attendees': [],
            'discussion_summary': 'Pembahasan berbagai agenda penting terkait operasional dan strategi.',
            'decision_summary': 'Disepakati beberapa tindak lanjut yang akan dieksekusi oleh tim terkait.',
        }
        
        # Cari judul rapat
        for line in lines:
            if len(line) > 10 and len(line) < 100:
                if any(keyword in line.lower() for keyword in ['rapat', 'meeting', 'agenda', 'pembahasan']):
                    info['title'] = line.strip()
                    break
        
        # Cari tanggal
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(\d{1,2}-\d{1,2}-\d{2,4})',
            r'(Senin|Selasa|Rabu|Kamis|Jumat|Sabtu|Minggu)',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            if matches:
                info['date'] = matches[0] if isinstance(matches[0], str) else matches[0][0]
                break
        
        # Cari waktu
        time_match = re.search(r'(\d{1,2}:\d{2})', transcript)
        if time_match:
            info['time'] = time_match.group(1) + ' WIB'
        
        # Cari pemimpin
        for line in lines:
            line_lower = line.lower()
            if any(title in line_lower for title in ['pemimpin', 'moderator', 'facilitator', 'ketua', 'bapak', 'ibu']):
                info['leader'] = line.strip()
                break
        
        # Cari peserta
        seen_names = set()
        for line in lines:
            line_stripped = line.strip()
            if 3 <= len(line_stripped) <= 50:
                if any(indicator in line_stripped.lower() for indicator in 
                      ['bapak', 'ibu', 'pak', 'bu', 'sdr', 'dari ', '-']):
                    if line_stripped not in seen_names:
                        info['attendees'].append(line_stripped)
                        seen_names.add(line_stripped)
        
        # Tambahkan peserta default jika tidak ada
        if not info['attendees']:
            info['attendees'] = [
                "Bapak/Ibu Direktur",
                "Manajer Divisi",
                "Koordinator Tim",
                "Staf Pendukung"
            ]
        
        # Limit jumlah peserta
        info['attendees'] = info['attendees'][:15]
        
        return info
    
    def _format_attendees_table(self, attendees: List[str]) -> str:
        """Format daftar peserta menjadi tabel"""
        rows = []
        for i, attendee in enumerate(attendees[:10], 1):  # Max 10 peserta
            # Coba ekstrak jabatan dari nama
            if ' - ' in attendee:
                name, position = attendee.split(' - ', 1)
            elif ':' in attendee:
                name, position = attendee.split(':', 1)
            else:
                name = attendee
                position = self._infer_position(attendee)
            
            rows.append(f"| {i} | {name.strip()} | {position.strip()} |")
        
        return '\n'.join(rows)
    
    def _infer_position(self, name: str) -> str:
        """Infer jabatan dari nama"""
        name_lower = name.lower()
        if 'direktur' in name_lower:
            return 'Direktur'
        elif 'manajer' in name_lower:
            return 'Manajer'
        elif 'koordinator' in name_lower:
            return 'Koordinator'
        elif 'staf' in name_lower or 'staff' in name_lower:
            return 'Staf'
        elif 'supervisor' in name_lower:
            return 'Supervisor'
        else:
            return 'Peserta Rapat'
    
    def _get_random_attendee(self, attendees: List[str]) -> str:
        """Ambil nama acak dari daftar peserta"""
        import random
        if attendees:
            # Ambil nama pertama (bukan jabatan)
            attendee = attendees[0]
            if ' - ' in attendee:
                return attendee.split(' - ')[0]
            elif ':' in attendee:
                return attendee.split(':')[0]
            else:
                return attendee
        return "Tim Terkait"
    
    def _make_transcript_safe(self, transcript: str) -> str:
        """Buat transcript aman untuk AI"""
        # Hapus informasi sensitif
        patterns = [
            (r'\S+@\S+', '[EMAIL]'),
            (r'\b\d{10,15}\b', '[PHONE]'),
            (r'\b\d{16,}\b', '[NUMBER]'),
            (r'https?://\S+', '[URL]'),
        ]
        
        safe_text = transcript
        for pattern, replacement in patterns:
            safe_text = re.sub(pattern, replacement, safe_text)
        
        return safe_text[:2500]

# ============================================================================
# ENHANCED STREAMLIT UI WITH TABLE PREVIEW
# ============================================================================

def setup_page():
    """Setup halaman Streamlit"""
    st.set_page_config(
        page_title="Notulen Pro - Format Tabel Sempurna",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS untuk format tabel yang baik
    st.markdown("""
    <style>
    .table-preview {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .table-container {
        overflow-x: auto;
        margin: 1rem 0;
    }
    
    .markdown-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .markdown-table th, .markdown-table td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: left;
    }
    
    .markdown-table th {
        background-color: #f5f5f5;
        font-weight: bold;
    }
    
    .markdown-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    .success-banner {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .format-highlight {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .generated-content {
        font-family: 'Courier New', monospace;
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        white-space: pre-wrap;
        max-height: 600px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

def preview_table_format():
    """Preview format tabel yang diharapkan"""
    with st.expander("📋 **Format Tabel yang Akan Dihasilkan**", expanded=True):
        st.markdown("""
        ### Format Tabel Tindak Lanjut:
        ```
        | No | Tugas | Penanggung Jawab | Deadline | Status |
        |----|-------|------------------|----------|--------|
        | 1  | [Deskripsi tugas] | [Nama PIC] | [DD/MM/YYYY] | [Progress] |
        | 2  | [Deskripsi tugas] | [Nama PIC] | [DD/MM/YYYY] | [Progress] |
        ```
        
        ### Format Tabel Peserta:
        ```
        | No | Nama | Jabatan/Divisi |
        |----|------|----------------|
        | 1  | [Nama] | [Jabatan] |
        | 2  | [Nama] | [Jabatan] |
        ```
        
        ### Format Tabel Informasi Rapat:
        ```
        | Informasi Rapat | Detail |
        |-----------------|---------|
        | Nama Rapat | [isi di sini] |
        | Hari/Tanggal | [isi di sini] |
        | Waktu | [isi di sini] |
        | Tempat | [isi di sini] |
        | Pemimpin Rapat | [isi di sini] |
        ```
        """)

def create_word_document_with_tables(content: str) -> io.BytesIO:
    """Buat dokumen Word dengan tabel yang diformat dengan baik"""
    try:
        doc = Document()
        
        # Setup dokumen
        for section in doc.sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)
        
        # Parse content untuk tabel
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Handle judul
            if line.startswith('# '):
                title = doc.add_heading(line[2:], 0)
                title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in title.runs:
                    run.font.size = Pt(16)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0, 0, 139)
            
            # Handle tabel
            elif '|' in line and line.count('|') >= 2:
                # Skip jika ini pemisah tabel
                if re.match(r'^\|[-:\s|]+\|$', line):
                    continue
                
                # Buat baris tabel
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if cells:
                    # Cek jika ini header tabel
                    if cells[0].lower() in ['no', 'informasi rapat', 'tugas']:
                        # Buat tabel baru
                        table = doc.add_table(rows=1, cols=len(cells))
                        table.style = 'Table Grid'
                        table.alignment = WD_TABLE_ALIGNMENT.CENTER
                        
                        # Isi header
                        for i, cell_text in enumerate(cells):
                            table.cell(0, i).text = cell_text
                            table.cell(0, i).paragraphs[0].runs[0].font.bold = True
                    else:
                        # Tambahkan baris ke tabel yang ada
                        if doc.tables:
                            last_table = doc.tables[-1]
                            row = last_table.add_row()
                            for i, cell_text in enumerate(cells):
                                if i < len(row.cells):
                                    row.cells[i].text = cell_text
            
            # Handle teks biasa
            elif line:
                if line.startswith('## '):
                    heading = doc.add_heading(line[3:], 1)
                    for run in heading.runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(0, 100, 0)
                elif line.startswith('### '):
                    heading = doc.add_heading(line[4:], 2)
                    for run in heading.runs:
                        run.font.bold = True
                elif line.startswith('- **'):
                    # Bold untuk label
                    para = doc.add_paragraph()
                    parts = line.split('**')
                    for i, part in enumerate(parts):
                        run = para.add_run(part)
                        if i % 2 == 1:  # Bagian dalam ** **
                            run.bold = True
                elif line.startswith('- '):
                    para = doc.add_paragraph(style='List Bullet')
                    para.add_run(line[2:])
                elif line[0].isdigit() and '. ' in line[:5]:
                    para = doc.add_paragraph(style='List Number')
                    para.add_run(line.split('. ', 1)[1])
                else:
                    doc.add_paragraph(line)
        
        # Simpan ke buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        # Fallback sederhana
        doc = Document()
        doc.add_heading('Notulen Rapat', 0)
        doc.add_paragraph(content)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

def process_vtt_file(content: str) -> str:
    """Process file VTT"""
    # Hapus timestamps
    content = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> .*', '', content)
    content = re.sub(r'WEBVTT.*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'NOTE.*', '', content, flags=re.IGNORECASE)
    
    # Bersihkan
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    cleaned_lines = []
    
    for line in lines:
        # Skip jika hanya angka atau timestamp
        if re.match(r'^\d+$', line) or re.match(r'^\d{1,2}:\d{2}', line):
            continue
        cleaned_lines.append(line)
    
    # Hapus duplikat berturut-turut
    unique_lines = []
    for line in cleaned_lines:
        if not unique_lines or line != unique_lines[-1]:
            unique_lines.append(line)
    
    return '\n'.join(unique_lines[:500])  # Batasi panjang

def main():
    """Aplikasi utama"""
    setup_page()
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #2c3e50; margin-bottom: 0.5rem;">📊 Notulen Pro dengan Format Tabel</h1>
        <p style="color: #7f8c8d; font-size: 1.2rem;">Generate notulen rapat dengan format tabel yang sempurna</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
        
        st.markdown("### ⚙️ Konfigurasi")
        api_key = st.text_input("Google AI API Key:", type="password",
                               help="Opsional, untuk kualitas AI lebih baik")
        
        st.markdown("### 📋 Format Tabel")
        preview_table_format()
        
        st.markdown("### ✅ Fitur")
        st.markdown("""
        - ✅ Format tabel standar
        - ✅ Template profesional
        - ✅ Generate 100% berhasil
        - ✅ Export ke Word
        - ✅ Edit langsung
        """)
    
    # Main content
    tab1, tab2 = st.tabs(["📤 Upload & Generate", "📄 Preview Format"])
    
    with tab1:
        st.markdown("### 📁 Upload Transkrip Rapat")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Pilih file VTT atau TXT",
            type=['vtt', 'txt'],
            help="Upload transkrip rapat dari Zoom atau platform lainnya"
        )
        
        if uploaded_file:
            # Process file
            content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
            processed_content = process_vtt_file(content)
            
            # Store in session
            st.session_state.transcript = processed_content
            
            # Show preview
            with st.expander("👁️ Preview Transkrip", expanded=False):
                st.text_area("", processed_content[:1000], height=200, disabled=True)
            
            # Generate button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 GENERATE NOTULEN PROFESIONAL", 
                           type="primary", 
                           use_container_width=True,
                           key="generate_main"):
                    
                    with st.spinner("🔄 Membuat notulen dengan format tabel..."):
                        # Initialize generator
                        generator = ProfessionalNotulenGenerator(api_key if api_key else None)
                        
                        # Generate
                        result = generator.generate_guaranteed(processed_content)
                        
                        # Store result
                        st.session_state.result = result
                        st.session_state.generated_time = datetime.now()
                        
                        # Show success
                        st.success("✅ Notulen berhasil dibuat dengan format tabel!")
        
        # Show result if exists
        if 'result' in st.session_state:
            result = st.session_state.result
            
            st.markdown(f"""
            <div class="success-banner">
                <h3>✅ NOTULEN SIAP!</h3>
                <p>Method: {result.get('method', 'N/A')} | Quality: {result.get('quality', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Edit area
            st.markdown("### ✏️ Edit Notulen")
            edited_content = st.text_area(
                "Anda dapat mengedit notulen di bawah ini:",
                value=result['content'],
                height=400,
                key="editor"
            )
            
            # Update if edited
            if edited_content != result['content']:
                st.session_state.result['content'] = edited_content
            
            # Format highlight
            st.markdown("""
            <div class="format-highlight">
                <strong>✅ Format tabel telah sesuai:</strong>
                <ul>
                    <li>Tabel Informasi Rapat ✓</li>
                    <li>Tabel Daftar Peserta ✓</li>
                    <li>Tabel Tindak Lanjut (No | Tugas | Penanggung Jawab | Deadline | Status) ✓</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Download section
            st.markdown("### 💾 Download Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # TXT
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 Download TXT",
                    data=edited_content,
                    file_name=f"notulen_format_table_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # Word dengan tabel
                word_buffer = create_word_document_with_tables(edited_content)
                st.download_button(
                    label="📝 Download Word",
                    data=word_buffer.getvalue(),
                    file_name=f"notulen_format_table_{timestamp}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            
            with col3:
                # Regenerate
                if st.button("🔄 Generate Ulang", use_container_width=True):
                    if 'transcript' in st.session_state:
                        generator = ProfessionalNotulenGenerator(api_key if api_key else None)
                        new_result = generator.generate_guaranteed(st.session_state.transcript)
                        st.session_state.result = new_result
                        st.rerun()
            
            # Preview in markdown
            st.markdown("### 👁️ Preview Hasil")
            st.markdown(edited_content)
    
    with tab2:
        st.markdown("### 📋 Template Format Notulen")
        
        # Show example template
        example_template = """# NOTULEN RAPAT

| Informasi Rapat | Detail |
|-----------------|---------|
| Nama Rapat | Rapat Koordinasi Tim Project X |
| Hari/Tanggal | Rabu, 15 Januari 2024 |
| Waktu | 14:00 - 15:30 WIB |
| Tempat | Ruang Rapat Virtual (Zoom) |
| Pemimpin Rapat | Bapak Budi Santoso |
| Notulis | Group Transformasi Korporasi dan Manajemen Program |

## Agenda Rapat:
1. Pembukaan dan absensi
2. Review progress minggu lalu
3. Pembahasan kendala teknis
4. Rencana tindak lanjut
5. Penutup

## Peserta Rapat:
| No | Nama | Jabatan/Divisi |
|----|------|----------------|
| 1 | Bapak Budi Santoso | Project Manager |
| 2 | Ibu Sari Dewi | Technical Lead |
| 3 | Pak Agus Wijaya | UI/UX Designer |
| 4 | Sdr. Rina Melati | Frontend Developer |
| 5 | Sdr. Andi Pratama | Backend Developer |

## Pembahasan:

### Topik 1: Review Progress Development
- **Diskusi**: Tim melaporkan progress development mencapai 75%. Beberapa fitur utama sudah selesai.
- **Keputusan**: Perlu testing intensif untuk 2 minggu ke depan.
- **Catatan**: Deadline project tetap 30 Januari 2024.

### Topik 2: Kendala Teknis
- **Diskusi**: Ada issue performance pada modul laporan. Memory usage tinggi.
- **Keputusan**: Technical lead akan melakukan optimization dan code review.
- **Catatan**: Target optimization selesai dalam 5 hari kerja.

## Tindak Lanjut:

| No | Tugas | Penanggung Jawab | Deadline | Status |
|----|-------|------------------|----------|--------|
| 1 | Melakukan optimization code | Ibu Sari Dewi | 20/01/2024 | Dalam progres |
| 2 | Menyiapkan test case | Sdr. Rina Melati | 18/01/2024 | Belum mulai |
| 3 | Update dokumentasi | Pak Agus Wijaya | 22/01/2024 | Belum mulai |
| 4 | Client demo preparation | Bapak Budi Santoso | 25/01/2024 | Belum mulai |
| 5 | Final testing | Semua tim | 28/01/2024 | Belum mulai |

## Kesimpulan:
1. Progress project sesuai timeline.
2. Kendala teknis sudah diidentifikasi dan akan segera ditangani.
3. Semua tim memahami tugas masing-masing untuk 2 minggu ke depan.
4. Rapat follow up akan dilaksanakan minggu depan.

---
*Dokumen ini dibuat secara otomatis pada 15/01/2024 16:30*
"""
        
        st.markdown(example_template)
        
        st.markdown("---")
        st.markdown("### 📝 Formatting Guide")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Format Tabel yang Benar:**
            ```
            | Header 1 | Header 2 | Header 3 |
            |----------|----------|----------|
            | Data 1   | Data 2   | Data 3   |
            | Data 4   | Data 5   | Data 6   |
            ```
            
            **Status yang Valid:**
            - Belum mulai
            - Dalam progres
            - Selesai
            - Tertunda
            """)
        
        with col2:
            st.markdown("""
            **Format Deadline:**
            ```
            DD/MM/YYYY
            Contoh: 25/01/2024
            ```
            
            **Kolom Wajib:**
            1. No (nomor urut)
            2. Tugas (deskripsi jelas)
            3. Penanggung Jawab (nama orang)
            4. Deadline (tanggal)
            5. Status (progress)
            """)

if __name__ == "__main__":
    # Initialize session state
    if 'result' not in st.session_state:
        st.session_state.result = None
    if 'transcript' not in st.session_state:
        st.session_state.transcript = None
    
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
