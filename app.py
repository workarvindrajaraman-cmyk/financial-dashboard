import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Live Finance Dashboard", 
    page_icon="📈", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- SIMULATE LIVE DATA STATE ---
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now().strftime("%I:%M:%S %p")
if 'data_multiplier' not in st.session_state:
    st.session_state.data_multiplier = 1.0

# --- CSS INJECTION (MATCHING THE VIDEO AESTHETIC) ---
css = """
<style>
#MainMenu {visibility: hidden;} 
footer {visibility: hidden;} 
.stApp { background-color: #09090b; }

/* The Live Pulsing Indicator */
.header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.dash-title { color: #f4f4f5; font-size: 24px; font-weight: 700; margin: 0; }
.live-badge { display: flex; align-items: center; background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 12px; border-radius: 20px; color: #10b981; font-size: 12px; font-weight: 600; }
.pulse-dot { height: 8px; width: 8px; background-color: #10b981; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite; }
@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* KPI Cards */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
.kpi-card { background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 15px; display: flex; flex-direction: column; }
.kpi-label { color: #a1a1aa; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
.kpi-val { color: #f4f4f5; font-size: 28px; font-weight: 700; margin: 0; }
.kpi-sub { font-size: 12px; margin-top: 5px; }
.pos { color: #10b981; }
.neg { color: #f43f5e; }
.neut { color: #a1a1aa; }

/* Tables */
div[data-testid="stDataFrame"] > div > div > div > div { background-color: #18181b !important; border-radius: 8px; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- TOP HEADER ---
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.markdown("<h1 class='dash-title'>Finance Dashboard — Fin_database</h1>", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%;">
            <div class="live-badge">
                <div class="pulse-dot"></div>
                Live • Last updated: {st.session_state.last_update}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- REFRESH BUTTON (SIMULATES API CALL) ---
if st.button("🔄 Force Sync API Data", type="primary"):
    st.session_state.last_update = datetime.now().strftime("%I:%M:%S %p")
    st.session_state.data_multiplier *= np.random.uniform(0.98, 1.05) # Random flutter
    st.rerun()

# --- MOCK DATA GENERATION (Scaled by multiplier) ---
mult = st.session_state.data_multiplier

kpi_data = {
    "Total Revenue": {"val": f"${13.7 * mult:.1f}M", "sub": "From raw transactions", "stat": "neut"},
    "Gross Profit": {"val": f"${8.4 * mult:.1f}M", "sub": f"{(61.3 * mult):.1f}% margin", "stat": "pos"},
    "Marketing Spend": {"val": f"${2.1 * mult:.1f}M", "sub": "12 total channels", "stat": "neut"},
    "CAC": {"val": f"${41.8 / mult:.1f}K", "sub": "Cost per 2025 acquisition", "stat": "pos"},
    "Active Customers": {"val": int(97 * mult), "sub": "10.2% churn rate", "stat": "neg"},
    "Open Pipeline": {"val": f"${9.4 * mult:.1f}M", "sub": "Weighted by probability", "stat": "pos"},
    "Avg Resolution Time": {"val": f"{34.9 / mult:.1f} hours", "sub": "Support operations", "stat": "pos"},
    "Budget Variance": {"val": f"{-4.2 * mult:.1f}%", "sub": "Actual vs Budget Revenue", "stat": "neg"}
}

# --- RENDER KPI GRID ---
kpi_html = "<div class='kpi-grid'>"
for k, v in kpi_data.items():
    sub_class = "pos" if v['stat'] == 'pos' else "neg" if v['stat'] == 'neg' else "neut"
    kpi_html += f"""
        <div class="kpi-card">
            <div class="kpi-label">{k}</div>
            <div class="kpi-val">{v['val']}</div>
            <div class="kpi-sub {sub_class}">{v['sub']}</div>
        </div>
    """
kpi_html += "</div>"
st.markdown(kpi_html, unsafe_allow_html=True)


# --- CHART THEMES ---
CHART_THEME = dict(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#a1a1aa", size=11),
    margin=dict(t=30, b=20, l=20, r=20),
    xaxis=dict(showgrid=False, zeroline=False, linecolor="#27272a"),
    yaxis=dict(showgrid=True, gridcolor="#27272a", zeroline=False)
)

# --- ROW 1: MAIN CHARTS ---
c1, c2 = st.columns([2.5, 1])

with c1:
    st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Revenue vs COGS vs Gross Profit</div>", unsafe_allow_html=True)
    months = ["11/25", "12/25", "01/26", "02/26", "03/26", "04/26", "05/26", "06/26"]
    rev = [0.8, 0.9, 1.1, 1.0, 1.3, 1.5, 1.4, 1.7]
    cogs = [0.3, 0.35, 0.4, 0.4, 0.45, 0.5, 0.55, 0.6]
    gp = [r - c for r, c in zip(rev, cogs)]
    
    rev = [r * mult for r in rev]
    gp = [g * mult for g in gp]

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=months, y=rev, name="Revenue", line=dict(color="#3b82f6", width=3)))
    fig1.add_trace(go.Scatter(x=months, y=cogs, name="COGS", line=dict(color="#f43f5e", width=2, dash="dot")))
    fig1.add_trace(go.Scatter(x=months, y=gp, name="Gross Profit", fill='tozeroy', line=dict(color="#10b981", width=3), fillcolor="rgba(16, 185, 129, 0.1)"))
    fig1.update_layout(**CHART_THEME, height=300, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Revenue By Region</div>", unsafe_allow_html=True)
    regions = ["North America", "APAC", "Europe", "LATAM"]
    reg_vals = [55, 20, 15, 10]
    fig2 = go.Figure(go.Pie(labels=regions, values=reg_vals, hole=0.6, marker_colors=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]))
    fig2.update_layout(**CHART_THEME, height=300, showlegend=True, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig2, use_container_width=True)


# --- ROW 2: SUB CHARTS ---
c3, c4, c5 = st.columns(3)

with c3:
    st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Sales Pipeline by Stage</div>", unsafe_allow_html=True)
    stages = ["Lead", "Qualified", "Proposal", "Negotiation", "Closed Won"]
    vals = [4.5, 3.2, 2.1, 1.5, 4.8]
    vals = [v * mult for v in vals]
    fig3 = go.Figure(go.Bar(x=stages, y=vals, marker_color="#3b82f6"))
    fig3.update_layout(**CHART_THEME, height=250)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Marketing Spend vs Leads</div>", unsafe_allow_html=True)
    channels = ["Email", "Events", "Facebook", "Google Ads", "LinkedIn"]
    spend = [50, 120, 80, 200, 150]
    leads = [100, 300, 150, 400, 250]
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(x=channels, y=spend, name="Spend ($K)", marker_color="#f59e0b"))
    fig4.add_trace(go.Scatter(x=channels, y=leads, name="Leads", line=dict(color="#10b981", width=3), yaxis="y2"))
    fig4.update_layout(**CHART_THEME, height=250, yaxis2=dict(overlaying="y", side="right", showgrid=False))
    st.plotly_chart(fig4, use_container_width=True)

with c5:
    st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Support Tickets by Priority</div>", unsafe_allow_html=True)
    priority = ["Critical", "High", "Medium", "Low"]
    tickets = [12, 45, 120, 85]
    fig5 = go.Figure(go.Bar(x=priority, y=tickets, marker_color=["#f43f5e", "#f97316", "#3b82f6", "#10b981"]))
    fig5.update_layout(**CHART_THEME, height=250)
    st.plotly_chart(fig5, use_container_width=True)

# --- ROW 3: DATA TABLES ---
c6, c7 = st.columns(2)

with c6:
    st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Top Customers by Revenue</div>", unsafe_allow_html=True)
    df_cust = pd.DataFrame({
        "Customer": ["Zenith Software", "Kylem Labs", "Nova Networks", "Sapphire Logistics", "Harbor Aerospace"],
        "Segment": ["Enterprise", "Enterprise", "Mid-Market", "Enterprise", "Enterprise"],
        "Region": ["North America", "APAC", "Europe", "North America", "APAC"],
        "Revenue": [f"${889 * mult:.1f}K", f"${750 * mult:.1f}K", f"${645 * mult:.1f}K", f"${590 * mult:.1f}K", f"${553 * mult:.1f}K"]
    })
    st.dataframe(df_cust, use_container_width=True, hide_index=True)

with c7:
    st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Sales Rep Leaderboard</div>", unsafe_allow_html=True)
    df_reps = pd.DataFrame({
        "Rep": ["Casey Turner", "Jamie Davis", "Chris Wong", "Sam Chen", "Taylor Brooks"],
        "Deals Won": [12, 10, 9, 10, 8],
        "Revenue": [f"${3.9 * mult:.1f}M", f"${2.4 * mult:.1f}M", f"${1.7 * mult:.1f}M", f"${1.5 * mult:.1f}M", f"${1.1 * mult:.1f}M"]
    })
    st.dataframe(df_reps, use_container_width=True, hide_index=True)