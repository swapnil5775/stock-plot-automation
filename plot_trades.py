import os
import requests
import pandas as pd
import mplfinance as mpf
import numpy as np
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

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"API Request Failed: {err}")
        return pd.DataFrame()

    json_data = response.json()
    
    results = json_data.get('results', [])
    if not results:
        print("Warning: No data received from Polygon API.")
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Convert epoch timestamp (ms) to datetime in EST
    df['datetime'] = pd.to_datetime(df['t'], unit='ms', utc=True).dt.tz_convert('US/Eastern')

    # Sort by datetime and set as index
    df.sort_values('datetime', inplace=True)
    df.set_index('datetime', inplace=True)

    # Rename columns to match mplfinance requirements
    df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'}, inplace=True)
    
    # Select only required columns
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    return df

# -------------------------------------------------------------------
# 2. Function to load unusual trades and align timestamps correctly
# -------------------------------------------------------------------
def fetch_unusual_trades(stock_df):
    unusual_csv_path = 'data/unusual_trades.csv'
    if os.path.exists(unusual_csv_path):
        df = pd.read_csv(unusual_csv_path)

        # Convert 'Time' to datetime
        df['datetime'] = pd.to_datetime(df['Time']).dt.tz_convert('US/Eastern')

        # Ensure 'Premium' column exists and fill missing values with 0
        df['Premium'] = df['Premium'].fillna(0)

        # Align unusual trades to stock data timestamps (Prevent "x and y size mismatch" error)
        df = df.set_index('datetime').reindex(stock_df.index, method='nearest')

        # Scale dot size (normalize within reasonable range)
        df['DotSize'] = np.interp(df['Premium'], (df['Premium'].min(), df['Premium'].max()), (30, 300))

        return df if not df.empty else None
    return None

# -------------------------------------------------------------------
# 3. Main execution: Fetch, save CSV, verify, and plot candlestick chart
# -------------------------------------------------------------------
def main():
    os.makedirs('data', exist_ok=True)
    os.makedirs('out', exist_ok=True)

    # Fetch stock data
    stock_df = fetch_stock_data()
    if stock_df.empty:
        print("Error: No data fetched, skipping CSV write and chart plot.")
        return

    # Save stock data to CSV
    stock_csv_path = 'data/stock_data.csv'
    stock_df.to_csv(stock_csv_path, index_label='Time')

    # Fetch unusual trades
    unusual_df = fetch_unusual_trades(stock_df)

    # Prepare plot additions (if unusual trades exist)
    add_plots = None
    if unusual_df is not None and not unusual_df.empty:
        # Create scatter plot for unusual trades
        add_plots = mpf.make_addplot(
            unusual_df['Price'], 
            scatter=True, 
            markersize=unusual_df['DotSize'],  # Dot size based on Premium
            marker='o', 
            color='blue'
        )

    # Define market colors
    mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit', volume='in')

    # Custom rc settings
    custom_rc = {
        'ytick.labelleft': False,
        'ytick.labelright': True,
        'ytick.left': False,
        'ytick.right': True
    }

    style = mpf.make_mpf_style(marketcolors=mc, rc=custom_rc)

    # Generate large full-screen chart
    plot_filename = 'out/latest_plot_large.png'
    mpf.plot(
        stock_df,
        type='candle',
        style=style,
        title="AAPL 5-Minute Candlestick Chart with Unusual Trades",
        volume=True,
        ylabel='Price (USD)',
        ylabel_lower='Volume',
        addplot=add_plots,  # Add blue dots
        figsize=(20, 10),  # MAKE IT FULL SIZE
        savefig=plot_filename
    )

    print(f"✅ Large Candlestick chart saved to {plot_filename}")

    # Update HTML file with cache-busting timestamp
    import time
    timestamp = int(time.time())
    html_content = f"""<html>
<head><title>Latest Stock Chart</title></head>
<body>
<h1>Latest AAPL 5-Minute Candlestick Chart with Unusual Trades</h1>
<img src="latest_plot_large.png?v={timestamp}" alt="Stock Chart" width="100%" />
</body>
</html>"""
    
    with open('out/index.html', 'w') as f:
        f.write(html_content)

    print(f"✅ HTML file updated with latest large chart: out/index.html")

if __name__ == "__main__":
    main()
