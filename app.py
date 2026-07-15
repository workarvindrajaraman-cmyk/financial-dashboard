import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(
    page_title="CapEx Engine Pro", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- HYPER-MODERN CSS INJECTION (THE "REEL" LOOK) ---
css = """
<style>
#MainMenu {visibility: hidden;} 
footer {visibility: hidden;} 

/* Main App Background */
.stApp {
    background-color: #050505;
}

/* Custom Alert Box */
.terminal-box {
    background: linear-gradient(145deg, #09090b, #18181b);
    border: 1px solid #27272a;
    border-left: 4px solid #00e5ff;
    padding: 20px; 
    border-radius: 8px;
    color: #e4e4e7;
    font-size: 16px;
    box-shadow: 0 4px 20px rgba(0, 229, 255, 0.05);
    margin-bottom: 25px;
}

/* Glassmorphism KPI Cards */
.kpi-card {
    background: linear-gradient(180deg, #18181b 0%, #09090b 100%);
    border: 1px solid #27272a;
    border-radius: 12px;
    padding: 20px 15px;
    text-align: center;
    box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    transition: transform 0.2s ease-in-out;
}
.kpi-card:hover {
    transform: translateY(-5px);
    border-color: #00e5ff;
}
.kpi-title {
    color: #a1a1aa;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
    margin-bottom: 8px;
}
.kpi-value {
    color: #ffffff;
    font-size: 32px;
    font-weight: 800;
    margin: 0;
    text-shadow: 0 0 10px rgba(255,255,255,0.1);
}
.kpi-value.cyan { color: #00e5ff; text-shadow: 0 0 15px rgba(0,229,255,0.3); }
.kpi-value.emerald { color: #10b981; text-shadow: 0 0 15px rgba(16,185,129,0.3); }
.kpi-value.rose { color: #f43f5e; }

/* Styling Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 20px; }
.stTabs [data-baseweb="tab"] { 
    color: #71717a; font-weight: 600; font-size: 16px; background: transparent; 
}
.stTabs [data-baseweb="tab"][aria-selected="true"] { 
    color: #00e5ff !important; border-bottom-color: #00e5ff !important; 
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚡ CapEx Analytics")
    st.caption("Terminal v2.0 | Engineer-to-CFO Engine")
    st.divider()

    with st.expander("🌍 Macro & Financials", expanded=True):
        yrs = st.slider("Analysis Horizon (Yrs)", 3, 15, 10)
        wacc = st.number_input("WACC / Hurdle Rate (%)", value=12.0, step=0.5)
        tax = st.number_input("Corporate Tax Rate (%)", value=25.0, step=1.0)
        pwr_cost = st.number_input("Energy Cost (₹/kWh)", value=8.5, step=0.5)
        unit_px = st.number_input("Unit Sale Price (₹)", value=1500.0, step=50.0)
        demand = st.number_input("Annual Demand", value=100000, step=5000)

    with st.expander("🏚️ Scenario A: Old Machine"):
        old_salvage_L = st.number_input("Current Salvage (₹ Lakhs)", value=20.0, step=1.0)
        old_kwh = st.number_