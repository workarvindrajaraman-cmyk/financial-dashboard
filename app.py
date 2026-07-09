import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import json
import plotly.express as px
import plotly.graph_objects as go

# --- DASHBOARD CONFIGURATION ---
st.set_page_config(page_title="Corporate Financial Engine", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state['initialized'] = True

if 's_rev' not in st.session_state: st.session_state.s_rev = 15.0
if 's_cogs' not in st.session_state: st.session_state.s_cogs = 30.0
if 's_tax' not in st.session_state: st.session_state.s_tax = 25.0
if 's_wacc' not in st.session_state: st.session_state.s_wacc = 10.0
if 's_tgr' not in st.session_state: st.session_state.s_tgr = 2.5
if 's_end_yr' not in st.session_state: st.session_state.s_end_yr = 2023
if 's_act_yr' not in st.session_state: st.session_state.s_act_yr = 2
if 's_for_yr' not in st.session_state: st.session_state.s_for_yr = 5
if 's_grid' not in st.session_state: st.session_state.s_grid = None

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

with st.sidebar:
    st.markdown("### 🏢 Analyst Portfolio")
    st.caption("Developed by: **Arvind Rajaraman**")
    st.divider()

if st.sidebar.button("➕ Start New Model", use_container_width=True):
    st.session_state.clear()
    st.rerun()

with st.sidebar:
    st.header("🎛️ Engine Controls")
    company_name = st.text_input("Company Name", value="", placeholder="Enter Company Name...")
    unit = st.radio("Display Unit:", ["Crores", "Lakhs"], index=0, horizontal=True)
    input_scale = st.radio("Data Input Format:", ["Already Formatted", "Raw Values"], index=0, help="If raw, engine divides automatically.")
    unit_suffix = "₹ Cr" if unit == "Crores" else "₹ L"
    st.divider()
    
    with st.expander("⏳ Timeline Settings", expanded=True):
        t1, t2 = st.columns(2)
        end_hist_year = t1.number_input("Last Actual", value=st.session_state.s_end_yr, step=1)
        hist_years_count = t2.number_input("Actual Yrs", min_value=1, max_value=10, value=st.session_state.s_act_yr)
        forecast_years = st.slider("Forecast Horizon", min_value=1, max_value=10, value=st.session_state.s_for_yr)

    hist_years_list = [f"{end_hist_year - hist_years_count + 1 + i}A" for i in range(hist_years_count)]
    metrics = ["Revenue", "COGS", "S&G Expenses", "Depreciation", "Interest", "Current Assets", "Total Assets", "Current Liabilities", "Total Debt", "Total Equity", "Operating CF", "CapEx", "Financing CF", "Shares Outstanding"]
    
    default_data = {"Metric": metrics}
    for y in hist_years_list: default_data[y] = [0.0] * len(metrics)
    hist_df_template = pd.DataFrame(default_data).set_index("Metric")

    if st.session_state.s_grid is not None:
        start_grid = st.session_state.s_grid
        for y in hist_years_list:
            if y not in start_grid.columns: start_grid[y] = 0.0
        start_grid = start_grid[hist_years_list]
    else:
        start_grid = hist_df_template

    with st.expander(f"🏢 Historical Actuals ({unit_suffix})", expanded=True):
        edited_hist_df = st.data_editor(start_grid, use_container_width=True)

    with st.expander("📈 Forecasting & Assumptions"):
        rev_growth_input = st.number_input("Revenue Growth (%)", value=st.session_state.s_rev, step=1.0)
        cogs_percent_input = st.number_input("COGS % of Revenue", value=st.session_state.s_cogs, step=1.0)
        tax_input = st.number_input("Taxes (%)", value=st.session_state.s_tax, step=1.0)
        wacc_input = st.number_input("WACC (%)", value=st.session_state.s_wacc, step=0.5)
        tg_input = st.number_input("Terminal Growth (%)", value=st.session_state.s_tgr, step=0.1)

    st.divider()
    st.subheader("🕰️ Model History")
    db_file = "history_db.json"

    def load_db():
        if os.path.exists(db_file):
            try:
                with open(db_file, "r") as f: return json.load(f)
            except: return {}
        return {}

    hist_db = load_db()
    hist_names = list(hist_db.keys())

    if hist_names:
        sel_hist = st.selectbox("Saved Models:", ["-- Select --"] + hist_names)
        c_load, c_del = st.columns(2)
        with c_load:
            if st.button("Load", use_container_width=True) and sel_hist != "-- Select --":
                data = hist_db[sel_hist]
                st.session_state.s_rev, st.session_state.s_cogs = data.get("rev", 15.0), data.get("cogs", 30.0)
                st.session_state.s_tax, st.session_state.s_wacc = data.get("tax", 25.0), data.get("wacc", 10.0)
                st.session_state.s_tgr, st.session_state.s_end_yr = data.get("tgr", 2.5), data.get("end_y", 2023)
                st.session_state.s_act_yr, st.session_state.s_for_yr = data.get("act_y", 2), data.get("for_y", 5)
                st.session_state.s_grid = pd.DataFrame(data.get("grid", {}))
                st.rerun()
        with c_del:
            if st.button("Delete", use_container_width=True) and sel_hist != "-- Select --":
                del hist_db[sel_hist]
                with open(db_file, "w") as f: json.dump(hist_db, f)
                st.success(f"Deleted '{sel_hist}'!")
                st.rerun()

    save_name = st.text_input("Name this model:")
    if st.button("Save Data", use_container_width=True) and save_name:
        hist_db[save_name] = {
            "rev": rev_growth_input, "cogs": cogs_percent_input, "tax": tax_input, "wacc": wacc_input,
            "tgr": tg_input, "end_y": end_hist_year, "act_y": hist_years_count, "for_y": forecast_years,
            "grid": edited_hist_df.to_dict()
        }
        with open(db_file, "w") as f: json.dump(hist_db, f)
        st.success(f"Saved '{save_name}'!")
        st.rerun()

# --- FINANCIAL ENGINE CORE ---
years = hist_years_list + [f"{end_hist_year + i}F" for i in range(1, forecast_years + 1)]
forecast_year_labels = [y for y in years if "F" in y]

df_master = pd.DataFrame(index=metrics, columns=years, dtype=float).fillna(0.0)
divisor = 10000000.0 if (input_scale == "Raw Values" and unit == "Crores") else (100000.0 if input_scale == "Raw Values" and unit == "Lakhs" else 1.0)

for m in metrics:
    for y in hist_years_list:
        try: df_master.loc[m, y] = float(edited_hist_df.loc[m, y]) / divisor
        except: df_master.loc[m, y] = 0.0

for i in range(forecast_years):
    prev_y, curr_y = years[len(hist_years_list) + i - 1], years[len(hist_years_list) + i]
    try: prev_rev = float(df_master.loc["Revenue", prev_y])
    except: prev_rev = 0.0

    df_master.loc["Revenue", curr_y] = prev_rev * (1 + rev_growth_input / 100)
    df_master.loc["COGS", curr_y] = df_master.loc["Revenue", curr_y] * (cogs_percent_input / 100)
    
    sg_prev = float(df_master.loc["S&G Expenses", prev_y])
    df_master.loc["S&G Expenses", curr_y] = sg_prev * 1.05 if sg_prev != 0 else df_master.loc["Revenue", curr_y] * 0.10
    df_master.loc["Depreciation", curr_y] = df_master.loc["Revenue", curr_y] * 0.05
    df_master.loc["Interest", curr_y] = float(df_master.loc["Interest", prev_y])
    df_master.loc["Total Assets", curr_y] = float(df_master.loc["Total Assets", prev_y]) * 1.05
    df_master.loc["Total Debt", curr_y] = max(float(df_master.loc["Total Debt", prev_y]) * 0.90, 0)
    df_master.loc["Total Equity", curr_y] = float(df_master.loc["Total Equity", prev_y]) * 1.08
    df_master.loc["Current Assets", curr_y] = df_master.loc["Total Assets", curr_y] * 0.3
    df_master.loc["Current Liabilities", curr_y] = float(df_master.loc["Current Liabilities", prev_y]) * 1.02
    df_master.loc["CapEx", curr_y] = -df_master.loc["Revenue", curr_y] * 0.08
    df_master.loc["Shares Outstanding", curr_y] = float(df_master.loc["Shares Outstanding", prev_y])

df_master = df_master.astype(float)
df_master.loc["Gross Profit"] = df_master.loc["Revenue"] - df_master.loc["COGS"]
df_master.loc["EBITDA"] = df_master.loc["Gross Profit"] - df_master.loc["S&G Expenses"]
df_master.loc["EBIT"] = df_master.loc["EBITDA"] - df_master.loc["Depreciation"]
df_master.loc["EBT"] = df_master.loc["EBIT"] - df_master.loc["Interest"]
df_master.loc["Tax"] = df_master.loc["EBT"].apply(lambda x: max(x, 0)) * (tax_input / 100)
df_master.loc["Net Income"] = df_master.loc["EBT"] - df_master.loc["Tax"]
df_master.loc["Operating CF"] = df_master.loc["Net Income"] + df_master.loc["Depreciation"]
df_master.loc["Free Cash Flow"] = df_master.loc["Operating CF"] + df_master.loc["CapEx"]
df_master.loc["Financing CF"] = df_master.loc["Total Debt"].diff().fillna(0)
df_master.loc["Net Cash Flow"] = df_master.loc["Operating CF"] + df_master.loc["CapEx"] + df_master.loc["Financing CF"]
df_master.loc["Gross Margin (%)"] = (df_master.loc["Gross Profit"] / df_master.loc["Revenue"].replace(0, np.nan)) * 100
df_master.loc["EBITDA Margin (%)"] = (df_master.loc["EBITDA"] / df_master.loc["Revenue"].replace(0, np.nan)) * 100
df_master.loc["Net Margin (%)"] = (df_master.loc["Net Income"] / df_master.loc["Revenue"].replace(0, np.nan)) * 100

def safe_div(a, b):
    try: return float(a) / float(b) if float(b) != 0 else 0.0
    except: return 0.0

kpi_df = pd.DataFrame(columns=years, dtype=float)
for y in years:
    kpi_df.loc["ROE (%)", y] = safe_div(df_master.loc["Net Income", y], df_master.loc["Total Equity", y]) * 100
    kpi_df.loc["ROCE (%)", y] = safe_div(df_master.loc["EBIT", y], df_master.loc["Total Assets", y] - df_master.loc["Current Liabilities", y]) * 100
    kpi_df.loc["EPS", y] = safe_div(df_master.loc["Net Income", y], df_master.loc["Shares Outstanding", y])
    kpi_df.loc["Current Ratio", y] = safe_div(df_master.loc["Current Assets", y], df_master.loc["Current Liabilities", y])
    kpi_df.loc["Debt to Equity", y] = safe_div(df_master.loc["Total Debt", y], df_master.loc["Total Equity", y])
    kpi_df.loc["EBITDA Margin (%)", y] = safe_div(df_master.loc["EBITDA", y], df_master.loc["Revenue", y]) * 100
    kpi_df.loc["Net Margin (%)", y] = safe_div(df_master.loc["Net Income", y], df_master.loc["Revenue", y]) * 100
    kpi_df.loc["FCF Yield (%)", y] = safe_div(df_master.loc["Free Cash Flow", y], df_master.loc["Revenue", y]) * 100
kpi_df = kpi_df.astype(float)

base_yr, final_yr = hist_years_list[-1], years[-1]
fcf_series = df_master.loc["Free Cash Flow", forecast_year_labels].astype(float)
discount_factors = [(1 + wacc_input / 100) ** (i + 1) for i in range(len(forecast_year_labels))]
pv_fcfs = [fcf / df for fcf, df in zip(fcf_series, discount_factors)]
pv_fcf_total = sum(pv_fcfs)
denom = (wacc_input / 100) - (tg_input / 100)
last_fcf = float(fcf_series.iloc[-1]) if len(fcf_series) > 0 else 0.0
terminal_value = (last_fcf * (1 + tg_input / 100)) / denom if denom > 0 else 0.0
pv_tv = terminal_value / discount_factors[-1] if discount_factors else 0.0
enterprise_value = pv_fcf_total + pv_tv
net_debt = float(df_master.loc["Total Debt", base_yr]) - float(df_master.loc["Current Assets", base_yr])
equity_value = enterprise_value - net_debt
shares = float(df_master.loc["Shares Outstanding", base_yr])
implied_share_price = safe_div(equity_value, shares)

wacc_range = np.round(np.arange(wacc_input - 2.0, wacc_input + 2.5, 0.5), 1)
tgr_range = np.round(np.arange(tg_input - 1.0, tg_input + 1.5, 0.5), 1)

def dcf_ev(w, tg):
    disc = [(1 + w / 100) ** (i + 1) for i in range(len(forecast_year_labels))]
    pv = sum([f / d for f, d in zip(fcf_series, disc)])
    denom_ = (w / 100) - (tg / 100)
    tv = (last_fcf * (1 + tg / 100)) / denom_ if denom_ > 0 else 0.0
    ptv = tv / disc[-1] if disc else 0.0
    return pv + ptv

def dcf_price(w, tg):
    return safe_div(dcf_ev(w, tg) - net_debt, shares)

sensitivity_ev = pd.DataFrame(index=[f"{w}%" for w in wacc_range], columns=[f"{t}%" for t in tgr_range])
sensitivity_price = pd.DataFrame(index=[f"{w}%" for w in wacc_range], columns=[f"{t}%" for t in tgr_range])

for w in wacc_range:
    for t in tgr_range:
        if w / 100 > t / 100:
            sensitivity_ev.loc[f"{w}%", f"{t}%"] = round(dcf_ev(w, t), 1)
            sensitivity_price.loc[f"{w}%", f"{t}%"] = round(dcf_price(w, t), 2)
        else:
            sensitivity_ev.loc[f"{w}%", f"{t}%"], sensitivity_price.loc[f"{w}%", f"{t}%"] = np.nan, np.nan

sensitivity_ev = sensitivity_ev.astype(float)
sensitivity_price = sensitivity_price.astype(float)

display_name = company_name if company_name else "New Model"
st.title(f"📈 {display_name} — Analytics Suite")
st.caption(f"Figures in **{unit_suffix}** · Indian Standards")

has_data = float(df_master.loc["Revenue", base_yr]) > 0
if has_data:
    st.markdown(f"""<div class='ai-box'><strong>🤖 AI Analyst Summary:</strong><br>Revenue grows at <strong>{rev_growth_input}%</strong>. EBITDA shifts to <strong>{float(kpi_df.loc["EBITDA Margin (%)", final_yr]):.1f}%</strong>. Enterprise Value: <strong>{enterprise_value:,.1f}</strong>. Share Price: <strong>{implied_share_price:,.2f}</strong>.</div>""", unsafe_allow_html=True)
else:
    st.info("💡 Enter historical actuals in the sidebar.")

st.subheader("Key Performance Indicators")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Revenue", f"{unit_suffix} {df_master.loc['Revenue', final_yr]:,.0f}")
k2.metric("EBITDA", f"{unit_suffix} {df_master.loc['EBITDA', final_yr]:,.0f}")
k3.metric("Term. ROE", f"{kpi_df.loc['ROE (%)', final_yr]:.1f}%")
k4.metric("FCF", f"{unit_suffix} {df_master.loc['Free Cash Flow', final_yr]:,.0f}")
k5.metric("EV", f"{unit_suffix} {enterprise_value:,.1f}")
k6.metric("Share Px", f"{unit_suffix} {implied_share_price:,.2f}")

st.divider()
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📑 Statements", "📊 KPIs", "💰 DCF", "🎯 Sensitivity", "🔬 Exports"])
DARK_TEMPLATE, GREEN, RED, BLUE, AMBER = "plotly_dark", "#00b050", "#ef4444", "#3b82f6", "#f59e0b"

with tab1:
    st.subheader(f"Income Statement ({unit_suffix})")
    is_rows = ["Revenue", "COGS", "Gross Profit", "Gross Margin (%)", "S&G Expenses", "EBITDA", "EBITDA Margin (%)", "Depreciation", "EBIT", "Interest", "EBT", "Tax", "Net Income", "Net Margin (%)"]
    is_df = df_master.loc[[r for r in is_rows if r in df_master.index]]

    def style_is(df):
        styled = df.style.format(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
        def row_color(row_name):
            if "Margin" in row_name or "%" in row_name: return "background-color: #1a2e1a; color: #00b050;"
            if row_name in ["Gross Profit", "EBITDA", "Net Income"]: return "background-color: #0d1f0d; color: #00b050;"
            return ""
        for row in df.index:
            style = row_color(row)
            if style: styled = styled.apply(lambda x, r=row, s=style: [s if x.name == r else "" for _ in x], axis=1)
        return styled

    st.dataframe(style_is(is_df), use_container_width=True)

    st.subheader("📈 Revenue, EBITDA & Net Income Trend")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=years, y=df_master.loc["Revenue", years].tolist(), name="Revenue", marker_color=GREEN, opacity=0.85))
    fig_trend.add_trace(go.Bar(x=years, y=df_master.loc["EBITDA", years].tolist(), name="EBITDA", marker_color=BLUE, opacity=0.85))
    fig_trend.add_trace(go.Scatter(x=years, y=df_master.loc["Net Income", years].tolist(), name="Net Income", mode="lines+markers", line=dict(color=AMBER, width=3), marker=dict(size=8)))
    if len(hist_years_list) > 0 and len(forecast_year_labels) > 0:
        fig_trend.add_vline(x=len(hist_years_list) - 0.5, line_dash="dash", line_color="#64748b", annotation_text="Forecast", annotation_position="top right", annotation_font_color="#94a3b8")
    fig_trend.update_layout(template=DARK_TEMPLATE, barmode="group", title=f"Trend ({unit_suffix})", xaxis_title="Year", yaxis_title=unit_suffix, legend=dict(orientation="h", y=1.1), height=420)
    st.plotly_chart(fig_trend, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_fcf = go.Figure()
        fcf_vals = df_master.loc["Free Cash Flow", years].tolist()
        fig_fcf.add_trace(go.Bar(x=years, y=fcf_vals, marker_color=[GREEN if v >= 0 else RED for v in fcf_vals], name="FCF"))
        fig_fcf.add_trace(go.Scatter(x=years, y=df_master.loc["Operating CF", years].tolist(), name="Operating CF", mode="lines+markers", line=dict(color=AMBER, width=2), marker=dict(size=6)))
        fig_fcf.update_layout(template=DARK_TEMPLATE, title=f"Cash Flow ({unit_suffix})", xaxis_title="Year", yaxis_title=unit_suffix, height=380)
        st.plotly_chart(fig_fcf, use_container_width=True)

    with c2:
        fig_margins = go.Figure()
        fig_margins.add_trace(go.Scatter(x=years, y=df_master.loc["Gross Margin (%)", years].tolist(), name="Gross Margin", mode="lines+markers", line=dict(color=GREEN, width=3)))
        fig_margins.add_trace(go.Scatter(x=years, y=df_master.loc["EBITDA Margin (%)", years].tolist(), name="EBITDA Margin", mode="lines+markers", line=dict(color=BLUE, width=3)))
        fig_margins.add_trace(go.Scatter(x=years, y=df_master.loc["Net Margin (%)", years].tolist(), name="Net Margin", mode="lines+markers", line=dict(color=AMBER, width=3)))
        fig_margins.update_layout(template=DARK_TEMPLATE, title="Margins (%)", xaxis_title="Year", yaxis_title="%", height=380)
        st.plotly_chart(fig_margins, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader(f"Balance Sheet ({unit_suffix})")
        bs_rows = ["Total Assets", "Current Assets", "Current Liabilities", "Total Debt", "Total Equity"]
        st.dataframe(df_master.loc[bs_rows].style.format("{:,.1f}", na_rep="—"), use_container_width=True)
    with c4:
        st.subheader(f"Cash Flow ({unit_suffix})")
        cf_rows = ["Operating CF", "CapEx", "Financing CF", "Free Cash Flow", "Net Cash Flow"]
        st.dataframe(df_master.loc[cf_rows].style.format("{:,.1f}", na_rep="—"), use_container_width=True)

with tab2:
    st.subheader("Advanced Financial Metrics")
    st.dataframe(kpi_df.style.format("{:,.2f}", na_rep="—"), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_ret = go.Figure()
        fig_ret.add_trace(go.Bar(x=years, y=kpi_df.loc["ROE (%)", years].tolist(), name="ROE (%)", marker_color=GREEN))
        fig_ret.add_trace(go.Bar(x=years, y=kpi_df.loc["ROCE (%)", years].tolist(), name="ROCE (%)", marker_color=BLUE))
        fig_ret.update_layout(template=DARK_TEMPLATE, barmode="group", title="Returns (%)", xaxis_title="Year", yaxis_title="%", height=380)
        st.plotly_chart(fig_ret, use_container_width=True)

    with c2:
        fig_lev = go.Figure()
        fig_lev.add_trace(go.Scatter(x=years, y=kpi_df.loc["Debt to Equity", years].tolist(), name="D/E Ratio", mode="lines+markers", line=dict(color=RED, width=3)))
        fig_lev.add_trace(go.Scatter(x=years, y=kpi_df.loc["Current Ratio", years].tolist(), name="Current Ratio", mode="lines+markers", line=dict(color=GREEN, width=3)))
        fig_lev.update_layout(template=DARK_TEMPLATE, title="Ratios", xaxis_title="Year", yaxis_title="Ratio (x)", height=380)
        st.plotly_chart(fig_lev, use_container_width=True)

with tab3:
    st.subheader("DCF Breakdown")
    val_debt, val_cash = float(df_master.loc["Total Debt", base_yr]), float(df_master.loc["Current Assets", base_yr])
    dcf_data = {
        "Metric": ["PV of FCFs", "Terminal Value", "PV of TV", "Enterprise Value", "Less: Debt", "Add: Cash", "Equity Value", "Shares", "Implied Price"],
        f"Value ({unit_suffix})": [pv_fcf_total, terminal_value, pv_tv, enterprise_value, val_debt, val_cash, equity_value, shares, implied_share_price]
    }
    st.dataframe(pd.DataFrame(dcf_data).set_index("Metric").style.format("{:,.2f}", na_rep="—"), use_container_width=True)

    st.divider()
    st.subheader("🏗️ EV Bridge Waterfall")
    nd_val = val_debt - val_cash
    fig_br = go.Figure(go.Waterfall(
        name="EV Bridge", orientation="v", measure=["relative", "relative", "total", "relative", "total"],
        x=["PV FCF", "PV TV", "EV", "Net Debt", "Equity"], y=[pv_fcf_total, pv_tv, 0, -nd_val, 0],
        connector={"line": {"color": "#475569"}}, increasing={"marker": {"color": GREEN}}, decreasing={"marker": {"color": RED}}, totals={"marker": {"color": BLUE}},
        text=[f"{pv_fcf_total:,.1f}", f"{pv_tv:,.1f}", f"{enterprise_value:,.1f}", f"{abs(nd_val):,.1f}", f"{equity_value:,.1f}"], textposition="outside"
    ))
    fig_br.update_layout(template=DARK_TEMPLATE, title=f"Bridge ({unit_suffix})", yaxis_title=unit_suffix, height=480, showlegend=False)
    st.plotly_chart(fig_br, use_container_width=True)

with tab4:
    st.subheader("🎯 Sensitivity Analysis")
    col_sens1, col_sens2 = st.columns(2)
    
    def color_ev_cell(val):
        if pd.isna(val): return "background-color: #1e293b; color: #64748b;"
        if val > enterprise_value * 1.05: return "background-color: #052e0a; color: #00b050;"
        if val > enterprise_value * 0.95: return "background-color: #0d2818; color: #86efac;"
        if val < enterprise_value * 0.90: return "background-color: #2d0a0a; color: #fca5a5;"
        return "background-color: #1a1a2e; color: #cbd5e1;"

    def color_pr_cell(val):
        if pd.isna(val): return "background-color: #1e293b; color: #64748b;"
        if implied_share_price != 0:
            if val > implied_share_price * 1.10: return "background-color: #052e0a; color: green;"
            if val > implied_share_price * 0.95: return "background-color: #0d2818; color: lime;"
            if val < implied_share_price * 0.85: return "background-color: #2d0a0a; color: red;"
        return "background-color: #1a1a2e; color: #cbd5e1;"

    with col_sens1:
        st.markdown(f"#### EV Sensitivity ({unit_suffix})")
        st.dataframe(sensitivity_ev.style.map(color_ev_cell).format("{:,.1f}", na_rep="N/A"), use_container_width=True)

    with col_sens2:
        st.markdown(f"#### Price Sensitivity ({unit_suffix})")
        st.dataframe(sensitivity_price.style.map(color_pr_cell).format("{:,.2f}", na_rep="N/A"), use_container_width=True)

    st.divider()
    st.subheader("🌡️ Heatmap")
    ev_heat = sensitivity_ev.fillna(0).values.tolist()
    txt_arr = [[f"{unit_suffix}\n{v:,.0f}" if v != 0 else "N/A" for v in row] for row in ev_heat]
    
    fig_heat = go.Figure(data=go.Heatmap(
        z=ev_heat, x=[f"TGR {c}" for c in sensitivity_ev.columns], y=[f"WACC {r}" for r in sensitivity_ev.index],
        colorscale=[[0.0, "#2d0a0a"], [0.3, "#7f1d1d"], [0.5, "#1a2e1a"], [0.7, "#14532d"], [1.0, "#00b050"]],
        text=txt_arr, texttemplate="%{text}", textfont={"size": 11}, hoverongaps=False
    ))
    fig_heat.update_layout(template=DARK_TEMPLATE, title=f"EV Sensitivity ({unit_suffix})", xaxis_title="TGR", yaxis_title="WACC", height=420)
    st.plotly_chart(fig_heat, use_container_width=True)

with tab5:
    st.info("📥 Export boardroom-ready model to Excel.")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        t_fmt = workbook.add_format({'bold': True, 'font_size': 20, 'font_color': '#00b050', 'font_name': 'Arial'})
        s_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#64748b', 'font_name': 'Arial'})
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#0f172a', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        i_fmt = workbook.add_format({'bold': True, 'bg_color': '#f8fafc', 'font_color': '#0f172a', 'border': 1, 'border_color': '#cbd5e1'})
        n_fmt = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'border_color': '#cbd5e1'})
        p_fmt = workbook.add_format({'num_format': '0.00"%"', 'border': 1, 'border_color': '#cbd5e1'}) 

        def write_sht(df, s_name, title, is_pct=False):
            df.to_excel(writer, sheet_name=s_name, startrow=4, startcol=1)
            ws = writer.sheets[s_name]
            ws.hide_gridlines(2)
            ws.set_column('A:A', 3)
            ws.write('B2', display_name.upper() if display_name else "VAL", t_fmt)
            ws.write('B3', title, s_fmt)
            ws.set_column('B:B', 28, i_fmt)
            fmt = p_fmt if is_pct else n_fmt
            for c_num, c_name in enumerate(df.columns):
                ws.set_column(c_num + 2, c_num + 2, 15, fmt)
                ws.write(4, c_num + 2, c_name, h_fmt)
            ws.write(4, 1, "Metric", h_fmt)

        write_sht(df_master, 'Statements', f'Model ({unit_suffix})')
        write_sht(kpi_df, 'KPIs', 'KPIs & Ratios')
        write_sht(pd.DataFrame(dcf_data).set_index("Metric"), 'DCF', f'DCF ({unit_suffix})')

        sensitivity_ev.to_excel(writer, sheet_name='Sens-EV', startrow=4, startcol=1)
        ws_ev = writer.sheets['Sens-EV']
        ws_ev.hide_gridlines(2)
        ws_ev.set_column('A:A', 3)
        ws_ev.write('B2', display_name.upper() if display_name else "VAL", t_fmt)
        ws_ev.write('B3', f'EV Sens ({unit_suffix})', s_fmt)
        ws_ev.set_column('B:B', 15, i_fmt)
        for c_num, c_name in enumerate(sensitivity_ev.columns):
            ws_ev.set_column(c_num + 2, c_num + 2, 15, n_fmt)
            ws_ev.write(4, c_num + 2, c_name, h_fmt)
        ws_ev.write(4, 1, "WACC \ TGR", h_fmt)
        
        c_fmt_dict = {'type': '3_color_scale', 'min_color': '#fca5a5', 'mid_color': '#f8fafc', 'max_color': '#86efac'}
        ws_ev.conditional_format(5, 2, 5 + len(sensitivity_ev.index) - 1, 2 + len(sensitivity_ev.columns) - 1, c_fmt_dict)

        sensitivity_price.to_excel(writer, sheet_name='Sens-Px', startrow=4, startcol=1)
        ws_pr = writer.sheets['Sens-Px']
        ws_pr.hide_gridlines(2)
        ws_pr.set_column('A:A', 3)
        ws_pr.write('B2', display_name.upper() if display_name else "VAL", t_fmt)
        ws_pr.write('B3', f'Px Sens ({unit_suffix})', s_fmt)
        ws_pr.set_column('B:B', 15, i_fmt)
        for c_num, c_name in enumerate(sensitivity_price.columns):
            ws_pr.set_column(c_num + 2, c_num + 2, 15, n_fmt)
            ws_pr.write(4, c_num + 2, c_name, h_fmt)
        ws_pr.write(4, 1, "WACC \ TGR", h_fmt)
        ws_pr.conditional_format(5, 2, 5 + len(sensitivity_price.index) - 1, 2 + len(sensitivity_price.columns) - 1, c_fmt_dict)

        ws_c = workbook.add_worksheet('Visuals')
        ws_c.hide_gridlines(2)
        ws_c.set_column('A:A', 3)
        ws_c.write('B2', display_name.upper() if display_name else "VAL", t_fmt)
        ws_c.write('B3', 'Visual Analytics Deck', s_fmt)
        ny = len(years)

        c1 = workbook.add_chart({'type': 'column'})
        rr, er = df_master.index.get_loc('Revenue') + 5, df_master.index.get_loc('EBITDA') + 5
        c1.add_series({'name': ['Statements', rr, 1], 'categories': ['Statements', 4, 2, 4, 1 + ny], 'values': ['Statements', rr, 2, rr, 1 + ny], 'fill': {'color': '#00b050'}})
        c1.add_series({'name': ['Statements', er, 1], 'categories': ['Statements', 4, 2, 4, 1 + ny], 'values': ['Statements', er, 2, er, 1 + ny], 'fill': {'color': '#3b82f6'}})
        c1.set_title({'name': f'Rev vs EBITDA ({unit_suffix})'})
        c1.set_legend({'position': 'bottom'})
        c1.set_plotarea({'border': {'color': '#cbd5e1'}})
        ws_c.insert_chart('B7', c1, {'x_scale': 1.3, 'y_scale': 1.2})
        
        c2 = workbook.add_chart({'type': 'line'})
        fr, orw = df_master.index.get_loc('Free Cash Flow') + 5, df_master.index.get_loc('Operating CF') + 5
        c2.add_series({'name': ['Statements', fr, 1], 'categories': ['Statements', 4, 2, 4, 1 + ny], 'values': ['Statements', fr, 2, fr, 1 + ny], 'line': {'color': '#00b050', 'width': 2.5}})
        c2.add_series({'name': ['Statements', orw, 1], 'categories': ['Statements', 4, 2, 4, 1 + ny], 'values': ['Statements', orw, 2, orw, 1 + ny], 'line': {'color': '#f59e0b', 'width': 2.5}})
        c2.set_title({'name': f'Cash Flows ({unit_suffix})'})
        c2.set_legend({'position': 'bottom'})
        c2.set_plotarea({'border': {'color': '#cbd5e1'}})
        ws_c.insert_chart('K7', c2, {'x_scale': 1.3, 'y_scale': 1.2})
        
        c3 = workbook.add_chart({'type': 'column'})
        ror, rcr = kpi_df.index.get_loc('ROE (%)') + 5, kpi_df.index.get_loc('ROCE (%)') + 5
        c3.add_series({'name': ['KPIs', ror, 1], 'categories': ['KPIs', 4, 2, 4, 1 + ny], 'values': ['KPIs', ror, 2, ror, 1 + ny], 'fill': {'color': '#00b050'}})
        c3.add_series({'name': ['KPIs', rcr, 1], 'categories': ['KPIs', 4, 2, 4, 1 + ny], 'values': ['KPIs', rcr, 2, rcr, 1 + ny], 'fill': {'color': '#3b82f6'}})
        c3.set_title({'name': 'Returns (%)'})
        c3.set_legend({'position': 'bottom'})
        c3.set_plotarea({'border': {'color': '#cbd5e1'}})
        ws_c.insert_chart('B26', c3, {'x_scale': 1.3, 'y_scale': 1.2})
        
    output.seek(0)
    f_name = f"{display_name.replace(' ', '_')}_Model.xlsx"
    st.download_button(label="📥 Download Full Valuation Suite (.xlsx)", data=output.getvalue(), file_name=f_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
