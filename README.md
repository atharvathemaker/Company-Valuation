Markdown
# 📊 Interactive FCFF Valuation Dashboard

A dynamic financial tool built with Streamlit that calculates the **Free Cash Flow to Firm (FCFF)** valuation for global stocks.

## 🚀 Features
* **Real-Time Data:** Fetches 3-year historical stock data via Yahoo Finance to calculate Beta.
* **Macro Integration:** Pulls Risk-Free Rates and Equity Risk Premiums (ERP) using updated datasets.
* **Flexible Inputs:** Choose to calculate FCFF via EBIT, EBITDA, Net Income, or Cash Flow from Operations.
* **Dynamic Export:** Download a fully functional Excel model with live formulas based on your inputs.

## 🛠️ Installation & Local Setup
1. Clone this repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/valuation-dashboard.git](https://github.com/YOUR_USERNAME/valuation-dashboard.git)
Install dependencies:

Bash
pip install -r requirements.txt
Run the dashboard:

Bash
streamlit run app.py
📈 Usage
Enter the Stock Ticker (e.g., AAPL) and Benchmark (e.g., ^GSPC).

Input 5 years of historical financial data in the editable table.

Adjust the Terminal Growth Rate and WACC overrides as needed.

View the intrinsic valuation and download the Excel model for further analysis.

📚 Credits
Valuation methodology based on Aswath Damodaran's framework.
