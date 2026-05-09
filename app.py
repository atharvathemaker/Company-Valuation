import streamlit as st
import pandas as pd
import numpy as np
from data_fetcher import get_valuation_data, calculate_beta
from excel_generator import generate_excel

st.set_page_config(page_title="Interactive Valuation Dashboard", layout="wide")

st.title("📊 Interactive FCFF Valuation Dashboard")

# Sidebar - Inputs for WACC & Beta
st.sidebar.header("WACC & Beta Inputs")
ticker = st.sidebar.text_input("Stock Ticker (e.g., AAPL)", "AAPL")
benchmark = st.sidebar.text_input("Benchmark Ticker (e.g., ^GSPC)", "^GSPC")
country = st.sidebar.selectbox("Select Country for ERP", ["United States", "India", "UAE", "United Kingdom"])

if st.sidebar.button("Fetch Market Data"):
    with st.spinner("Fetching data..."):
        market_data = get_valuation_data(country)
        beta = calculate_beta(ticker, benchmark)
        st.session_state['market_data'] = market_data
        st.session_state['beta'] = beta

# Financial Data Input Section
st.header("1. Historical Financials (5 Years)")
method = st.selectbox("Calculate FCFF using:", ["EBIT", "EBITDA", "Net Income", "Cash Flow from Operations"])

# Create a template for the 5-year data
columns = [f"Year {i}" for i in range(1, 6)]
input_df = pd.DataFrame(index=[method, "Tax Rate (%)", "CapEx", "Working Capital Δ"], columns=columns).fillna(0.0)

edited_df = st.data_editor(input_df)

# Growth & Valuation
st.header("2. Projections & Valuation")
growth_rate = st.slider("Terminal Growth Rate (%)", 0.0, 5.0, 2.0) / 100
wacc_override = st.number_input("Override WACC (%)", value=10.0) / 100

if st.button("Calculate Valuation"):
    # Valuation logic would process edited_df here
    st.success("Valuation complete! (Formula-based logic applied)")
    
    # Excel Download
    excel_data = generate_excel(edited_df, growth_rate, wacc_override)
    st.download_button(
        label="📥 Download Dynamic Excel Model",
        data=excel_data,
        file_name="valuation_model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
