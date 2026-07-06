import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go

# --- DASHBOARD CONFIGURATION ---
st.set_page_config(page_title="Corporate Financial Engine", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# FORCE MEMORY WIPE ON FIRST LOAD
if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state['initialized'] = True

# Custom Enterprise-Grade Styling
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    thead tr th { background-color: #00b050 !important; color: white !important; font-weight: bold !important; font-size: 14px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; font-size: 16px; font-weight: 600; color: #94a3b8; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #00b050 !important; border-bottom-color: #00b050 !important; }
    div[data-testid="stMetricValue"] { color: #00b050; }
    div.stButton > button:first-child, div.stDownloadButton > button:first-child { background-color: #00b050 !important; color: white !important; border: none !important; }
    .ai-box { background-color: #0e1117; border-left: 4px solid #00b050; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# --- PORTFOLIO BRANDING ---
with st.sidebar:
    st.markdown("### 🏢 Analyst Portfolio")
    st.caption("Developed by: **Arvind Rajaraman**")
    st.divider()

if st.sidebar.button("➕ Start New Model (Clear Data)", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# --- SIDEBAR: DATA UPLOAD & CONTROLS ---
with st.sidebar:
    st.header("🎛️ Engine Controls")
    company_name = st.text_input("Company Name", value="", placeholder="Enter Company Name...")
    unit = st.radio("Display Unit:", ["Crores", "Lakhs", "Millions"], index=0, horizontal=True)
    
    st.divider()
    st.subheader("📁 Data Ingestion")
    uploaded_file = st.file_uploader("Upload Financial Statements", type=['csv', 'xlsx'], help="Upload historical data to bypass manual entry.")
    
    with st.expander("⏳ Timeline Settings", expanded=True):
        t1, t2 = st.columns(2)
        end_hist_year = t1.number_input("Last Actual Year", value=2023, step=1)
        hist_years_count = t2.number_input("Actual Years", min_value=1, max_value=10, value=2, step=1)
        forecast_years = st.slider("Forecast Horizon", min_value=1, max_value=10, value=5)
    
    hist_years_list = [f"{end_hist_year - hist_years_count + 1 + i}A" for i in range(hist_years_count)]
    
    # Initialize Default Financial Matrix with Zeros
    metrics = [
        "Revenue", "COGS", "S&G Expenses", "Depreciation", "Interest", 
        "Current Assets", "Total Assets", "Current Liabilities", "Total Debt", "Total Equity",
        "Operating CF", "CapEx", "Financing CF", "Shares Outstanding"
    ]
    default_data = {"Metric": metrics}
    for y in hist_years_list:
        default_data[y] = [0.0]*len(metrics)
            
    hist_df_template = pd.DataFrame(default_data).set_index("Metric")
    
    # Handle Upload vs Manual
    if uploaded_file is not None:
        try:
            hist_df = pd.read_csv(uploaded_file, index_col=0) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, index_col=0)
            st.success("Data successfully loaded!")
        except Exception:
            st.error("Format error. Using manual input.")
            hist_df = hist_df_template
    else:
        hist_df = hist_df_template

    with st.expander("🏢 Historical Actuals (Editor)", expanded=(uploaded_file is None)):
        edited_hist_df = st.data_editor(hist_df, use_container_width=True)

    with st.expander("📈 Forecasting & DCF Assumptions"):
        rev_growth_input = st.number_input("Forecast Revenue Growth (%)", value=15.0, step=1.0)
        cogs_percent_input = st.number_input("Forecast COGS % of Revenue", value=30.0, step=1.0)
        tax_input = st.number_input("Forecast Taxes (%)", value=25.0, step=1.0)
        wacc_input = st.number_input("WACC (Discount Rate %)", value=10.0, step=0.5)
        tg_input = st.number_input("Terminal Growth Rate (%)", value=2.5, step=0.1)

# --- FINANCIAL ENGINE CORE ---
years = hist_years_list + [f"{end_hist_year + i}F" for i in range(1, forecast_years + 1)]
df_master = pd.DataFrame(index=metrics, columns=years)
df_master.update(edited_hist_df)

# Forecasting Logic
for i in range(forecast_years):
    prev_y = years[len(hist_years_list) + i - 1]
    curr_y = years[len(hist_years_list) + i]
    
    df_master.loc["Revenue", curr_y] = df_master.loc["Revenue", prev_y] * (1 + rev_growth_input/100)
    df_master.loc["COGS", curr_y] = df_master.loc["Revenue", curr_y] * (cogs_percent_input/100)
    df_master.loc["S&G Expenses", curr_y] = df_master.loc["S&G Expenses", prev_y] * 1.05 
    df_master.loc["Depreciation", curr_y] = df_master.loc["Revenue", curr_y] * 0.05
    df_master.loc["Interest", curr_y] = df_master.loc["Interest", prev_y]
    df_master.loc["Total Assets", curr_y] = df_master.loc["Total Assets", prev_y] * 1.05
    df_master.loc["Total Debt", curr_y] = max(df_master.loc["Total Debt", prev_y] - 1000, 0)
    df_master.loc["Total Equity", curr_y] = df_master.loc["Total Equity", prev_y] * 1.08
    df_master.loc["Current Assets", curr_y] = df_master.loc["Total Assets", curr_y] * 0.3
    df_master.loc["Current Liabilities", curr_y] = df_master.loc["Current Liabilities", prev_y] * 1.02
    df_master.loc["CapEx", curr_y] = -df_master.loc["Revenue", curr_y] * 0.08
    df_master.loc["Shares Outstanding", curr_y] = df_master.loc["Shares Outstanding", prev_y]

# Calculate Derived Lines
df_master.loc["Gross Profit"] = df_master.loc["Revenue"] - df_master.loc["COGS"]
df_master.loc["EBITDA"] = df_master.loc["Gross Profit"] - df_master.loc["S&G Expenses"]
df_master.loc["EBIT"] = df_master.loc["EBITDA"] - df_master.loc["Depreciation"]
df_master.loc["EBT"] = df_master.loc["EBIT"] - df_master.loc["Interest"]
df_master.loc["Tax"] = df_master.loc["EBT"] * (tax_input/100)
df_master.loc["Net Income"] = df_master.loc["EBT"] - df_master.loc["Tax"]
df_master.loc["Operating CF"] = df_master.loc["Net Income"] + df_master.loc["Depreciation"]
df_master.loc["Free Cash Flow"] = df_master.loc["Operating CF"] + df_master.loc["CapEx"]
df_master.loc["Financing CF"] = df_master.loc["Total Debt"].diff().fillna(0)
df_master.loc["Net Cash Flow"] = df_master.loc["Operating CF"] + df_master.loc["CapEx"] + df_master.loc["Financing CF"]

# Advanced KPIs
kpi_df = pd.DataFrame(columns=years)
def safe_divide(a, b): return (a / b) if b and b != 0 else 0.0

for y in years:
    kpi_df.loc["ROE (%)", y] = safe_divide(df_master.loc["Net Income", y], df_master.loc["Total Equity", y]) * 100
    kpi_df.loc["ROCE (%)", y] = safe_divide(df_master.loc["EBIT", y], (df_master.loc["Total Assets", y] - df_master.loc["Current Liabilities", y])) * 100
    kpi_df.loc["EPS", y] = safe_divide(df_master.loc["Net Income", y], df_master.loc["Shares Outstanding", y])
    kpi_df.loc["Current Ratio", y] = safe_divide(df_master.loc["Current Assets", y], df_master.loc["Current Liabilities", y])
    kpi_df.loc["Debt to Equity", y] = safe_divide(df_master.loc["Total Debt", y], df_master.loc["Total Equity", y])
    kpi_df.loc["EBITDA Margin (%)", y] = safe_divide(df_master.loc["EBITDA", y], df_master.loc["Revenue", y]) * 100

# DCF Valuation Logic
forecast_fcf = df_master.loc["Free Cash Flow", [y for y in years if "F" in y]].astype(float)
discount_factors = [(1 + wacc_input/100)**(i+1) for i in range(forecast_years)]
pv_fcf = sum([fcf / df for fcf, df in zip(forecast_fcf, discount_factors)])
denominator = ((wacc_input/100) - (tg_input/100))
terminal_value = (forecast_fcf.iloc[-1] * (1 + tg_input/100)) / denominator if denominator != 0 else 0
pv_tv = terminal_value / discount_factors[-1] if discount_factors else 0
enterprise_value = pv_fcf + pv_tv
equity_value = enterprise_value - df_master.loc["Total Debt", hist_years_list[-1]] + df_master.loc["Current Assets", hist_years_list[-1]] 
implied_share_price = safe_divide(equity_value, df_master.loc["Shares Outstanding", hist_years_list[-1]])

# --- UI DISPLAY ---
display_name = company_name if company_name else "New Model"
st.title(f"📈 {display_name} Corporate Analytics & Valuation Suite")

# AI Analyst Summary
final_yr = years[-1]
base_yr = hist_years_list[-1]
st.markdown(f"""
    <div class="ai-box">
        <strong>🤖 AI Analyst Summary:</strong><br>
        Revenue is forecast to grow at an average rate of {rev_growth_input}%, driving top-line from {unit} {df_master.loc['Revenue', base_yr]:,.1f} to {unit} {df_master.loc['Revenue', final_yr]:,.1f} by {final_yr}. 
        EBITDA margins are projected to shift from {kpi_df.loc['EBITDA Margin (%)', base_yr]:.1f}% to {kpi_df.loc['EBITDA Margin (%)', final_yr]:.1f}%. 
        Based on the DCF valuation (WACC: {wacc_input}%, Terminal Growth: {tg_input}%), the implied Enterprise Value is <strong>{unit} {enterprise_value:,.1f}</strong>, 
        yielding an intrinsic share price of <strong>{unit} {implied_share_price:,.2f}</strong>. Overall financial structure indicates a Debt/Equity ratio shifting to {kpi_df.loc['Debt to Equity', final_yr]:.2f}.
    </div>
""", unsafe_allow_html=True)

# Main KPIs
st.subheader("Key Performance Indicators")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric(f"Rev ({final_yr})", f"{df_master.loc['Revenue', final_yr]:,.0f}")
k2.metric(f"EBITDA ({final_yr})", f"{df_master.loc['EBITDA', final_yr]:,.0f}")
k3.metric("Terminal ROE", f"{kpi_df.loc['ROE (%)', final_yr]:.1f}%")
k4.metric("Free Cash Flow", f"{df_master.loc['Free Cash Flow', final_yr]:,.0f}")
k5.metric("Enterprise Value", f"{enterprise_value:,.0f}")
k6.metric("Implied Share Px", f"{implied_share_price:,.2f}")

st.divider()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📑 Master Statements", "📊 Advanced KPIs", "💰 DCF Valuation", "🔬 Download & Exports"])

def format_df(df): return df.style.format("{:,.1f}", na_rep="")

with tab1:
    st.subheader("Income Statement")
    st.dataframe(format_df(df_master.loc[["Revenue", "COGS", "Gross Profit", "S&G Expenses", "EBITDA", "Depreciation", "EBIT", "Interest", "EBT", "Tax", "Net Income"]]), use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Balance Sheet")
        st.dataframe(format_df(df_master.loc[["Total Assets", "Current Assets", "Total Liabilities" if "Total Liabilities" in df_master.index else "Current Liabilities", "Total Debt", "Total Equity"]]), use_container_width=True)
    with c2:
        st.subheader("Cash Flow Statement")
        st.dataframe(format_df(df_master.loc[["Operating CF", "CapEx", "Financing CF", "Free Cash Flow", "Net Cash Flow"]]), use_container_width=True)

with tab2:
    st.subheader("Advanced Financial Metrics")
    st.dataframe(kpi_df.style.format("{:,.2f}"), use_container_width=True)
    
    fig = px.bar(kpi_df.T.reset_index(), x='index', y=['ROE (%)', 'ROCE (%)'], barmode='group', title="Return on Capital Metrics", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Discounted Cash Flow (DCF) Breakdown")
    dcf_data = {
        "Metric": ["Present Value of FCFs", "Terminal Value (TV)", "Present Value of TV", "Enterprise Value (EV)", "Total Debt", "Cash (Current Assets proxy)", "Equity Value", "Shares Outstanding", "Implied Share Price"],
        "Value": [pv_fcf, terminal_value, pv_tv, enterprise_value, df_master.loc["Total Debt", base_yr], df_master.loc["Current Assets", base_yr], equity_value, df_master.loc["Shares Outstanding", base_yr], implied_share_price]
    }
    st.table(pd.DataFrame(dcf_data).set_index("Metric").style.format("{:,.2f}"))

with tab4:
    st.info("Export the fully linked three-statement model and valuation matrix.")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_master.to_excel(writer, sheet_name='Three Statement Model')
        kpi_df.to_excel(writer, sheet_name='Advanced KPIs')
    st.download_button("📥 Download Full Enterprise Report (.xlsx)", output.getvalue(), f"{display_name.replace(' ', '_')}_Valuation_Model.xlsx")
