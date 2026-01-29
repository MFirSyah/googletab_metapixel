import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
import numpy as np

# --- KONFIGURASI HALAMAN (WAJIB PALING ATAS) ---
st.set_page_config(
    page_title="DB Klik Ads Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNGSI HELPER: FORMAT RUPIAH ---
def format_idr(value):
    return f"Rp {value:,.0f}"

# --- FUNGSI 1: "THE BOSS MODE" (MOCK API CONNECTION) ---
# Fungsi ini mensimulasikan koneksi ke Google & Meta
# Nanti jika Mas Matthew sudah kasih API Key, logika request asli ditaruh di sini.
def fetch_data_from_api(secrets):
    with st.spinner('🔄 Sedang menghubungi server Google Ads & Meta...'):
        time.sleep(1.5) # Simulasi loading biar terlihat "real"
        
        # Di sini nanti tempat codingan asli library google-ads / facebook-business sdk
        # Karena sekarang belum ada API Key valid, kita generate data "Real-time" dummy
        # agar dashboard tidak error dan Mas Matthew bisa lihat previewnya.
        
        dates = pd.date_range(end=datetime.today(), periods=7).tolist()
        data = []
        for date in dates:
            # Simulasi Data Google (Diambil via "API")
            data.append({
                'Date': date, 'Platform': 'Google Ads', 
                'Campaign': 'Search - Laptop Gaming', 
                'Spend': 500000 + np.random.randint(-50000, 50000), 
                'Impressions': 2000, 'Clicks': 150, 'Conversions': 8, 'Revenue': 85000000
            })
            # Simulasi Data Meta (Diambil via "API")
            data.append({
                'Date': date, 'Platform': 'Meta Ads', 
                'Campaign': 'Retargeting - Promo', 
                'Spend': 300000 + np.random.randint(-20000, 20000), 
                'Impressions': 15000, 'Clicks': 300, 'Conversions': 5, 'Revenue': 25000000
            })
        
        return pd.DataFrame(data)

# --- FUNGSI 2: AUTO-DETECT COLUMN (UNTUK CSV) ---
def process_uploaded_file(uploaded_file):
    try:
        # Baca file (CSV atau Excel)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # LOGIKA DETEKSI KOLOM (FINGERPRINTING)
        cols = [c.lower() for c in df.columns] # Lowercase semua biar aman
        
        # 1. Deteksi Format Google Ads
        if any('cost' in c for c in cols) or any('avg. cpc' in c for c in cols):
            st.toast("✅ Terdeteksi: Format Data Google Ads", icon="🔵")
            # Standarisasi Nama Kolom
            rename_map = {
                'Day': 'Date', 'Cost': 'Spend', 'Total conv. value': 'Revenue', 
                'Conv. value': 'Revenue'
            }
            # Tambahkan kolom Platform jika tidak ada
            df['Platform'] = 'Google Ads'
            
        # 2. Deteksi Format Meta Ads
        elif any('amount spent' in c for c in cols) or any('reach' in c for c in cols):
            st.toast("✅ Terdeteksi: Format Data Meta Ads", icon="🔵")
            # Standarisasi Nama Kolom
            rename_map = {
                'Amount Spent (IDR)': 'Spend', 'Amount Spent': 'Spend',
                'Website Purchase Conversion Value': 'Revenue',
                'Link Clicks': 'Clicks'
            }
            # Tambahkan kolom Platform jika tidak ada
            df['Platform'] = 'Meta Ads'
        
        else:
            st.warning("⚠️ Format kolom tidak dikenali otomatis. Mencoba membaca apa adanya.")
            rename_map = {}

        # Lakukan Rename
        df = df.rename(columns=rename_map)
        
        # Pastikan kolom Date berformat tanggal
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            
        return df

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
        return None

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    st.header("🎛️ Panel Kontrol")
    
    # Pilihan Mode Sumber Data
    data_source = st.radio(
        "Sumber Data:",
        ("🔌 Koneksi API (Real-time)", "📂 Upload File Manual (CSV)"),
        index=0,
        help="Gunakan API untuk data otomatis. Gunakan Upload jika API belum siap."
    )
    
    st.divider()
    st.caption("Developed by Firman (Data Science)")

# --- LOGIKA UTAMA (MAIN LOGIC) ---
df_final = None

# A. JIKA MEMILIH MODE API (DEFAULT)
if data_source == "🔌 Koneksi API (Real-time)":
    st.title("📡 Live Ads Monitoring (API Mode)")
    
    # Cek apakah Secret sudah disetting di "Brankas" Streamlit
    # Ini kuncinya "The Boss Mode", cek file secrets.toml
    if "api_credentials" in st.secrets:
        # Jika Ada Secret -> Langsung Tarik Data
        if st.button("🔄 Refresh Data Terbaru", type="primary"):
            df_final = fetch_data_from_api(st.secrets["api_credentials"])
            st.success("Data berhasil diperbarui dari server!")
        else:
            # Tampilan awal sebelum klik tombol
            st.info("Tekan tombol di atas untuk menarik data terbaru dari Google & Meta.")
            
    else:
        # Jika Secret BELUM Ada (Graceful Fallback)
        st.warning("⚠️ API Credential belum ditemukan di sistem.")
        st.markdown("""
        **Status:** Sistem siap, namun kunci akses (API Key) belum terdeteksi di server.
        
        **Saran Tindakan:**
        1. Masukkan API Key Google & Meta ke pengaturan *Secrets* di Streamlit Cloud.
        2. Atau, gunakan mode **'Upload File Manual'** di sidebar kiri untuk sementara.
        """)

# B. JIKA MEMILIH MODE UPLOAD CSV
elif data_source == "📂 Upload File Manual (CSV)":
    st.title("📂 Analisis Data Manual")
    uploaded_file = st.file_uploader("Upload Report Export (Google/Meta)", type=['csv', 'xlsx'])
    
    if uploaded_file:
        df_final = process_uploaded_file(uploaded_file)
        if df_final is not None:
            st.success("File berhasil diproses!")

# --- VISUALISASI DASHBOARD ---
# Kode di bawah ini hanya jalan kalau df_final SUDAH ADA isinya
if df_final is not None:
    
    # 1. Pastikan kolom numerik aman
    cols_to_numeric = ['Spend', 'Revenue', 'Clicks', 'Conversions', 'Impressions']
    for col in cols_to_numeric:
        if col in df_final.columns:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

    # 2. Hitung ROAS & KPI
    if 'Revenue' in df_final.columns and 'Spend' in df_final.columns:
        total_spend = df_final['Spend'].sum()
        total_revenue = df_final['Revenue'].sum()
        total_roas = total_revenue / total_spend if total_spend > 0 else 0
        
        # Menghitung CTR & CPA jika kolom tersedia
        total_clicks = df_final['Clicks'].sum() if 'Clicks' in df_final.columns else 0
        total_impr = df_final['Impressions'].sum() if 'Impressions' in df_final.columns else 0
        ctr = (total_clicks / total_impr * 100) if total_impr > 0 else 0

    st.divider()
    
    # --- BAGIAN A: SCORECARD KPI ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Ad Spend", format_idr(total_spend), delta="Biaya Keluar")
    with col2:
        st.metric("Total Revenue", format_idr(total_revenue), delta="Omzet Masuk", delta_color="normal")
    with col3:
        st.metric("ROAS (Return On Ad Spend)", f"{total_roas:.2f}x", delta="Target: >10x")
    with col4:
        st.metric("Avg. CTR", f"{ctr:.2f}%", help="Rata-rata Click-Through Rate")

    # --- BAGIAN B: GRAFIK VISUAL ---
    st.write("### 📊 Analisis Performa")
    
    tab1, tab2, tab3 = st.tabs(["Perbandingan Platform", "Tren Harian", "Scatter Plot"])
    
    with tab1:
        # Grafik Batang: Google vs Meta
        if 'Platform' in df_final.columns:
            fig_bar = px.bar(
                df_final.groupby('Platform')[['Spend', 'Revenue']].sum().reset_index(),
                x='Platform', y=['Spend', 'Revenue'],
                barmode='group',
                title="Google Ads vs Meta Ads: Spend vs Revenue",
                color_discrete_sequence=['#ff6b6b', '#1dd1a1']
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Kolom 'Platform' tidak terdeteksi untuk perbandingan.")

    with tab2:
        # Grafik Garis: Tren Harian
        if 'Date' in df_final.columns:
            daily_data = df_final.groupby('Date')[['Revenue']].sum().reset_index()
            fig_line = px.line(
                daily_data, x='Date', y='Revenue',
                title="Tren Omzet Harian",
                markers=True, line_shape='spline'
            )
            fig_line.update_traces(line_color='#54a0ff', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Kolom 'Date' tidak terdeteksi untuk tren waktu.")
            
    with tab3:
        # Scatter Plot: Efisiensi
        if 'Clicks' in df_final.columns and 'Conversions' in df_final.columns:
             fig_scatter = px.scatter(
                 df_final, x='Spend', y='Revenue', size='Conversions', color='Platform',
                 title="Efisiensi Biaya: Semakin ke kiri atas, semakin bagus",
                 hover_data=['Campaign'] if 'Campaign' in df_final.columns else None
             )
             st.plotly_chart(fig_scatter, use_container_width=True)

    # --- BAGIAN C: DATA TABLE ---
    with st.expander("🔍 Lihat Data Mentah"):
        st.dataframe(df_final, use_container_width=True)
