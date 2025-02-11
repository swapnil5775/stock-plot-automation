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

        # Convert 'Time' to datetime and set index
        df['datetime'] = pd.to_datetime(df['Time']).dt.tz_convert('US/Eastern')
        df.set_index('datetime', inplace=True)

        # Drop missing Premium values to avoid x/y mismatch
        df.dropna(subset=['Premium', 'Size'], inplace=True)

        # Scale dot size based on Premium values (Ensure it matches length of Price)
        df['DotSize'] = np.interp(df['Premium'], (df['Premium'].min(), df['Premium'].max()), (50, 500))

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

    # Prepare addplot for unusual trades (Only for existing timestamps)
    add_plots = []
    if unusual_df is not None and not unusual_df.empty:
        add_plots.append(
            mpf.make_addplot(
                unusual_df["Price"],  # Plot only existing timestamps
                scatter=True,  # Only show dots
                markersize=unusual_df["DotSize"],  # Bigger dots for higher premium
                marker="o", 
                color="blue"
            )
        )

    # Prepare addplot for Trade Size as a bar chart (Only existing timestamps)
    if unusual_df is not None and not unusual_df.empty:
        add_plots.append(
            mpf.make_addplot(
                unusual_df["Size"],  # Ensure only matching timestamps
                type="bar",  # Vertical bars
                color="purple",
                panel=2,  # Draw in a separate panel below volume
                ylabel="Trade Size"
            )
        )

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
        addplot=add_plots,  # Add blue dots for Premium & Size bars
        figsize=(20, 12),
        panel_ratios=(6, 2, 2),  # Increase third panel for size
        returnfig=True  # Returns the figure & list of axes
    )

    # Extract first axis (main stock chart)
    ax1 = axes[0]  # Fix: Extract the first axis from list
    ax2 = ax1.twinx()  # Correctly create secondary Y-axis

    # Set labels for Premium axis
    ax2.set_ylabel("Premium (USD)", fontsize=12, color="blue")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(format_premium))  # Format as K/M
    ax2.tick_params(axis="y", labelcolor="blue")  # Set label color to blue

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
