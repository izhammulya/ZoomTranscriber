import streamlit as st
import re
from datetime import datetime
import io
import google.generativeai as genai
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

def process_vtt_text(vtt_text):
    cleaned_text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt_text)
    cleaned_text = re.sub(r"WEBVTT.*\n", "", cleaned_text)
    cleaned_text = "\n".join([line.strip() for line in cleaned_text.splitlines() if line.strip()])
    sentences = [s.strip() for s in cleaned_text.split(". ") if s.strip()]

    summary = [sentences[i] for i in range(0, len(sentences), 5) if i < len(sentences)]

    return {
        'summary': summary,
        'full_text': cleaned_text,
        'original_length': len(sentences),
        'summary_length': len(summary),
        'sentences': sentences
    }

def generate_notulen(summary):
    notulen = "📌 Notulen Rapat\n\n"
    notulen += "Ringkasan:\n" + "\n".join(f"- {s.strip()}" for s in summary if s.strip())
    return notulen

def generate_notulen_with_ai(sentences):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")

        prompt = f"""
Buatkan notulen rapat yang rapi dan formal dari transkrip rapat berikut:

{sentences}

FORMAT YANG DIHARAPKAN:

# Notulen Rapat
|Nama Rapat|[isi nama rapat]|
|---|---|
|Hari/Tanggal|[...]|
|Waktu|[...]|
|Tempat|[...]|
|Pemimpin Rapat|[...]|
|Dibuat oleh|Group Transformasi Korporasi dan Manajemen Program|

**Agenda:**
- [...]

**Peserta Rapat:**
|No||Nama/Jabatan|
|---|---|---|
|1|[...]|
|2|[...]|

|Poin Diskusi dan Arahan|Penanggung Jawab|
|---|---|
|[...]||

**Disclaimer:**
_Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final._
"""
        response = model.generate_content(prompt, generation_config={
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        })

        if response and response.text:
            cleaned_response = response.text.strip()
            if not cleaned_response.startswith("# Notulen Rapat"):
                lines = cleaned_response.split('\n')
                for i, line in enumerate(lines):
                    if "Notulen Rapat" in line:
                        cleaned_response = '\n'.join(lines[i:])
                        break
            return {'success': True, 'content': cleaned_response, 'error': None}
        else:
            return {'success': False, 'content': None, 'error': 'Empty response'}
    except Exception as e:
        return {'success': False, 'content': None, 'error': str(e)}

def create_word_document(content):
    try:
        doc = Document()
        title = doc.add_heading('Notulen Rapat', level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('|') and line.endswith('|'):
                table_data = []
                while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    row = [cell.strip() for cell in lines[i].split('|') if cell.strip()]
                    table_data.append(row)
                    i += 1
                if table_data:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for r, row_data in enumerate(table_data):
                        for c, cell_data in enumerate(row_data):
                            table.cell(r, c).text = cell_data
            elif line.startswith('**') and line.endswith('**'):
                doc.add_heading(line.replace('**', ''), level=2)
            elif line.startswith('- '):
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(line[2:])
            elif line.startswith('_') and line.endswith('_'):
                p = doc.add_paragraph()
                p.add_run(line[1:-1]).italic = True
            else:
                doc.add_paragraph(line)
            i += 1

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error creating Word document: {e}")
        return None

def main():
    st.set_page_config(page_title="Meeting Transcript Processor", page_icon="📝", layout="wide")

    st.markdown('<h1 style="text-align:center">📝 Meeting Transcript Processor</h1>', unsafe_allow_html=True)
    st.markdown("Upload Zoom transcript (.vtt) → ringkasan otomatis → notulen formal dengan AI")

    uploaded_file = st.file_uploader("Upload VTT Transcript", type=['vtt'])
    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8")
        result = process_vtt_text(content)
        notulen = generate_notulen(result['summary'])

        st.success("✅ Transcript processed successfully!")
        st.subheader("📋 Basic Summary")
        st.text_area("Basic Summary", value=notulen, height=250)

        if st.button("🚀 Generate Formal Meeting Minutes with AI"):
            with st.spinner("Generating AI Notulen..."):
                ai_result = generate_notulen_with_ai(result['full_text'])
                if ai_result['success']:
                    st.subheader("🤖 AI-Generated Notulen")
                    st.markdown(ai_result['content'], unsafe_allow_html=True)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button("📄 Download as TXT",
                        data=ai_result['content'],
                        file_name=f"Notulen_Rapat_{timestamp}.txt",
                        mime="text/plain"
                    )

                    word_buffer = create_word_document(ai_result['content'])
                    if word_buffer:
                        st.download_button("📄 Download as Word",
                            data=word_buffer.getvalue(),
                            file_name=f"Notulen_Rapat_{timestamp}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                else:
                    st.error(f"❌ Error: {ai_result['error']}")

if __name__ == "__main__":
    main()
