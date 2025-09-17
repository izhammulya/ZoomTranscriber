# app.py

import streamlit as st
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
import google.generativeai as genai

# Function to generate Notulen Rapat with Gemini
def generate_notulen_with_ai(sentences):
    try:
        # Read API key from secrets.toml
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)

        # Use Gemini model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Prompt with strict format
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
        return response.text

    except Exception as e:
        return f"⚠️ Terjadi error: {str(e)}"


# Function to export notulen to Word
def export_to_word(notulen_text):
    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    # Add content
    for line in notulen_text.split("\n"):
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("**") and line.endswith("**"):
            doc.add_heading(line.replace("**", ""), level=2)
        elif line.strip().startswith("|"):
            # Handle tables
            rows = []
            for row in line.split("\n"):
                if row.strip():
                    rows.append([cell.strip() for cell in row.split("|") if cell.strip()])
            if rows:
                table = doc.add_table(rows=len(rows), cols=len(rows[0]))
                table.style = "Table Grid"
                for i, row in enumerate(rows):
                    for j, cell in enumerate(row):
                        table.cell(i, j).text = cell
        else:
            paragraph = doc.add_paragraph(line)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Save file
    output_path = "Notulen_Rapat.docx"
    doc.save(output_path)
    return output_path


# Streamlit app
def main():
    st.title("📝 Generator Notulen Rapat Otomatis")
    st.write("Upload transkrip atau masukkan teks, aplikasi akan membuat notulen formal secara otomatis.")

    # Pilihan input
    option = st.radio("Pilih cara input:", ("📄 Upload File", "⌨️ Tulis Manual"))

    sentences = ""

    if option == "📄 Upload File":
        uploaded_file = st.file_uploader("Upload file transkrip (txt/docx)", type=["txt", "docx"])
        if uploaded_file is not None:
            if uploaded_file.type == "text/plain":
                sentences = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = Document(uploaded_file)
                sentences = "\n".join([para.text for para in doc.paragraphs])
            st.success("✅ Transkrip berhasil dibaca!")

    elif option == "⌨️ Tulis Manual":
        sentences = st.text_area("Masukkan transkrip rapat di sini:", height=300)

    # Tombol generate
    if st.button("Generate Notulen"):
        if sentences.strip():
            with st.spinner("Sedang membuat notulen..."):
                notulen = generate_notulen_with_ai(sentences)

            st.subheader("📄 Hasil Notulen:")
            st.markdown(notulen)

            # Export option
            file_path = export_to_word(notulen)
            with open(file_path, "rb") as f:
                st.download_button("📥 Download Notulen (Word)", f, file_name="Notulen_Rapat.docx")

        else:
            st.warning("⚠️ Mohon masukkan atau upload transkrip rapat terlebih dahulu.")


if __name__ == "__main__":
    main()
