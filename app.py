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
def fetch_data_from_api(secrets):
    with st.spinner('🔄 Sedang menghubungi server Google Ads & Meta...'):
        time.sleep(1.5) # Simulasi loading
        
        # Simulasi Data Dummy (Backup jika API belum connect)
        dates = pd.date_range(end=datetime.today(), periods=7).tolist()
        data = []
        for date in dates:
            data.append({
                'Date': date, 'Platform': 'Google Ads', 
                'Campaign': 'Search - Laptop Gaming', 
                'Spend': 500000 + np.random.randint(-50000, 50000), 
                'Impressions': 2000, 'Clicks': 150, 'Conversions': 8, 'Revenue': 85000000
            })
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
        # Baca file sesuai format
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # LOGIKA DETEKSI KOLOM (FINGERPRINTING)
        cols = [c.lower() for c in df.columns] 
        
        # 1. Deteksi Format Google Ads
        if any('cost' in c for c in cols) or any('avg. cpc' in c for c in cols):
            # Standarisasi Nama Kolom
            rename_map = {
                'Day': 'Date', 'Cost': 'Spend', 'Total conv. value': 'Revenue', 
                'Conv. value': 'Revenue'
            }
            # Tambahkan kolom Platform
            df['Platform'] = 'Google Ads'
            
        # 2. Deteksi Format Meta Ads
        elif any('amount spent' in c for c in cols) or any('reach' in c for c in cols):
            # Standarisasi Nama Kolom
            rename_map = {
                'Amount Spent (IDR)': 'Spend', 'Amount Spent': 'Spend',
                'Website Purchase Conversion Value': 'Revenue',
                'Link Clicks': 'Clicks'
            }
            # Tambahkan kolom Platform
            # Jika belum ada nama khusus, set default Meta Ads
            if 'Platform' not in df.columns:
                df['Platform'] = 'Meta Ads'
        
        else:
            rename_map = {}

        # Lakukan Rename
        df = df.rename(columns=rename_map)
        
        # --- FIX: PARSING TANGGAL (PENTING!) ---
        if 'Date' in df.columns:
            # dayfirst=True memaksa baca format DD/MM/YYYY (Format Indo)
            # errors='coerce' mengubah tanggal ngawur jadi NaT (Not a Time) biar gak error
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            
        return df

    except Exception as e:
        st.error(f"Gagal memproses file {uploaded_file.name}: {e}")
        return None

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    st.header("🎛️ Panel Kontrol")
    
    # Pilihan Mode Sumber Data
    data_source = st.radio(
        "Sumber Data:",
        ("🔌 Koneksi API (Real-time)", "📂 Upload File Manual (CSV)"),
        index=0
    )
    
    st.divider()
    st.caption("Developed by Firman (Data Science)")

# --- LOGIKA UTAMA (MAIN LOGIC) ---
df_final = None

# A. MODE API
if data_source == "🔌 Koneksi API (Real-time)":
    st.title("📡 Live Ads Monitoring (API Mode)")
    
    if "api_credentials" in st.secrets:
        if st.button("🔄 Refresh Data Terbaru", type="primary"):
            df_final = fetch_data_from_api(st.secrets["api_credentials"])
            st.success("Data berhasil diperbarui dari server!")
        else:
            st.info("Tekan tombol di atas untuk menarik data terbaru.")
    else:
        st.warning("⚠️ API Credential belum ditemukan.")
        st.markdown("Sistem siap. Silakan gunakan mode **Upload File Manual** jika API Key belum tersedia.")

# B. MODE UPLOAD CSV (MULTI-FILE SUPPORT)
elif data_source == "📂 Upload File Manual (CSV)":
    st.title("📂 Analisis Data Manual")
    
    # Perubahan: accept_multiple_files=True
    uploaded_files = st.file_uploader(
        "Upload Report Export (Bisa pilih 3 file sekaligus: Google, Pixel 1, Pixel 2)", 
        type=['csv', 'xlsx'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        all_dataframes = []
        with st.spinner('Sedang menggabungkan data...'):
            for file in uploaded_files:
                processed_df = process_uploaded_file(file)
                if processed_df is not None:
                    # Tambahan: Kasih label file asal jika Platform belum terdeteksi spesifik
                    # Biar Pixel 1 dan Pixel 2 gak kecampur jadi satu "Meta Ads" doang
                    if 'Platform' in processed_df.columns and processed_df['Platform'].iloc[0] == 'Meta Ads':
                        # Deteksi manual sederhana berdasarkan nama file
                        if 'internal' in file.name.lower() or 'pixel_1' in file.name.lower():
                            processed_df['Platform'] = 'Meta Ads (Internal)'
                        elif 'agency' in file.name.lower() or 'pixel_2' in file.name.lower():
                            processed_df['Platform'] = 'Meta Ads (Agency)'
                    
                    all_dataframes.append(processed_df)
                    st.toast(f"✅ Berhasil memuat: {file.name}", icon="📄")
        
        # Gabungkan semua file jadi satu tabel besar
        if all_dataframes:
            df_final = pd.concat(all_dataframes, ignore_index=True)
            st.success(f"Berhasil menggabungkan {len(uploaded_files)} file data!")

# --- VISUALISASI DASHBOARD ---
if df_final is not None and not df_final.empty:
    
    # 1. Pastikan kolom numerik aman
    cols_to_numeric = ['Spend', 'Revenue', 'Clicks', 'Conversions', 'Impressions']
    for col in cols_to_numeric:
        if col in df_final.columns:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

    # 2. Hitung ROAS & KPI Total
    if 'Revenue' in df_final.columns and 'Spend' in df_final.columns:
        total_spend = df_final['Spend'].sum()
        total_revenue = df_final['Revenue'].sum()
        # Hindari pembagian dengan nol
        total_roas = total_revenue / total_spend if total_spend > 0 else 0
        
        total_clicks = df_final['Clicks'].sum() if 'Clicks' in df_final.columns else 0
        total_impr = df_final['Impressions'].sum() if 'Impressions' in df_final.columns else 0
        ctr = (total_clicks / total_impr * 100) if total_impr > 0 else 0

    st.divider()
    
    # --- BAGIAN A: SCORECARD KPI ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Ad Spend", format_idr(total_spend), delta="Total Biaya")
    with col2:
        st.metric("Total Revenue", format_idr(total_revenue), delta="Total Omzet")
    with col3:
        st.metric("ROAS (Efisiensi)", f"{total_roas:.2f}x", delta="Target: >10x")
    with col4:
        st.metric("Avg. CTR", f"{ctr:.2f}%")

    # --- BAGIAN B: GRAFIK VISUAL ---
    st.write("### 📊 Analisis Performa")
    
    tab1, tab2, tab3 = st.tabs(["Perbandingan Platform", "Tren Harian", "Scatter Plot"])
    
    with tab1:
        if 'Platform' in df_final.columns:
            # Agregasi per Platform
            platform_summary = df_final.groupby('Platform')[['Spend', 'Revenue']].sum().reset_index()
            # Hitung ROAS per platform buat label
            platform_summary['ROAS'] = platform_summary['Revenue'] / platform_summary['Spend']
            
            fig_bar = px.bar(
                platform_summary,
                x='Platform', y=['Spend', 'Revenue'],
                barmode='group',
                title="Google Ads vs Meta Ads: Mana yang Lebih Cuan?",
                color_discrete_sequence=['#ff6b6b', '#1dd1a1'],
                hover_data=['ROAS']
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Kolom 'Platform' tidak terdeteksi.")

    with tab2:
        if 'Date' in df_final.columns:
            # Agregasi per Tanggal dan Platform (biar garisnya pisah)
            daily_data = df_final.groupby(['Date', 'Platform'])[['Revenue']].sum().reset_index()
            fig_line = px.line(
                daily_data, x='Date', y='Revenue', color='Platform',
                title="Tren Omzet Harian per Platform",
                markers=True, line_shape='spline'
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Kolom 'Date' tidak terdeteksi.")
            
    with tab3:
        if 'Clicks' in df_final.columns and 'Conversions' in df_final.columns:
             fig_scatter = px.scatter(
                 df_final, x='Spend', y='Revenue', size='Conversions', color='Platform',
                 title="Efisiensi Biaya (Makin besar bola = Makin banyak penjualan)",
                 hover_data=['Campaign'] if 'Campaign' in df_final.columns else None
             )
             st.plotly_chart(fig_scatter, use_container_width=True)

    # --- BAGIAN C: DATA TABLE ---
    with st.expander("🔍 Lihat Data Mentah Gabungan"):
        st.dataframe(df_final.sort_values(by='Date', ascending=False), use_container_width=True)
