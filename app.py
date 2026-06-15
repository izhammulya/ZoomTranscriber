import streamlit as st
import re
import time
import io
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ==============================================================================
# SECTION 1: DATA PROCESSING & EXPORT TOOLS
# ==============================================================================

def process_vtt_text(vtt_text):
    cleaned = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*\n?", "", vtt_text)
    cleaned = re.sub(r"WEBVTT.*\n?", "", cleaned)
    return "\n".join([line.strip() for line in cleaned.splitlines() if line.strip()])

def create_word_document(content):
    doc = Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(1)
    
    title = doc.add_heading('Notulen Rapat', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

    lines = content.split('\n')
    in_table = False
    table_data = []

    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith('|') and line_strip.endswith('|'):
            if not in_table:
                in_table = True
                table_data = []
            if re.match(r'^\|[-\s|]+\|$', line_strip):
                continue
            cells = [cell.strip() for cell in line_strip.strip('|').split('|')]
            table_data.append(cells)
        else:
            if in_table:
                table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                table.style = 'Table Grid'
                for i, row in enumerate(table_data):
                    for j in range(min(len(table_data[0]), len(row))):
                        table.cell(i, j).text = row[j]
                in_table = False
                table_data = []
                doc.add_paragraph()

            if line_strip.startswith('# ') and line_strip != "# Notulen Rapat":
                doc.add_heading(line_strip[2:], level=1)
            elif line_strip.startswith('## '):
                doc.add_heading(line_strip[3:], level=2)
            elif line_strip.startswith('- ') or line_strip.startswith('* '):
                doc.add_paragraph(line_strip[2:], style='List Bullet')
            elif line_strip and line_strip != "# Notulen Rapat": 
                p = doc.add_paragraph()
                parts = re.split(r'(\*\*.*?\*\*)', line_strip)
                for part in parts:
                    if part.startswith('**') and part.endswith('**'):
                        p.add_run(part[2:-2]).bold = True
                    else:
                        p.add_run(part)

    if in_table:
        table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
        table.style = 'Table Grid'
        for i, row in enumerate(table_data):
            for j in range(min(len(table_data[0]), len(row))):
                table.cell(i, j).text = row[j]

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==============================================================================
# SECTION 2: AI CORE ENGINE (SMART FALLBACK)
# ==============================================================================

def generate_with_fallback(prompt_text, api_key):
    genai.configure(api_key=api_key)
    
    # Prefix "models/" wajib ada pada SDK Python
    FALLBACK_MODELS = [
       "models/gemini-3.5-flash",       
        "models/gemini-3.1-flash-lite",  
        "models/gemini-2.5-flash",       
        "models/gemini-2.5-pro",         
        "models/gemini-2.5-flash-lite"
    ]
    
    generation_config = {"temperature": 0.1, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192}
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
    
    last_error = None
    for i, model_name in enumerate(FALLBACK_MODELS):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt_text, 
                generation_config=generation_config, 
                safety_settings=safety_settings
            )
            
            # Deteksi output terpotong
            if response.candidates and response.candidates[0].finish_reason.name == 'MAX_TOKENS':
                raise Exception("MAX_TOKENS_REACHED")
                
            if response.text:
                return {"success": True, "content": response.text}
                
        except Exception as e:
            last_error = str(e)
            err_str = last_error.lower()
            
            if i < len(FALLBACK_MODELS) - 1:
                if '429' in err_str or 'quota' in err_str or 'exhausted' in err_str:
                    time.sleep(2.5) # Delay 2.5 detik sesuai logika awal
                elif '404' in err_str or 'not found' in err_str:
                    pass # Langsung lompat jika model tidak tersedia
                elif 'max_tokens' in err_str:
                    pass # Lompat ke model dengan kapasitas lebih besar
    
    return {"success": False, "error": f"Semua model gagal merespon. Error: {last_error}"}

# ==============================================================================
# SECTION 3: STREAMLIT UI (MNEV INTELLIGENCE)
# ==============================================================================

st.set_page_config(page_title="MNEV Intelligence | Notulen Generator", page_icon="📝", layout="wide")

# Custom CSS mereplikasi Tailwind UI
st.markdown("""
<style>
    .stApp { background-color: #faf9f6; font-family: 'Inter', sans-serif; color: #292524; }
    
    /* Header Custom */
    .mnev-header {
        background: white; border-bottom: 1px solid #e5e7eb; padding: 1rem 2rem;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .mnev-logo-box { background: #292524; color: white; padding: 0.5rem 0.75rem; border-radius: 4px; font-weight: bold; font-size: 0.875rem; letter-spacing: 0.1em; }
    .mnev-title { font-family: 'Lora', serif; font-weight: bold; font-size: 1.25rem; color: #292524; margin: 0; display: flex; align-items: center; gap: 8px;}
    .mnev-subtitle { font-size: 0.7rem; color: #78716c; margin: 0; letter-spacing: 0.05em; font-weight: 500;}
    .mnev-badge { background: #f5f5f4; border: 1px solid #e7e5e4; padding: 2px 6px; border-radius: 4px; font-size: 0.6rem; color: #57534e; font-family: sans-serif;}
    
    /* Tombol Khusus MNEV (#596248) */
    div.stButton > button:first-child {
        background-color: #596248; color: white; width: 100%; border-radius: 8px; border: none; font-weight: 500; padding: 0.75rem; transition: all 0.2s;
    }
    div.stButton > button:first-child:hover { background-color: #4a523b; }
    
    /* Container Box */
    .custom-box { background: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 2px 10px -3px rgba(0,0,0,0.05); border: 1px solid #e7e5e4; }
</style>

<div class="mnev-header">
    <div style="display: flex; align-items: center; gap: 1rem;">
        <div class="mnev-logo-box">MNEV</div>
        <div>
            <h1 class="mnev-title">MNEV Intelligence <span class="mnev-badge">V2.0</span></h1>
            <p class="mnev-subtitle">Notulen Generator & Repair • Group Monitoring dan Evaluasi Strategi Perusahaan</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# State Management
if "transcript_text" not in st.session_state: st.session_state.transcript_text = ""
if "ai_notulen" not in st.session_state: st.session_state.ai_notulen = ""
if "ai_repaired" not in st.session_state: st.session_state.ai_repaired = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []

try:
    api_key = st.secrets["api_key"]
except:
    api_key = None

# Tata Letak Grid (1/3 Kiri, 2/3 Kanan)
col_left, col_right = st.columns([4, 8], gap="large")

with col_left:
    st.markdown('<div class="custom-box">', unsafe_allow_html=True)
    st.markdown("### 📄 Data Transkrip Mentah")
    st.caption("Gunakan salah satu atau gabungkan keduanya.")
    
    if not api_key:
        st.error("API Key belum dikonfigurasi di st.secrets.")
        
    uploaded_file = st.file_uploader("Pilih Berkas Rapat (.VTT / .TXT)", type=['vtt', 'txt'])
    
    st.markdown("<center><span style='font-size:0.7rem; color:#a8a29e; font-weight:bold; letter-spacing:0.1em;'>DAN / ATAU</span></center>", unsafe_allow_html=True)
    
    manual_input = st.text_area("Tempel transkrip manual:", height=150, placeholder="Teks yang diketik di sini akan otomatis digabungkan dengan file unggahan (jika ada).")
    
    if st.button("Generate Notulen Otomatis"):
        if not uploaded_file and not manual_input.strip():
            st.warning("Silakan unggah file VTT atau paste teks transkrip manual.")
        elif not api_key:
            st.error("Masukkan API Key terlebih dahulu.")
        else:
            combined_transcript = ""
            if uploaded_file:
                raw_text = uploaded_file.getvalue().decode("utf-8")
                combined_transcript += "SUMBER 1 (TRANSKRIP OTOMATIS):\n" + process_vtt_text(raw_text) + "\n\n"
            if manual_input.strip():
                combined_transcript += "SUMBER 2 (CATATAN MANUAL):\n" + manual_input.strip() + "\n\n"
                
            st.session_state.transcript_text = combined_transcript
            
            prompt = f"""**INI ADALAH DATA RAPAT FORMAL PERUSAHAAN PELINDO. BUATKAN NOTULEN RAPAT DENGAN BAHASA INDONESIA YANG SANGAT FORMAL, BAKU, DAN PROFESIONAL. HANYA FOKUS PADA AGENDA, DISKUSI, DAN KEPUTUSAN SAJA.**

Anda akan menerima data transkrip/catatan rapat yang merupakan GABUNGAN dari beberapa sumber (contoh: gabungan file transkrip otomatis VTT Zoom dan catatan teks manual). Analisis dan sintesis seluruh teks gabungan tersebut sebagai satu kesatuan alur rapat yang utuh.

Buatkan notulen rapat yang rapi dan komprehensif dari data rapat berikut:

{combined_transcript}

FORMAT YANG DIHARAPKAN (Gunakan format Tabel Markdown persis seperti ini):

# Notulen Rapat

| Judul | Keterangan |
|---|---|
| Nama Rapat | [Ekstrak/Isi nama rapat] |
| Hari/Tanggal | [Ekstrak hari, tanggal] |
| Waktu | [Ekstrak waktu rapat] |
| Tempat | [Ekstrak lokasi/metode rapat] |
| Pemimpin Rapat | [Ekstrak jabatan pemimpin rapat] |
| Dibuat oleh | Group Monitoring Evaluasi Strategi Perusahaan dan Inovasi |

**Agenda:**
- [Daftar agenda rapat secara lengkap]

**Peserta Rapat:**
| No | Nama/Jabatan |
|---|---|
| 1 | [Nama peserta 1 / Jabatan] |

**Poin Diskusi dan Arahan:**
| Pembahasan / Topik | Penanggung Jawab |
|---|---|
| **[Topik Pembahasan 1 di sini]** | |
| **Poin Diskusi:** | |
| [Jabatan/Nama] menyampaikan:<br>• [Poin penyampaian 1 yang deskriptif, menjaga konteks teknis/strategis, dan menggunakan bahasa korporat formal]<br>• [Poin penyampaian 2 yang utuh dan tidak menghilangkan makna asli] | |
| [Jabatan/Nama lain] menyampaikan/menyoroti:<br>• [Poin elaborasi yang komprehensif] | |
| **Kesimpulan :** | |
| [Jabatan/Nama] memberikan arahan sebagai berikut:<br>• [Poin kesimpulan yang jelas, tegas, dan dapat ditindaklanjuti] | [Jabatan Penanggung Jawab] |

**Disclaimer:**
_Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final._

INSTRUKSI KHUSUS DAN KETAT:
1. Identifikasi Pembicara: Wajib mengekstrak siapa yang berbicara. Gunakan Jabatan (jika disebutkan/diketahui) atau nama peserta.
2. Kedalaman Makna (SANGAT PENTING): JANGAN meringkas poin diskusi terlalu ekstrem. Pertahankan substansi, detail teknis, metrik/angka, dan konteks strategis dari pembicaraan asli. Setiap bullet point (•) harus berupa kalimat atau frasa yang utuh.
3. Gaya Bahasa Profesional: Ubah bahasa lisan, slang, atau catatan kasar menjadi bahasa dokumen korporat tingkat tinggi. Gunakan kata kerja aktif/pasif yang formal (misal: "menyoroti pentingnya...", "mengusulkan skema...", "menjabarkan kendala...", "menginstruksikan agar...").
4. Struktur Diskusi & Kesimpulan: Patuhi hierarki tabel: Topik -> "Poin Diskusi:" -> Siapa menyampaikan apa -> "Kesimpulan :" -> Arahan dan Penanggung Jawab di kolom kanan.
5. Penggabungan Konteks: Gabungkan konteks dari berbagai sumber agar kronologi nyambung secara logis tanpa duplikasi informasi."""

            with st.spinner("🤖 Menganalisis dan menyatukan data..."):
                res = generate_with_fallback(prompt, api_key)
                if res['success']:
                    st.session_state.ai_notulen = res['content']
                else:
                    st.error(res['error'])
    st.markdown('</div>', unsafe_allow_html=True)


with col_right:
    tab1, tab2, tab3 = st.tabs(["📝 Hasil AI Notulen", "💬 Tanya Jawab", "🛠️ Repair Notulen (Standarisasi)"])
    
    with tab1:
        if st.session_state.ai_notulen:
            # Tombol Download
            c1, c2, c3 = st.columns([2, 2, 6])
            with c1:
                word_buffer = create_word_document(st.session_state.ai_notulen)
                st.download_button("📄 Unduh Word (.docx)", word_buffer.getvalue(), "Notulen_Rapat.docx", use_container_width=True)
            with c2:
                st.download_button("📝 Unduh TXT", st.session_state.ai_notulen, "Notulen_Rapat.txt", use_container_width=True)
            
            st.divider()
            with st.container(border=True):
                st.markdown(st.session_state.ai_notulen)
        else:
            st.info("Belum Ada Data Transkrip. Hasil AI Notulen akan muncul di sini.")

    with tab2:
        if not st.session_state.transcript_text:
            st.warning("Silakan generate notulen terlebih dahulu agar AI memiliki konteks transkrip.")
        else:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            if u_input := st.chat_input("Tanyakan spesifik terkait transkrip..."):
                st.session_state.chat_history.append({"role": "user", "content": u_input})
                with st.chat_message("user"):
                    st.markdown(u_input)
                
                with st.chat_message("assistant"):
                    with st.spinner("Mengetik..."):
                        context = f"TRANSKRIP REFERENSI:\n{st.session_state.transcript_text}\n\nPERTANYAAN: {u_input}\n\nINSTRUKSI: Jawablah hanya berdasarkan transkrip di atas dengan bahasa Indonesia formal."
                        chat_res = generate_with_fallback(context, api_key)
                        if chat_res['success']:
                            st.markdown(chat_res['content'])
                            st.session_state.chat_history.append({"role": "assistant", "content": chat_res['content']})
                        else:
                            st.error(chat_res['error'])

    with tab3:
        st.markdown("### Standarisasi Draf Kasar")
        raw_notes = st.text_area("Tempel catatan rapat yang berantakan, tulisan dari WhatsApp, atau draf kasar di sini... AI akan merapikannya sesuai format pelindo.", height=150)
        
        if st.button("Reparasi & Format ke Tabel", key="btn_repair"):
            if not raw_notes.strip():
                st.warning("Silakan tempel draf kasar terlebih dahulu.")
            elif not api_key:
                st.error("API Key missing.")
            else:
                prompt_repair = f"""Anda adalah asisten AI profesional untuk Pelindo. Tugas Anda adalah mereparasi draf rapat yang acak-acakan menjadi bahasa Indonesia yang sangat formal, baku, dan kaya akan konteks profesional.

        DRAF KASAR:
        \"\"\"
        {raw_notes}
        \"\"\"

        FORMAT WAJIB YANG HARUS DIGUNAKAN (Gunakan Tabel Markdown):
        # Notulen Rapat
        | Judul | Keterangan |
        |---|---|
        | Nama Rapat | [Ekstrak/Buat nama rapat] |
        | Hari/Tanggal | [Ekstrak tanggal] |
        | Waktu | [Ekstrak waktu] |
        | Tempat | [Ekstrak tempat] |
        | Pemimpin Rapat | [Ekstrak pemimpin] |
        | Dibuat oleh | Group Monitoring Evaluasi Strategi Perusahaan dan Inovasi |

        **Agenda:**\n- [Daftar agenda]

        **Peserta Rapat:**
        | No | Nama/Jabatan |
        |---|---|
        | 1 | [Ekstrak nama] |

        **Poin Diskusi dan Arahan:**
        | Pembahasan / Topik | Penanggung Jawab |
        |---|---|
        | **[Topik Pembahasan]** | |
        | **Poin Diskusi:** | |
        | [Jabatan/Nama] menyampaikan:<br>• [Poin penyampaian yang telah dielevasi menjadi bahasa formal tanpa mengurangi makna asli] | |
        | **Kesimpulan :** | |
        | [Jabatan/Nama] memberikan arahan sebagai berikut:<br>• [Poin arahan yang tegas] | [Penanggung Jawab] |

        **Disclaimer:**\n_Jika tidak ada tanggapan dalam tiga hari sejak dokumen ini didistribusikan, maka dokumen ini dianggap final._
        
        INSTRUKSI REPARASI:
        1. Jangan menghilangkan substansi atau mengecilkan makna dari draf asli. Perbaiki tata bahasanya saja menjadi kalimat korporat yang elegan.
        2. Jika ada kalimat yang terpotong di draf, buat agar terdengar masuk akal dan formal secara bisnis."""
                
                with st.spinner("🤖 Memproses reparasi notulen..."):
                    res_rep = generate_with_fallback(prompt_repair, api_key)
                    if res_rep['success']:
                        st.session_state.ai_repaired = res_rep['content']
                    else:
                        st.error(res_rep['error'])
        
        if st.session_state.ai_repaired:
            st.divider()
            rc1, rc2, _ = st.columns([2, 2, 6])
            with rc1:
                r_word_buffer = create_word_document(st.session_state.ai_repaired)
                st.download_button("📄 Unduh Word", r_word_buffer.getvalue(), "Reparasi_Notulen.docx", key="dl_rep_word", use_container_width=True)
            with rc2:
                st.download_button("📝 Unduh TXT", st.session_state.ai_repaired, "Reparasi_Notulen.txt", key="dl_rep_txt", use_container_width=True)
            
            with st.container(border=True):
                st.markdown(st.session_state.ai_repaired)
