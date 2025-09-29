import streamlit as st
import re
from datetime import datetime
import io
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import parse_xml


def process_vtt_text(vtt_text):
    """
    Process VTT text to clean timestamps and metadata
    """
    cleaned_text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt_text)
    cleaned_text = re.sub(r"WEBVTT.*\n", "", cleaned_text)
    cleaned_text = "\n".join([line.strip() for line in cleaned_text.splitlines() if line.strip()])
    return cleaned_text


def generate_notulen_with_ai(sentences, api_key):
    """
    Generate formal meeting minutes using Google Gemini API
    """
    try:
        # Initialize Gemini with API Key
        genai.configure(api_key=api_key)

        # Use the same model you specified
        model = genai.GenerativeModel("models/gemini-2.5-flash")

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

        # Generation config
        generation_config = {
            "temperature": 0.5,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        # Generate
        response = model.generate_content(prompt, generation_config=generation_config)

        if response and response.text:
            cleaned_response = response.text.strip()
            if not cleaned_response.startswith("# Notulen Rapat"):
                lines = cleaned_response.split('\n')
                for i, line in enumerate(lines):
                    if "Notulen Rapat" in line:
                        cleaned_response = '\n'.join(lines[i:])
                        break

            return {"success": True, "content": cleaned_response, "error": None}
        else:
            return {"success": False, "content": None, "error": "Empty response from model"}

    except Exception as e:
        return {"success": False, "content": None, "error": str(e)}


def create_word_document(content, filename):
    """
    Create a Word document from the generated content following the template
    """
    try:
        doc = Document()

        # Set margins
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # Add title
        title = doc.add_heading('Notulen Rapat', level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].font.size = Pt(16)
        title.runs[0].font.bold = True

        # Parse the AI output
        lines = content.split('\n')
        agenda_items, participants, discussion_points = [], [], []
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith('- ') and 'Agenda:' not in line:
                agenda_items.append(line[2:])
            elif line.startswith('|') and '|' in line and any(char.isdigit() for char in line.split('|')[1]):
                parts = line.split('|')
                if len(parts) >= 4 and parts[1].strip().isdigit():
                    participants.append((parts[1].strip(), parts[3].strip()))
            elif line.startswith('|Poin Diskusi dan Arahan|'):
                current_section = 'discussion'
            elif current_section == 'discussion' and line.startswith('|'):
                parts = line.split('|')
                if len(parts) >= 3:
                    if not parts[1].startswith('Kesimpulan') and parts[1].strip():
                        discussion_points.append({
                            'topic': parts[1].strip(),
                            'responsible': parts[2].strip() if len(parts) > 2 else ''
                        })
                    elif 'Kesimpulan' in parts[1]:
                        if discussion_points:
                            discussion_points[-1]['conclusion'] = parts[2].strip() if len(parts) > 2 else ''

        # Meeting Info Table
        info_table = doc.add_table(rows=6, cols=2)
        info_table.style = 'Table Grid'
        info_table.cell(0, 0).text = "Nama Rapat"
        info_table.cell(1, 0).text = "Hari/Tanggal"
        info_table.cell(2, 0).text = "Waktu"
        info_table.cell(3, 0).text = "Tempat"
        info_table.cell(4, 0).text = "Pemimpin Rapat"
        info_table.cell(5, 0).text = "Dibuat oleh"
        info_table.cell(5, 1).text = "Group Transformasi Korporasi dan Manajemen Program"

        # Agenda
        doc.add_paragraph()
        doc.add_heading('Agenda:', level=2)
        for item in agenda_items:
            p = doc.add_paragraph(item, style='List Bullet')
            for run in p.runs:
                run.font.size = Pt(10)

        # Participants
        doc.add_paragraph()
        doc.add_heading('Peserta Rapat:', level=2)
        if participants:
            part_table = doc.add_table(rows=len(participants) + 1, cols=3)
            part_table.style = 'Table Grid'
            part_table.cell(0, 0).text = "No"
            part_table.cell(0, 1).text = ""
            part_table.cell(0, 2).text = "Nama/Jabatan"
            for i, (num, participant) in enumerate(participants, 1):
                part_table.cell(i, 0).text = num
                part_table.cell(i, 2).text = participant

        # Discussion
        doc.add_paragraph()
        doc.add_heading('Poin Diskusi dan Arahan:', level=2)
        if discussion_points:
            disc_table = doc.add_table(rows=0, cols=2)
            disc_table.style = 'Table Grid'
            for point in discussion_points:
                row = disc_table.add_row().cells
                row[0].text = point['topic']
                row[1].text = point['responsible']
                if 'conclusion' in point:
                    row = disc_table.add_row().cells
                    row[0].text = "Kesimpulan :\n• " + point['conclusion']
                    row[1].text = point['responsible']

        # Disclaimer
        doc.add_paragraph()
        disclaimer = doc.add_paragraph()
        disclaimer.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        disclaimer_run = disclaimer.add_run("Disclaimer:\n")
        disclaimer_run.italic = True
        disclaimer_run.font.size = Pt(10)
        disclaimer.add_run(
            "Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final."
        ).italic = True

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

    # Header
    st.markdown('<h1 style="text-align:center;">📝 Notulen Zoom Meeting Generator by TKMP</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#666;">Generate Notulen dengan praktis no ribet</p>', unsafe_allow_html=True)

    # Get API key
    try:
        api_key = st.secrets["api_key"]
        api_key_available = True
    except Exception:
        api_key, api_key_available = None, False

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        if api_key_available:
            st.success("✅ API Key loaded successfully")
        else:
            st.error("❌ API Key not found")

    # Upload
    uploaded_file = st.file_uploader("📁 Upload Transkrip Zoom (.vtt only)", type=['vtt'])
    if uploaded_file is not None:
        if st.button("🚀 Generate Notulen", type="primary"):
            if not api_key_available:
                st.error("Please configure your API key in secrets.toml first")
                return
            with st.spinner("🤖 AI is processing your transcript..."):
                content = uploaded_file.getvalue().decode("utf-8")
                cleaned_text = process_vtt_text(content)
                ai_result = generate_notulen_with_ai(cleaned_text, api_key)
                if ai_result['success']:
                    st.session_state.ai_notulen = ai_result['content']
                    st.success("✅ Generate Notulen berhasil!")
                else:
                    st.error(f"❌ Error: {ai_result['error']}")

    if 'ai_notulen' in st.session_state:
        st.divider()
        st.markdown("### 📋 Generated Notulen")
        st.markdown(st.session_state.ai_notulen, unsafe_allow_html=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        word_buffer = create_word_document(st.session_state.ai_notulen, f"Notulen_{timestamp}.docx")
        if word_buffer:
            st.download_button(
                label="📝 Download Word Document",
                data=word_buffer.getvalue(),
                file_name=f"Notulen_meeting_{timestamp}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )


if __name__ == "__main__":
    main()
