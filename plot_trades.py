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
        "apiKey": "_VWEacE9BO3i32DCVduC9DDmj77fBM8R"  # Secure this key in production!
    }
    response = requests.get(url, params=params, timeout=10)

    # Raise error if response is unsuccessful
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"API Request Failed: {err}")
        return pd.DataFrame()  # Return empty DataFrame if API fails

    json_data = response.json()
    
    # Debug: Print API response metadata
    print(f"API Response Metadata: {json_data.keys()}")
    print(f"Results Count: {json_data.get('resultsCount', 0)}")

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

    # Debug: Print first few rows
    print("Fetched DataFrame:\n", df.head())

    return df

# -------------------------------------------------------------------
# 2. Function to verify and debug CSV writing
# -------------------------------------------------------------------
def verify_csv(file_path):
    if os.path.exists(file_path):
        print(f"✅ CSV file successfully created: {file_path}")
        try:
            df = pd.read_csv(file_path)
            print("CSV File Content Preview:\n", df.head())
        except Exception as e:
            print(f"Error reading the CSV file: {e}")
    else:
        print(f"❌ CSV file not found at: {file_path}")

# -------------------------------------------------------------------
# 3. Main execution: Fetch, save CSV, verify, and plot candlestick chart
# -------------------------------------------------------------------
def main():
    # Ensure required directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('out', exist_ok=True)

    # Fetch the latest stock data from the API
    stock_df = fetch_stock_data()

    # Check if data exists before saving
    if stock_df.empty:
        print("Error: No data fetched, skipping CSV write and chart plot.")
        return

    # Save DataFrame to CSV with EST timestamps
    stock_csv_path = 'data/stock_data.csv'
    stock_df.to_csv(stock_csv_path, index_label='Time')
    print(f"✅ Stock data saved to {stock_csv_path}")

    # Verify CSV content
    verify_csv(stock_csv_path)

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
    plot_filename = 'out/latest_plot.png'
    mpf.plot(
        stock_df,
        type='candle',
        style=style,
        title="AAPL 5-Minute Candlestick Chart",
        volume=True,
        ylabel='Price (USD)',        # Price label on the y-axis (will appear on the right)
        ylabel_lower='Volume',
        savefig=plot_filename
    )

    print(f"✅ Candlestick chart saved to {plot_filename}")

    # Create HTML file with cache-busting timestamp
    import time
    timestamp = int(time.time())
    html_content = f"""<html>
<head><title>Latest Stock Chart</title></head>
<body>
<h1>Latest AAPL 5-Minute Candlestick Chart</h1>
<img src="latest_plot.png?v={timestamp}" alt="Stock Chart" />
</body>
</html>"""
    
    with open('out/index.html', 'w') as f:
        f.write(html_content)

    print(f"✅ HTML file updated with latest chart: out/index.html")

if __name__ == "__main__":
    main()
