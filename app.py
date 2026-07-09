import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import json
import plotly.express as px
import plotly.graph_objects as go

# --- DASHBOARD CONFIGURATION ---
st.set_page_config(
    page_title="Corporate Financial Engine", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state['initialized'] = True

if 's_rev' not in st.session_state: 
    st.session_state.s_rev = 15.0
if 's_cogs' not in st.session_state: 
    st.session_state.s_cogs = 30.0
if 's_tax' not in st.session_state: 
    st.session_state.s_tax = 25.0
if 's_wacc' not in st.session_state: 
    st.session_state.s_wacc = 10.0
if 's_tgr' not in st.session_state: 
    st.session_state.s_tgr = 2.5
if 's_end_yr' not in st.session_state: 
    st.session_state.s_end_yr = 2023
if 's_act_yr' not in st.session_state: 
    st.session_state.s_act_yr = 2
if 's_for_yr' not in st.session_state: 
    st.session_state.s_for_yr = 5
if 's_grid' not in st.session_state: 
    st.session_state.s_grid = None

# --- SAFE CSS INJECTION ---
css_code = (
    "<style>\n"
    "#MainMenu {visibility: hidden;}\n"
    "footer {visibility: hidden;}\n"
    "thead tr th { \n"
    "    background-color: #00b050 !important; \n"
    "    color: white !important; \n"
    "    font-weight: bold !important; \n"
    "    font-size: 14px; \n"
    "}\n"
    ".stTabs [data-baseweb=\"tab-list\"] { gap: 24px; }\n"
    ".stTabs [data-baseweb=\"tab\"] { \n"
    "    height: 50px; background-color: transparent; \n"
    "    font-size: 16px; font-weight: 600; color: #94a3b8; \n"
    "}\n"
    ".stTabs [data-baseweb=\"tab\"][aria-selected=\"true\"] { \n"
    "    color: #00b050 !important; \n"
    "    border-bottom-color: #00b050 !important; \n"
    "}\n"
    "div[data-testid=\"stMetricValue\"] { color: #00b050; }\n"
    "div.stButton > button:first-child, \n"
    "div.stDownloadButton > button:first-child { \n"
    "    background-color: #00b050 !important; \n"
    "    color: white !important; border: none !important; \n"
    "}\n"
    ".ai-box { \n"
    "    background-color: #0e1117; \n"
    "    border-left: 4px solid #00b050; \n"
    "    padding: 15px; border-radius: 5px; \n"
    "    margin-bottom: 20px; font-style: italic; \n"
    "}\n"
    "</style>"
)
st.markdown(css_code, unsafe_allow_html=True)

# --- PORTFOLIO BRANDING ---
with st.sidebar:
    st.markdown("### 🏢 Analyst Portfolio")
    st.caption("Developed by: **Arvind Rajaraman**")
    st.divider()

if st.sidebar.button(
    "➕ Start New Model", 
    use_container_width=True
):
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
        ["Already Formatted", "Raw Values"], 
        index=0, 
        help="If raw, engine divides automatically."
    )
    unit_suffix = "₹ Cr" if unit == "Crores" else "₹ L"

    st.divider()
    
    with st.expander("⏳ Timeline Settings", expanded=True):
        t1, t2 = st.columns(2)
        end_hist_year = t1.number_input(
            "Last Actual", 
            value=st.session_state.s_end_yr, 
            step=1
        )
        hist_years_count = t2.number_input(
            "Actual Yrs", 
            min_value=1, 
            max_value=10, 
            value=st.session_state.s_act_yr
        )
        forecast_years = st.slider(
            "Forecast Horizon", 
            min_value=1, 
            max_value=10, 
            value=st.session_state.s_for_yr
        )

    hist_years_list = [
        f"{end_hist_year - hist_years_count + 1 + i}A" 
        for i in range(hist_years_count)
    ]

    metrics = [
        "Revenue", "COGS", "S&G Expenses", "Depreciation", 
        "Interest", "Current Assets", "Total Assets", 
        "Current Liabilities", "Total Debt", "Total Equity",
        "Operating CF", "CapEx", "Financing CF", 
        "Shares Outstanding"
    ]
    
    default_data = {"Metric": metrics}
    for y in hist_years_list:
        default_data[y] = [0.0] * len(metrics)

    hist_df_template = pd.DataFrame(default_data).set_index(
        "Metric"
    )

    if st.session_state.s_grid is not None:
        start_grid = st.session_state.s_grid
        for y in hist_years_list:
            if y not in start_grid.columns:
                start_grid[y] = 0.0
        start_grid = start_grid[hist_years_list]
    else:
        start_grid = hist_df_template

    with st.expander(
        f"🏢 Historical Actuals ({unit_suffix})", 
        expanded=True
    ):
        edited_hist_df = st.data_editor(
            start_grid, use_container_width=True
        )

    with st.expander("📈 Forecasting & Assumptions"):
        rev_growth_input = st.number_input(
            "Revenue Growth (%)", 
            value=st.session_state.s_rev, 
            step=1.0
        )
        cogs_percent_input = st.number_input(
            "COGS % of Revenue", 
            value=st.session_state.s_cogs, 
            step=1.0
        )
        tax_input = st.number_input(
            "Taxes (%)", 
            value=st.session_state.s_tax, 
            step=1.0
        )
        wacc_input = st.number_input(
            "WACC (%)", 
            value=st.session_state.s_wacc, 
            step=0.5
        )
        tg_input = st.number_input(
            "Terminal Growth (%)", 
            value=st.session_state.s_tgr, 
            step=0.1
        )

    st.divider()
    
    # --- HISTORY DATABASE MANAGER ---
    st.subheader("🕰️ Model History")
    db_file = "history_db.json"

    def load_db():
        if os.path.exists(db_file):
            try:
                with open(db_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    hist_db = load_db()
    hist_names = list(hist_db.keys())

    if hist_names:
        sel_hist = st.selectbox(
            "Saved Models:", 
            ["-- Select --"] + hist_names
        )
        
        # Load & Delete Buttons side-by-side
        c_load, c_del = st.columns(2)
        
        with c_load:
            if st.button("Load", use_container_width=True):
                if sel_hist != "-- Select --":
                    data = hist_db[sel_hist]
                    
                    st.session_state.s_rev = data.get("rev", 15.0)
                    st.session_state.s_cogs = data.get("cogs", 30.0)
                    st.session_state.s_tax = data.get("tax", 25.0)
                    st.session_state.s_wacc = data.get("wacc", 10.0)
                    st.session_state.s_tgr = data.get("tgr", 2.5)
                    
                    st.session_state.s_end_yr = data.get("end_y", 2023)
                    st.session_state.s_act_yr = data.get("act_y", 2)
                    st.session_state.s_for_yr = data.get("for_y", 5)
                    
                    grid_dict = data.get("grid", {})
                    st.session_state.s_grid = pd.DataFrame(grid_dict)
                    st.rerun()
                    
        with c_del:
            if st.button("Delete", use_container_width=True):
                if sel_hist != "-- Select --":
                    del hist_db[sel_hist]
                    with open(db_file, "w") as f:
                        json.dump(hist_db, f)
                    st.success(f"Deleted '{sel_hist}'!")
                    st.rerun()

    save_name = st.text_input("Name this model:")
    if st.button("Save Data", use_container_width=True):
        if save_name:
            hist_db[save_name] = {
                "rev": rev_growth_input,
                "cogs": cogs_percent_input,
                "tax": tax_input,
                "wacc": wacc_input,
                "tgr": tg_input,
                "end_y": end_hist_year,
                "act_y": hist_years_count,
                "for_y": forecast_years,
                "grid": edited_hist_df.to_dict()
            }
            with open(db_file, "w") as f:
                json.dump(hist_db, f)
            st.success(f"Saved '{save_name}'!")
            st.rerun()

# --- FINANCIAL ENGINE CORE ---
years = hist_years_list + [
    f"{end_hist_year + i}F" for i in range(1, forecast_years + 1)
]
forecast_year_labels = [y for y in years if "F" in y]

df_master = pd.DataFrame(
    index=metrics, columns=years, dtype=float
)
df_master = df_master.fillna(0.0)

if input_scale == "Raw Values" and unit == "Crores":
    divisor = 10000000.0
elif input_scale == "Raw Values" and unit == "Lakhs":
    divisor = 100000.0
else:
    divisor = 1.0

for m in metrics:
    for y in hist_years_list:
        try:
            val = float(edited_hist_df.loc[m, y])
            df_master.loc[m, y] = val / divisor
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

    df_master.loc["Revenue", curr_y] = (
        prev_rev * (1 + rev_growth_input / 100)
    )
    
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

def calc_tax(x):
    return max(x, 0)

df_master.loc["Tax"] = (
    df_master.loc["EBT"].apply(calc_tax) * (tax_input / 100)
)
df_master.loc["Net Income"] = (
    df_master.loc["EBT"] - df_master.loc["Tax"]
)
df_master.loc["Operating CF"] = (
    df_master.loc["Net Income"] + df_master.loc["Depreciation"]
)
df_master.loc["Free Cash Flow"] = (
    df_master.loc["Operating CF"] + df_master.loc["CapEx"]
)
df_master.loc["Financing CF"] = (
    df_master.loc["Total Debt"].diff().fillna(0)
)
df_master.loc["Net Cash Flow"] = (
    df_master.loc["Operating CF"] + 
    df_master.loc["CapEx"] + 
    df_master.loc["Financing CF"]
)

df_master.loc["Gross Margin (%)"] = (
    df_master.loc["Gross Profit"] / 
    df_master.loc["Revenue"].replace(0, np.nan)
) * 100

df_master.loc["EBITDA Margin (%)"] = (
    df_master.loc["EBITDA"] / 
    df_master.loc["Revenue"].replace(0, np.nan)
) * 100

df_master.loc["Net Margin (%)"] = (
    df_master.loc["Net Income"] / 
    df_master.loc["Revenue"].replace(0, np.nan)
) * 100

# --- KPI CALCULATIONS ---
def safe_div(a, b):
    try:
        a, b = float(a), float(b)
        return a / b if b != 0 else 0.0
    except:
        return 0.0

kpi_df = pd.DataFrame(columns=years, dtype=float)
for y in years:
    kpi_df.loc["ROE (%)", y] = safe_div(
        df_master.loc["Net Income", y], 
        df_master.loc["Total Equity", y]
    ) * 100
    
    kpi_df.loc["ROCE (%)", y] = safe_div(
        df_master.loc["EBIT", y], 
        df_master.loc["Total Assets", y] - 
        df_master.loc["Current Liabilities", y]
    ) * 100
    
    kpi_df.loc["EPS", y] = safe_div(
        df_master.loc["Net Income", y], 
        df_master.loc["Shares Outstanding", y]
    )
    
    kpi_df.loc["Current Ratio", y] = safe_div(
        df_master.loc["Current Assets", y], 
        df_master.loc["Current Liabilities", y]
    )
    
    kpi_df.loc["Debt to Equity", y] = safe_div(
        df_master.loc["Total Debt", y], 
        df_master.loc["Total Equity", y]
    )
    
    kpi_df.loc["EBITDA Margin (%)", y] = safe_div(
        df_master.loc["EBITDA", y], 
        df_master.loc["Revenue", y]
    ) * 100
    
    kpi_df.loc["Net Margin (%)", y] = safe_div(
        df_master.loc["Net Income", y], 
        df_master.loc["Revenue", y]
    ) * 100
    
    kpi_df.loc["FC
