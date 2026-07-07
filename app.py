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
    
    # STRICTLY INDIAN STANDARDS
    unit = st.radio("Display Unit:", ["Crores", "Lakhs"], index=0, horizontal=True)
    
    st.divider()
    st.subheader("📁 Data Ingestion")
    # Added PDF to accepted types to show capability awareness
    uploaded_file = st.file_uploader("Upload Financial Statements", type=['csv', 'xlsx', 'pdf'], help="Upload historical data to bypass manual entry.")
    
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
    
    # Safe Upload Logic with PDF Trap
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                hist_df = pd.read_csv(uploaded_file, index_col=0)
                st.success("CSV Data successfully loaded!")
            elif uploaded_file.name.endswith('.xlsx'):
                hist_df = pd.read_excel(uploaded_file, index_col=0)
                st.success("Excel Data successfully loaded!")
            elif uploaded_file.name.endswith('.pdf'):
                st.warning("⚠️ PDF parsing requires advanced AI text extraction and is currently in beta. Please use CSV or XLSX for automatic population.")
                hist_df = hist_df_template
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

# --- EXCEL CHARTING ENGINE ---
@st.cache_data
def generate_excel_with_charts(df, kpi, year_list, final_year):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Financials')
        kpi.to_excel(writer, sheet_name='KPIs')
        
        workbook = writer.book
        ws_charts = workbook.add_worksheet('Visual Dashboards')
        num_years = len(year_list)

        # 1. Excel Native Chart: Revenue vs EBITDA (Column)
        chart1 = workbook.add_chart({'type': 'column'})
        rev_row = df.index.get_loc('Revenue') + 1
        ebitda_row = df.index.get_loc('EBITDA') + 1

        chart1.add_series({
            'name': ['Financials', rev_row, 0], 
            'categories': ['Financials', 0, 1, 0, num_years], 
            'values': ['Financials', rev_row, 1, rev_row, num_years], 
            'fill': {'color': '#1f77b4'}
        })
        chart1.add_series({
            'name': ['Financials', ebitda_row, 0], 
            'categories': ['Financials', 0, 1, 0, num_years], 
            'values': ['Financials', ebitda_row, 1, ebitda_row, num_years], 
            'fill': {'color': '#2ca02c'}
        })
        
        chart1.set_title({'name': 'Revenue vs EBITDA Trajectory'})
        chart1.set_x_axis({'name': 'Financial Years', 'name_font': {'bold': True}})
        chart1.set_y_axis({'name': f'Value in {unit}', 'name_font': {'bold': True}, 'major_gridlines': {'visible': True}})
        ws_charts.insert_chart('B2', chart1, {'x_scale': 1.5, 'y_scale': 1.5})

        # 2. Excel Native Chart: ROE & ROCE (Line Chart)
        chart2 = workbook.add_chart({'type': 'line'})
        roe_row = kpi.index.get_loc('ROE (%)') + 1
        roce_row = kpi.index.get_loc('ROCE (%)') + 1

        chart2.add_series({
            'name': ['KPIs', roe_row, 0], 
            'categories': ['KPIs', 0, 1, 0, num_years], 
            'values': ['KPIs', roe_row, 1, roe_row, num_years], 
            'line': {'width': 2.5, 'color': '#ff7f0e'}
        })
        chart2.add_series({
            'name': ['KPIs', roce_row, 0], 
            'categories': ['KPIs', 0, 1, 0, num_years], 
            'values': ['KPIs', roce_row, 1, roce_row, num_years], 
            'line': {'width': 2.5, 'color': '#d62728'}
        })
        
        chart2.set_title({'name': 'Return on Capital (Efficiency)'})
        chart2.set_x_axis({'name': 'Financial Years'})
        chart2.set_y_axis({'name': 'Percentage (%)'})
        ws_charts.insert_chart('B20', chart2, {'x_scale': 1.5, 'y_scale': 1.5})

        # 3. Excel Native Chart: Cost Structure (Pie Chart)
        costs_list = ['COGS', 'S&G Expenses', 'Depreciation', 'Interest', 'Tax']
        ws_charts.write('Q1', 'Cost Component')
        ws_charts.write('R1', 'Value')
        for idx, cost in enumerate(costs_list):
            ws_charts.write(idx+1, 16, cost)
            ws_charts.write(idx+1, 17, df.loc[cost, final_year])

        chart3 = workbook.add_chart({'type': 'pie'})
        chart3.add_series({
            'name': 'Cost Structure', 
            'categories': ['Visual Dashboards', 1,
