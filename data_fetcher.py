import yfinance as yf
import pandas as pd
import requests
import io

def fetch_damodaran_data():
    """
    Fetches the Country Risk Premium dataset from Aswath Damodaran's website.
    Returns a pandas DataFrame containing Country and Equity Risk Premium.
    """
    url = "https://www.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Read the Excel file into pandas, starting after header rows
        df = pd.read_excel(io.BytesIO(response.content), sheet_name='ERPs by country', skiprows=7)
        
        # Columns mapping based on typical Damodaran sheet structure
        # Col 0: Country
        # Col 4: Total Equity Risk Premium
        # Col 5: Country Risk Premium
        df = df.rename(columns={
            df.columns[0]: 'Country',
            df.columns[4]: 'Total_ERP',
            df.columns[5]: 'Country_Risk_Premium'
        })
        
        # Keep only the relevant columns and drop rows where Country is NaN or Total_ERP is not a number
        df = df[['Country', 'Total_ERP', 'Country_Risk_Premium']]
        df = df.dropna(subset=['Country', 'Total_ERP'])
        
        # Filter out rows that are not actual countries (like formatting or totals)
        df['Total_ERP'] = pd.to_numeric(df['Total_ERP'], errors='coerce')
        df = df.dropna(subset=['Total_ERP'])
        
        return df

    except Exception as e:
        print(f"Error fetching Damodaran data: {e}")
        return None

def calculate_beta(stock_ticker, benchmark_ticker="^GSPC", period="3y"):
    """
    Calculates Beta by comparing historical returns of the stock vs the benchmark.
    """
    try:
        stock = yf.Ticker(stock_ticker)
        benchmark = yf.Ticker(benchmark_ticker)
        
        hist_stock = stock.history(period=period)['Close']
        hist_bench = benchmark.history(period=period)['Close']
        
        df = pd.DataFrame({
            'Stock': hist_stock,
            'Market': hist_bench
        }).dropna()
        
        if df.empty:
            return None
            
        returns = df.pct_change().dropna()
        
        cov = returns['Stock'].cov(returns['Market'])
        var = returns['Market'].var()
        
        if var == 0:
            return None
            
        beta = cov / var
        return beta
        
    except Exception as e:
        print(f"Error calculating beta: {e}")
        return None

def fetch_risk_free_rate(country="United States"):
    """
    Fetch the 10-year treasury yield using yfinance.
    Defaulting to US 10-Year Treasury Yield (^TNX).
    In a fully global model, we would map countries to their specific bonds.
    """
    try:
        # Fetching US 10-Year Treasury yield (^TNX)
        tnx = yf.Ticker("^TNX")
        history = tnx.history(period="5d")
        
        if history.empty:
            return 0.04 # fallback 4%
            
        latest_yield = history['Close'].iloc[-1]
        
        # ^TNX is quoted in percentage points (e.g., 4.5 for 4.5%)
        # Convert to decimal
        return latest_yield / 100.0
    except Exception as e:
        print(f"Error fetching risk free rate: {e}")
        return 0.04 # fallback

if __name__ == "__main__":
    df = fetch_damodaran_data()
    if df is not None:
        print("Damodaran Data head:")
        print(df.head())
        print("US ERP:", df[df['Country'] == 'United States']['Total_ERP'].values)
    
    beta = calculate_beta("AAPL")
    print(f"\nAAPL Beta vs ^GSPC (3y): {beta}")
    
    rfr = fetch_risk_free_rate()
    print(f"Risk Free Rate (US 10Y): {rfr:.4f}")
