import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="DB Klik Ads Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNGSI HELPER ---
def format_idr(value):
    return f"Rp {value:,.0f}"

def format_idr_short(value):
    # Format angka besar jadi ringkas (1 Juta -> 1M, 1 Ribu -> 1k) untuk Label Grafik
    if value >= 1000000000:
        return f"{value/1000000000:.1f}Milyar"
    elif value >= 1000000:
        return f"{value/1000000:.1f}Jt"
    elif value >= 1000:
        return f"{value/1000:.0f}rb"
    return str(value)

# --- FUNGSI 1: MOCK API (THE BOSS MODE) ---
def fetch_data_from_api(secrets):
    with st.spinner('🔄 Menghubungi server Google Ads & Meta...'):
        time.sleep(1.5)
        # Data Dummy Cerdas
        dates = pd.date_range(end=datetime.today(), periods=14).tolist()
        data = []
        for date in dates:
            # Google Ads (Cenderung High Revenue)
            data.append({
                'Date': date, 'Platform': 'Google Ads', 
                'Campaign': 'Search - Laptop Gaming', 
                'Spend': 500000 + np.random.randint(-50000, 50000), 
                'Impressions': 2000, 'Clicks': 150, 'Conversions': 8, 'Revenue': 85000000
            })
            # Meta Ads Internal (Cenderung High Traffic, Low ROAS)
            data.append({
                'Date': date, 'Platform': 'Meta Ads (Internal)', 
                'Campaign': 'Awareness - Promo', 
                'Spend': 300000 + np.random.randint(-20000, 20000), 
                'Impressions': 15000, 'Clicks': 300, 'Conversions': 2, 'Revenue': 5000000
            })
             # Meta Ads Agency (Cenderung Efisien)
            data.append({
                'Date': date, 'Platform': 'Meta Ads (Agency)', 
                'Campaign': 'Retargeting - Cart', 
                'Spend': 400000 + np.random.randint(-20000, 20000), 
                'Impressions': 5000, 'Clicks': 200, 'Conversions': 5, 'Revenue': 25000000
            })
        return pd.DataFrame(data)

# --- FUNGSI 2: PROCESS CSV ---
def process_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        cols = [c.lower() for c in df.columns] 
        
        # Deteksi Google Ads
        if any('cost' in c for c in cols) or any('avg. cpc' in c for c in cols):
            rename_map = {'Day': 'Date', 'Cost': 'Spend', 'Total conv. value': 'Revenue', 'Conv. value': 'Revenue'}
            df['Platform'] = 'Google Ads'
        # Deteksi Meta Ads
        elif any('amount spent' in c for c in cols) or any('reach' in c for c in cols):
            rename_map = {'Amount Spent (IDR)': 'Spend', 'Amount Spent': 'Spend', 'Website Purchase Conversion Value': 'Revenue', 'Link Clicks': 'Clicks'}
            if 'Platform' not in df.columns:
                df['Platform'] = 'Meta Ads'
        else:
            rename_map = {}

        df = df.rename(columns=rename_map)
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Error pada file {uploaded_file.name}: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Panel Kontrol")
    data_source = st.radio("Sumber Data:", ("🔌 Koneksi API (Real-time)", "📂 Upload File Manual (CSV)"))
    st.divider()
    st.caption("Developed by Firman (Data Science)")

# --- MAIN LOGIC ---
df_final = None

# LOAD DATA
if data_source == "🔌 Koneksi API (Real-time)":
    st.title("📡 Live Ads Monitoring")
    if "api_credentials" in st.secrets:
        if st.button("🔄 Refresh Data Terbaru", type="primary"):
            df_final = fetch_data_from_api(st.secrets["api_credentials"])
            st.success("Data updated!")
        else:
            st.info("Tekan tombol di atas untuk menarik data terbaru.")
    else:
        st.warning("⚠️ API belum terhubung.")
        st.write("Silakan gunakan mode Upload CSV di sidebar.")

elif data_source == "📂 Upload File Manual (CSV)":
    st.title("📂 Analisis Data Manual")
    uploaded_files = st.file_uploader("Upload Report (Bisa Multiple File)", type=['csv', 'xlsx'], accept_multiple_files=True)
    
    if uploaded_files:
        dfs = []
        for file in uploaded_files:
            processed = process_uploaded_file(file)
            if processed is not None:
                # Labeling Otomatis
                if 'Platform' in processed.columns and processed['Platform'].iloc[0] == 'Meta Ads':
                    if 'internal' in file.name.lower() or 'pixel_1' in file.name.lower():
                        processed['Platform'] = 'Meta Ads (Internal)'
                    elif 'agency' in file.name.lower() or 'pixel_2' in file.name.lower():
                        processed['Platform'] = 'Meta Ads (Agency)'
                dfs.append(processed)
        if dfs:
            df_final = pd.concat(dfs, ignore_index=True)

# PROCESS DATA
if df_final is not None and not df_final.empty:
    
    # 1. Bersihkan Data Numerik
    num_cols = ['Spend', 'Revenue', 'Clicks', 'Conversions', 'Impressions']
    for col in num_cols:
        if col in df_final.columns:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

    # 2. FILTER TANGGAL (REVISI 4)
    st.sidebar.divider()
    st.sidebar.subheader("📅 Filter Periode")
    if 'Date' in df_final.columns:
        min_d, max_d = df_final['Date'].min().date(), df_final['Date'].max().date()
        try:
            start_date, end_date = st.sidebar.date_input("Pilih Rentang:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        except:
            start_date, end_date = min_d, max_d
        
        # Terapkan Filter
        mask = (df_final['Date'].dt.date >= start_date) & (df_final['Date'].dt.date <= end_date)
        df_filtered = df_final.loc[mask]
    else:
        df_filtered = df_final

    # 3. Hitung KPI (Berdasarkan Data Terfilter)
    tot_spend = df_filtered['Spend'].sum()
    tot_rev = df_filtered['Revenue'].sum()
    tot_roas = tot_rev / tot_spend if tot_spend > 0 else 0
    
    # --- UI DASHBOARD ---
    
    # KPI SCORECARD
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Biaya (Spend)", format_idr(tot_spend))
    c2.metric("Total Omzet (Revenue)", format_idr(tot_rev))
    c3.metric("ROAS (Efisiensi)", f"{tot_roas:.2f}x", delta="Target >10x")
    c4.metric("Total Transaksi", f"{df_filtered['Conversions'].sum():,.0f}")
    
    st.divider()

    # --- INSIGHT OTOMATIS (REVISI 1) ---
    if 'Platform' in df_filtered.columns and not df_filtered.empty:
        # Cari platform terbaik
        summary = df_filtered.groupby('Platform')[['Spend', 'Revenue']].sum().reset_index()
        summary['ROAS'] = summary['Revenue'] / summary['Spend']
        best = summary.loc[summary['ROAS'].idxmax()]
        
        st.subheader("💡 Insight & Rekomendasi")
        st.info(f"""
        **🏆 Juara Profitabilitas: {best['Platform']}**
        
        Berdasarkan data periode ini, **{best['Platform']}** adalah yang paling 'Cuan'.
        * **ROAS:** Mencapai **{best['ROAS']:.2f}x**. (Setiap keluar Rp 1.000, balik Rp {best['ROAS']*1000:,.0f}).
        * **Rekomendasi:** Detail perbandingan lengkap bisa dilihat pada **Tab Grafik** di bawah ini. Cek apakah budget bisa dialihkan ke sini.
        """)
    
    # --- GRAFIK ---
    tab1, tab2, tab3 = st.tabs(["📊 Perbandingan Bar Chart", "📈 Tren & Tabel Harian", "🎯 Scatter Plot (Efisiensi)"])
    
    with tab1:
        st.write("#### Perbandingan Biaya vs Hasil")
        if 'Platform' in df_filtered.columns:
            # (REVISI 2: Munculkan Nilai di Bar)
            summary_grouped = df_filtered.groupby('Platform')[['Spend', 'Revenue']].sum().reset_index()
            
            # Kita buat data teks untuk label (biar rapi misal: 10Jt)
            summary_grouped['Text_Rev'] = summary_grouped['Revenue'].apply(format_idr_short)
            summary_grouped['Text_Spend'] = summary_grouped['Spend'].apply(format_idr_short)
            
            fig_bar = px.bar(
                summary_grouped, 
                x='Platform', y=['Spend', 'Revenue'], 
                barmode='group',
                text_auto=False, # Kita custom text-nya di bawah
                color_discrete_sequence=['#ff6b6b', '#1dd1a1'],
                title="Komparasi Head-to-Head"
            )
            
            # Paksa label muncul di luar batang
            fig_bar.update_traces(texttemplate='%{y:.2s}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Data Platform tidak tersedia.")

    with tab2:
        st.write("#### Pergerakan Omzet Harian")
        if 'Date' in df_filtered.columns:
            daily_agg = df_filtered.groupby(['Date', 'Platform'])[['Revenue']].sum().reset_index()
            
            fig_line = px.line(
                daily_agg, x='Date', y='Revenue', color='Platform',
                markers=True, title="Tren Revenue per Hari"
            )
            fig_line.update_layout(xaxis_title="Tanggal", yaxis_title="Omzet")
            st.plotly_chart(fig_line, use_container_width=True)
            
            # (REVISI 3: Tabel Nilai Grafik)
            st.write("#### 📋 Rincian Nilai Harian (Table View)")
            pivot_table = daily_agg.pivot(index='Date', columns='Platform', values='Revenue').fillna(0)
            
            # Format tanggal jadi string biar rapi di tabel
            pivot_table.index = pivot_table.index.strftime('%d-%m-%Y')
            
            st.dataframe(pivot_table.style.format("Rp {:,.0f}"), use_container_width=True)
        else:
            st.warning("Data Tanggal tidak tersedia.")

    with tab3:
        st.write("#### Peta Efisiensi Iklan")
        
        # (REVISI 5: Penjelasan Scatter Plot)
        with st.expander("ℹ️ Panduan Cara Membaca Grafik Ini (Klik untuk buka)"):
            st.markdown("""
            Grafik ini membagi performa ke dalam 4 kuadran imajiner:
            
            1.  **Kiri Atas (Mutiara Terpendam):** Biaya murah, tapi Omzet tinggi. **Pertahankan & Scale Up!**
            2.  **Kanan Atas (Mesin Uang):** Biaya besar, Omzet juga besar. Ini adalah kampanye utama Anda.
            3.  **Kanan Bawah (Zona Bahaya/Boncos):** Biaya besar, tapi Omzet kecil. **Segera matikan atau perbaiki iklannya.**
            4.  **Kiri Bawah (Eksperimen):** Biaya kecil, Omzet kecil. Biasanya iklan baru testing.
            
            *Ukuran bola menunjukkan jumlah transaksi (Sales).*
            """)

        if 'Clicks' in df_filtered.columns and 'Conversions' in df_filtered.columns:
            fig_scatter = px.scatter(
                df_filtered, 
                x='Spend', y='Revenue', 
                size='Conversions', color='Platform',
                hover_data=['Campaign'] if 'Campaign' in df_filtered.columns else None,
                labels={'Spend': 'Biaya Iklan (Cost)', 'Revenue': 'Omzet (Revenue)'}
            )
            # Tambah garis diagonal ROAS 10x (Target)
            max_val = max(df_filtered['Spend'].max(), df_filtered['Revenue'].max())
            fig_scatter.add_shape(type="line", x0=0, y0=0, x1=max_val/10, y1=max_val,
                                line=dict(color="Green", width=1, dash="dot"))
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("Data tidak cukup untuk Scatter Plot.")

    # RAW DATA
    with st.expander("🔍 Lihat Data Mentah"):
        st.dataframe(df_filtered.sort_values(by='Date', ascending=False), use_container_width=True)
