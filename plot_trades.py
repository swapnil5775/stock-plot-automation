import os
import requests
import time
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
        "apiKey": "_VWEacE9BO3i32DCVduC9DDmj77fBM8R"  # Secure this key in production!
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    json_data = response.json()
    results = json_data.get('results', [])
    if not results:
        raise ValueError("No data received from Polygon API")

    # Create DataFrame from API results
    df = pd.DataFrame(results)

    # Convert epoch timestamp (ms) to datetime in UTC then to EST
    df['datetime'] = pd.to_datetime(df['t'], unit='ms', utc=True).dt.tz_convert('US/Eastern')
    
    # Sort by datetime and set as index
    df.sort_values('datetime', inplace=True)
    df.set_index('datetime', inplace=True)
    
    # Rename columns to standard names expected by mplfinance:
    # 'o' -> Open, 'h' -> High, 'l' -> Low, 'c' -> Close, 'v' -> Volume
    df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'}, inplace=True)
    
    # Keep only the necessary columns for candlestick plotting
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    return df

# -------------------------------------------------------------------
# 2. Main execution: Fetch, save CSV, and plot candlestick chart with volume
# -------------------------------------------------------------------
def main():
    # Ensure required directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('out', exist_ok=True)
    
    # Fetch the latest stock data from the API
    stock_df = fetch_stock_data()
    
    # Save the DataFrame to CSV with a 'Time' column from the index
    stock_csv_path = 'data/stock_data.csv'
    stock_df.to_csv(stock_csv_path, index_label='Time')
    
    # Define market colors: green for upward candles, red for downward candles.
    mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit', volume='in')
    
    # Custom rc settings to place the price axis on the right
    custom_rc = {
        'ytick.labelleft': False,   # Hide left y-axis labels
        'ytick.labelright': True,   # Show right y-axis labels
        'ytick.left': False,        # Hide left y-axis ticks
        'ytick.right': True         # Show right y-axis ticks
    }
    
    style = mpf.make_mpf_style(marketcolors=mc, rc=custom_rc)
    
    # Generate the candlestick chart with volume sub-plot
    mpf.plot(
        stock_df,
        type='candle',
        style=style,
        title="AAPL 5-Minute Candlestick Chart",
        volume=True,
        ylabel='Price (USD)',        # Price label on the y-axis (will appear on the right)
        ylabel_lower='Volume',
        savefig='out/latest_plot.png'
    )
    
timestamp = int(time.time())  # Generate a unique timestamp
html_content = f"""<html>
<head><title>Latest Stock Chart</title></head>
<body>
<h1>Latest AAPL 5-Minute Candlestick Chart</h1>
<img src="latest_plot.png?v={timestamp}" alt="Stock Chart" />
</body>
</html>"""
with open('out/index.html', 'w') as f:
    f.write(html_content)
    
if __name__ == "__main__":
    main()
