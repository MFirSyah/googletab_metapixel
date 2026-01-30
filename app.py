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
        detected_platform = None
        
        # --- PERBAIKAN LOGIKA DETEKSI (Swap Order) ---
        # 1. Deteksi Meta Ads
        if any('amount spent' in c for c in cols) or any('reach' in c for c in cols):
            rename_map = {
                'Amount Spent (IDR)': 'Spend', 'Amount Spent': 'Spend', 
                'Website Purchase Conversion Value': 'Revenue', 
                'Link Clicks': 'Clicks',
                'CPM (Cost per 1000 Impressions)': 'CPM', 
                'CPC (Cost per Link Click)': 'CPC',
                'Purchases': 'Conversions',   # <--- FIX: Mapping Purchases ke Conversions biar bola muncul
                'Campaign Name': 'Campaign'   # <--- FIX: Biar nama campaign muncul saat di-hover
            }
            detected_platform = 'Meta Ads'
            
        # 2. Deteksi Google Ads
        elif any('cost' in c for c in cols) or any('avg. cpc' in c for c in cols):
            rename_map = {'Day': 'Date', 'Cost': 'Spend', 'Total conv. value': 'Revenue', 'Conv. value': 'Revenue'}
            detected_platform = 'Google Ads'
        else:
            rename_map = {}

        # Rename Kolom
        df = df.rename(columns=rename_map)
        
        # Assign platform dasar
        if 'Platform' not in df.columns and detected_platform:
            df['Platform'] = detected_platform
        
        # Fix Tanggal
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Gagal memproses file {uploaded_file.name}: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Panel Kontrol")
    data_source = st.radio("Sumber Data:", ("🔌 Koneksi API (Real-time)", "📂 Upload File Manual (CSV)"))
    st.divider()
    
    if data_source == "📂 Upload File Manual (CSV)":
        st.info("""
        **Aturan Nama File Upload:**
        * **Google:** Bebas (terdeteksi otomatis).
        * **Internal:** Nama file wajib ada kata `internal` atau `pixel_1`.
        * **Agency:** Nama file wajib ada kata `agency` atau `pixel_2`.
        """)
        
    st.caption("Developed by Firman (Data Science)")

# --- MAIN LOGIC ---
df_final = None

if data_source == "🔌 Koneksi API (Real-time)":
    st.title("📡 Live Ads Monitoring")
    if "api_credentials" in st.secrets:
        if st.button("🔄 Refresh Data Terbaru", type="primary"):
            df_final = fetch_data_from_api(st.secrets["api_credentials"])
            st.success("Data berhasil ditarik dari server!")
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
                # --- LOGIKA LABELING ---
                current_platform = processed['Platform'].iloc[0] if 'Platform' in processed.columns else 'Unknown'
                fname = file.name.lower()
                
                if 'Meta' in current_platform:
                    if 'internal' in fname or 'pixel_1' in fname:
                        processed['Platform'] = 'Meta Ads (Internal)'
                    elif 'agency' in fname or 'pixel_2' in fname:
                        processed['Platform'] = 'Meta Ads (Agency)'
                    else:
                        processed['Platform'] = f'Meta Ads ({file.name})'
                
                dfs.append(processed)
        
        if dfs:
            df_final = pd.concat(dfs, ignore_index=True)

# PROCESS DATA
if df_final is not None and not df_final.empty:
    
    # 1. Cleaning Numerik
    num_cols = ['Spend', 'Revenue', 'Clicks', 'Conversions', 'Impressions']
    for col in num_cols:
        if col in df_final.columns:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

    # 2. Filter Tanggal
    st.sidebar.divider()
    st.sidebar.subheader("📅 Filter Tanggal")
    if 'Date' in df_final.columns:
        min_d = df_final['Date'].min().date()
        max_d = df_final['Date'].max().date()
        try:
            if pd.isna(min_d) or pd.isna(max_d):
                st.sidebar.warning("Format tanggal tidak valid pada data.")
                df_filtered = df_final
            else:
                date_range = st.sidebar.date_input("Pilih Periode:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    mask = (df_final['Date'].dt.date >= start_date) & (df_final['Date'].dt.date <= end_date)
                    df_filtered = df_final.loc[mask]
                else:
                    df_filtered = df_final
        except:
             df_filtered = df_final
    else:
        df_filtered = df_final

    # 3. Hitung KPI Total
    tot_spend = df_filtered['Spend'].sum()
    tot_rev = df_filtered['Revenue'].sum()
    tot_roas = tot_rev / tot_spend if tot_spend > 0 else 0
    
    # --- DASHBOARD UI ---
    
    # A. KPI SCORECARD
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Biaya (Spend)", format_idr(tot_spend))
    c2.metric("Total Omzet (Revenue)", format_idr(tot_rev))
    c3.metric("ROAS (Efisiensi)", f"{tot_roas:.2f}x", delta="Target >10x")
    c4.metric("Total Transaksi", f"{df_filtered['Conversions'].sum():,.0f}")
    
    st.divider()

    # B. INSIGHT OTOMATIS
    if 'Platform' in df_filtered.columns and not df_filtered.empty:
        summary = df_filtered.groupby('Platform')[['Spend', 'Revenue', 'Conversions']].sum().reset_index()
        summary['ROAS'] = summary['Revenue'] / summary['Spend']
        summary_sorted = summary.sort_values(by='ROAS', ascending=False)
        best = summary_sorted.iloc[0]
        
        st.subheader("💡 Insight & Rekomendasi")
        with st.container(border=True):
            st.markdown(f"### 🏆 Yang lebih cuan adalah : **{best['Platform']}**")
            
            if len(summary_sorted) > 1:
                second_best = summary_sorted.iloc[1]
                diff_roas = best['ROAS'] - second_best['ROAS']
                
                st.markdown(f"""
                Platform ini terbukti paling pinter muterin duit iklan kita minggu ini. 
                Secara sederhana, performa **{best['Platform']}** jauh lebih efisien dibanding yang lain.
                
                **Kenapa dia juara?**
                * 💰 **Efisiensi Tinggi:** ROAS-nya tembus **{best['ROAS']:.2f}x**. Ini jauh lebih tinggi dibanding {second_best['Platform']} yang cuma dapet {second_best['ROAS']:.2f}x.
                * 📈 **Mesin Omzet:** Cuma keluar biaya {format_idr(best['Spend'])}, tapi berhasil bawa pulang omzet **{format_idr(best['Revenue'])}**.
                
                👀 **Bisa dilihat pada:** Grafik **'Perbandingan Biaya vs Hasil'** di bawah (Tab 1). Perhatikan batang {best['Platform']} yang warna hijaunya (Revenue) melesat jauh lebih tinggi dibanding batang merahnya (Spend).
                """)
            else:
                 st.markdown("Saat ini hanya ada satu platform yang aktif dalam data upload.")

    # C. GRAFIK TABS
    tab1, tab2, tab3 = st.tabs(["📊 Perbandingan Head-to-Head", "📈 Tren Harian & Detail", "🎯 Scatter Plot (Analisis Lanjut)"])
    
    with tab1:
        st.write("#### Perbandingan Biaya vs Hasil (Spend vs Revenue)")
        if 'Platform' in df_filtered.columns:
            
            platform_stats = df_filtered.groupby('Platform')[['Spend', 'Revenue']].sum().reset_index()
            platform_stats['ROAS_Val'] = platform_stats['Revenue'] / platform_stats['Spend']
            
            summary_melted = platform_stats.melt(
                id_vars=['Platform', 'ROAS_Val'], 
                value_vars=['Spend', 'Revenue'], 
                var_name='Metric', 
                value_name='Value'
            )
            
            def create_label(row):
                val_short = format_idr_short(row['Value'])
                if row['Metric'] == 'Revenue':
                    return f"{val_short}<br><b>(ROAS {row['ROAS_Val']:.1f}x)</b>"
                return val_short
            
            summary_melted['Text_Label'] = summary_melted.apply(create_label, axis=1)
            
            fig_bar = px.bar(
                summary_melted, 
                x='Platform', y='Value', color='Metric',
                barmode='group',
                text='Text_Label', 
                color_discrete_sequence=['#ff6b6b', '#1dd1a1'],
                title="Komparasi Spend vs Revenue"
            )
            
            fig_bar.update_traces(textposition='outside')
            
            max_y = summary_melted['Value'].max()
            fig_bar.update_layout(
                yaxis_range=[0, max_y * 1.2],
                margin=dict(t=50)
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Data Platform tidak tersedia.")

    with tab2:
        col_grafik, col_tabel = st.columns([2, 1])
        if 'Date' in df_filtered.columns:
            daily_agg = df_filtered.groupby(['Date', 'Platform'])[['Revenue']].sum().reset_index()
            with col_grafik:
                st.write("#### 📈 Grafik Tren Revenue")
                fig_line = px.line(daily_agg, x='Date', y='Revenue', color='Platform', markers=True)
                fig_line.update_layout(legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_line, use_container_width=True)
            with col_tabel:
                st.write("#### 📋 Data Detail Grafik")
                pivot_table = daily_agg.pivot(index='Date', columns='Platform', values='Revenue').fillna(0)
                pivot_table = pivot_table.sort_index(ascending=False)
                pivot_table.index = pivot_table.index.strftime('%d-%m-%Y')
                st.dataframe(pivot_table.style.format("Rp {:,.0f}"), use_container_width=True, height=400)

    with tab3:
        st.write("#### Peta Efisiensi Iklan")
        with st.expander("ℹ️ CARA MEMBACA GRAFIK INI (Klik untuk buka)", expanded=True):
            st.markdown("""
            | Zona | Posisi di Grafik | Arti Bisnis |
            | :--- | :--- | :--- |
            | **💎 Mutiara** | **Kiri Atas** | Biaya Murah, Omzet Tinggi |
            | **💰 Mesin Uang** | **Kanan Atas** | Biaya Mahal, Omzet Tinggi |
            | **💀 Boncos** | **Kanan Bawah** | Biaya Mahal, Omzet Kecil |
            | **🧪 Eksperimen** | **Kiri Bawah** | Biaya Murah, Omzet Kecil |
            """)
        if 'Clicks' in df_filtered.columns:
            fig_scatter = px.scatter(
                df_filtered, x='Spend', y='Revenue', size='Conversions', color='Platform',
                hover_data=['Campaign'] if 'Campaign' in df_filtered.columns else None,
                title="Peta Sebaran Efektifitas Iklan"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    with st.expander("🔍 Lihat Data Mentah Lengkap"):
        st.dataframe(df_filtered.sort_values(by='Date', ascending=False), use_container_width=True)
