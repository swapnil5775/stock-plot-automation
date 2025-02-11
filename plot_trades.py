import os
import requests
import pandas as pd
import mplfinance as mpf
from datetime import datetime

# -------------------------------------------------------------------
# 1. Function to fetch 5-minute candlestick data from Polygon.io API
# -------------------------------------------------------------------
def fetch_stock_data():
    url = "https://api.polygon.io/v2/aggs/ticker/AAPL/range/5/minute/2025-01-21/2025-01-29"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": "_VWEacE9BO3i32DCVduC9DDmj77fBM8R"  # Ensure this key is secured in production!
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    json_data = response.json()
    results = json_data.get('results', [])
    
    if not results:
        raise ValueError("No data received from Polygon API")

    # Create DataFrame from API results
    df = pd.DataFrame(results)
    # Convert epoch timestamp (ms) to datetime
    df['datetime'] = pd.to_datetime(df['t'], unit='ms')
    df.sort_values('datetime', inplace=True)
    df.set_index('datetime', inplace=True)
    # Rename columns to the standard names expected by mplfinance
    df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'}, inplace=True)
    # Keep only the required columns
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    return df

# -------------------------------------------------------------------
# 2. Optional: Function to load unusual trades (if available)
# -------------------------------------------------------------------
def fetch_unusual_trades():
    unusual_csv_path = 'data/unusual_trades.csv'
    if os.path.exists(unusual_csv_path):
        df = pd.read_csv(unusual_csv_path)
        # Assume the CSV has a 'Time' column in a parseable datetime format and a 'Price' column.
        df['datetime'] = pd.to_datetime(df['Time'])
        df.set_index('datetime', inplace=True)
        return df
    return None

# -------------------------------------------------------------------
# 3. Main execution: Fetch, save CSV, plot candlestick chart, generate HTML
# -------------------------------------------------------------------
def main():
    # Ensure required directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('out', exist_ok=True)
    
    # Fetch the latest stock data from the API
    stock_df = fetch_stock_data()
    # Save the data to CSV
    stock_csv_path = 'data/stock_data.csv'
    stock_df.to_csv(stock_csv_path)
    
    # Optionally, fetch unusual trades data to overlay (if present)
    unusual_df = fetch_unusual_trades()
    add_plots = None
    if unusual_df is not None:
        # Create an addplot series for unusual trades as scatter markers.
        # Note: Adjust markersize and marker type as desired.
        add_plots = mpf.make_addplot(unusual_df['Price'], type='scatter', markersize=50, marker='^', color='blue')
    
    # Define market colors: green for upward candles, red for downward candles.
    mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit', volume='in')
    style = mpf.make_mpf_style(marketcolors=mc)
    
    # Generate the candlestick chart. Volume is included.
    mpf.plot(
        stock_df,
        type='candle',
        style=style,
        title="AAPL 5-Minute Candlestick Chart",
        volume=True,
        addplot=add_plots,
        savefig='out/latest_plot.png'
    )
    
    # Create a simple HTML file to display the generated chart
    with open('out/index.html', 'w') as f:
        f.write("""<html>
<head><title>Latest Stock Chart</title></head>
<body>
<h1>Latest AAPL 5-Minute Candlestick Chart</h1>
<img src="latest_plot.png" alt="Stock Chart" />
</body>
</html>""")

if __name__ == "__main__":
    main()
