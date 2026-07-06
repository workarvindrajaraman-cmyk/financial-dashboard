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

# Custom Enterprise-Grade Styling
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
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
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
    div[data-testid="stMetricValue"] { color: #00b050; }
    div.stButton > button:first-child, div.stDownloadButton > button:first-child {
        background-color: #00b050 !important;
        color: white !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PORTFOLIO BRANDING ---
with st.sidebar:
    st.markdown("### 🏢 Analyst Portfolio")
    st.caption("Developed by: **Arvind Rajaraman**")
    st.divider()

# --- RESET FUNCTIONALITY ---
if st.sidebar.button("➕ Start New Model (Clear Data)", use_container_width=True, help="Wipes all data to start a fresh analysis."):
    st.session_state.clear()
    st.session_state['is_cleared'] = True
    st.rerun()

is_cleared = st.session_state.get('is_cleared', False)

# --- SIDEBAR: INPUT PARAMETERS ---
with st.sidebar:
    st.header("🎛️ Engine Controls")
    company_name = st.text_input("Company Name", value="" if is_cleared else "JK Tyres", help="This name will populate across all charts and the final Excel export.")
    unit = st.radio("Display Unit:", ["Crores", "Lakhs"], index=0, horizontal=True)
    
    st.divider()
    
    with st.expander("⏳ Timeline Settings", expanded=True):
        t1, t2 = st.columns(2)
        end_hist_year = t1.number_input("Last Actual Year", value=2023, step=1)
        hist_years_count = t2.number_input("Actual Years", min_value=1, max_value=10, value=2, step=1)
        forecast_years = st.slider("Forecast Horizon", min_value=1, max_value=10, value=4, help="Number of future years to project.")
    
    with st.expander("🏢 Historical Actuals", expanded=True):
        st.caption("Edit values directly in the grid below:")
        hist_years_list = [f"{end_hist_year - hist_years_count + 1 + i}A" for i in range(hist_years_count)]
        default_data = {"Metric": ["Revenue", "COGS", "S&G Expenses", "Depreciation", "Interest"]}
        for i, y in enumerate(hist_years_list):
            if not is_cleared and i == len(hist_years_list) - 2: 
                default_data[y] = [30000.0, 10000.0, 5000.0, 1000.0, 1500.0]
            elif not is_cleared and i == len(hist_years_list) - 1:
                default_data[y] = [40000.0, 12000.0, 6000.0, 1200.0, 2000.0]
            else:
                default_data[y] = [0.0, 0.0, 0.0, 0.0, 0.0]
                
        hist_df = pd.DataFrame(default_data).set_index("Metric")
        edited_hist_df = st.data_editor(hist_df, use_container_width=True)
        
        revenue = edited_hist_df.loc["Revenue"].tolist()
        cogs = edited_hist_df.loc["COGS"].tolist()
        sga = edited_hist_df.loc["S&G Expenses"].tolist()
        depreciation = edited_hist_df.loc["Depreciation"].tolist()
        interest = edited_hist_df.loc["Interest"].tolist()
    
    with st.expander("📈 Key Assumptions & Valuation", expanded=False):
        rev_growth_input = st.number_input("Forecast Revenue Growth (%)", value=0.0 if is_cleared else 35.0, step=1.0)
        cogs_percent_input = st.number_input("Forecast COGS % of Revenue", value=0.0 if is_cleared else 30.0, step=1.0)
        sga_input = st.number_input(f"Forecast S&G ({unit})", value=0.0 if is_cleared else 7000.0, step=500.0)
        dep_percent_input = st.number_input("Forecast Depreciation % Sales", value=0.0 if is_cleared else 5.0, step=0.5)
        interest_input = st.number_input(f"Forecast Interest ({unit})", value=0.0 if is_cleared else 2500.0, step=100.0)
        tax_input = st.number_input("Forecast Taxes (%)", value=0.0 if is_cleared else 30.0, step=1.0)
        st.divider()
        ev_multiple = st.number_input("Target EV/EBITDA Multiple", value=8.0, step=0.5, help="Used to calculate Implied Enterprise Value.")
    
    with st.expander("🔄 Sensitivity & Weights", expanded=False):
        change_pct_input = st.number_input("Scenario Change (%)", value=0.0 if is_cleared else 15.0, step=1.0)
        st.caption("Costing Analysis Weights")
        cw1, cw2 = st.columns(2)
        w_cogs, w_sga = cw1.number_input("COGS Wgt", value=0.1, step=0.1), cw2.number_input("S&G Wgt", value=0.2, step=0.1)
        w_dep, w_int = cw1.number_input("Dep Wgt", value=0.2, step=0.1), cw2.number_input("Int Wgt", value=0.2, step=0.1)
        w_tax = cw1.number_input("Tax Wgt", value=0.3, step=0.1)

# Variables
rev_growth, cogs_percent, dep_percent, tax_rate = rev_growth_input/100, cogs_percent_input/100, dep_percent_input/100, tax_input/100
change_modifier = 1 + (change_pct_input / 100)
weights_array = [w_cogs, w_sga, w_dep, w_int, w_tax]

# --- FINANCIAL ENGINE ---
years = hist_years_list + [f"{end_hist_year + i}F" for i in range(1, forecast_years + 1)]
for i in range(forecast_years): 
    prev_rev = revenue[-1]
    revenue.append(prev_rev * (1 + rev_growth))
    cogs.append(revenue[-1] * cogs_percent)
    sga.append(sga_input)
    depreciation.append(revenue[-1] * dep_percent)
    interest.append(interest_input)

df_is = pd.DataFrame({"Revenue": revenue, "COGS": cogs, "Selling, General & Adm Expenses": sga, "Depreciation": depreciation, "Interest": interest}, index=years).T
df_is.loc["Gross Profit"] = df_is.loc["Revenue"] - df_is.loc["COGS"]
df_is.loc["EBIDTA"] = df_is.loc["Gross Profit"] - df_is.loc["Selling, General & Adm Expenses"]
df_is.loc["EBT"] = df_is.loc["EBIDTA"] - df_is.loc["Depreciation"] - df_is.loc["Interest"]
df_is.loc["Tax"] = df_is.loc["EBT"] * tax_rate
df_is.loc["Net Income"] = df_is.loc["EBT"] - df_is.loc["Tax"]
df_is = df_is.reindex(["Revenue", "COGS", "Gross Profit", "Selling, General & Adm Expenses", "EBIDTA", "Depreciation", "Interest", "EBT", "Tax", "Net Income"])

# 2. Key Drivers
drivers_data = {}
for i, y in enumerate(hist_years_list):
    rev_val, prev_rev = revenue[i], revenue[i-1] if i > 0 else 0
    growth = f"{((rev_val / prev_rev) - 1) * 100:.2f}%" if prev_rev != 0 else "0.00%"
    cogs_p = f"{(cogs[i] / rev_val) * 100:.2f}%" if rev_val != 0 else "0.00%"
    dep_p = f"{(depreciation[i] / rev_val) * 100:.2f}%" if rev_val != 0 else "0.00%"
    tax_p = f"{tax_input:.2f}%" if i == len(hist_years_list)-1 else "NA"
    drivers_data[y] = [growth, cogs_p, f"{sga[i]:,.1f}", dep_p, f"{interest[i]:,.1f}", tax_p]
for i in range(1, forecast_years + 1):
    drivers_data[f"{end_hist_year+i}F"] = [f"{rev_growth_input:.2f}%", f"{cogs_percent_input:.2f}%", f"{sga_input:,.1f}", f"{dep_percent_input:.2f}%", f"{interest_input:,.1f}", f"{tax_input:.2f}%"]
df_drivers = pd.DataFrame(drivers_data, index=["Revenue Growth", "COGS % of Revenue", "S&G Expenses", "Depreciation % Sales", "Interest", "Taxes"])

# 3. Common Size & 4. Change Analysis
df_common = df_is.copy()
for col in df_common.columns: df_common[col] = (df_is[col] / df_is.loc["Revenue", col]).replace([np.inf, -np.inf], 0).fillna(0)
df_change = df_is * change_modifier

# 5. Costing Analysis
cost_rows = ["COGS", "Selling, General & Adm Expenses", "Depreciation", "Interest", "Tax"]
all_cost_rows = cost_rows + ["Total", " ", "Average", "Weighted Average", "Median", "  ", "Min", "Max", "Small", "Large"]
df_cost = pd.DataFrame(index=all_cost_rows)
weights_column = []
for r in all_cost_rows:
    if r in cost_rows: weights_column.append(weights_array[cost_rows.index(r)])
    elif r == "Total": weights_column.append(sum(weights_array))
    else: weights_column.append("")
df_cost["Weights"] = weights_column
for year in years:
    data = df_is.loc[cost_rows, year]
    df_cost.loc[cost_rows, year] = data
    df_cost.loc["Total", year] = data.sum()
    df_cost.loc["Average", year] = data.mean()
    df_cost.loc["Weighted Average", year] = sum(data * weights_array)
    df_cost.loc["Median", year] = data.median()
    df_cost.loc["Min", year] = data.min()
    df_cost.loc["Max", year] = data.max()
    df_cost.loc["Small", year] = data.nsmallest(2).iloc[-1]
    df_cost.loc["Large", year] = data.nlargest(2).iloc[-1]
df_cost = df_cost.astype(object).fillna("")

# --- EXCEL ENGINE ---
@st.cache_data(show_spinner=False)
def generate_excel(df_is_c, df_drivers_c, df_common_c, df_change_c, df_cost_c, c_name, u_name, c_pct, y_list):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook, worksheet = writer.book, writer.book.add_worksheet('Financial Report')
        worksheet.hide_gridlines(2)
        top_header_fmt = workbook.add_format({'bg_color': '#00b050', 'font_color': 'white', 'bold': True, 'border': 1})
        sub_header_fmt = workbook.add_format({'bg_color': '#c4d79b', 'bold': True, 'border': 1})
        company_fmt, index_fmt, bold_index_fmt = workbook.add_format({'bold': True}), workbook.add_format({'border': 1}), workbook.add_format({'bold': True, 'border': 1})
        money_fmt, bold_money_fmt = workbook.add_format({'num_format': '#,##0.0', 'border': 1}), workbook.add_format({'bold': True, 'num_format': '#,##0.0', 'border': 1})
        pct_fmt, blue_pct_fmt, weight_fmt = workbook.add_format({'num_format': '0.00%', 'border': 1}), workbook.add_format({'font_color': 'blue', 'num_format': '0.00%', 'bold': True}), workbook.add_format({'num_format': '0.1', 'border': 1, 'align': 'center'})
        worksheet.set_column(0, 0, 35); worksheet.set_column(1, 1, 10); worksheet.set_column(2, len(y_list) + 1, 15) 
        worksheet.merge_range(0, 0, 0, 1, f"INR ({u_name})", top_header_fmt)
        for col_num, year in enumerate(y_list): worksheet.write(0, col_num + 2, year, top_header_fmt)
        worksheet.write(1, 0, c_name if c_name else "New Model", company_fmt)
        current_row = 2
        def write_table(df_ref, title, start_row, is_pct=False, is_drivers=False, bold_rows=[], has_weights=False):
            if title:
                if has_weights: worksheet.write(start_row, 0, title, sub_header_fmt); worksheet.write(start_row, 1, "Weights", sub_header_fmt)
                else: worksheet.merge_range(start_row, 0, start_row, 1, title, sub_header_fmt)
                for c in range(2, len(y_list) + 2): worksheet.write(start_row, c, "", sub_header_fmt)
                start_row += 1
            r = start_row
            for index_val in df_ref.index:
                is_bold = index_val in bold_rows
                if has_weights: worksheet.write(r, 0, index_val, bold_index_fmt if is_bold else index_fmt)
                else: worksheet.merge_range(r, 0, r, 1, index_val, bold_index_fmt if is_bold else index_fmt)
                for c, val in enumerate(df_ref.loc[index_val]):
                    col_index = c + 1 if has_weights else c + 2
                    if pd.isna(val) or val == "" or val == " ": worksheet.write(r, col_index, "", index_fmt); continue
                    if is_drivers or (is_pct and c > 0 if has_weights else is_pct): worksheet.write(r, col_index, val, index_fmt if is_drivers else pct_fmt)
                    elif has_weights and c == 0: worksheet.write(r, col_index, val, bold_index_fmt if is_bold else weight_fmt)
                    else: worksheet.write(r, col_index, val, bold_money_fmt if is_bold else money_fmt)
                r += 1
            return r
        current_row = write_table(df_is_c, f"Income Statement - {c_name}", current_row, bold_rows=['Gross Profit', 'EBIDTA', 'EBT', 'Net Income'])
        current_row = write_table(df_drivers_c, f"Key Assumption Drivers - {c_name}", current_row + 1, is_drivers=True)
        current_row = write_table(df_common_c, f"Common Size Statement - {c_name}", current_row + 1, is_pct=True)
        worksheet.merge_range(current_row + 1, 0, current_row + 1, 1, f"Change Analysis Statement - {c_name}", sub_header_fmt)
        for c in range(2, len(y_list) + 2): worksheet.write(current_row + 1, c, "", sub_header_fmt)
        worksheet.merge_range(current_row + 2, 0, current_row + 2, 1, f"{c_pct}%", blue_pct_fmt)
        current_row = write_table(df_change_c, "", current_row + 3, bold_rows=['Gross Profit', 'EBIDTA', 'EBT', 'Net Income'])
        current_row = write_table(df_cost_c, f"Costing Analysis", current_row + 1, bold_rows=['Total'], has_weights=True)
    return output.getvalue()

# --- UI DISPLAY ---
display_name = company_name if company_name else "New Model"
st.title(f"📈 {display_name} Corporate Analytics Suite")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
final_yr, base_yr = years[-1], hist_years_list[-1]
final_rev_val, final_ebitda_val = df_is.loc['Revenue', final_yr], df_is.loc['EBIDTA', final_yr]
ebitda_margin_calc = (final_ebitda_val / final_rev_val) * 100 if final_rev_val != 0 else 0.0

kpi1.metric(f"Projected Revenue ({final_yr})", f"{final_rev_val:,.1f}", f"{final_rev_val - df_is.loc['Revenue', base_yr]:,.1f} from {base_yr}")
kpi2.metric(f"Projected Net Income ({final_yr})", f"{df_is.loc['Net Income', final_yr]:,.1f}", f"{df_is.loc['Net Income', final_yr] - df_is.loc['Net Income', base_yr]:,.1f} from {base_yr}")
kpi3.metric("Terminal EBITDA Margin", f"{ebitda_margin_calc:.1f}%", "Profitability Metric")
kpi4.metric(f"Implied EV ({ev_multiple}x)", f"{final_ebitda_val * ev_multiple:,.1f}", "Derived via EV/EBITDA")

st.divider()
tab1, tab2, tab3 = st.tabs(["📑 Master Statements", "📊 Visual Analytics", "🔬 Deep Dive Analysis"])
def style_df(df, bold_rows): return df.style.format("{:,.1f}", na_rep="").apply(lambda r: ['font-weight: bold; color: black; background-color: #f8f9fa;'] * len(r) if r.name in bold_rows else [''] * len(r), axis=1)

with tab1:
    col_dl, _ = st.columns([1, 2])
    excel_binary = generate_excel(df_is, df_drivers, df_common, df_change, df_cost, display_name, unit, change_pct_input, years)
    col_dl.download_button("📥 Download Enterprise Excel Report", excel_binary, f"{display_name.replace(' ', '_')}_Pro_Forma.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    st.subheader(f"Income Statement - INR ({unit})"); st.dataframe(style_df(df_is, ['Gross Profit', 'EBIDTA', 'EBT', 'Net Income']), width="stretch")
    st.subheader("Key Assumption Drivers"); st.dataframe(df_drivers, width="stretch")
    st.subheader("Common Size Statement"); st.dataframe(df_common.style.format("{:.2%}"), width="stretch")
with tab2:
    st.subheader("Financial Trajectory & Profitability")
    c1, c2 = st.columns(2)
    chart_df = df_is.T.reset_index().rename(columns={'index': 'Year'})
    fig1 = px.bar(chart_df, x='Year', y='Revenue', title="Revenue vs. Profitability Growth", template="plotly_dark")
    fig1.add_trace(go.Scatter(x=chart_df['Year'], y=chart_df['EBIDTA'], mode='lines+markers', name='EBITDA', line=dict(color='#00b050', width=3)))
    c1.plotly_chart(fig1, use_container_width=True)
    final_costs = df_cost.loc[['COGS', 'Selling, General & Adm Expenses', 'Depreciation', 'Interest', 'Tax'], final_yr].reset_index()
    final_costs.columns = ['Cost Component', 'Value']
    fig2 = px.pie(final_costs, values='Value', names='Cost Component', hole=0.5, title=f"Terminal Cost Structure ({final_yr})", template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
    c2.plotly_chart(fig2, use_container_width=True)
with tab3:
    st.subheader(f"Change Analysis ({change_pct_input}% Scenario)"); st.dataframe(style_df(df_change, ['Gross Profit', 'EBIDTA', 'EBT', 'Net Income']), width="stretch")
    st.subheader("Costing & Statistical Analysis"); st.dataframe(df_cost.style.format(lambda v: f"{v:,.1f}" if isinstance(v, (int, float)) else v).apply(lambda r: ['font-weight: bold; color: black; background-color: #f8f9fa;'] * len(r) if r.name == 'Total' else [''] * len(r), axis=1), width="stretch")