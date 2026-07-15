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
        wacc = st.number_input("WACC / Hurdle Rate (%)", value=12.0)
        tax = st.number_input("Corporate Tax Rate (%)", value=25.0)
        pwr_cost = st.number_input("Energy Cost (₹/kWh)", value=8.5)
        unit_px = st.number_input("Unit Sale Price (₹)", value=1500.0)
        demand = st.number_input("Annual Demand", value=100000)

    with st.expander("🏚️ Scenario A: Old Machine"):
        old_salvage = st.number_input("Current Salvage (₹)", value=2000000)
        old_kwh = st.number_input("Old Energy (kWh/unit)", value=45.0)
        old_def = st.number_input("Old Defect Rate (%)", value=8.0)
        old_maint = st.number_input("Old Maint. (₹/Yr)", value=4500000)
        old_labor = st.number_input("Old Labor (₹/Yr)", value=3000000)

    with st.expander("✨ Scenario B: New Machine"):
        new_capex = st.number_input("New CapEx (₹)", value=35000000)
        new_kwh = st.number_input("New Energy (kWh/unit)", value=18.0)
        new_def = st.number_input("New Defect Rate (%)", value=1.5)
        new_maint = st.number_input("New Maint. (₹/Yr)", value=800000)
        new_labor = st.number_input("New Labor (₹/Yr)", value=1200000)
        new_salvage = st.number_input("End Salvage (₹)", value=5000000)
        
        st.caption("Financing:")
        debt_pct = st.number_input("Debt Funded (%)", value=70.0)
        debt_rate = st.number_input("Interest Rate (%)", value=9.0)
        debt_term = st.number_input("Loan Term (Yrs)", value=5)

# --- CORE ENGINE LOGIC ---
cols = [f"Yr {y}" for y in range(0, yrs + 1)]
idx = [
    "Gross Units Req.", "Good Units Sold", "Revenue",
    "Energy Cost", "Scrap Material Cost", "Labor Cost", "Maint. Cost", 
    "Total OpEx", "EBITDA", "Depreciation", "Interest", 
    "EBT", "Taxes", "Net Income", "CapEx / Salvage", "Principal Paid",
    "Levered Free Cash Flow", "Discount Factor", "PV of FCF"
]

df_A = pd.DataFrame(index=idx, columns=cols).fillna(0.0)
df_B = pd.DataFrame(index=idx, columns=cols).fillna(0.0)
raw_mat_cost = 400.0

loan_amt = new_capex * (debt_pct / 100.0)
eq_amt = new_capex - loan_amt
r_per = debt_rate / 100.0

if r_per > 0 and debt_term > 0:
    pmt = (r_per * loan_amt) / (1 - (1 + r_per)**-debt_term)
else:
    pmt = loan_amt / debt_term if debt_term > 0 else 0.0

depr_yr = (new_capex - new_salvage) / yrs
rem_bal = loan_amt

for y in range(1, yrs + 1):
    c = f"Yr {y}"
    disc = 1 / ((1 + wacc / 100.0) ** y)
    df_A.loc["Discount Factor", c] = disc
    df_B.loc["Discount Factor", c] = disc
    
    # -- SCENARIO A --
    gross_A = demand / (1 - (old_def / 100.0))
    df_A.loc["Gross Units Req.", c] = gross_A
    df_A.loc["Good Units Sold", c] = demand
    df_A.loc["Revenue", c] = demand * unit_px
    df_A.loc["Energy Cost", c] = gross_A * old_kwh * pwr_cost
    df_A.loc["Scrap Material Cost", c] = (gross_A - demand) * raw_mat_cost
    df_A.loc["Labor Cost", c] = old_labor
    df_A.loc["Maint. Cost", c] = old_maint
    
    opex_A = (df_A.loc["Energy Cost", c] + df_A.loc["Scrap Material Cost", c] + 
              df_A.loc["Labor Cost", c] + df_A.loc["Maint. Cost", c])
    df_A.loc["Total OpEx", c] = opex_A
    ebitda_A = df_A.loc["Revenue", c] - opex_A
    df_A.loc["EBITDA", c] = ebitda_A
    
    ebt_A = ebitda_A
    tax_A = max(ebt_A, 0) * (tax / 100.0)
    ni_A = ebt_A - tax_A
    
    fcf_A = ni_A
    if y == yrs:
        fcf_A += old_salvage
        df_A.loc["CapEx / Salvage", c] = old_salvage
        
    df_A.loc["Levered Free Cash Flow", c] = fcf_A
    df_A.loc["PV of FCF", c] = fcf_A * disc

    # -- SCENARIO B --
    gross_B = demand / (1 - (new_def / 100.0))
    df_B.loc["Gross Units Req.", c] = gross_B
    df_B.loc["Good Units Sold", c] = demand
    df_B.loc["Revenue", c] = demand * unit_px
    df_B.loc["Energy Cost", c] = gross_B * new_kwh * pwr_cost
    df_B.loc["Scrap Material Cost", c] = (gross_B - demand) * raw_mat_cost
    df_B.loc["Labor Cost", c] = new_labor
    df_B.loc["Maint. Cost", c] = new_maint
    
    opex_B = (df_B.loc["Energy Cost", c] + df_B.loc["Scrap Material Cost", c] + 
              df_B.loc["Labor Cost", c] + df_B.loc["Maint. Cost", c])
    df_B.loc["Total OpEx", c] = opex_B
    ebitda_B = df_B.loc["Revenue", c] - opex_B
    df_B.loc["EBITDA", c] = ebitda_B
    
    df_B.loc["Depreciation", c] = depr_yr
    
    if y <= debt_term:
        inter = rem_bal * r_per
        prin = pmt - inter
        rem_bal -= prin
    else:
        inter, prin = 0.0, 0.0
        
    df_B.loc["Interest", c] = inter
    df_B.loc["Principal Paid", c] = prin
    
    ebt_B = ebitda_B - depr_yr - inter
    tax_B = max(ebt_B, 0) * (tax / 100.0)
    ni_B = ebt_B - tax_B
    
    fcf_B = ni_B + depr_yr - prin
    if y == yrs:
        fcf_B += new_salvage
        df_B.loc["CapEx / Salvage", c] = new_salvage
        
    df_B.loc["Levered Free Cash Flow", c] = fcf_B
    df_B.loc["PV of FCF", c] = fcf_B * disc

# Year 0 Initials
df_A.loc["Discount Factor", "Yr 0"] = 1.0
df_B.loc["Discount Factor", "Yr 0"] = 1.0

init_outflow = eq_amt - old_salvage
df_B.loc["CapEx / Salvage", "Yr 0"] = -(new_capex - old_salvage)
df_B.loc["Levered Free Cash Flow", "Yr 0"] = -init_outflow
df_B.loc["PV of FCF", "Yr 0"] = -init_outflow

# --- METRICS ---
npv_A = df_A.loc["PV of FCF"].sum()
npv_B = df_B.loc["PV of FCF"].sum()
delta_npv = npv_B - npv_A

try: irr_B = np.irr(df_B.loc["Levered Free Cash Flow"].values.tolist()) * 100.0
except: irr_B = 0.0

cum_cf_A = np.cumsum(df_A.loc["Levered Free Cash Flow"].values)
cum_cf_B = np.cumsum(df_B.loc["Levered Free Cash Flow"].values)
delta_cfs = [b - a for a, b in zip(cum_cf_A, cum_cf_B)]

cross_yr = -1
for i, val in enumerate(delta_cfs):
    if val >= 0 and i > 0:
        cross_yr = i
        break

# --- FRONTEND UI (REEL STYLE) ---
st.markdown("<h1 style='color: #ffffff; font-weight: 800; font-size: 38px; letter-spacing: -1px;'>CAPEX OVERHAUL ENGINE</h1>", unsafe_allow_html=True)

advice = "🟢 APPROVE CAPEX" if delta_npv > 0 else "🔴 REJECT CAPEX"
reason = f"The retrofit drives a net value creation (Delta NPV) of ₹{delta_npv:,.0f}." if delta_npv > 0 else "Energy and scrap savings do not justify the cost of capital."

st.markdown(f"""
    <div class='terminal-box'>
        <span style='color:#00e5ff; font-weight:bold; letter-spacing:1px;'>// SYSTEM ADVISORY: {advice}</span><br><br>
        {reason} The financial model projects an Equity IRR of <strong>{irr_B:.1f}%</strong>.<br>
        Thermodynamic efficiency & yield optimization triggers an annual EBITDA expansion from 
        <span style='color:#f43f5e;'>₹{df_A.loc['EBITDA','Yr 1']:,.0f}</span> to <span style='color:#10b981;'>₹{df_B.loc['EBITDA','Yr 1']:,.0f}</span>.
    </div>
""", unsafe_allow_html=True)

# Custom Glassmorphism KPI Row
c1, c2, c3, c4 = st.columns(4)

delta_color = "emerald" if delta_npv > 0 else "rose"

c1.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Status Quo NPV</div>
        <div class="kpi-value">₹{npv_A/10000000:,.2f}Cr</div>
    </div>
""", unsafe_allow_html=True)

c2.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">New Machine NPV</div>
        <div class="kpi-value cyan">₹{npv_B/10000000:,.2f}Cr</div>
    </div>
""", unsafe_allow_html=True)

c3.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Value Created (Δ)</div>
        <div class="kpi-value {delta_color}">+ ₹{delta_npv/10000000:,.2f}Cr</div>
    </div>
""", unsafe_allow_html=True)

c4.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Equity IRR</div>
        <div class="kpi-value cyan">{irr_B:.1f}%</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- TERMINAL STYLE PLOTLY CHARTS ---
t1, t2, t3 = st.tabs(["📉 Cumulative Break-Even", "⚙️ OpEx Shift", "📄 Raw Data Export"])

CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#a1a1aa"),
    xaxis=dict(showgrid=False, zeroline=False, linecolor="#27272a"),
    yaxis=dict(showgrid=True, gridcolor="#27272a", zeroline=False),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

with t1:
    fig_line = go.Figure()
    # Neon Pink for Old, Neon Cyan for New
    fig_line.add_trace(go.Scatter(x=cols, y=cum_cf_A, name="Old Machine", line=dict(color="#f43f5e", width=4)))
    fig_line.add_trace(go.Scatter(x=cols, y=cum_cf_B, name="New Machine", line=dict(color="#00e5ff", width=4)))
    
    if cross_yr > 0:
        fig_line.add_vline(x=cross_yr, line_dash="dot", line_color="#10b981", annotation_text=f"Break-Even: Yr {cross_yr}", annotation_font_color="#10b981")
    
    fig_line.update_layout(**CHART_LAYOUT, height=450)
    st.plotly_chart(fig_line, use_container_width=True)

with t2:
    c1, c2 = st.columns(2)
    op_cols = ["Energy Cost", "Scrap Material Cost", "Labor Cost", "Maint. Cost"]
    colors = ['#00e5ff', '#3b82f6', '#f43f5e', '#10b981']
    
    with c1:
        vals_A = [df_A.loc[r, "Yr 1"] for r in op_cols]
        fig_pieA = go.Figure(go.Pie(labels=op_cols, values=vals_A, hole=0.6, marker_colors=colors))
        fig_pieA.update_layout(**CHART_LAYOUT, title="Old Machine OpEx (Yr 1)", height=350)
        st.plotly_chart(fig_pieA, use_container_width=True)
    with c2:
        vals_B = [df_B.loc[r, "Yr 1"] for r in op_cols]
        fig_pieB = go.Figure(go.Pie(labels=op_cols, values=vals_B, hole=0.6, marker_colors=colors))
        fig_pieB.update_layout(**CHART_LAYOUT, title="New Machine OpEx (Yr 1)", height=350)
        st.plotly_chart(fig_pieB, use_container_width=True)

with t3:
    st.info("📥 Export mathematical proof to Excel for Board review.")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_A.to_excel(writer, sheet_name='Scenario A (Old)')
        df_B.to_excel(writer, sheet_name='Scenario B (New)')
    output.seek(0)
    st.download_button(
        label="📥 Download Excel Terminal Export (.xlsx)", 
        data=output.getvalue(), 
        file_name="CapEx_Terminal_Model.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        use_container_width=True
    )