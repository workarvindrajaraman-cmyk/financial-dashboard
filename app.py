import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go

# --- DASHBOARD CONFIGURATION ---
st.set_page_config(
    page_title="Corporate Financial Engine", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state['initialized'] = True

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    thead tr th { 
        background-color: #00b050 !important; 
        color: white !important; 
        font-weight: bold !important; 
        font-size: 14px; 
    }
    .stTabs [data-baseweb="tab-list"] { 
        gap: 24px; 
    }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: transparent; 
        font-size: 16px; 
        font-weight: 600; 
        color: #94a3b8; 
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { 
        color: #00b050 !important; 
        border-bottom-color: #00b050 !important; 
    }
    div[data-testid="stMetricValue"] { 
        color: #00b050; 
    }
    div.stButton > button:first-child, 
    div.stDownloadButton > button:first-child { 
        background-color: #00b050 !important; 
        color: white !important; 
        border: none !important; 
    }
    .ai-box { 
        background-color: #0e1117; 
        border-left: 4px solid #00b050; 
        padding: 15px; 
        border-radius: 5px; 
        margin-bottom: 20px; 
        font-style: italic; 
    }
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

# --- SIDEBAR: DATA CONTROLS ---
with st.sidebar:
    st.header("🎛️ Engine Controls")
    company_name = st.text_input(
        "Company Name", 
        value="", 
        placeholder="Enter Company Name..."
    )

    unit = st.radio(
        "Display Unit:", 
        ["Crores", "Lakhs"], 
        index=0, 
        horizontal=True
    )
    input_scale = st.radio(
        "Data Input Format:", 
        [f"Already in {unit}", "Raw Values (Needs Scaling)"], 
        index=0, 
        help="If raw, engine will divide automatically."
    )
    unit_suffix = "₹ Cr" if unit == "Crores" else "₹ L"

    st.divider()
    
    with st.expander("⏳ Timeline Settings", expanded=True):
        t1, t2 = st.columns(2)
        end_hist_year = t1.number_input(
            "Last Actual Year", value=2023, step=1
        )
        hist_years_count = t2.number_input(
            "Actual Years", min_value=1, max_value=10, value=2, step=1
        )
        forecast_years = st.slider(
            "Forecast Horizon", min_value=1, max_value=10, value=5
        )

    hist_years_list = [
        f"{end_hist_year - hist_years_count + 1 + i}A" 
        for i in range(hist_years_count)
    ]

    metrics = [
        "Revenue", "COGS", "S&G Expenses", "Depreciation", "Interest",
        "Current Assets", "Total Assets", "Current Liabilities", 
        "Total Debt", "Total Equity",
        "Operating CF", "CapEx", "Financing CF", "Shares Outstanding"
    ]
    default_data = {"Metric": metrics}
    for y in hist_years_list:
        default_data[y] = [0.0] * len(metrics)

    hist_df_template = pd.DataFrame(default_data).set_index("Metric")

    with st.expander(f"🏢 Historical Actuals ({unit_suffix})", expanded=True):
        edited_hist_df = st.data_editor(
            hist_df_template, use_container_width=True
        )

    with st.expander("📈 Forecasting & DCF Assumptions"):
        rev_growth_input = st.number_input(
            "Forecast Revenue Growth (%)", value=15.0, step=1.0
        )
        cogs_percent_input = st.number_input(
            "Forecast COGS % of Revenue", value=30.0, step=1.0
        )
        tax_input = st.number_input(
            "Forecast Taxes (%)", value=25.0, step=1.0
        )
        wacc_input = st.number_input(
            "WACC (Discount Rate %)", value=10.0, step=0.5
        )
        tg_input = st.number_input(
            "Terminal Growth Rate (%)", value=2.5, step=0.1
        )

# --- FINANCIAL ENGINE CORE ---
years = hist_years_list + [
    f"{end_hist_year + i}F" for i in range(1, forecast_years + 1)
]
forecast_year_labels = [y for y in years if "F" in y]

df_master = pd.DataFrame(index=metrics, columns=years, dtype=float)
df_master = df_master.fillna(0.0)

if input_scale == "Raw Values (Needs Scaling)" and unit == "Crores":
    divisor = 10000000.0
elif input_scale == "Raw Values (Needs Scaling)" and unit == "Lakhs":
    divisor = 100000.0
else:
    divisor = 1.0

for m in metrics:
    for y in hist_years_list:
        try:
            df_master.loc[m, y] = float(edited_hist_df.loc[m, y]) / divisor
        except:
            df_master.loc[m, y] = 0.0

# Forecasting Logic
for i in range(forecast_years):
    prev_y = years[len(hist_years_list) + i - 1]
    curr_y = years[len(hist_years_list) + i]

    try:
        prev_rev = float(df_master.loc["Revenue", prev_y])
    except:
        prev_rev = 0.0

    if prev_rev == 0:
        prev_rev = 0.0

    df_master.loc["Revenue", curr_y] = prev_rev * (1 + rev_growth_input / 100)
    
    df_master.loc["COGS", curr_y] = (
        df_master.loc["Revenue", curr_y] * (cogs_percent_input / 100)
    )
    
    sg_prev = float(df_master.loc["S&G Expenses", prev_y])
    if sg_prev != 0:
        df_master.loc["S&G Expenses", curr_y] = sg_prev * 1.05
    else:
        df_master.loc["S&G Expenses", curr_y] = (
            df_master.loc["Revenue", curr_y] * 0.10
        )
    
    df_master.loc["Depreciation", curr_y] = (
        df_master.loc["Revenue", curr_y] * 0.05
    )
    
    df_master.loc["Interest", curr_y] = float(
        df_master.loc["Interest", prev_y]
    )
    
    df_master.loc["Total Assets", curr_y] = float(
        df_master.loc["Total Assets", prev_y]
    ) * 1.05
    
    df_master.loc["Total Debt", curr_y] = max(
        float(df_master.loc["Total Debt", prev_y]) * 0.90, 0
    )
    
    df_master.loc["Total Equity", curr_y] = float(
        df_master.loc["Total Equity", prev_y]
    ) * 1.08
    
    df_master.loc["Current Assets", curr_y] = (
        df_master.loc["Total Assets", curr_y] * 0.3
    )
    
    df_master.loc["Current Liabilities", curr_y] = float(
        df_master.loc["Current Liabilities", prev_y]
    ) * 1.02
    
    df_master.loc["CapEx", curr_y] = (
        -df_master.loc["Revenue", curr_y] * 0.08
    )
    
    df_master.loc["Shares Outstanding", curr_y] = float(
        df_master.loc["Shares Outstanding", prev_y]
    )

df_master = df_master.astype(float)

# Derived P&L Lines
df_master.loc["Gross Profit"] = (
    df_master.loc["Revenue"] - df_master.loc["COGS"]
)
df_master.loc["EBITDA"] = (
    df_master.loc["Gross Profit"] - df_master.loc["S&G Expenses"]
)
df_master.loc["EBIT"] = (
    df_master.loc["EBITDA"] - df_master.loc["Depreciation"]
)
df_master.loc["EBT"] = (
    df_master.loc["EBIT"] - df_master.loc["Interest"]
)
df_master.loc["Tax"] = (
    df_master.loc["EBT"].apply(lambda x: max(x
