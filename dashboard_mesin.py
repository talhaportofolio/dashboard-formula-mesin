import streamlit as st
import pandas as pd
import re
import plotly.express as px

# Konfigurasi halaman agar lebar
st.set_page_config(page_title="Data Viewer", layout="wide", page_icon="⚙️")

# --- INITIALIZE SESSION STATE ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'
if 'df_main' not in st.session_state:
    st.session_state.df_main = None

# ==========================================
# PAGE 1: LANDING PAGE (INPUT DATA)
# ==========================================
if st.session_state.current_page == 'landing':
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("⚙️ Dashboard PT Ultra Prima Abadi - Formula")
        st.markdown("### Selamat Datang")
        st.markdown("Silakan pilih sumber data untuk memulai analisis kerusakan mesin.")
        st.markdown("---")
        
        source_option = st.radio("Pilih Metode Input:", ["Upload File Excel", "Link Google Sheet"], horizontal=True)
        
        final_file_path = None
        
        if source_option == "Upload File Excel":
            uploaded_file = st.file_uploader("📂 Upload File Mesin (.xlsx, .csv)", type=["xlsx", "csv"])
            if uploaded_file:
                final_file_path = uploaded_file

        else:
            st.info("💡 Pastikan Google Sheet diatur ke **'Anyone with the link'**.")
            sheet_url = st.text_input("🔗 Paste Link Google Sheet:", placeholder="https://docs.google.com/spreadsheets/d/...")
            
            if sheet_url:
                match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
                if match:
                    sheet_id = match.group(1)
                    final_file_path = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
                else:
                    st.error("Link tidak valid.")

        if final_file_path:
            if st.button("🚀 Proses Data", type="primary", use_container_width=True):
                with st.spinner("Membaca dan merapikan struktur tabel..."):
                    try:
                        # 1. Baca data mentah tanpa header terlebih dahulu
                        if hasattr(final_file_path, 'name') and final_file_path.name.endswith('.csv'):
                            df_raw = pd.read_csv(final_file_path, header=None)
                        else:
                            df_raw = pd.read_excel(final_file_path, header=None)
                        
                        # 2. Forward fill (isi otomatis ke bawah) untuk AREA dan KATEGORI karena aslinya di-merge
                        df_raw[0] = df_raw[0].ffill()
                        df_raw[1] = df_raw[1].ffill()
                        
                        # 3. Ambil baris yang berisi judul/header (Baris ke-2 dan ke-3 di Excel = Index 1 dan 2)
                        row_1 = df_raw.iloc[1].copy() # Baris berisi angka tanggal (1, 2, 3...)
                        row_2 = df_raw.iloc[2].copy() # Baris berisi NO, NAMA MESIN, KERUSAKAN, STATUS
                        
                        # Forward fill baris tanggal ke samping (agar 1, kosong, kosong menjadi 1, 1, 1)
                        # Kita mulai dari kolom ke-4 (index 4)
                        row_1.iloc[4:] = row_1.iloc[4:].ffill()
                        
                        # 4. Buat penamaan kolom gabungan yang sangat rapi
                        new_columns = []
                        for i in range(len(df_raw.columns)):
                            if i == 0: new_columns.append("AREA")
                            elif i == 1: new_columns.append("KATEGORI")
                            elif i == 2: new_columns.append("NO")
                            elif i == 3: new_columns.append("NAMA MESIN")
                            else:
                                # Menggabungkan Tanggal (Baris 1) dan Jenis Laporan (Baris 2)
                                tgl = str(row_1[i]).replace(".0", "").strip()
                                tipe = str(row_2[i]).strip()
                                
                                if tgl.lower() != 'nan' and tipe.lower() != 'nan':
                                    new_columns.append(f"Tgl {tgl} - {tipe}")
                                else:
                                    new_columns.append(f"Kolom_Kosong_{i}")
                        
                        # Terapkan nama kolom yang baru dibuat
                        df_raw.columns = new_columns
                        
                        # 5. Potong data utama (mulai dari baris ke-4 / index 3 ke bawah)
                        df_bersih = df_raw.iloc[3:].reset_index(drop=True)
                        
                        # 6. Bersihkan baris & kolom yang sama sekali tidak ada datanya
                        # Hapus kolom yang namanya "Kolom_Kosong"
                        kolom_valid = [col for col in df_bersih.columns if "Kolom_Kosong" not in col]
                        df_bersih = df_bersih[kolom_valid]
                        
                        # Hapus baris kosong
                        df_bersih = df_bersih.dropna(how='all')
                        
                        # Simpan ke session state
                        st.session_state.df_main = df_bersih
                        st.session_state.current_page = 'viewer'
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat memproses data: {e}")

# ==========================================
# PAGE 2: DATA VIEWER (TABEL)
# ==========================================
elif st.session_state.current_page == 'viewer':
    
    # Layout Header
    c1, c2 = st.columns([8, 1])
    with c1:
        st.title("⚙️ Dashboard PT Ultra Prima Abadi - Formula")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Kembali", use_container_width=True):
            st.session_state.current_page = 'landing'
            st.session_state.df_main = None
            st.rerun()
            
    st.success("Data berhasil dimuat! Baris dan kolom yang di-merge telah diratakan agar mudah dibaca.")
    
    if st.session_state.df_main is not None:
        df = st.session_state.df_main.copy()
        
        # Membuat 2 kolom bersebelahan (Kiri untuk grafik, Kanan untuk tabel)
        # Rasio 1 : 2 agar tabel mendapatkan porsi layar yang lebih lebar
        col_kiri, col_kanan = st.columns([1, 2])
        
        with col_kiri:
            # --- LOGIKA GRAFIK KERUSAKAN MESIN ---
            st.markdown("### 📊 Frekuensi Kerusakan")
            
            # Cari semua kolom yang memiliki kata "KERUSAKAN" di judulnya
            kolom_kerusakan = [col for col in df.columns if 'KERUSAKAN' in str(col).upper()]
            
            if kolom_kerusakan:
                def cek_rusak(val):
                    v = str(val).strip().lower()
                    if v in ['nan', 'none', '', '-', '0']:
                        return 0
                    return 1
                
                # Menghitung jumlah hari rusak
                df['Jumlah Kerusakan'] = df[kolom_kerusakan].apply(lambda x: x.map(cek_rusak)).sum(axis=1)
                
                df_grafik = df[['NAMA MESIN', 'Jumlah Kerusakan']].copy()
                df_grafik['NAMA MESIN'] = df_grafik['NAMA MESIN'].astype(str)
                df_grafik = df_grafik.groupby('NAMA MESIN')['Jumlah Kerusakan'].sum().reset_index()
                df_grafik = df_grafik[df_grafik['Jumlah Kerusakan'] > 0]
                df_grafik = df_grafik.sort_values(by='Jumlah Kerusakan', ascending=True)
                
                if not df_grafik.empty:
                    # Mengatur tinggi container sama dengan tinggi tabel (600px) agar sejajar rapi
                    with st.container(height=600):
                        dynamic_height = max(400, len(df_grafik) * 40)
                        
                        fig = px.bar(
                            df_grafik, 
                            x='Jumlah Kerusakan', 
                            y='NAMA MESIN', 
                            orientation='h',
                            text_auto=True
                        )
                        
                        fig.update_layout(
                            height=dynamic_height,
                            yaxis={'categoryorder':'total ascending'},
                            margin=dict(l=0, r=0, t=10, b=0),
                            xaxis_title="Total Hari Rusak",
                            yaxis_title="Nama Mesin"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Belum ada data kerusakan yang tercatat di file ini.")
            else:
                st.warning("Kolom berisi 'KERUSAKAN' tidak ditemukan.")

        with col_kanan:
            # --- MENAMPILKAN TABEL KESELURUHAN ---
            st.markdown("### 📋 Detail Data Keseluruhan")
            st.dataframe(st.session_state.df_main, use_container_width=True, height=600)
