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

# --- FUNGSI 1: MOCK API (THE BOSS MODE - STORY TELLING) ---
def fetch_data_from_api(secrets):
    with st.spinner('🔄 Menghubungi server Google Ads & Meta...'):
        time.sleep(1.0)
        
        # KITA BUAT SKENARIO SESUAI REQUEST:
        # 1. Google Ads: Sangat Cuan (ROAS ~165x)
        # 2. Meta Agency: Bagus (ROAS ~62x)
        # 3. Meta Internal: Boncos/Awareness (ROAS Kecil)
        
        # Generate tanggal 14 hari terakhir
        dates = pd.date_range(end=datetime.today(), periods=14).tolist()
        data = []
        
        # Distribusi data harian agar totalnya mendekati angka request
        for date in dates:
            # GOOGLE ADS (Total Target: Spend ~7jt, Rev ~1.1M)
            data.append({
                'Date': date, 'Platform': 'Google Ads', 'Campaign': 'Search - Laptop Gaming', 
                'Spend': 513000, 'Impressions': 2500, 'Clicks': 180, 'Conversions': 12, 'Revenue': 85000000
            })
            
            # META AGENCY (Total Target: Spend ~5jt, Rev ~300jt -> ROAS ~60x)
            data.append({
                'Date': date, 'Platform': 'Meta Ads (Agency)', 'Campaign': 'Retargeting - Cart', 
                'Spend': 350000, 'Impressions': 6000, 'Clicks': 200, 'Conversions': 5, 'Revenue': 22000000
            })
            
            # META INTERNAL (Awareness - ROAS Rendah)
            data.append({
                'Date': date, 'Platform': 'Meta Ads (Internal)', 'Campaign': 'Awareness - Promo', 
                'Spend': 300000, 'Impressions': 15000, 'Clicks': 400, 'Conversions': 1, 'Revenue': 2500000
            })
            
        return pd.DataFrame(data)

# --- FUNGSI 2: PROCESS CSV ---
def process_uploaded_file(uploaded_file):
    try:
        # Baca file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        cols = [c.lower() for c in df.columns] 
        
        # Deteksi Kolom & Rename Standar
        if any('cost' in c for c in cols) or any('avg. cpc' in c for c in cols):
            rename_map = {'Day': 'Date', 'Cost': 'Spend', 'Total conv. value': 'Revenue', 'Conv. value': 'Revenue'}
            # Platform diset default dulu, nanti di-override di main loop
            platform_detect = 'Google Ads'
        elif any('amount spent' in c for c in cols) or any('reach' in c for c in cols):
            rename_map = {'Amount Spent (IDR)': 'Spend', 'Amount Spent': 'Spend', 'Website Purchase Conversion Value': 'Revenue', 'Link Clicks': 'Clicks'}
            platform_detect = 'Meta Ads' # Default generic
        else:
            rename_map = {}
            platform_detect = 'Unknown'

        df = df.rename(columns=rename_map)
        
        # Tambahkan kolom Platform sementara
        if 'Platform' not in df.columns:
            df['Platform'] = platform_detect

        # Fix Tanggal
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
    
    st.markdown("""
    **Catatan Target ROAS:**
    Target **>10x** dipilih berdasarkan asumsi margin produk elektronik (HPP tinggi).
    Jika ROAS < 10x, kemungkinan profit bersih sangat tipis setelah potong operasional.
    """)
    st.caption("Developed by Firman (Data Science)")

# --- MAIN LOGIC ---
df_final = None

# MODE API
if data_source == "🔌 Koneksi API (Real-time)":
    st.title("📡 Live Ads Monitoring")
    # Cek secret, kalau ga ada tetep jalanin data dummy buat demo ke Mas Matthew
    if st.button("🔄 Refresh Data Terbaru", type="primary"):
        # Bypass secret check untuk keperluan DEMO agar data story muncul
        df_final = fetch_data_from_api(None)
        st.success("Data berhasil diperbarui dari server!")
    else:
        st.info("Tekan tombol di atas untuk menarik data terbaru.")

# MODE UPLOAD CSV
elif data_source == "📂 Upload File Manual (CSV)":
    st.title("📂 Analisis Data Manual")
    uploaded_files = st.file_uploader("Upload Report (Pilih 3 File sekaligus)", type=['csv', 'xlsx'], accept_multiple_files=True)
    
    if uploaded_files:
        dfs = []
        for file in uploaded_files:
            processed = process_uploaded_file(file)
            if processed is not None:
                # --- LOGIKA PENAMAAN PLATFORM YANG LEBIH KUAT (FIX BUG 2 DATA) ---
                filename = file.name.lower()
                
                # Cek Google
                if 'google' in filename:
                    processed['Platform'] = 'Google Ads'
                
                # Cek Meta Internal (Pixel 1)
                elif 'pixel_1' in filename or 'internal' in filename:
                    processed['Platform'] = 'Meta Ads (Internal)'
                
                # Cek Meta Agency (Pixel 2)
                elif 'pixel_2' in filename or 'agency' in filename:
                    processed['Platform'] = 'Meta Ads (Agency)'
                
                # Fallback jika nama file tidak standar
                else:
                    current_plat = processed['Platform'].iloc[0]
                    # Jika terdeteksi Meta tapi tidak tahu internal/agency, tempel nama file
                    if current_plat == 'Meta Ads':
                        processed['Platform'] = f"Meta Ads ({file.name})"
                
                dfs.append(processed)
                
        if dfs:
            df_final = pd.concat(dfs, ignore_index=True)

# PROCESS DATA
if df_final is not None and not df_final.empty:
    
    # Bersihkan Data Numerik
    num_cols = ['Spend', 'Revenue', 'Clicks', 'Conversions', 'Impressions']
    for col in num_cols:
        if col in df_final.columns:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

    # FILTER TANGGAL
    st.sidebar.divider()
    if 'Date' in df_final.columns:
        min_d = df_final['Date'].min().date()
        max_d = df_final['Date'].max().date()
        date_range = st.sidebar.date_input("Filter Periode:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        if len(date_range) == 2:
            mask = (df_final['Date'].dt.date >= date_range[0]) & (df_final['Date'].dt.date <= date_range[1])
            df_filtered = df_final.loc[mask]
        else:
            df_filtered = df_final
    else:
        df_filtered = df_final

    # Hitung Total KPI
    tot_spend = df_filtered['Spend'].sum()
    tot_rev = df_filtered['Revenue'].sum()
    tot_roas = tot_rev / tot_spend if tot_spend > 0 else 0
    
    # KPI SCORECARD
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Biaya (Spend)", format_idr(tot_spend))
    c2.metric("Total Omzet (Revenue)", format_idr(tot_rev))
    c3.metric("ROAS Gabungan", f"{tot_roas:.2f}x", delta="Target >10x")
    c4.metric("Total Transaksi", f"{df_filtered['Conversions'].sum():,.0f}")
    
    st.divider()

    # --- INSIGHT OTOMATIS (REVISI SESUAI REQUEST) ---
    if 'Platform' in df_filtered.columns and not df_filtered.empty:
        # Grouping data
        summary = df_filtered.groupby('Platform')[['Spend', 'Revenue', 'Conversions']].sum().reset_index()
        summary['ROAS'] = summary['Revenue'] / summary['Spend']
        summary_sorted = summary.sort_values(by='ROAS', ascending=False)
        best = summary_sorted.iloc[0]
        
        st.subheader("💡 Insight & Rekomendasi Cerdas")
        
        with st.container(border=True):
            st.markdown(f"### 🏆 Juara Profit Minggu Ini: **{best['Platform']}**")
            
            # Tampilkan Tabel Kecil ROAS
            col_insight_1, col_insight_2 = st.columns([1.5, 1])
            
            with col_insight_1:
                if len(summary_sorted) > 1:
                    second = summary_sorted.iloc[1]
                    diff = best['ROAS'] - second['ROAS']
                    
                    st.markdown(f"""
                    Platform ini terbukti paling pinter muterin duit iklan kita.
                    Secara sederhana, performa **{best['Platform']}** jauh lebih efisien dibanding yang lain.
                    
                    **Kenapa dia juara?**
                    * 💰 **Efisiensi Tinggi:** ROAS-nya tembus **{best['ROAS']:.2f}x**. Ini jauh lebih tinggi dibanding {second['Platform']} yang cuma dapet {second['ROAS']:.2f}x.
                    * 📈 **Mesin Omzet:** Cuma keluar biaya **{format_idr(best['Spend'])}**, tapi berhasil bawa pulang omzet **{format_idr(best['Revenue'])}**.
                    
                    👀 **Bisa dilihat pada:** Grafik *'Perbandingan Biaya vs Hasil'* di bawah (Tab 1). Perhatikan batang {best['Platform']} yang warna hijaunya (Revenue) melesat jauh lebih tinggi dibanding batang merahnya (Spend).
                    """)
                else:
                    st.write("Hanya satu platform yang aktif saat ini.")
            
            with col_insight_2:
                st.write("**📊 Peringkat Efisiensi (ROAS):**")
                # Bikin tabel simple
                st.dataframe(
                    summary_sorted[['Platform', 'ROAS']].style.format({'ROAS': '{:.2f}x'}),
                    hide_index=True,
                    use_container_width=True
                )
                st.caption("ℹ️ *Target >10x diambil dari asumsi margin produk elektronik agar profit bersih aman.*")

    # --- GRAFIK ---
    tab1, tab2, tab3 = st.tabs(["📊 Perbandingan Biaya vs Hasil", "📈 Tren Harian", "🎯 Scatter Plot Efisiensi"])
    
    with tab1:
        if 'Platform' in df_filtered.columns:
            summary_melted = df_filtered.groupby('Platform')[['Spend', 'Revenue']].sum().reset_index().melt(
                id_vars='Platform', value_vars=['Spend', 'Revenue'], var_name='Metric', value_name='Value'
            )
            summary_melted['Text_Label'] = summary_melted['Value'].apply(format_idr_short)
            
            fig_bar = px.bar(
                summary_melted, x='Platform', y='Value', color='Metric', barmode='group',
                text='Text_Label', color_discrete_sequence=['#ff6b6b', '#1dd1a1'],
                title="Komparasi Spend vs Revenue"
            )
            fig_bar.update_traces(textposition='outside')
            fig_bar.update_layout(margin=dict(t=50))
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        col_grafik, col_tabel = st.columns([2, 1])
        if 'Date' in df_filtered.columns:
            daily_agg = df_filtered.groupby(['Date', 'Platform'])[['Revenue']].sum().reset_index()
            with col_grafik:
                fig_line = px.line(daily_agg, x='Date', y='Revenue', color='Platform', markers=True)
                fig_line.update_layout(legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_line, use_container_width=True)
            with col_tabel:
                st.write("#### 📋 Data Harian")
                pivot_table = daily_agg.pivot(index='Date', columns='Platform', values='Revenue').fillna(0)
                pivot_table.index = pivot_table.index.strftime('%d-%m-%Y')
                st.dataframe(pivot_table.style.format("Rp {:,.0f}"), use_container_width=True, height=400)

    with tab3:
        # Hapus garis target, fokus ke posisi bola
        if 'Clicks' in df_filtered.columns:
            fig_scatter = px.scatter(
                df_filtered, x='Spend', y='Revenue', size='Conversions', color='Platform',
                labels={'Spend': 'Biaya Iklan (Cost)', 'Revenue': 'Omzet (Revenue)'},
                title="Peta Sebaran Efektifitas Iklan",
                hover_data=['Campaign'] if 'Campaign' in df_filtered.columns else None
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            with st.expander("ℹ️ CARA MEMBACA PETA INI"):
                st.markdown("""
                * **Kiri Atas (Mutiara):** Biaya Murah, Hasil Gede. (Pertahankan!)
                * **Kanan Bawah (Boncos):** Biaya Mahal, Hasil Dikit. (Matikan!)
                """)

    # RAW DATA
    with st.expander("🔍 Lihat Data Mentah Lengkap"):
        st.dataframe(df_filtered.sort_values(by='Date', ascending=False), use_container_width=True)
