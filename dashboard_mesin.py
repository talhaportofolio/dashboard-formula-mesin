import streamlit as st
import pandas as pd
import re
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashbord SG Formula", layout="wide", page_icon="⚙️")

# CSS Kustom (Diperbarui untuk Layout Rapat/One Screen)
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    h1 { color: #2c3e50; font-size: 2rem !important; margin-bottom: 0 !important; }
    .stDataFrame { border: 1px solid #ddd; background-color: white; }
    div[data-testid="stMetricValue"] { font-size: 20px; color: #e74c3c; }
    div[data-testid="stMetricLabel"] { font-size: 14px; }
    
    /* --- COMPACT LAYOUT CSS --- */
    .block-container {
        padding-top: 1rem !important; /* Mengurangi jarak atas */
        padding-bottom: 1rem !important;
    }
    
    /* --- SEMBUNYIKAN ELEMENT STREAMLIT ASLI --- */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Custom CSS untuk Tombol Filter (Pills / Multiselect) agar berwarna merah muda */
    div[data-testid="stPills"] button, div[data-testid="stSegmentedControl"] button {
        border: 1px solid #ff4b4b !important;
        color: #ff4b4b !important;
        background-color: #fff0f0 !important;
        border-radius: 20px !important;
    }
    div[data-testid="stPills"] button[aria-selected="true"], div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    
</style>
""", unsafe_allow_html=True)

# --- FUNGSI GLOBAL ---
def cek_rusak(val):
    """Fungsi untuk mengecek apakah sel menandakan kerusakan atau ada isinya"""
    v = str(val).strip().lower()
    if v in ['nan', 'none', '', '-', '0']:
        return 0
    return 1

@st.cache_data(ttl=600)
def process_data(file_path):
    """Fungsi untuk mengekstrak dan merapikan data dari format Excel Kerusakan Harian"""
    if hasattr(file_path, 'name') and file_path.name.endswith('.csv'):
        df_raw = pd.read_csv(file_path, header=None)
    else:
        df_raw = pd.read_excel(file_path, header=None)
    
    # Forward fill untuk AREA dan KATEGORI
    df_raw[0] = df_raw[0].ffill()
    df_raw[1] = df_raw[1].ffill()
    
    # Ambil baris yang berisi judul/header
    row_1 = df_raw.iloc[1].copy() 
    row_2 = df_raw.iloc[2].copy() 
    
    # Forward fill baris tanggal ke samping
    row_1.iloc[4:] = row_1.iloc[4:].ffill()
    
    # Buat penamaan kolom gabungan
    new_columns = []
    for i in range(len(df_raw.columns)):
        if i == 0: new_columns.append("AREA")
        elif i == 1: new_columns.append("KATEGORI")
        elif i == 2: new_columns.append("NO")
        elif i == 3: new_columns.append("NAMA MESIN")
        else:
            tgl = str(row_1[i]).replace(".0", "").strip()
            tipe = str(row_2[i]).strip()
            if tgl.lower() != 'nan' and tipe.lower() != 'nan':
                new_columns.append(f"Tgl {tgl} - {tipe}")
            else:
                new_columns.append(f"Kolom_Kosong_{i}")
    
    df_raw.columns = new_columns
    df_bersih = df_raw.iloc[3:].reset_index(drop=True)
    
    kolom_valid = [col for col in df_bersih.columns if "Kolom_Kosong" not in col]
    df_bersih = df_bersih[kolom_valid]
    df_bersih = df_bersih.dropna(how='all')
    return df_bersih

# --- INITIALIZE SESSION STATE ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'
if 'df_main' not in st.session_state:
    st.session_state.df_main = None
if 'selected_machine' not in st.session_state:
    st.session_state.selected_machine = None
if 'filter_area' not in st.session_state:
    st.session_state.filter_area = ["MOLD", "INJECTION", "FILLING", "CUTTING", "PACKING", "UTILITY"]
if 'file_path' not in st.session_state:
    st.session_state.file_path = None

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
                        df_loaded = process_data(final_file_path)
                        if not df_loaded.empty:
                            st.session_state.df_main = df_loaded
                            st.session_state.file_path = final_file_path # Simpan untuk refresh
                            st.session_state.filter_area = ["MOLD", "INJECTION", "FILLING", "CUTTING", "PACKING", "UTILITY"]
                            st.session_state.current_page = 'viewer'
                            st.rerun()
                        else:
                            st.error("Data kosong atau gagal dibaca.")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat memproses data: {e}")

# ==========================================
# PAGE 2: DATA VIEWER (TABEL & GRAFIK)
# ==========================================
elif st.session_state.current_page == 'viewer':
    
    # --- HEADER COMPACT ---
    c1, c2, c3 = st.columns([6, 1, 1])
    with c1:
        st.markdown("### ⚙️ Dashboard PT Ultra Prima Abadi - Formula")
    with c2:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            if st.session_state.file_path:
                with st.spinner("Mengambil data terbaru..."):
                    try:
                        df_new = process_data(st.session_state.file_path)
                        st.session_state.df_main = df_new
                    except Exception as e:
                        st.error(f"Gagal memuat ulang: {e}")
            st.rerun()
            
    with c3:
        if st.button("⬅️ Ganti File"):
            st.session_state.current_page = 'landing'
            st.session_state.df_main = None
            st.session_state.filter_area = ["MOLD", "INJECTION", "FILLING", "CUTTING", "PACKING", "UTILITY"]
            st.session_state.file_path = None
            st.cache_data.clear()
            st.rerun()
            
    if st.session_state.df_main is not None:
        df = st.session_state.df_main.copy()
        
        # --- TOP BAR: METRICS & FILTER SEJAJAR ---
        col_m1, col_m2, col_f = st.columns([1, 1, 3])
        
        with col_f:
            area_options = ["MOLD", "INJECTION", "FILLING", "CUTTING", "PACKING", "UTILITY"]
            
            if 'filter_area' not in st.session_state:
                st.session_state.filter_area = area_options
                
            if hasattr(st, 'pills'):
                try:
                    selected_area = st.pills("Filter Area:", area_options, selection_mode="multi", key="filter_area")
                except TypeError:
                    selected_area = st.multiselect("Filter Area:", area_options, key="filter_area")
            else:
                selected_area = st.multiselect("Filter Area:", area_options, key="filter_area")
                
        # Logika memfilter Dataframe berdasarkan area yang dipilih
        if 'KATEGORI' in df.columns:
            if selected_area:
                pattern = "|".join(selected_area)
                df = df[df['KATEGORI'].astype(str).str.upper().str.contains(pattern, na=False)]
            else:
                df = df.iloc[0:0]
        else:
            st.warning("Kolom 'KATEGORI' tidak ditemukan dalam data.")
        
        # Menghitung metrik 
        jumlah_mesin = df['NAMA MESIN'].nunique() if 'NAMA MESIN' in df.columns else 0
        
        kolom_kerusakan = [col for col in df.columns if 'KERUSAKAN' in str(col).upper()]
        if kolom_kerusakan:
            df['Jumlah Kerusakan'] = df[kolom_kerusakan].apply(lambda x: x.map(cek_rusak)).sum(axis=1)
            total_hari_rusak = int(df['Jumlah Kerusakan'].sum())
        else:
            total_hari_rusak = 0
            
        # Menampilkan metrik di sisi kiri (Styling sudah diatur via CSS stMetricValue)
        with col_m1:
            st.metric("Jumlah Mesin", f"{jumlah_mesin}")
        with col_m2:
            st.metric("Total Hari Rusak", f"{total_hari_rusak}")
            
        st.divider()
        
        # --- VISUALISASI ---
        col_kiri, col_kanan = st.columns([1, 2])
        
        with col_kiri:
            st.caption("📊 **Frekuensi Kerusakan per Mesin** (Klik batang untuk melihat detail)")
            
            if kolom_kerusakan:
                df_grafik = df[['NAMA MESIN', 'Jumlah Kerusakan']].copy()
                df_grafik['NAMA MESIN'] = df_grafik['NAMA MESIN'].astype(str)
                df_grafik = df_grafik.groupby('NAMA MESIN')['Jumlah Kerusakan'].sum().reset_index()
                df_grafik = df_grafik[df_grafik['Jumlah Kerusakan'] > 0]
                df_grafik = df_grafik.sort_values(by='Jumlah Kerusakan', ascending=True)
                
                if not df_grafik.empty:
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
                            yaxis_title="Nama Mesin",
                            clickmode='event+select'
                        )
                        
                        event = st.plotly_chart(
                            fig, 
                            use_container_width=True, 
                            on_select="rerun", 
                            selection_mode="points"
                        )
                        
                        if event and event.get("selection", {}).get("points"):
                            clicked_machine = event["selection"]["points"][0]["y"]
                            st.session_state.selected_machine = clicked_machine
                            st.session_state.current_page = 'detail'
                            st.rerun()

                else:
                    st.info("Belum ada data kerusakan yang tercatat di Area ini.")
            else:
                st.warning("Kolom berisi 'KERUSAKAN' tidak ditemukan.")

        with col_kanan:
            st.caption("📋 **Detail Data Keseluruhan Mesin**")
            st.dataframe(df, use_container_width=True, height=600)

# ==========================================
# PAGE 3: DETAIL PAGE (DRILL DOWN)
# ==========================================
elif st.session_state.current_page == 'detail':
    
    machine_name = st.session_state.selected_machine
    df = st.session_state.df_main
    
    # Tombol Kembali ditempatkan di atas Judul
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state.selected_machine = None
        st.session_state.current_page = 'viewer'
        st.rerun()
            
    st.markdown(f"### 🔎 Analisis Detail: **{machine_name}**")
            
    df_machine = df[df['NAMA MESIN'].astype(str) == machine_name]
    
    if not df_machine.empty:
        area = df_machine['AREA'].values[0] if 'AREA' in df_machine.columns else "-"
        kategori = df_machine['KATEGORI'].values[0] if 'KATEGORI' in df_machine.columns else "-"
        
        col_info1, col_info2, col_info3 = st.columns([1, 1, 2]) # Memberi ruang kosong di kanan agar lebih rapi
        # Menggunakan st.metric karena CSS kita sudah memformatnya menjadi merah (color: #e74c3c) dan berukuran 20px
        with col_info1:
            st.metric("Area Pabrik", str(area))
        with col_info2:
            st.metric("Kategori Mesin", str(kategori))
            
        st.divider()
        st.caption("📅 **Rincian Kerusakan per Hari**")
        
        histori_kerusakan = []
        
        hari_tersedia = set()
        for col in df.columns:
            match = re.match(r'Tgl\s+(\d+)\s+-', str(col), re.IGNORECASE)
            if match:
                hari_tersedia.add(int(match.group(1)))
                
        hari_tersedia = sorted(list(hari_tersedia))
        
        for hari in hari_tersedia:
            kolom_hari_ini = [col for col in df.columns if str(col).startswith(f"Tgl {hari} -")]
            data_hari_ini = {"Hari Ke-": f"Hari {hari}"}
            ada_isi = False
            
            for col in kolom_hari_ini:
                nilai_sel = df_machine[col].values[0]
                tipe = str(col).replace(f"Tgl {hari} - ", "").strip()
                
                if cek_rusak(nilai_sel):
                    ada_isi = True
                    data_hari_ini[tipe] = str(nilai_sel)
                else:
                    data_hari_ini[tipe] = "-"
                    
            if ada_isi:
                histori_kerusakan.append(data_hari_ini)
        
        if histori_kerusakan:
            df_histori = pd.DataFrame(histori_kerusakan)
            df_histori.set_index("Hari Ke-", inplace=True)
            
            st.markdown(
                """
                <style>
                div[data-testid="stTable"] table { table-layout: fixed !important; width: 100% !important; }
                div[data-testid="stTable"] th:first-child { width: 100px !important; white-space: nowrap !important; }
                </style>
                """, unsafe_allow_html=True
            )
            
            st.table(df_histori)
        else:
            st.info("Tidak ada kerusakan atau catatan spesifik yang tercatat untuk mesin ini pada periode tersebut.")
            
        st.divider()
        st.caption("👁️ **Tampilan Baris Excel Asli**")
        st.dataframe(df_machine, use_container_width=True, hide_index=True)
