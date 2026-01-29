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
    # Format angka besar jadi ringkas (1 Juta -> 1.0Jt, 1 Ribu -> 1k)
    if value >= 1000000000:
        return f"{value/1000000000:.1f}M"
    elif value >= 1000000:
        return f"{value/1000000:.1f}Jt"
    elif value >= 1000:
        return f"{value/1000:.0f}rb"
    return str(int(value))

# --- FUNGSI 1: MOCK API (THE BOSS MODE) ---
def fetch_data_from_api(secrets):
    with st.spinner('🔄 Menghubungi server Google Ads & Meta...'):
        time.sleep(1.5)
        dates = pd.date_range(end=datetime.today(), periods=14).tolist()
        data = []
        for date in dates:
            data.append({
                'Date': date, 'Platform': 'Google Ads', 
                'Campaign': 'Search - Laptop Gaming', 
                'Spend': 500000 + np.random.randint(-50000, 50000), 
                'Impressions': 2000, 'Clicks': 150, 'Conversions': 8, 'Revenue': 85000000
            })
            data.append({
                'Date': date, 'Platform': 'Meta Ads (Internal)', 
                'Campaign': 'Awareness - Promo', 
                'Spend': 300000 + np.random.randint(-20000, 20000), 
                'Impressions': 15000, 'Clicks': 300, 'Conversions': 2, 'Revenue': 5000000
            })
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
        
        if any('cost' in c for c in cols) or any('avg. cpc' in c for c in cols):
            rename_map = {'Day': 'Date', 'Cost': 'Spend', 'Total conv. value': 'Revenue', 'Conv. value': 'Revenue'}
            df['Platform'] = 'Google Ads'
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

    # 2. FILTER TANGGAL (SIDEBAR)
    st.sidebar.divider()
    st.sidebar.subheader("📅 Filter Tanggal")
    if 'Date' in df_final.columns:
        min_d = df_final['Date'].min().date()
        max_d = df_final['Date'].max().date()
        
        try:
            date_range = st.sidebar.date_input(
                "Pilih Periode:",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
                mask = (df_final['Date'].dt.date >= start_date) & (df_final['Date'].dt.date <= end_date)
                df_filtered = df_final.loc[mask]
            else:
                df_filtered = df_final
        except:
            st.sidebar.error("Silakan pilih tanggal awal dan akhir.")
            df_filtered = df_final
    else:
        df_filtered = df_final

    # 3. Hitung KPI (Data Terfilter)
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

    # --- INSIGHT OTOMATIS (DESKRIPSI ALASAN) ---
    if 'Platform' in df_filtered.columns and not df_filtered.empty:
        summary = df_filtered.groupby('Platform')[['Spend', 'Revenue', 'Conversions']].sum().reset_index()
        summary['ROAS'] = summary['Revenue'] / summary['Spend']
        
        # Urutkan dari ROAS tertinggi
        summary_sorted = summary.sort_values(by='ROAS', ascending=False)
        best = summary_sorted.iloc[0]
        
        # Logika Deskripsi Alasan
        alasan = ""
        if len(summary_sorted) > 1:
            second_best = summary_sorted.iloc[1]
            diff_roas = best['ROAS'] - second_best['ROAS']
            alasan = f"""
            **Alasan Pendukung:**
            * **Efisiensi Tinggi:** ROAS-nya mencapai **{best['ROAS']:.2f}x**, unggul {diff_roas:.2f} poin dibandingkan {second_best['Platform']} ({second_best['ROAS']:.2f}x).
            * **Kontribusi Omzet:** Menghasilkan total revenue **{format_idr(best['Revenue'])}** dari biaya iklan {format_idr(best['Spend'])}.
            * **Bisa dilihat pada:** Grafik 'Perbandingan Head-to-Head' di bawah, batang {best['Platform']} menunjukkan rasio pendapatan tertinggi dibanding biaya.
            """
        else:
            alasan = "Merupakan satu-satunya platform yang aktif pada periode ini."

        st.subheader("💡 Insight & Rekomendasi")
        st.info(f"""
        **🏆 Yang lebih cuan adalah: {best['Platform']}**
        
        {alasan}
        """)
    
    # --- GRAFIK ---
    tab1, tab2, tab3 = st.tabs(["📊 Perbandingan Head-to-Head", "📈 Tren Harian & Detail", "🎯 Scatter Plot (Analisis Lanjut)"])
    
    with tab1:
        st.write("#### Perbandingan Biaya vs Hasil")
        if 'Platform' in df_filtered.columns:
            # Siapkan data Melt agar label text bisa dipasang spesifik per bar
            summary_melted = df_filtered.groupby('Platform')[['Spend', 'Revenue']].sum().reset_index().melt(
                id_vars='Platform', 
                value_vars=['Spend', 'Revenue'], 
                var_name='Metric', 
                value_name='Value'
            )
            # Buat kolom text khusus format pendek (10Jt, 500rb)
            summary_melted['Text_Label'] = summary_melted['Value'].apply(format_idr_short)
            
            fig_bar = px.bar(
                summary_melted, 
                x='Platform', y='Value', color='Metric',
                barmode='group',
                text='Text_Label', # Munculkan nilai bar
                color_discrete_sequence=['#ff6b6b', '#1dd1a1'],
                title="Komparasi Spend vs Revenue"
            )
            
            # Posisikan text di luar bar agar terbaca
            fig_bar.update_traces(textposition='outside')
            # Tambah margin atas biar text ga kepotong
            fig_bar.update_layout(margin=dict(t=50))
            
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Data Platform tidak tersedia.")

    with tab2:
        col_grafik, col_tabel = st.columns([2, 1])
        
        if 'Date' in df_filtered.columns:
            daily_agg = df_filtered.groupby(['Date', 'Platform'])[['Revenue']].sum().reset_index()
            
            with col_grafik:
                st.write("#### 📈 Grafik Tren Revenue")
                fig_line = px.line(
                    daily_agg, x='Date', y='Revenue', color='Platform',
                    markers=True, title="Pergerakan Omzet per Hari"
                )
                fig_line.update_layout(legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_line, use_container_width=True)
            
            with col_tabel:
                st.write("#### 📋 Data Detail Grafik")
                st.caption("Nilai omzet untuk setiap titik (dot) pada grafik di samping:")
                
                # Pivot table biar mudah dibaca per tanggal
                pivot_table = daily_agg.pivot(index='Date', columns='Platform', values='Revenue').fillna(0)
                # Sort tanggal descending (terbaru di atas)
                pivot_table = pivot_table.sort_index(ascending=False)
                # Format tanggal index
                pivot_table.index = pivot_table.index.strftime('%d-%m-%Y')
                
                st.dataframe(
                    pivot_table.style.format("Rp {:,.0f}"), 
                    use_container_width=True,
                    height=400
                )
        else:
            st.warning("Data Tanggal tidak tersedia.")

    with tab3:
        st.write("#### Peta Efisiensi Iklan")
        
        # Penjelasan Scatter Plot Lengkap
        with st.expander("ℹ️ CARA MEMBACA GRAFIK INI (Klik untuk buka)", expanded=True):
            st.markdown("""
            Grafik ini memetakan performa iklan ke dalam 4 zona berdasarkan **Biaya (Sumbu X)** dan **Hasil (Sumbu Y)**:
            
            | Zona | Posisi di Grafik | Arti Bisnis | Tindakan |
            | :--- | :--- | :--- | :--- |
            | **💎 Mutiara Terpendam** | **Kiri Atas** | Biaya Murah, Omzet Tinggi | **Scale Up!** Tambah budget di sini. |
            | **💰 Mesin Uang** | **Kanan Atas** | Biaya Mahal, Omzet Tinggi | **Maintain.** Ini tulang punggung bisnismu. |
            | **💀 Zona Boncos** | **Kanan Bawah** | Biaya Mahal, Omzet Kecil | **Matikan/Evaluasi.** Iklan ini merugi. |
            | **🧪 Eksperimen** | **Kiri Bawah** | Biaya Murah, Omzet Kecil | **Pantau.** Iklan baru atau testing. |
            
            *Besar lingkaran = Jumlah Transaksi (Sales).*
            """)

        if 'Clicks' in df_filtered.columns and 'Conversions' in df_filtered.columns:
            fig_scatter = px.scatter(
                df_filtered, 
                x='Spend', y='Revenue', 
                size='Conversions', color='Platform',
                hover_data=['Campaign'] if 'Campaign' in df_filtered.columns else None,
                labels={'Spend': 'Biaya Iklan (Cost)', 'Revenue': 'Omzet (Revenue)'},
                title="Peta Sebaran Efektifitas Iklan"
            )
            
            # Tambah garis diagonal ROAS 10x (Target Hijau)
            max_val = max(df_filtered['Spend'].max(), df_filtered['Revenue'].max())
            if max_val > 0:
                fig_scatter.add_shape(type="line", x0=0, y0=0, x1=max_val/10, y1=max_val,
                                    line=dict(color="Green", width=1, dash="dot"))
                fig_scatter.add_annotation(x=max_val/10, y=max_val, text="Garis Target (ROAS 10x)", 
                                         showarrow=False, yshift=10, font=dict(color="Green"))
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("Data tidak cukup untuk Scatter Plot.")

    # RAW DATA
    with st.expander("🔍 Lihat Data Mentah Lengkap"):
        st.dataframe(df_filtered.sort_values(by='Date', ascending=False), use_container_width=True)
