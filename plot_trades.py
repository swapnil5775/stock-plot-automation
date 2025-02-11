import os
import requests
import pandas as pd
import mplfinance as mpf
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time  # For dynamic filenames

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

        # Align unusual trades to stock data timestamps
        df = df.set_index('datetime').reindex(stock_df.index)

        # Set missing values to NaN to avoid line drawing
        df['Price'] = df['Price'].where(df['Price'].notna(), np.nan)

        # Scale dot size (normalize within reasonable range)
        df['DotSize'] = np.interp(df['Premium'], (df['Premium'].min(), df['Premium'].max()), (50, 300))

        return df if not df.empty else None
    return None

# -------------------------------------------------------------------
# 3. Function to format Premium values (convert to "K" or "M")
# -------------------------------------------------------------------
def format_premium(value, _):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.0f}K"
    return str(int(value))

# -------------------------------------------------------------------
# 4. Main execution: Fetch, save CSV, verify, and plot candlestick chart
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

    # Prepare addplot for unusual trades
    add_plots = None
    if unusual_df is not None and not unusual_df.empty:
        add_plots = [
            mpf.make_addplot(
                unusual_df["Price"], 
                scatter=True,  # Only show dots
                markersize=unusual_df["DotSize"],  # Bigger dots for higher premium
                marker="o", 
                color="blue"
            )
        ]

    # Define market colors
    mc = mpf.make_marketcolors(up="green", down="red", edge="inherit", wick="inherit", volume="in")

    # Custom rc settings
    custom_rc = {
        "ytick.labelleft": True,   # Enable left Y-axis for Premium
        "ytick.labelright": True,  # Enable right Y-axis for Stock Price
        "ytick.left": True,        # Show left Y-axis ticks
        "ytick.right": True        # Show right Y-axis ticks
    }

    style = mpf.make_mpf_style(marketcolors=mc, rc=custom_rc)

    # Generate dynamic filename with timestamp
    timestamp = int(time.time())  # Unique timestamp
    plot_filename = f"out/latest_plot_{timestamp}.png"

    # Create figure and axes
    fig, axes = mpf.plot(
        stock_df,
        type="candle",
        style=style,
        title="AAPL 5-Minute Candlestick Chart with Unusual Trades",
        volume=True,
        ylabel="Stock Price (USD)",  # Right Y-axis
        addplot=add_plots,  # Add blue dots for Premium
        figsize=(20, 10),
        returnfig=True  # Returns the figure & list of axes
    )

    # Extract first axis (main stock chart)
    ax1 = axes[0]  # Fix: Extract the first axis from list
    ax2 = ax1.twinx()  # Correctly create secondary Y-axis

    # Set labels for Premium axis
    ax2.set_ylabel("Premium (USD)", fontsize=12, color="blue")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(format_premium))  # Format as K/M
    ax2.tick_params(axis="y", labelcolor="blue")  # Set label color to blue
    ax2.set_ylim(unusual_df['Premium'].min(), unusual_df['Premium'].max())  # Set proper scale

    # Save the updated plot
    fig.savefig(plot_filename)
    print(f"✅ Large Candlestick chart saved to {plot_filename}")

    # Update HTML file with dynamic filename
    html_content = f"""<html>
<head><title>Latest Stock Chart</title></head>
<body>
<h1>Latest AAPL 5-Minute Candlestick Chart with Unusual Trades</h1>
<img src="{plot_filename}" alt="Stock Chart" width="100%" />
</body>
</html>"""

    with open("out/index.html", "w") as f:
        f.write(html_content)

    print(f"✅ HTML file updated with latest chart: {plot_filename}")

if __name__ == "__main__":
    main()
