# app.py

import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

# --- Function: Extract transcript from uploaded .vtt file ---
def extract_transcript_from_vtt(uploaded_file):
    """
    Extract transcript text from a .vtt file uploaded in Streamlit
    """
    text = ""
    for line in uploaded_file:
        line = line.decode("utf-8").strip()
        if line and not line.startswith("WEBVTT") and "-->" not in line:
            text += line + " "
    return text.strip()

# --- Function: Save to Word file ---
def save_to_word(content, filename="Notulen_Rapat.docx"):
    doc = Document()

    # Title
    title = doc.add_paragraph("Notulen Rapat")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.runs[0]
    run.font.size = Pt(14)
    run.bold = True

    doc.add_paragraph(content)
    doc.save(filename)
    return filename

# --- Function: Generate notulen with Gemini ---
def generate_notulen_with_ai(sentences, api_key):
    """
    Generate formal meeting minutes using Google Gemini API
    Uses the strict notulen prompt
    """
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Use the latest recommended model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Strict prompt for formal notulen
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

        response = model.generate_content(prompt)

        if response and hasattr(response, "text") and response.text:
            return {
                'success': True,
                'content': response.text.strip(),
                'error': None
            }
        else:
            return {
                'success': False,
                'content': None,
                'error': "Empty response from Gemini model"
            }

    except Exception as e:
        return {
            'success': False,
            'content': None,
            'error': str(e)
        }

# --- Streamlit App ---
def main():
    st.set_page_config(page_title="AI Notulen Rapat", layout="wide")

    st.title("📝 Notulen Rapat Otomatis dengan Gemini AI")

    # Sidebar for file upload
    st.sidebar.header("Upload File")
    uploaded_file = st.sidebar.file_uploader("Upload file .vtt", type=["vtt"])

    # Tabs
    tab1, tab2 = st.tabs(["📄 Ringkasan Dasar", "🤖 Notulen AI (Gemini)"])

    if uploaded_file is not None:
        # Extract transcript
        transcript_text = extract_transcript_from_vtt(uploaded_file)

        with tab1:
            st.subheader("Hasil Ekstraksi Transkrip")
            st.text_area("Transkrip:", transcript_text, height=300)

        with tab2:
            st.subheader("Hasil Notulen AI (Gemini)")
            gemini_api_key = st.text_input(
                "Masukkan Google Gemini API Key",
                type="password",
                help="Dapatkan API key dari https://makersuite.google.com/app/apikey",
                placeholder="AIza..."
            )

            if gemini_api_key:
                if st.button("🔑 Generate Notulen"):
                    with st.spinner("Menghasilkan notulen rapat dengan Gemini..."):
                        ai_result = generate_notulen_with_ai(transcript_text, gemini_api_key)

                    if ai_result['success']:
                        st.success("✅ Notulen berhasil dibuat!")
                        st.markdown(ai_result['content'])

                        # Save to Word option
                        if st.download_button(
                            label="💾 Download Notulen (Word)",
                            data=save_to_word(ai_result['content']),
                            file_name="Notulen_Rapat.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        ):
                            st.info("File berhasil disimpan")

                    else:
                        st.error(f"❌ Terjadi kesalahan: {ai_result['error']}")

if __name__ == "__main__":
    main()
