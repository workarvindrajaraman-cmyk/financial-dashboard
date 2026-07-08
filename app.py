import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go

# --- DASHBOARD CONFIGURATION ---
st.set_page_config(page_title="Corporate Financial Engine", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state['initialized'] = True

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

# --- SIDEBAR: DATA CONTROLS ---
with st.sidebar:
    st.header("🎛️ Engine Controls")
    company_name = st.text_input("Company Name", value="", placeholder="Enter Company Name...")

    unit = st.radio("Display Unit:", ["Crores", "Lakhs"], index=0, horizontal=True)
    input_scale = st.radio("Data Input Format:", [f"Already in {unit}", "Raw Values (Needs Scaling)"], index=0, help="If raw, engine will divide by 1Cr or 1Lakh automatically.")
    unit_suffix = "₹ Cr" if unit == "Crores" else "₹ L"

    st.divider()
    
    with st.expander("⏳ Timeline Settings", expanded=True):
        t1, t2 = st.columns(2)
        end_hist_year = t1.number_input("Last Actual Year", value=2023, step=1)
        hist_years_count = t2.number_input("Actual Years", min_value=1, max_value=10, value=2, step=1)
        forecast_years = st.slider("Forecast Horizon", min_value=1, max_value=10, value=5)

    hist_years_list = [f"{end_hist_year - hist_years_count + 1 + i}A" for i in range(hist_years_count)]

    metrics = [
        "Revenue", "COGS", "S&G Expenses", "Depreciation", "Interest",
        "Current Assets", "Total Assets", "Current Liabilities", "Total Debt", "Total Equity",
        "Operating CF", "CapEx", "Financing CF", "Shares Outstanding"
    ]
    default_data = {"Metric": metrics}
    for y in hist_years_list:
        default_data[y] = [0.0] * len(metrics)

    hist_df_template = pd.DataFrame(default_data).set_index("Metric")

    with st.expander(f"🏢 Historical Actuals ({unit_suffix})", expanded=True):
        edited_hist_df = st.data_editor(hist_df_template, use_container_width=True)

    with st.expander("📈 Forecasting & DCF Assumptions"):
        rev_growth_input = st.number_input("Forecast Revenue Growth (%)", value=15.0, step=1.0)
        cogs_percent_input = st.number_input("Forecast COGS % of Revenue", value=30.0, step=1.0)
        tax_input = st.number_input("Forecast Taxes (%)", value=25.0, step=1.0)
        wacc_input = st.number_input("WACC (Discount Rate %)", value=10.0, step=0.5)
        tg_input = st.number_input("Terminal Growth Rate (%)", value=2.5, step=0.1)

# --- FINANCIAL ENGINE CORE ---
years = hist_years_list + [f"{end_hist_year + i}F" for i in range(1, forecast_years + 1)]
forecast_year_labels = [y for y in years if "F" in y]

df_master = pd.DataFrame(index=metrics, columns=years, dtype=float)
df_master = df_master.fillna(0.0)

divisor = 10000000.0 if (input_scale == "Raw Values (Needs Scaling)" and unit == "Crores") else (100000.0 if input_scale == "Raw Values (Needs Scaling)" and unit == "Lakhs" else 1.0)

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

    prev_rev = float(df_master.loc["Revenue", prev_y]) if float(df_master.loc["Revenue", prev_y]) != 0 else 0.0

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

# Derived P&L Lines
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

# --- KPI CALCULATIONS ---
def safe_div(a, b):
    try:
        a, b = float(a), float(b)
        return a / b if b != 0 else 0.0
    except:
        return 0.0

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

# --- DCF VALUATION ---
base_yr = hist_years_list[-1]
final_yr = years[-1]

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

# --- WACC x TGR SENSITIVITY MATRIX ---
wacc_range = np.round(np.arange(wacc_input - 2.0, wacc_input + 2.5, 0.5), 1)
tgr_range = np.round(np.arange(tg_input - 1.0, tg_input + 1.5, 0.5), 1)

def dcf_ev(w, tg):
    disc = [(1 + w / 100) ** (i + 1) for i in range(len(forecast_year_labels))]
    pv = sum([fcf / d for fcf, d in zip(fcf_series, disc)])
    denom_ = (w / 100) - (tg / 100)
    tv = (last_fcf * (1 + tg / 100)) / denom_ if denom_ > 0 else 0.0
    ptv = tv / disc[-1] if disc else 0.0
    return pv + ptv

def dcf_price(w, tg):
    ev = dcf_ev(w, tg)
    eq = ev - net_debt
    return safe_div(eq, shares)

sensitivity_ev = pd.DataFrame(index=[f"{w}%" for w in wacc_range], columns=[f"{t}%" for t in tgr_range])
sensitivity_price = pd.DataFrame(index=[f"{w}%" for w in wacc_range], columns=[f"{t}%" for t in tgr_range])

for w in wacc_range:
    for t in tgr_range:
        if w / 100 > t / 100:
            sensitivity_ev.loc[f"{w}%", f"{t}%"] = round(dcf_ev(w, t), 1)
            sensitivity_price.loc[f"{w}%", f"{t}%"] = round(dcf_price(w, t), 2)
        else:
            sensitivity_ev.loc[f"{w}%", f"{t}%"] = np.nan
            sensitivity_price.loc[f"{w}%", f"{t}%"] = np.nan

sensitivity_ev = sensitivity_ev.astype(float)
sensitivity_price = sensitivity_price.astype(float)

# --- HEADER ---
display_name = company_name if company_name else "New Model"
st.title(f"📈 {display_name} — Corporate Analytics & Valuation Suite")
st.caption(f"All figures in **{unit_suffix}** · Indian Financial Standards")

has_data = float(df_master.loc["Revenue", base_yr]) > 0

if has_data:
    rev_base = float(df_master.loc["Revenue", base_yr])
    rev_final = float(df_master.loc["Revenue", final_yr])
    ebitda_base = float(kpi_df.loc["EBITDA Margin (%)", base_yr])
    ebitda_final = float(kpi_df.loc["EBITDA Margin (%)", final_yr])
    de_final = float(kpi_df.loc["Debt to Equity", final_yr])
    st.markdown(f"""
        <div class="ai-box">
            <strong>🤖 AI Analyst Summary:</strong><br>
            Revenue is forecast to grow at <strong>{rev_growth_input}%</strong> p.a., driving top-line from 
            <strong>{unit_suffix} {rev_base:,.1f}</strong> ({base_yr}) to <strong>{unit_suffix} {rev_final:,.1f}</strong> ({final_yr}). 
            EBITDA margins are projected to shift from <strong>{ebitda_base:.1f}%</strong> to <strong>{ebitda_final:.1f}%</strong>. 
            Based on the DCF valuation (WACC: {wacc_input}%, Terminal Growth: {tg_input}%), the implied Enterprise Value is <strong>{unit_suffix} {enterprise_value:,.1f}</strong>, 
            yielding an intrinsic share price of <strong>{unit_suffix} {implied_share_price:,.2f}</strong>. 
            Debt/Equity ratio shifts to <strong>{de_final:.2f}x</strong> by {final_yr}.
        </div>
    """, unsafe_allow_html=True)
else:
    st.info("💡 Enter historical actuals in the sidebar to generate the AI Analyst Summary and all charts.")

st.subheader("Key Performance Indicators")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric(f"Revenue ({final_yr})", f"{unit_suffix} {df_master.loc['Revenue', final_yr]:,.0f}")
k2.metric(f"EBITDA ({final_yr})", f"{unit_suffix} {df_master.loc['EBITDA', final_yr]:,.0f}")
k3.metric("Terminal ROE", f"{kpi_df.loc['ROE (%)', final_yr]:.1f}%")
k4.metric("Free Cash Flow", f"{unit_suffix} {df_master.loc['Free Cash Flow', final_yr]:,.0f}")
k5.metric("Enterprise Value", f"{unit_suffix} {enterprise_value:,.1f}")
k6.metric("Implied Share Price", f"{unit_suffix} {implied_share_price:,.2f}")

st.divider()

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📑 Master Statements", "📊 Advanced KPIs", "💰 DCF Valuation", "🎯 Sensitivity Analysis", "🔬 Download & Exports"])

DARK_TEMPLATE = "plotly_dark"
GREEN, RED, BLUE, AMBER = "#00b050", "#ef4444", "#3b82f6", "#f59e0b"

with tab1:
    st.subheader(f"Income Statement ({unit_suffix})")
    is_rows = ["Revenue", "COGS", "Gross Profit", "Gross Margin (%)", "S&G Expenses", "EBITDA", "EBITDA Margin (%)", "Depreciation", "EBIT", "Interest", "EBT", "Tax", "Net Income", "Net Margin (%)"]
    is_df = df_master.loc[[r for r in is_rows if r in df_master.index]]

    def style_is(df):
        styled = df.style.format(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
        def row_color(row_name):
            if "Margin" in row_name or "%" in row_name: return "background-color: #1a2e1a; color: #00b050; font-style: italic;"
            elif row_name in ["Gross Profit", "EBITDA", "Net Income"]: return "background-color: #0d1f0d; font-weight: bold; color: #00b050;"
            return ""
        for row in df.index:
            style = row_color(row)
            if style: styled = styled.apply(lambda x, r=row, s=style: [s if x.name == r else "" for _ in x], axis=1)
        return styled

    st.dataframe(style_is(is_df), use_container_width=True)

    st.subheader("📈 Revenue, EBITDA & Net Income Trend")
    fig_trend = go.Figure()
    
    # Safely broken down lines to prevent truncation
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
            annotation_text="Forecast →", 
            annotation_position="top right", 
            annotation_font_color="#94a3b8"
        )
    
    fig_trend.update_layout(
        template=DARK_TEMPLATE, 
        barmode="group", 
        title=f"Revenue, EBITDA & Net Income ({unit_suffix})", 
        xaxis_title="Year", 
        yaxis_title=unit_suffix, 
        legend=dict(orientation="h", y=1.1), 
        height=420
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_fcf = go.Figure()
        fcf_vals = df_master.loc["Free Cash Flow", years].values.tolist()
        
        fig_fcf.add_trace(go.Bar(
            x=years, 
            y=fcf_vals, 
            marker_color=[GREEN if v >= 0 else RED for v in fcf_vals], 
            name="FCF"
        ))
        
        fig_fcf.add_trace(go.Scatter(
            x=years, 
            y=df_master.loc["Operating CF", years].values.tolist(), 
            name="Operating CF", 
            mode="lines+markers", 
            line=dict(color=AMBER, width=2), 
            marker=dict(size=6)
        ))
        
        fig_fcf.update_layout(
            template=DARK_TEMPLATE, 
            title=f"Free Cash Flow vs Operating CF ({unit_suffix})", 
            xaxis_title="Year", 
            yaxis_title=unit_suffix, 
            height=380
        )
        st.plotly_chart(fig_fcf, use_container_width=True)

    with c2:
        fig_margins = go.Figure()
        
        fig_margins.add_trace(go.Scatter(
            x=years, 
            y=df_master.loc["Gross Margin (%)", years].values.tolist(), 
            name="Gross Margin", 
            mode="lines+markers", 
            line=dict(color=GREEN, width=3), 
            marker=dict(size=7)
        ))
        
        fig_margins.add_trace(go.Scatter(
            x=years, 
            y=df_master.loc["EBITDA Margin (%)", years].values.tolist(), 
            name="EBITDA Margin", 
            mode="lines+markers", 
            line=dict(color=BLUE, width=3), 
            marker=dict(size=7)
        ))
        
        fig_margins.add_trace(go.Scatter(
            x=years, 
            y=df_master.loc["Net Margin (%)", years].values.tolist(), 
            name="Net Margin", 
            mode="lines+markers", 
            line=dict(color=AMBER, width=3), 
            marker=dict(size=7)
        ))
        
        fig_margins.update_layout(
            template=DARK_TEMPLATE, 
            title="Margin Evolution (%)", 
            xaxis_title="Year", 
            yaxis_title="%", 
            height=380
        )
        st.plotly_chart(fig_margins, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader(f"Balance Sheet ({unit_suffix})")
        st.dataframe(df_master.loc[["Total Assets", "Current Assets", "Current Liabilities", "Total Debt", "Total Equity"]].style.format("{:,.1f}", na_rep="—"), use_container_width=True)
    with c4:
        st.subheader(f"Cash Flow Statement ({unit_suffix})")
        st.dataframe(df_master.loc[["Operating CF", "CapEx", "Financing CF", "Free Cash Flow", "Net Cash Flow"]].style.format("{:,.1f}", na_rep="—"), use_container_width=True)

with tab2:
    st.subheader(f"Advanced Financial Metrics")
    st.dataframe(kpi_df.style.format("{:,.2f}", na_rep="—"), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_returns = go.Figure()
        
        fig_returns.add_trace(go.Bar(
            x=years, 
            y=kpi_df.loc["ROE (%)", years].values.tolist(), 
            name="ROE (%)", 
            marker_color=GREEN
        ))
        
        fig_returns.add_trace(go.Bar(
            x=years, 
            y=kpi_df.loc["ROCE (%)", years].values.tolist(), 
            name="ROCE (%)", 
            marker_color=BLUE
        ))
        
        fig_returns.update_layout(
            template=DARK_TEMPLATE, 
            barmode="group", 
            title="Return on Capital Metrics (%)", 
            xaxis_title="Year", 
            yaxis_title="%", 
            height=380
        )
        st.plotly_chart(fig_returns, use_container_width=True)

    with c2:
        fig_lev = go.Figure()
        
        fig_lev.add_trace(go.Scatter(
            x=years, 
            y=kpi_df.loc["Debt to Equity", years].values.tolist(), 
            name="D/E Ratio", 
            mode="lines+markers", 
            line=dict(color=RED, width=3), 
            marker=dict(size=8)
        ))
        
        fig_lev.add_trace(go.Scatter(
            x=years, 
            y=kpi_df.loc["Current Ratio", years].values.tolist(), 
            name="Current Ratio", 
            mode="lines+markers", 
            line=dict(color=GREEN, width=3), 
            marker=dict(size=8)
        ))
        
        fig_lev.update_layout(
            template=DARK_TEMPLATE, 
            title="Leverage & Liquidity Ratios", 
            xaxis_title="Year", 
            yaxis_title="Ratio (x)", 
            height=380
        )
        st.plotly_chart(fig_lev, use_container_width=True)

with tab3:
    st.subheader("Discounted Cash Flow (DCF) Breakdown")
    dcf_data = {
        "Metric": ["Present Value of FCFs", "Terminal Value (TV)", "Present Value of TV", "Enterprise Value (EV)", "Less: Total Debt", "Add: Cash (Proxy)", "Equity Value", "Shares Outstanding", "Implied Share Price"],
        f"Value ({unit_suffix})": [pv_fcf_total, terminal_value, pv_tv, enterprise_value, float(df_master.loc["Total Debt", base_yr]), float(df_master.loc["Current Assets", base_yr]), equity_value, shares, implied_share_price]
    }
    st.dataframe(pd.DataFrame(dcf_data).set_index("Metric").style.format("{:,.2f}", na_rep="—"), use_container_width=True)

    st.divider()
    st.subheader("🏗️ Enterprise Value Bridge (Waterfall)")
    
    net_debt_val = float(df_master.loc["Total Debt", base_yr]) - float(df_master.loc["Current Assets", base_yr])
    
    fig_bridge = go.Figure(go.Waterfall(
        name="EV Bridge", 
        orientation="v", 
        measure=["relative", "relative", "total", "relative", "total"],
        x=["PV of FCFs", "PV of Terminal Value", "Enterprise Value", "Less: Net Debt", "Equity Value"],
        y=[pv_fcf_total, pv_tv, 0, -net_debt_val, 0],
        connector={"line": {"color": "#475569"}}, 
        increasing={"marker": {"color": GREEN}}, 
        decreasing={"marker": {"color": RED}}, 
        totals={"marker": {"color": "#3b82f6"}},
        text=[
            f"{unit_suffix} {pv_fcf_total:,.1f}", 
            f"{unit_suffix} {pv_tv:,.1f}", 
            f"{unit_suffix} {enterprise_value:,.1f}", 
            f"({unit_suffix} {abs(net_debt_val):,.1f})" if net_debt_val > 0 else f"{unit_suffix} {abs(net_debt_val):,.1f}", 
            f"{unit_suffix} {equity_value:,.1f}"
        ],
        textposition="outside"
    ))
    
    fig_bridge.update_layout(
        template=DARK_TEMPLATE, 
        title=f"EV Bridge: PV of FCFs + Terminal Value → Equity Value ({unit_suffix})", 
        yaxis_title=unit_suffix, 
        height=480, 
        showlegend=False
    )
    st.plotly_chart(fig_bridge, use_container_width=True)

with tab4:
    st.subheader("🎯 WACC × Terminal Growth Rate Sensitivity Analysis")
    st.caption(f"Base case: WACC = {wacc_input}% | TGR = {tg_input}% | All values in {unit_suffix}")

    col_sens1, col_sens2 = st.columns(2)
    with col_sens1:
        st.markdown(f"#### Enterprise Value Sensitivity ({unit_suffix})")
        def color_ev_cell(val):
            if pd.isna(val): return "background-color: #1e293b; color: #64748b;"
            if val > enterprise_value * 1.05: return "background-color: #052e0a; color: #00b050; font-weight: bold;"
            elif val > enterprise_value * 0.95: return "background-color: #0d2818; color: #86efac;"
            elif val < enterprise_value * 0.90: return "background-color: #2d0a0a; color: #fca5a5;"
            return "background-color: #1a1a2e; color: #cbd5e1;"
        st.dataframe(sensitivity_ev.style.map(color_ev_cell).format("{:,.1f}", na_rep="N/A"), use_container_width=True)

    with col_sens2:
        st.markdown(f"#### Implied Share Price Sensitivity ({unit_suffix})")
        def color_price_cell(val):
            if pd.isna(val): return "background-color: #1e293b; color: #64748b;"
            if implied_share_price != 0:
                if val > implied_share_price * 1.10: return "background-color: #052e0a; color: #00b050; font-weight: bold;"
                elif val > implied_share_price * 0.95: return "background-color: #0d2818; color: #86efac;"
                elif val < implied_share_price * 0.85: return "background-color: #2d0a0a; color: #fca5a5;"
            return "background-color: #1a1a2e; color: #cbd5e1;"
        st.dataframe(sensitivity_price.style.map(color_price_cell).format("{:,.2f}", na_rep="N/A"), use_container_width=True)

    st.divider()
    st.subheader("🌡️ EV Sensitivity Heatmap")
    ev_heatmap_data = sensitivity_ev.fillna(0).values.tolist()
    
    fig_heat = go.Figure(data=go.Heatmap(
        z=ev_heatmap_data, 
        x=[f"TGR {c}" for c in sensitivity_ev.columns], 
        y=[f"WACC {r}" for r in sensitivity_ev.index],
        colorscale=[[0.0, "#2d0a0a"], [0.3, "#7f1d1d"], [0.5, "#1a2e1a"], [0.7, "#14532d"], [1.0, "#00b050"]],
        text=[[f"{unit_suffix}\n{v:,.0f}" if v != 0 else "N/A" for v in row] for row in ev_heatmap_data], 
        texttemplate="%{text}", 
        textfont={"size": 11}, 
        hoverongaps=False
    ))
    
    fig_heat.update_layout(
        template=DARK_TEMPLATE, 
        title=f"Enterprise Value Sensitivity ({unit_suffix})", 
        xaxis_title="Terminal Growth Rate", 
        yaxis_title="WACC", 
        height=420
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with tab5:
    st.info("📥 Export the fully-linked three-statement model, KPIs, DCF, and sensitivity matrix to Excel.")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_master.to_excel(writer, sheet_name='Three Statement Model', startrow=2)
        kpi_df.to_excel(writer, sheet_name='Advanced KPIs', startrow=2)
        pd.DataFrame(dcf_data).set_index("Metric").to_excel(writer, sheet_name='DCF Valuation', startrow=2)
        sensitivity_ev.to_excel(writer, sheet_name='Sensitivity - EV', startrow=3)
        sensitivity_price.to_excel(writer, sheet_name='Sensitivity - Price', startrow=3)
    
    output.seek(0)

    st.download_button(
        label="📥 Download Full Valuation Suite (.xlsx)",
        data=output.getvalue(),
        file_name=f"{display_name.replace(' ', '_')}_Valuation_Suite.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
