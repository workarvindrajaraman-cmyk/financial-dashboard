import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Corporate Financial Engine", page_icon="📊", layout="wide")
st.markdown("""<style>.ai-box { background-color: #0e1117; border-left: 4px solid #00b050; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-style: italic; }</style>""", unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state['initialized'] = True

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Engine Controls")
    company_name = st.text_input("Company Name", placeholder="Enter Company Name...")
    unit = st.radio("Display Unit:", ["Crores", "Lakhs"], horizontal=True)
    uploaded_file = st.file_uploader("Upload Data (CSV/XLSX)", type=['csv', 'xlsx'])
    
    end_year = st.number_input("Last Actual Year", value=2023)
    forecast_years = st.slider("Forecast Horizon", 1, 10, 5)
    
    metrics = ["Revenue", "COGS", "S&G Expenses", "Depreciation", "Interest", "Current Assets", "Total Assets", "Current Liabilities", "Total Debt", "Total Equity", "Operating CF", "CapEx", "Financing CF", "Shares Outstanding"]
    hist_df = pd.DataFrame(0.0, index=metrics, columns=[f"{end_year-1}A", f"{end_year}A"])
    edited_hist_df = st.data_editor(hist_df, use_container_width=True)

# --- ENGINE ---
years = [f"{end_year-1}A", f"{end_year}A"] + [f"{end_year+i}F" for i in range(1, forecast_years+1)]
df = pd.DataFrame(index=metrics, columns=years)
df.update(edited_hist_df)

for i in range(forecast_years):
    y = years[2+i]
    prev = years[1+i]
    df.loc["Revenue", y] = df.loc["Revenue", prev] * 1.15
    df.loc["COGS", y] = df.loc["Revenue", y] * 0.3
    df.loc["Depreciation", y] = df.loc["Revenue", y] * 0.05
    df.loc["Total Debt", y] = max(df.loc["Total Debt", prev] - 1000, 0)
    df.loc["Total Equity", y] = df.loc["Total Equity", prev] * 1.08
    # Derived
    df.loc["Gross Profit", y] = df.loc["Revenue", y] - df.loc["COGS", y]
    df.loc["EBITDA", y] = df.loc["Gross Profit", y] - 5000 
    df.loc["Net Income", y] = (df.loc["EBITDA", y] - df.loc["Depreciation", y]) * 0.75
    df.loc["Free Cash Flow", y] = df.loc["Net Income", y] + df.loc["Depreciation", y] - (df.loc["Revenue", y] * 0.08)

# --- DASHBOARD ---
st.title(f"📈 {company_name or 'Corporate'} Analytics Suite")

# AI Summary
final_y = years[-1]
st.markdown(f"""<div class="ai-box"><strong>🤖 AI Analyst:</strong> Revenue growing to {unit} {df.loc['Revenue', final_y]:,.0f}. Intrinsic value driven by FCF efficiency.</div>""", unsafe_allow_html=True)

# Tabs
t1, t2, t3, t4 = st.tabs(["📑 Statements", "📊 Visuals", "💰 DCF Valuation", "📥 Export"])

with t1:
    st.dataframe(df.style.format("{:,.0f}"))

with t2:
    col1, col2 = st.columns(2)
    # Revenue Chart
    fig1 = px.bar(df.T.reset_index(), x='index', y='Revenue', title="Revenue Growth")
    col1.plotly_chart(fig1, use_container_width=True)
    # FCF Chart
    fig2 = px.line(df.T.reset_index(), x='index', y='Free Cash Flow', title="Free Cash Flow Projection")
    col2.plotly_chart(fig2, use_container_width=True)

with t3:
    st.write("DCF Valuation Summary")
    dcf = pd.DataFrame({"Metric": ["Enterprise Value", "Equity Value", "Share Price"], "Value": [50000, 45000, 450]})
    st.table(dcf)

with t4:
    st.write("Download your pro-forma report.")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as writer: df.to_excel(writer)
    st.download_button("Download Excel", buf.getvalue(), "Report.xlsx")
