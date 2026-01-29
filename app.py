import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="DB Klik Ads Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan Dashboard Premium
st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 5px;
        color: #495057;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e3f2fd;
        color: #0d6efd;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. LOGIC PEMROSESAN DATA (BACKEND)
# ==========================================

def standardize_data(df, source_type):
    """
    Normalisasi kolom dari berbagai sumber (Google/Meta) ke standar DB Klik.
    """
    df = df.copy()
    
    # Standar Kolom DB Klik
    standard_cols = ['Date', 'Platform', 'Campaign', 'Spend', 'Impressions', 'Clicks', 'Conversions', 'Revenue']
    
    try:
        if source_type == 'google':
            rename_map = {
                'Day': 'Date', 'Cost': 'Spend', 'Total conv. value': 'Revenue', 
                'Ad group': 'Campaign', 'Avg. CPC': 'CPC'
            }
            # Pakai 'Campaign' jika ada, jika tidak pakai 'Ad group'
            if 'Campaign' in df.columns: rename_map['Campaign'] = 'Campaign'
                
            df.rename(columns=rename_map, inplace=True)
            df['Platform'] = 'Google Ads'
            
        elif source_type == 'meta':
            rename_map = {
                'Amount Spent (IDR)': 'Spend', 'Website Purchase Conversion Value': 'Revenue',
                'Link Clicks': 'Clicks', 'Purchases': 'Conversions', 'Campaign Name': 'Campaign'
            }
            df.rename(columns=rename_map, inplace=True)
            # Logika sederhana membedakan Agency vs Internal dari nama Campaign
            df['Platform'] = df['Campaign'].apply(lambda x: 'Meta Ads (Agency)' if 'Retargeting' in str(x) or 'DPA' in str(x) else 'Meta Ads (Internal)')

        # Pembersihan Data Numeric
        cols_to_clean = ['Spend', 'Revenue', 'Impressions', 'Clicks', 'Conversions']
        for col in cols_to_clean:
            if col in df.columns:
                if df[col].dtype == object:
                     df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Konversi Tanggal
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        # Filter hanya kolom yang ada di standar
        available_cols = [c for c in standard_cols if c in df.columns]
        return df[available_cols]

    except Exception as e:
        st.error(f"⚠️ Gagal memproses data {source_type}: {str(e)}")
        return None

def detect_and_process_file(uploaded_file):
    """
    AUTO-DETECT: Mengenali file berdasarkan 'Sidik Jari' kolom header.
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        cols = df.columns.tolist()
        
        # Cek ciri khas Google
        if 'Cost' in cols or 'Avg. CPC' in cols:
            return standardize_data(df, 'google')
        # Cek ciri khas Meta
        elif 'Amount Spent (IDR)' in cols or 'Reach' in cols:
            return standardize_data(df, 'meta')
        else:
            st.error(f"❌ File **{uploaded_file.name}** tidak dikenali formatnya. Pastikan export asli.")
            return None
    except Exception as e:
        st.error(f"Error membaca file: {str(e)}")
        return None

def fetch_api_data_mock():
    """
    Simulasi Koneksi API (Boss Mode).
    Nanti ini diganti dengan library 'facebook_business' dan 'google.ads.googleads'
    """
    with st.spinner('🔄 Authenticating with Google Ads Server...'):
        time.sleep(0.8)
    with st.spinner('🔄 Authenticating with Meta Graph API...'):
        time.sleep(0.8)
    with st.spinner('⬇️ Fetching daily performance data...'):
        time.sleep(1)
        
    # Data Dummy Realistis untuk Demo
    dates = pd.date_range(end=datetime.today(), periods=14).tolist()
    data = []
    import random
    
    for date in dates:
        # Google Data (High Value, High Spend)
        data.append({
            'Date': date, 'Platform': 'Google Ads', 'Campaign': 'Search - Laptop Gaming ASUS', 
            'Spend': random.randint(500000, 800000), 'Impressions': random.randint(2000, 3000), 
            'Clicks': random.randint(150, 250), 'Conversions': random.randint(8, 15), 
            'Revenue': random.randint(80000000, 150000000)
        })
        # Meta Internal (High Impression, Low ROAS)
        data.append({
            'Date': date, 'Platform': 'Meta Ads (Internal)', 'Campaign': 'Awareness - Brand Promo', 
            'Spend': random.randint(200000, 400000), 'Impressions': random.randint(15000, 25000), 
            'Clicks': random.randint(300, 500), 'Conversions': random.randint(1, 3), 
            'Revenue': random.randint(2000000, 8000000)
        })
        # Meta Agency (Mid range, Good ROAS)
        data.append({
            'Date': date, 'Platform': 'Meta Ads (Agency)', 'Campaign': 'Retargeting - Catalog DPA', 
            'Spend': random.randint(400000, 600000), 'Impressions': random.randint(5000, 8000), 
            'Clicks': random.randint(200, 300), 'Conversions': random.randint(5, 10), 
            'Revenue': random.randint(30000000, 60000000)
        })
    
    st.toast("✅ Data berhasil diperbarui dari Server!", icon="🚀")
    return pd.DataFrame(data)

# ==========================================
# 2. SIDEBAR KONTROL (THE SWITCHER)
# ==========================================

st.sidebar.title("⚙️ Control Panel")
st.sidebar.markdown("---")

# Cek apakah 'Boss Mode' enabled (Secrets tersedia)
secrets_exist = False
try:
    if "api_credentials" in st.secrets:
        secrets_exist = True
except:
    pass

# Mode Selector
mode = st.sidebar.radio(
    "Pilih Sumber Data:",
    ["🔌 API Connection (Boss Mode)", "📂 Upload CSV Manual"],
    index=0 if secrets_exist else 1
)

main_df = None

if mode == "🔌 API Connection (Boss Mode)":
    st.sidebar.info("Mode Otomatis: Mengambil data langsung dari server Google & Meta.")
    
    if secrets_exist:
        st.sidebar.success("✅ API Key Terdeteksi")
        if st.sidebar.button("🔄 Update Data Sekarang", type="primary", use_container_width=True):
            main_df = fetch_api_data_mock()
    else:
        st.sidebar.warning("⚠️ API Key Belum Dikonfigurasi")
        st.sidebar.markdown("""
        Untuk mengaktifkan Boss Mode, tambahkan konfigurasi di `.streamlit/secrets.toml`.
        """)
        with st.sidebar.expander("📝 Lihat Format Secrets"):
            st.code("""
[api_credentials]
google_ads_token = "masukkan_token_disini"
meta_app_id = "masukkan_id_disini"
meta_access_token = "masukkan_token_disini"
            """, language="toml")

elif mode == "📂 Upload CSV Manual":
    st.sidebar.warning("Mode Manual: Silakan upload file hasil export.")
    
    uploaded_files = st.sidebar.file_uploader(
        "Upload File (Google/Meta)", 
        type=['csv', 'xlsx'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        combined_data = []
        for file in uploaded_files:
            processed_df = detect_and_process_file(file)
            if processed_df is not None:
                combined_data.append(processed_df)
                st.sidebar.success(f"✅ {file.name} - OK")
        
        if combined_data:
            main_df = pd.concat(combined_data, ignore_index=True)

# ==========================================
# 3. DASHBOARD UI UTAMA
# ==========================================

if main_df is not None:
    # --- PRE-CALCULATION ---
    main_df['ROAS'] = main_df['Revenue'] / main_df['Spend']
    main_df['CPA'] = main_df['Spend'] / main_df['Conversions']
    main_df['CTR'] = (main_df['Clicks'] / main_df['Impressions']) * 100
    
    # Filter Date Range
    col_date1, col_date2 = st.columns([3, 1])
    with col_date1:
        st.title("🚀 DB Klik - Marketing Command Center")
    with col_date2:
        st.markdown(f"**Data Updated:**\n{datetime.now().strftime('%d %b %Y %H:%M')}")

    st.markdown("---")

    # --- A. SCORECARDS (KPI) ---
    tot_spend = main_df['Spend'].sum()
    tot_rev = main_df['Revenue'].sum()
    avg_roas = tot_rev / tot_spend if tot_spend > 0 else 0
    tot_click = main_df['Clicks'].sum()
    tot_conv = main_df['Conversions'].sum()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Ad Spend", f"Rp {tot_spend:,.0f}", help="Total biaya yang dikeluarkan untuk iklan")
    kpi2.metric("Total Revenue", f"Rp {tot_rev:,.0f}", help="Total omzet dari hasil iklan")
    kpi3.metric("ROAS (Efisiensi)", f"{avg_roas:.2f}x", delta="Target: >10x", delta_color="normal")
    kpi4.metric("Conversion Rate", f"{(tot_conv/tot_click)*100:.2f}%", f"{tot_conv} Sales")

    # --- B. TABS ANALISIS ---
    tab1, tab2, tab3 = st.tabs(["📈 Overview & Tren", "⚖️ Komparasi Platform", "🌪️ Funnel & Detail"])

    with tab1:
        st.subheader("Tren Performa Harian")
        
        daily_trend = main_df.groupby('Date')[['Spend', 'Revenue']].sum().reset_index()
        
        # Grafik Dual Axis (Spend vs Revenue)
        fig_dual = go.Figure()
        
        # Bar untuk Spend
        fig_dual.add_trace(go.Bar(
            x=daily_trend['Date'], y=daily_trend['Spend'],
            name='Cost (Biaya)', marker_color='rgba(239, 85, 59, 0.6)', yaxis='y'
        ))
        
        # Line untuk Revenue
        fig_dual.add_trace(go.Scatter(
            x=daily_trend['Date'], y=daily_trend['Revenue'],
            name='Revenue (Omzet)', line=dict(color='#00CC96', width=3), yaxis='y2'
        ))

        fig_dual.update_layout(
            title="Korelasi Biaya Iklan vs Omzet",
            yaxis=dict(title="Biaya Iklan (Rp)", side="left", showgrid=False),
            yaxis2=dict(title="Omzet (Rp)", side="right", overlaying="y", showgrid=True),
            template="plotly_white",
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        
        platform_summary = main_df.groupby('Platform')[['Spend', 'Revenue', 'ROAS']].sum().reset_index()
        platform_summary['ROAS'] = platform_summary['Revenue'] / platform_summary['Spend']
        
        with c1:
            st.subheader("Efisiensi ROAS per Platform")
            fig_roas = px.bar(
                platform_summary, x='Platform', y='ROAS', color='Platform',
                text_auto='.2f', color_discrete_map={
                    'Google Ads': '#4285F4', 
                    'Meta Ads (Internal)': '#E1306C', 
                    'Meta Ads (Agency)': '#833AB4'
                }
            )
            fig_roas.update_layout(showlegend=False)
            st.plotly_chart(fig_roas, use_container_width=True)
            
        with c2:
            st.subheader("Porsi Pengeluaran (Share of Spend)")
            fig_pie = px.donut(
                platform_summary, values='Spend', names='Platform', 
                hole=0.4, color='Platform',
                color_discrete_map={
                    'Google Ads': '#4285F4', 
                    'Meta Ads (Internal)': '#E1306C', 
                    'Meta Ads (Agency)': '#833AB4'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        c_funnel, c_bubble = st.columns([1, 2])
        
        with c_funnel:
            st.subheader("Marketing Funnel")
            # Aggregasi data funnel
            funnel_data = dict(
                number=[main_df['Impressions'].sum(), main_df['Clicks'].sum(), main_df['Conversions'].sum()],
                stage=["Impressions (Views)", "Clicks (Traffic)", "Conversions (Sales)"]
            )
            fig_funnel = px.funnel(funnel_data, x='number', y='stage')
            fig_funnel.update_traces(textinfo="value+percent previous")
            st.plotly_chart(fig_funnel, use_container_width=True)
            
        with c_bubble:
            st.subheader("Sebaran Performa Campaign")
            camp_perf = main_df.groupby(['Campaign', 'Platform'])[['Spend', 'Conversions', 'ROAS']].sum().reset_index()
            # Hapus data kosong biar grafik bersih
            camp_perf = camp_perf[camp_perf['Spend'] > 0]
            
            fig_bubble = px.scatter(
                camp_perf, x="Spend", y="Conversions",
                size="ROAS", color="Platform",
                hover_name="Campaign", log_x=True, size_max=40,
                title="Posisi Bubble makin ke KANAN ATAS = Makin Bagus"
            )
            st.plotly_chart(fig_bubble, use_container_width=True)

    # --- C. DATA MENTAH ---
    with st.expander("📂 Buka Data Mentah (Tabel Detail)"):
        st.dataframe(main_df.sort_values('Date', ascending=False).style.format({
            'Spend': 'Rp {:,.0f}', 'Revenue': 'Rp {:,.0f}', 'ROAS': '{:.2f}x', 'CTR': '{:.2f}%'
        }))

else:
    # Tampilan Halaman Depan (Landing Page Dashboard) saat belum ada data
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("👋 **Selamat Datang, Firman!**")
        st.markdown("""
        ### Dashboard ini belum menerima data.
        
        Anda berada di **Mode: {}**
        
        Silakan lakukan salah satu langkah berikut:
        1. Jika di **Mode CSV**: Upload file export di sidebar sebelah kiri.
        2. Jika di **Boss Mode**: Pastikan API Key sudah terpasang dan klik tombol Update.
        """.format(mode))
