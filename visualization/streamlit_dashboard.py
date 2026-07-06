import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from google.cloud import bigquery
import os

# Page Configuration
st.set_page_config(
    page_title="Daily Stock Monitoring",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS Interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap');

    :root {
        --bg-primary:   #0D0F14;
        --bg-card:      #151820;
        --bg-surface:   #1C2030;
        --gold:         #F5C842;
        --gold-dim:     #A8892E;
        --green:        #3DD68C;
        --red:          #F05A5A;
        --text-primary: #E8EAF0;
        --text-muted:   #7A7F96;
        --border:       #252A3A;
    }

    [data-testid="stSidebar"] .stRadio p {
        color: var(--text-primary) !important;
        font-size: 15px;
        transition: color 0.3s ease;
    }
    [data-testid="stSidebar"] .stRadio div[role="radio"][aria-checked="true"] p {
        color: var(--gold) !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    [data-testid="stSidebar"] .stRadio div[role="radio"]:hover p {
        color: #FFFFFF !important;
    }
            
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-primary) !important;
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    [data-testid="stSidebar"] {
        background-color: var(--bg-card) !important;
        border-right: 1px solid var(--border);
    }
    [data-testid="stHeader"] { background-color: var(--bg-primary) !important; }

    .hero {
        background: linear-gradient(135deg, #0D0F14 0%, #1a1f30 60%, #0D1628 100%);
        border: 1px solid var(--gold-dim);
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 200px; height: 200px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(245,200,66,0.12) 0%, transparent 70%);
    }
    .hero-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 28px;
        font-weight: 600;
        color: var(--gold);
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        font-size: 14px;
        color: var(--text-muted);
        margin-top: 6px;
        font-family: 'IBM Plex Mono', monospace;
    }
    .hero-ts {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        color: var(--gold);
        margin-top: 12px;
    }

    .kpi-row { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 18px 24px;
        flex: 1;
        min-width: 150px;
        position: relative;
    }
    .kpi-card::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0;
        width: 40%; height: 2px;
        background: var(--gold);
        border-radius: 0 0 0 10px;
    }
    .kpi-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 28px; font-weight: 600; color: var(--gold); margin-top: 4px; }
    .kpi-sub   { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

    .section-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
        font-weight: 600;
        color: var(--gold);
        text-transform: uppercase;
        letter-spacing: 2px;
        border-left: 3px solid var(--gold);
        padding-left: 12px;
        margin: 28px 0 16px;
    }

    .dataframe, [data-testid="stDataFrame"] {
        background: var(--bg-card) !important;
        border-radius: 8px;
    }

    hr { border-color: var(--border) !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown { color: var(--text-primary) !important; }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# Cache Control
def cache_control() -> str:
    now_time = datetime.datetime.now()
    refresh_time = now_time.replace(hour=7, minute=0, second=0, microsecond=0)
    if now_time < refresh_time:
        valid_date = (now_time - datetime.timedelta(days=1)).date()
    else:
        valid_date = now_time.date()
    return f"Latest Update {valid_date}"

# BigQuery Connection
KEY_PATH = r"C:\Users\DELL\Portfolio\Stock Pipeline\visualization\streamlit_dashboard.json"

@st.cache_data(show_spinner=False)
def load_data_from_bq(cache_key: str):
    if os.path.exists(KEY_PATH):
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
    else:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        
    client = bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )

    query_prediksi = """
        SELECT *
        FROM `daily-stock-monitoring.clean_stock_data.stock_screening`
        WHERE Date = (SELECT MAX(Date) FROM `daily-stock-monitoring.clean_stock_data.stock_screening`)
    """

    query_fundamental = """
        SELECT *
        FROM `daily-stock-monitoring.clean_stock_data.transformed_stock_dashboard`
        WHERE Extraction_Date = (SELECT MAX(Extraction_Date) FROM `daily-stock-monitoring.clean_stock_data.transformed_stock_dashboard`)
    """

    df_p = client.query(query_prediksi).to_dataframe()
    df_f = client.query(query_fundamental).to_dataframe()
    return df_p, df_f

# Load Data
cache_key = cache_control()

with st.spinner("🔄 Getting data from BigQuery..."):
    try:
        df_pred_raw, df_fund_raw = load_data_from_bq(cache_key)
    except Exception as e:
        st.error(f"Connection Failed to BigQuery: {e}")
        st.stop()

# ==========================================
# PREPROCESSING & MERGING EFEKTIF
# ==========================================
if not df_pred_raw.empty and "Date" in df_pred_raw.columns:
    try:
        raw_date = pd.to_datetime(df_pred_raw["Date"].iloc[0])
        latest_available_date = raw_date.strftime("%Y-%m-%d")
    except:
        latest_available_date = str(df_pred_raw["Date"].iloc[0])
else:
    latest_available_date = datetime.datetime.now().strftime("%Y-%m-%d")

df_fund_clean = df_fund_raw.drop(columns=["Extraction_Date"], errors="ignore")

# Join Table
df_main = df_fund_clean.merge(df_pred_raw, on="Ticker", how="outer")

# Missing Value Handle
df_main["Prediction"] = df_main["Prediction"].fillna(0)
df_main["Probability"] = df_main["Probability"].fillna(0)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Filter & Navigation")
    st.markdown("---")

    page = st.radio(
        "Page",
        ["🏠 Overview", "📊 Stock Screening", "🔬 Fundamental Analysis",  "🔗 Combined View"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    sectors = ["All"] + sorted(df_main["Sector"].dropna().unique().tolist()) if "Sector" in df_main.columns else ["All"]
    selected_sector = st.selectbox("Sector", sectors)

    min_prob = st.slider("Min. Potential Probability", 0.40, 0.99, 0.60, 0.01)
    min_score = st.slider("Min. Fundamental Score", 0, 100, 40, 5)

    st.markdown("---")
    st.markdown(f"<small style='color:#7A7F96'>Cache key: `{cache_key}`</small>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Manually"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# APPLY GLOBAL FILTERS
# ==========================================
df_filtered = df_main.copy()

if selected_sector != "All":
    df_filtered = df_filtered[df_filtered["Sector"] == selected_sector]

df_filtered = df_filtered[
    ((df_filtered["Fundamental_Score"] >= min_score) | (df_filtered["Fundamental_Score"].isna())) &
    ((df_filtered["Prediction"] == 0) | (df_filtered["Probability"] >= min_prob))
]

# Header
st.markdown(f"""
<div class="hero">
    <p class="hero-title">📈 Daily Stock Monitoring</p>
    <p class="hero-sub">Stock Screening & Fundamental Analysis of Dow Jones Industrial Average Stocks</p>
    <p class="hero-ts">⏱ Latest Available Data is {latest_available_date}</p>
</div>
""", unsafe_allow_html=True)


# ==========================================
# PAGE 1: OVERVIEW
# ==========================================
if page == "🏠 Overview":

    # Semua metric sekarang menggunakan df_filtered
    n_potential   = len(df_filtered[df_filtered["Prediction"] == 1])
    strong_stocks = len(df_filtered[df_filtered["Fundamental_Score"] >= 25])
    both_good     = len(df_filtered[(df_filtered["Prediction"] == 1) & (df_filtered["Fundamental_Score"] >= 60)])

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">Potential Stocks</div>
            <div class="kpi-value">{n_potential}</div>
            <div class="kpi-sub">From {len(df_filtered)} Stocks (Probability >50%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Strong Fundamental</div>
            <div class="kpi-value">{strong_stocks}</div>
            <div class="kpi-sub">Minimum 25 from 100 Points</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Strong Buy</div>
            <div class="kpi-value">{both_good}</div>
            <div class="kpi-sub">Potential & Strong Fundamental Stocks</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Valuation Map
    st.markdown('<div class="section-header">Valuation Map by Forward P/E vs ROE</div>', unsafe_allow_html=True)
    df_bubble = df_filtered.dropna(subset=["Forward_PE", "Market_Cap", "ROE", "Fundamental_Score"]).copy()
    df_bubble["Signal"] = df_bubble["Prediction"].map({1: "Potential", 0: "Non Potential"})

    fig_bubble = px.scatter(
        df_bubble, x="Forward_PE", y="ROE", size="Fundamental_Score", color="Signal", text="Ticker",
        hover_data=["Company_Name", "Sector", "Fundamental_Score", "Market_Cap"],
        color_discrete_map={"Potential": "#F5C842", "Non Potential": "#3b4a6b"}, size_max=45
    )
    fig_bubble.update_traces(textposition="top center", textfont_size=9)
    fig_bubble.update_layout(
        plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#E8EAF0", height=460,
        xaxis=dict(gridcolor="#252A3A", title="Forward P/E"), yaxis=dict(gridcolor="#252A3A", title="ROE (%)"),
        legend=dict(bgcolor="#1C2030", font=dict(color="#F5C842"))
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown('<div class="section-header">Top Fundamental Score</div>', unsafe_allow_html=True)
        top15 = df_filtered.nlargest(15, "Fundamental_Score").sort_values("Fundamental_Score")
        colors = ["#F5C842" if p == 1 else "#3b4a6b" for p in top15["Prediction"]]
        
        fig_bar = go.Figure(go.Bar(
            x=top15["Fundamental_Score"], y=top15["Ticker"], orientation="h", 
            marker_color=colors, text=top15["Fundamental_Score"].astype(str), textposition="outside"
        ))
        fig_bar.update_layout(
            plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#E8EAF0", height=380,
            xaxis=dict(range=[0, 105], gridcolor="#252A3A"), yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            margin=dict(l=60, r=40, t=20, b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Sector Distribution</div>', unsafe_allow_html=True)
        sector_counts = df_filtered.groupby("Sector")["Fundamental_Score"].mean().sort_values(ascending=False)
        sector_counts.index = sector_counts.index.astype(str).str.replace(" ", "<br>")
        
        fig_pie = px.pie(names=sector_counts.index, values=sector_counts.values, hole=0.45, color_discrete_sequence=px.colors.sequential.Plasma)
        fig_pie.update_layout(
            plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#E8EAF0", height=380,
            legend=dict(bgcolor="#1C2030", font=dict(color="#F5C842")), margin=dict(l=10, r=10, t=20, b=10)
        )
        fig_pie.update_traces(textinfo="label+percent")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown('<div class="section-header">🌟 Strong Buy — Potential & Strong Fundamental Stocks</div>', unsafe_allow_html=True)
    df_strong = df_filtered[(df_filtered["Prediction"] == 1) & (df_filtered["Fundamental_Score"] >= 60)].sort_values("Fundamental_Score", ascending=False)

    if df_strong.empty:
        st.info("No stock fitted with criteria.")
    else:
        cols_show = [c for c in ["Ticker","Company_Name","Sector","Fundamental_Score","Probability","ROE","Profit_Margin","Forward_PE","Valuation_Category"] if c in df_strong.columns]
        st.dataframe(
            df_strong[cols_show].style
                .background_gradient(subset=["Fundamental_Score"], cmap="YlOrBr")
                .format({"Probability": "{:.1%}", "Fundamental_Score": "{:.0f}", "ROE": "{:.1f}%", "Profit_Margin": "{:.1f}%", "Forward_PE": "{:.1f}x"}),
            use_container_width=True, hide_index=True,
        )

# ==========================================
# PAGE 2: STOCK SCREENING
# ==========================================
elif page == "📊 Stock Screening":
    
    df_show = df_filtered.dropna(subset=["Probability"]).copy()
    df_show["Chart_Label"] = df_show["Prediction"].map({1: "Potential", 0: "Non Potential"})

    col_hist, col_donut, col_table = st.columns(3)
    with col_hist:
        st.markdown('<div class="section-header">Potential Probability Distribution</div>', unsafe_allow_html=True)
        fig_hist = px.histogram(
            df_show, x="Probability", nbins=20, color="Chart_Label",
            color_discrete_map={"Potential": "#F5C842", "Non Potential": "#3b4a6b"}, barmode="overlay", opacity=0.8
        )
        fig_hist.update_layout(
            plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#E8EAF0", height=350,
            xaxis=dict(tickformat=".0%", gridcolor="#252A3A"), yaxis=dict(gridcolor="#252A3A"),
            showlegend=False, margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_donut:
        st.markdown('<div class="section-header">Signal Distribution</div>', unsafe_allow_html=True)
        signal_counts = df_show["Chart_Label"].value_counts()
        fig_donut = go.Figure(go.Pie(
            labels=["Potential", "Non Potential"],
            values=[signal_counts.get("Potential", 0), signal_counts.get("Non Potential", 0)],
            hole=0.55, marker_colors=["#F5C842", "#3b4a6b"], rotation=0, direction='clockwise', sort=False
        ))
        fig_donut.update_layout(
            plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#E8EAF0", height=350, 
            legend=dict(bgcolor="#1C2030", font=dict(color="#F5C842"), orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_table:
        st.markdown('<div class="section-header">Prediction Table</div>', unsafe_allow_html=True)
        display_pred = df_show[["Ticker", "Chart_Label", "Probability"]].rename(columns={"Chart_Label": "Signal"})
        display_pred["Probability (%)"] = display_pred["Probability"] * 100
        
        st.dataframe(
            display_pred[["Ticker", "Signal", "Probability (%)"]].style.format({"Probability (%)": "{:.2f}"}),
            use_container_width=True, hide_index=True, height=350
        )

# ==========================================
# PAGE 3: FUNDAMENTAL ANALYSIS
# ==========================================
elif page == "🔬 Fundamental Analysis":

    st.markdown('<div class="section-header">DJIA Fundamental</div>', unsafe_allow_html=True)

    metric_groups = {
        "Profitability": ["ROE","ROA","Gross_Margin","Operating_Margin","Profit_Margin"],
        "Valuation":     ["Trailing_PE","Forward_PE","Price_to_Book","PEG_Ratio","EV_to_EBITDA"],
        "Liquidity":     ["Current_Ratio","Quick_Ratio","Debt_to_Equity","Cash_per_Share"],
        "Growth":        ["Revenue_Growth","Earnings_Growth","Fifty_Two_Week_Change"],
        "Risk":          ["Beta","Short_Ratio"],
    }
    selected_group = st.selectbox("Metrics Group", list(metric_groups.keys()))
    metrics = [m for m in metric_groups[selected_group] if m in df_filtered.columns]

    df_heat = df_filtered[["Ticker"] + metrics].set_index("Ticker")
    fig_heat = px.imshow(df_heat.T, color_continuous_scale="RdYlGn", aspect="auto", title=f"Heatmap {selected_group}")
    fig_heat.update_layout(
        plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#E8EAF0", height=max(450, len(metrics) * 60), 
        coloraxis_colorbar=dict(tickfont=dict(color="#E8EAF0")), margin=dict(l=10, r=10, t=40, b=80) 
    )
    fig_heat.update_xaxes(tickangle=45, dtick=1)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<div class="section-header">Radar Chart Comparison</div>', unsafe_allow_html=True)
    radar_tickers = st.multiselect(
        "Choose 2-6 stocks to compare",
        df_filtered["Ticker"].tolist(),
        default=df_filtered.nlargest(4, "Fundamental_Score")["Ticker"].tolist()[:4],
    )
    radar_metrics  = [m for m in ["ROE","Gross_Margin","Profit_Margin","Revenue_Growth","Fundamental_Score"] if m in df_filtered.columns]

    if radar_tickers and len(radar_tickers) >= 2:
        df_radar = df_filtered[df_filtered["Ticker"].isin(radar_tickers)][["Ticker"] + radar_metrics]
        
        for col in radar_metrics:
            mn, mx = df_filtered[col].min(), df_filtered[col].max()
            df_radar[col] = ((df_radar[col] - mn) / (mx - mn + 1e-9) * 100).round(1)

        clean_metrics = [m.replace("_", " ") for m in radar_metrics]
        fig_radar = go.Figure()
        palette = ["#F5C842","#3DD68C","#F05A5A","#60A5FA","#C084FC","#FB923C"]
        
        for i, row in df_radar.iterrows():
            vals = row[radar_metrics].tolist()
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=clean_metrics + [clean_metrics[0]], name=row["Ticker"],
                fill="toself", opacity=0.6, line_color=palette[i % len(palette)],
            ))
            
        fig_radar.update_layout(
            polar=dict(bgcolor="#1C2030", radialaxis=dict(visible=True, range=[0, 100], gridcolor="#252A3A"), angularaxis=dict(gridcolor="#252A3A")),
            paper_bgcolor="#151820", font_color="#E8EAF0", legend=dict(bgcolor="#1C2030", font=dict(color="#F5C842")), height=420,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown('<div class="section-header">Fundamental Data</div>', unsafe_allow_html=True)
    df_display = df_filtered.drop(columns=["Prediction", "Probability", "Company_Name", "Sector", "Date"], errors="ignore").copy()
    df_display = df_display.rename(columns=lambda x: str(x).replace("_", " "))
    
    fmt_cols = {c: "{:.2f}" for c in df_display.select_dtypes(include=["float"]).columns}
    if "Market Cap" in df_display.columns: fmt_cols["Market Cap"] = "{:,.0f}"

    st.dataframe(
        df_display.style.background_gradient(subset=["Fundamental Score"], cmap="YlOrBr").format(fmt_cols),
        use_container_width=True, hide_index=True, height=420,
    )

# ==========================================
# PAGE 4: COMBINED VIEW
# ==========================================
elif page == "🔗 Combined View":

    st.markdown('<div class="section-header">Potential Probability vs Fundamental Score</div>', unsafe_allow_html=True)

    df_plot = df_filtered.copy()
    df_plot["Category"] = df_plot.apply(
        lambda r: "🌟 Strong Buy" if r["Prediction"] == 1 and r["Fundamental_Score"] >= 60
        else ("⭐ Potential" if r["Prediction"] == 1
              else ("💎 Fundamental Strong" if r["Fundamental_Score"] >= 70 else "⬜ Watch List")), axis=1
    )

    color_map = {"🌟 Strong Buy": "#F5C842", "⭐ Potential": "#3DD68C", "💎 Fundamental Strong": "#60A5FA", "⬜ Watch List": "#3b4a6b"}
    df_plot["Category_Chart"] = df_plot["Category"].str.extract(r' (.*)')[0]
    color_map_chart = {k.split(' ', 1)[1]: v for k, v in color_map.items()}

    df_plot_2d = df_plot.dropna(subset=["Market_Cap"]).copy()
    df_plot_2d["Market_Cap"] = pd.to_numeric(df_plot_2d["Market_Cap"], errors="coerce")
    
    fig_2d = px.scatter(
        df_plot_2d.dropna(subset=["Market_Cap"]), x="Probability", y="Fundamental_Score", color="Category_Chart",
        color_discrete_map=color_map_chart, text="Ticker", size="Market_Cap", size_max=40,
        hover_data=["Company_Name","Sector","ROE","Forward_PE"], title="Market Cap Bubble"
    )
    
    fig_2d.add_hline(y=25, line_dash="dot", line_color="#7A7F96")
    fig_2d.add_vline(x=0.5, line_dash="dot", line_color="#7A7F96")
    fig_2d.add_shape(type="rect", x0=0.5, y0=60, x1=1.05, y1=105, fillcolor="rgba(245,200,66,0.05)", line_width=0)
    fig_2d.update_traces(textposition="top center", textfont_size=9)
    fig_2d.update_layout(
        plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#E8EAF0", height=500,
        xaxis=dict(tickformat=".0%", gridcolor="#252A3A", range=[0.3, 1.05]), yaxis=dict(gridcolor="#252A3A", range=[0, 105]),
        legend=dict(bgcolor="#1C2030", font=dict(color="#F5C842"))
    )
    st.plotly_chart(fig_2d, use_container_width=True)

    st.markdown('<div class="section-header">Quadrant Summary</div>', unsafe_allow_html=True)
    q_cols = st.columns(4)
    for i, (cat, color) in enumerate(color_map.items()):
        subset = df_plot[df_plot["Category"] == cat]
        tickers = ', '.join(subset['Ticker'].head(4).tolist()) or "&nbsp;"
        display_color = "#E8EAF0" if color == "#3b4a6b" else color
        
        q_cols[i].markdown(f"""
        <div class="kpi-card" style="height: 120px; display: flex; flex-direction: column; justify-content: space-between;">
            <div><div class="kpi-label" style="color: {display_color} !important;">{cat}</div>
            <div class="kpi-value" style="color: {display_color} !important;">{len(subset)}</div></div>
            <div class="kpi-sub">{tickers}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Integrated Table</div>', unsafe_allow_html=True)
    cols_show = [c for c in ["Ticker","Company_Name","Category","Probability","Fundamental_Score","ROE","Profit_Margin","Forward_PE","Revenue_Growth","Debt_to_Equity","Valuation_Category"] if c in df_plot.columns]
    
    df_table = df_plot[cols_show].sort_values(["Category","Fundamental_Score"], ascending=[True, False]).copy()
    df_table = df_table.rename(columns=lambda x: str(x).replace("_", " "))

    st.dataframe(
        df_table.style.background_gradient(subset=["Fundamental Score"], cmap="YlOrBr")
            .format({"Probability": "{:.1%}", "Fundamental Score": "{:.0f}", "ROE": "{:.1f}%", "Profit Margin": "{:.1f}%", "Forward PE": "{:.1f}x", "Revenue Growth": "{:.1f}%", "Debt to Equity": "{:.2f}"}),
        use_container_width=True, hide_index=True, height=450,
    )

    st.markdown('<div class="section-header">Growth vs Profitability</div>', unsafe_allow_html=True)
    df_gp = df_plot.dropna(subset=["Revenue_Growth", "Profit_Margin", "Fundamental_Score"]).copy()

    fig_gp = px.scatter(
        df_gp, x="Revenue_Growth", y="Profit_Margin", color="Category_Chart", color_discrete_map=color_map_chart,
        text="Ticker", size="Fundamental_Score", size_max=35, hover_data=["Company_Name","Earnings_Growth","ROE"]
    )
    fig_gp.add_hline(y=0, line_color="#252A3A")
    fig_gp.add_vline(x=0, line_color="#252A3A")
    fig_gp.update_traces(textposition="top center", textfont_size=9)
    fig_gp.update_layout(
        plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#E8EAF0", height=420,
        xaxis=dict(gridcolor="#252A3A", title="Revenue Growth (%)"), yaxis=dict(gridcolor="#252A3A", title="Profit Margin (%)"),
        legend=dict(bgcolor="#1C2030", font=dict(color="#F5C842"))
    )
    st.plotly_chart(fig_gp, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#7A7F96;font-size:12px;font-family:monospace;line-height:1.6'>"
    "RY Analytics House<br>"
    "Data from Yahoo Finance | Updated Every 07.00 WIB"
    "</p>",
    unsafe_allow_html=True,
)