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
        
        # Ensure column lengths match if timeline changed
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
            "Load Saved Model:", 
            ["-- Select --"] + hist_names
        )
        if st.button("Load Data"):
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

    save_name = st.text_input("Name this model:")
    if st.button("Save Data"):
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
    
    kpi_df.loc["FCF Yield (%)", y] = safe_div(
        df_master.loc["Free Cash Flow", y], 
        df_master.loc["Revenue", y]
    ) * 100

kpi_df = kpi_df.astype(float)

# --- DCF VALUATION ---
base_yr = hist_years_list[-1]
final_yr = years[-1]

fcf_series = df_master.loc["Free Cash Flow", forecast_year_labels]
fcf_series = fcf_series.astype(float)

discount_factors = [
    (1 + wacc_input / 100) ** (i + 1) 
    for i in range(len(forecast_year_labels))
]

pv_fcfs = []
for fcf, df in zip(fcf_series, discount_factors):
    pv_fcfs.append(fcf / df)
    
pv_fcf_total = sum(pv_fcfs)

denom = (wacc_input / 100) - (tg_input / 100)

if len(fcf_series) > 0:
    last_fcf = float(fcf_series.iloc[-1])
else:
    last_fcf = 0.0

if denom > 0:
    terminal_value = (last_fcf * (1 + tg_input / 100)) / denom
else:
    terminal_value = 0.0

if discount_factors:
    pv_tv = terminal_value / discount_factors[-1]
else:
    pv_tv = 0.0

enterprise_value = pv_fcf_total + pv_tv

net_debt = (
    float(df_master.loc["Total Debt", base_yr]) - 
    float(df_master.loc["Current Assets", base_yr])
)

equity_value = enterprise_value - net_debt
shares = float(df_master.loc["Shares Outstanding", base_yr])
implied_share_price = safe_div(equity_value, shares)

# --- WACC x TGR SENSITIVITY MATRIX ---
wacc_range = np.round(
    np.arange(wacc_input - 2.0, wacc_input + 2.5, 0.5), 1
)
tgr_range = np.round(
    np.arange(tg_input - 1.0, tg_input + 1.5, 0.5), 1
)

def dcf_ev(w, tg):
    disc = []
    for i in range(len(forecast_year_labels)):
        val = (1 + w / 100) ** (i + 1)
        disc.append(val)
        
    pv = sum([f / d for f, d in zip(fcf_series, disc)])
    denom_ = (w / 100) - (tg / 100)
    
    if denom_ > 0:
        tv = (last_fcf * (1 + tg / 100)) / denom_
    else:
        tv = 0.0
        
    if disc:
        ptv = tv / disc[-1]
    else:
        ptv = 0.0
        
    return pv + ptv

def dcf_price(w, tg):
    ev = dcf_ev(w, tg)
    eq = ev - net_debt
    return safe_div(eq, shares)

sensitivity_ev = pd.DataFrame(
    index=[f"{w}%" for w in wacc_range], 
    columns=[f"{t}%" for t in tgr_range]
)

sensitivity_price = pd.DataFrame(
    index=[f"{w}%" for w in wacc_range], 
    columns=[f"{t}%" for t in tgr_range]
)

for w in wacc_range:
    for t in tgr_range:
        if w / 100 > t / 100:
            val_ev = round(dcf_ev(w, t), 1)
            val_pr = round(dcf_price(w, t), 2)
            sensitivity_ev.loc[f"{w}%", f"{t}%"] = val_ev
            sensitivity_price.loc[f"{w}%", f"{t}%"] = val_pr
        else:
            sensitivity_ev.loc[f"{w}%", f"{t}%"] = np.nan
            sensitivity_price.loc[f"{w}%", f"{t}%"] = np.nan

sensitivity_ev = sensitivity_ev.astype(float)
sensitivity_price = sensitivity_price.astype(float)

# --- HEADER ---
display_name = company_name if company_name else "New Model"
st.title(f"📈 {display_name} — Analytics Suite")
st.caption(f"Figures in **{unit_suffix}** · Indian Standards")

has_data = float(df_master.loc["Revenue", base_yr]) > 0

if has_data:
    rev_base = float(df_master.loc["Revenue", base_yr])
    rev_final = float(df_master.loc["Revenue", final_yr])
    ebitda_base = float(kpi_df.loc["EBITDA Margin (%)", base_yr])
    ebitda_final = float(kpi_df.loc["EBITDA Margin (%)", final_yr])
    de_final = float(kpi_df.loc["Debt to Equity", final_yr])
    
    t1 = f"Revenue grows at <strong>{rev_growth_input}%</strong>. "
    t2 = f"EBITDA shifts to <strong>{ebitda_final:.1f}%</strong>. "
    t3 = f"Enterprise Value: <strong>{enterprise_value:,.1f}</strong>. "
    t4 = f"Share Price: <strong>{implied_share_price:,.2f}</strong>. "
    
    summary_text = (
        f"<div class='ai-box'>"
        f"<strong>🤖 AI Analyst Summary:</strong><br>"
        f"{t1}{t2}{t3}{t4}"
        f"</div>"
    )
    st.markdown(summary_text, unsafe_allow_html=True)
else:
    st.info("💡 Enter historical actuals in the sidebar.")

st.subheader("Key Performance Indicators")
k1, k2, k3, k4, k5, k6 = st.columns(6)

v_rev = df_master.loc['Revenue', final_yr]
k1.metric(f"Revenue", f"{unit_suffix} {v_rev:,.0f}")

v_ebt = df_master.loc['EBITDA', final_yr]
k2.metric(f"EBITDA", f"{unit_suffix} {v_ebt:,.0f}")

v_roe = kpi_df.loc['ROE (%)', final_yr]
k3.metric("Term. ROE", f"{v_roe:.1f}%")

v_fcf = df_master.loc['Free Cash Flow', final_yr]
k4.metric("FCF", f"{unit_suffix} {v_fcf:,.0f}")

k5.metric("EV", f"{unit_suffix} {enterprise_value:,.1f}")
k6.metric("Share Px", f"{unit_suffix} {implied_share_price:,.2f}")

st.divider()

# --- TABS ---
tab_names = [
    "📑 Statements", "📊 KPIs", 
    "💰 DCF", "🎯 Sensitivity", "🔬 Exports"
]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_names)

DARK_TEMPLATE = "plotly_dark"
GREEN = "#00b050"
RED = "#ef4444"
BLUE = "#3b82f6"
AMBER = "#f59e0b"

with tab1:
    st.subheader(f"Income Statement ({unit_suffix})")
    is_rows = [
        "Revenue", "COGS", "Gross Profit", "Gross Margin (%)", 
        "S&G Expenses", "EBITDA", "EBITDA Margin (%)", 
        "Depreciation", "EBIT", "Interest", "EBT", "Tax", 
        "Net Income", "Net Margin (%)"
    ]
    
    is_df = df_master.loc[
        [r for r in is_rows if r in df_master.index]
    ]

    def style_is(df):
        def fmt_fn(x):
            return f"{x:.1f}" if pd.notna(x) else "—"
            
        styled = df.style.format(fmt_fn)
        
        def row_color(row_name):
            if "Margin" in row_name or "%" in row_name: 
                return "background-color: #1a2e1a; color: #00b050;"
            if row_name in ["Gross Profit", "EBITDA", "Net Income"]: 
                return "background-color: #0d1f0d; color: #00b050;"
            return ""
            
        for row in df.index:
            style = row_color(row)
            if style: 
                styled = styled.apply(
                    lambda x, r=row, s=style: [
                        s if x.name == r else "" for _ in x
                    ], 
                    axis=1
                )
        return styled

    st.dataframe(style_is(is_df), use_container_width=True)

    st.subheader("📈 Revenue, EBITDA & Net Income Trend")
    fig_trend = go.Figure()
    
    fig_trend.add_trace(go.Bar(
        x=years, 
        y=df_master.loc["Revenue", years].values.tolist(), 
        name="Revenue", 
        marker_color=GREEN, 
        opacity=0.85
    ))
    
    fig_trend.add_trace(go.Bar(
        x=years, 
        y=df_master.loc["EBITDA", years].values.tolist(), 
        name="EBITDA", 
        marker_color=BLUE, 
        opacity=0.85
    ))
    
    fig_trend.add_trace(go.Scatter(
        x=years, 
        y=df_master.loc["Net Income", years].values.tolist(), 
        name="Net Income", 
        mode="lines+markers", 
        line=dict(color=AMBER, width=3), 
        marker=dict(size=8)
    ))
    
    if len(hist_years_list) > 0 and len(forecast_year_labels) > 0:
        fig_trend.add_vline(
            x=len(hist_years_list) - 0.5, 
            line_dash="dash", 
            line_color="#64748b", 
            annotation_text="Forecast", 
            annotation_position="top right", 
            annotation_font_color="#94a3b8"
        )
    
    fig_trend.update_layout(
        template=DARK_TEMPLATE, 
        barmode="group", 
        title=f"Trend ({unit_suffix})", 
        xaxis_title="Year", 
        yaxis_title=unit_suffix, 
        legend=dict(orientation="h", y=1.1), 
        height=420
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_fcf = go.Figure()
        fcf_vals = df_master.loc["Free Cash Flow", years].tolist()
        
        c_list = [GREEN if v >= 0 else RED for v in fcf_vals]
        
        fig_fcf.add_trace(go.Bar(
            x=years, 
            y=fcf_vals, 
            marker_color=c_list, 
            name="FCF"
        ))
        
        fig_fcf.add_trace(go.Scatter(
            x=years, 
            y=df_master.loc["Operating CF", years].tolist(), 
            name="Operating CF", 
            mode="lines+markers", 
            line=dict(color=AMBER, width=2), 
            marker=dict(size=6)
        ))
        
        fig_fcf.update_layout(
            template=DARK_TEMPLATE, 
            title=f"Cash Flow ({unit_suffix})", 
            xaxis_title="Year", 
            yaxis_title=unit_suffix, 
            height=380
        )
        st.plotly_
