import streamlit as st
import pandas as pd
import numpy as np
from data_fetcher import fetch_damodaran_data, calculate_beta, fetch_risk_free_rate

st.set_page_config(page_title="Valuation Dashboard", layout="wide")

st.title("Interactive Valuation Dashboard (FCFF)")

# Cache data fetching
@st.cache_data
def get_damodaran_data():
    return fetch_damodaran_data()

@st.cache_data
def get_risk_free_rate():
    return fetch_risk_free_rate()

@st.cache_data
def get_beta(ticker, benchmark):
    return calculate_beta(ticker, benchmark)

# Load base data
df_erp = get_damodaran_data()
rfr = get_risk_free_rate()

st.header("1. Cost of Capital (WACC) Assumptions")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Cost of Equity (Ke)")
    if df_erp is not None:
        countries = df_erp['Country'].tolist()
        default_idx = countries.index("United States") if "United States" in countries else 0
        selected_country = st.selectbox("Select Country for ERP", countries, index=default_idx, key="country_select")
        country_erp = df_erp[df_erp['Country'] == selected_country]['Total_ERP'].values[0]
    else:
        selected_country = "United States"
        country_erp = 0.045
        st.warning("Could not fetch Damodaran data. Using 4.5% default ERP.")

    ticker = st.text_input("Stock Ticker (for Beta)", value="AAPL", key="stock_ticker")
    benchmark = st.text_input("Benchmark Ticker", value="^GSPC", key="bench_ticker")
    
    calc_beta = get_beta(ticker, benchmark)
    if calc_beta is None:
        st.warning("Could not calculate beta. Using 1.0 default.")
        calc_beta = 1.0
        
    beta = st.number_input("Beta", value=float(calc_beta), format="%.4f", key="beta_input")
    rfr_input = st.number_input("Risk Free Rate", value=float(rfr), format="%.4f", key="rfr_input")
    erp_input = st.number_input("Equity Risk Premium (ERP)", value=float(country_erp), format="%.4f", key="erp_input")
    
    size_premium = st.number_input("Size Premium (%)", value=0.0, format="%.2f", key="sp_input") / 100.0
    csrp = st.number_input("Company Specific Risk Premium (%)", value=0.0, format="%.2f", key="csrp_input") / 100.0
    ke = rfr_input + (beta * erp_input) + size_premium + csrp
    st.metric("Calculated Cost of Equity (Ke)", f"{ke*100:.2f}%")

with col2:
    st.subheader("Cost of Debt (Kd) & Capital Structure")
    total_debt = st.number_input("Total Debt ($)", min_value=0.0, value=100000.0, key="debt_input")
    total_equity = st.number_input("Total Equity (Market Cap) ($)", min_value=0.0, value=400000.0, key="equity_input")
    kd_input = st.number_input("Pre-Tax Cost of Debt", value=0.05, format="%.4f", key="kd_input")
    tax_rate = st.number_input("Effective Tax Rate", value=0.21, format="%.4f", key="tax_input")
    
    total_capital = total_debt + total_equity
    if total_capital > 0:
        weight_debt = total_debt / total_capital
        weight_equity = total_equity / total_capital
    else:
        weight_debt = 0.0
        weight_equity = 1.0
        
    st.write(f"Weight of Equity: **{weight_equity*100:.2f}%**")
    st.write(f"Weight of Debt: **{weight_debt*100:.2f}%**")

with col3:
    st.subheader("WACC Calculation")
    calculated_wacc = (weight_equity * ke) + (weight_debt * kd_input * (1 - tax_rate))
    st.metric("Calculated WACC", f"{calculated_wacc*100:.2f}%")
    
    st.markdown("---")
    final_wacc = st.number_input("Override WACC for Valuation", value=float(calculated_wacc), format="%.4f", key="wacc_input")
    st.success(f"Final WACC used for Valuation: {final_wacc*100:.2f}%")


st.header("2. Financial Data (5 Years Historical)")

metric_choice = st.selectbox("Base Metric to calculate FCFF", ["CFO (Cash Flow from Operations)", "Net Income", "EBIT", "EBITDA"], key="metric_select")

# Define required rows based on chosen metric
required_rows = []
base_nwc_rows = ["Accounts Receivable", "Inventory", "Accounts Payable", "Stock-Based Compensation", "CapEx"]

if metric_choice == "CFO (Cash Flow from Operations)":
    # Working capital changes are typically already included in CFO. 
    # We only add back Interest*(1-t) and subtract CapEx.
    # Stock-Based Compensation is often a non-cash add-back already in CFO, but we allow an explicit input if needed.
    required_rows = ["CFO", "Interest Expense", "Stock-Based Compensation", "CapEx"]
elif metric_choice == "Net Income":
    required_rows = ["Net Income", "D&A", "Interest Expense"] + base_nwc_rows
elif metric_choice == "EBIT":
    required_rows = ["EBIT", "D&A"] + base_nwc_rows
elif metric_choice == "EBITDA":
    required_rows = ["EBITDA", "D&A"] + base_nwc_rows

# Prepare an empty DataFrame with 5 years
years = ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
initial_data = pd.DataFrame(0.0, index=required_rows, columns=years)

st.write("Enter historical financials (Year 1 is oldest, Year 5 is most recent).")
st.info("For Working Capital (AR, Inventory, AP), enter the absolute balances. The app will calculate the Year-over-Year changes. Year 1 changes assume prior year was the same as Year 1 (Change = 0).")
edited_df = st.data_editor(initial_data, use_container_width=True, key="financials_grid")

# Calculate historical FCFF based on edited_df
historical_fcff = pd.Series(0.0, index=years)

for i, yr in enumerate(years):
    try:
        # Calculate NWC Change for Net Income, EBIT, EBITDA
        if metric_choice != "CFO (Cash Flow from Operations)":
            if i == 0:
                # First year NWC change is 0 since we lack prior year data
                delta_nwc = 0.0
            else:
                prev_yr = years[i-1]
                ar_change = edited_df.loc["Accounts Receivable", yr] - edited_df.loc["Accounts Receivable", prev_yr]
                inv_change = edited_df.loc["Inventory", yr] - edited_df.loc["Inventory", prev_yr]
                ap_change = edited_df.loc["Accounts Payable", yr] - edited_df.loc["Accounts Payable", prev_yr]
                # Increase in current assets is a cash outflow, increase in current liability is cash inflow
                delta_nwc = (ar_change + inv_change) - ap_change

        sbc = edited_df.loc["Stock-Based Compensation", yr] if "Stock-Based Compensation" in edited_df.index else 0.0
        capex = edited_df.loc["CapEx", yr]

        if metric_choice == "CFO (Cash Flow from Operations)":
            cfo = edited_df.loc["CFO", yr]
            interest = edited_df.loc["Interest Expense", yr]
            # Assuming SBC is already added back in CFO, but if the user wants to adjust:
            # We will just do standard FCFF from CFO = CFO + Int(1-t) - CapEx. 
            historical_fcff[yr] = cfo + (interest * (1 - tax_rate)) - capex
            
        elif metric_choice == "Net Income":
            ni = edited_df.loc["Net Income", yr]
            da = edited_df.loc["D&A", yr]
            interest = edited_df.loc["Interest Expense", yr]
            historical_fcff[yr] = ni + da + sbc + (interest * (1 - tax_rate)) - delta_nwc - capex
            
        elif metric_choice == "EBIT":
            ebit = edited_df.loc["EBIT", yr]
            da = edited_df.loc["D&A", yr]
            historical_fcff[yr] = (ebit * (1 - tax_rate)) + da + sbc - delta_nwc - capex
            
        elif metric_choice == "EBITDA":
            ebitda = edited_df.loc["EBITDA", yr]
            da = edited_df.loc["D&A", yr]
            historical_fcff[yr] = (ebitda * (1 - tax_rate)) + (da * tax_rate) + sbc - delta_nwc - capex
    except KeyError as e:
        # Failsafe if columns are somehow misaligned
        pass

st.subheader("Calculated Historical FCFF")
fcff_df = pd.DataFrame([historical_fcff], index=["FCFF"])
st.dataframe(fcff_df, use_container_width=True)

st.header("3. Projections & Valuation")

st.subheader("FCFF Growth Rate Assumptions")

growth_method = st.radio("Starting Base Growth Rate:", 
                         ["Custom Input", "Historical CAGR (Year 1 to Year 5)"], key="growth_method_radio")
                         
if growth_method == "Historical CAGR (Year 1 to Year 5)":
    y1_fcff = historical_fcff["Year 1"]
    y5_fcff = historical_fcff["Year 5"]
    if y1_fcff > 0 and y5_fcff > 0:
        base_g = (y5_fcff / y1_fcff)**(1/4) - 1
        st.info(f"Calculated Historical CAGR: {base_g*100:.2f}%")
    else:
        base_g = 0.05
        st.warning("Cannot calculate CAGR with negative/zero values. Defaulting to 5%.")
else:
    base_g = 0.05

term_growth_rate = st.number_input("Terminal Growth Rate (%) (Compulsory)", value=2.0, format="%.2f", key="term_growth_input") / 100.0

st.write("Edit the year-by-year revenue/FCFF growth rates below. You can model a 'fade' to the terminal growth rate.")
proj_years = ["Proj Year 1", "Proj Year 2", "Proj Year 3", "Proj Year 4", "Proj Year 5"]

# Default growth rates: step down linearly from base_g to term_growth_rate
step = (base_g - term_growth_rate) / 5 if base_g > term_growth_rate else 0
default_growth_rates = [max(base_g - (step * i), term_growth_rate) for i in range(5)]
# Convert to percentages for the UI
default_growth_pct = [g * 100 for g in default_growth_rates]

growth_df_initial = pd.DataFrame([default_growth_pct], index=["Growth Rate (%)"], columns=proj_years)
edited_growth_df = st.data_editor(growth_df_initial, use_container_width=True, key="growth_rates_grid")

# Project 5 years into the future based on Year 5
projected_fcff = pd.Series(0.0, index=proj_years)
base_fcff = historical_fcff["Year 5"]

current_fcff = base_fcff
for yr in proj_years:
    g_rate = edited_growth_df.loc["Growth Rate (%)", yr] / 100.0
    current_fcff = current_fcff * (1 + g_rate)
    projected_fcff[yr] = current_fcff

st.subheader("Projected FCFF")
st.dataframe(pd.DataFrame([projected_fcff], index=["FCFF"]), use_container_width=True)

# Discounting and Valuation
st.subheader("Valuation Summary")

discount_factors = [(1 + final_wacc) ** (i + 1) for i in range(5)]
pv_of_fcff = sum([projected_fcff.iloc[i] / discount_factors[i] for i in range(5)])

# Terminal Value = (FCFF_Year5 * (1 + term_growth_rate)) / (WACC - term_growth_rate)
if final_wacc > term_growth_rate:
    terminal_value = (projected_fcff["Proj Year 5"] * (1 + term_growth_rate)) / (final_wacc - term_growth_rate)
    pv_of_tv = terminal_value / ((1 + final_wacc) ** 5)
    
    enterprise_value = pv_of_fcff + pv_of_tv
    equity_value_pre_discount = enterprise_value - total_debt
    liquidity_discount = st.number_input("Liquidity Discount (%)", value=0.0, format="%.2f", key="liq_disc_input") / 100.0
    equity_value = equity_value_pre_discount * (1 - liquidity_discount)
    
    st.write(f"**PV of Projected FCFF (5 Years):** ${pv_of_fcff:,.2f}")
    st.write(f"**Terminal Value:** ${terminal_value:,.2f}")
    st.write(f"**PV of Terminal Value:** ${pv_of_tv:,.2f}")
    st.write("---")
    st.markdown(f"### **Enterprise Value (Firm Value):** ${enterprise_value:,.2f}")
    st.markdown(f"### **Implied Equity Value:** ${equity_value:,.2f}")
    
else:
    st.error("WACC must be strictly greater than the Terminal Growth Rate to compute Terminal Value.")


st.header("4. Export Model")

from excel_generator import create_excel_model

try:
    excel_data = create_excel_model(
        df_historical=edited_df,
        metric_choice=metric_choice,
        tax_rate=tax_rate,
        rfr=rfr_input,
        beta=beta,
        erp=erp_input,
        size_premium=size_premium,
        csrp=csrp,
        ke=ke,
        total_debt=total_debt,
        total_equity=total_equity,
        kd=kd_input,
        wacc=final_wacc,
        term_growth=term_growth_rate,
        df_growth_rates=edited_growth_df,
        liquidity_discount=liquidity_discount
    )

    st.download_button(
        label="Download Valuation Model (Excel)",
        data=excel_data,
        file_name="valuation_model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
except Exception as e:
    st.error(f"Error generating Excel model: {e}")


st.header("4. Sensitivity Analysis & Visualizations")

col_vis_1, col_vis_2 = st.columns(2)

with col_vis_1:
    st.subheader("Historical vs Projected FCFF")
    # Combine historical and projected
    combined_fcff = pd.concat([historical_fcff, projected_fcff])
    
    st.bar_chart(combined_fcff)

with col_vis_2:
    st.subheader("Sensitivity Analysis: Enterprise Value")
    st.write("Varying WACC and Terminal Growth Rate (+/- 1%)")
    
    # Define ranges: Base +/- 1% in steps of 0.5%
    wacc_range = [final_wacc - 0.01, final_wacc - 0.005, final_wacc, final_wacc + 0.005, final_wacc + 0.01]
    g_range = [term_growth_rate - 0.01, term_growth_rate - 0.005, term_growth_rate, term_growth_rate + 0.005, term_growth_rate + 0.01]
    
    sensitivity_table = pd.DataFrame(index=[f"{w*100:.2f}%" for w in wacc_range], 
                                     columns=[f"{g*100:.2f}%" for g in g_range])
    
    # We already have pv_of_fcff. We just need to recalculate TV for each combination.
    for i, w in enumerate(wacc_range):
        for j, g in enumerate(g_range):
            if w > g:
                # Recalculate PV of FCFF using this specific WACC
                discount_factors_sens = [(1 + w) ** (k + 1) for k in range(5)]
                pv_fcff_sens = sum([projected_fcff.iloc[k] / discount_factors_sens[k] for k in range(5)])
                
                # Recalculate Terminal Value
                tv_sens = (projected_fcff["Proj Year 5"] * (1 + g)) / (w - g)
                pv_tv_sens = tv_sens / ((1 + w) ** 5)
                
                ev_sens = pv_fcff_sens + pv_tv_sens
                sensitivity_table.iloc[i, j] = f"${ev_sens:,.0f}"
            else:
                sensitivity_table.iloc[i, j] = "N/A"
                
    st.write("**Rows: WACC | Columns: Terminal Growth**")
    st.dataframe(sensitivity_table, use_container_width=True)
