import pandas as pd
import matplotlib.pyplot as plt

def main():
    # Read CSVs from 'data' folder
    stock_data = pd.read_csv('data/stock_data.csv')
    unusual_data = pd.read_csv('data/unusual_trades.csv')
    
    # TODO: Convert 'Time' columns to datetime if needed
    # stock_data['Time'] = pd.to_datetime(stock_data['Time'])
    # unusual_data['Time'] = pd.to_datetime(unusual_data['Time'])
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(stock_data['Time'], stock_data['Price'], label='Stock Price', color='blue')
    plt.scatter(unusual_data['Time'], unusual_data['Price'], label='Unusual Trade', color='red')
    plt.legend()
    plt.title("Stock Price with Unusual Trades")
    plt.xlabel("Time")
    plt.ylabel("Price")
    
    # Save the plot
    plt.tight_layout()
    plt.savefig('out/latest_plot.png')
    
    # Create a simple HTML file referencing the PNG
    with open('out/index.html', 'w') as f:
        f.write("""<html>
<head><title>Latest Stock Chart</title></head>
<body>
<h1>Daily Stock Chart with Unusual Trades</h1>
<img src="latest_plot.png" alt="Stock Chart" />
</body>
</html>""")

if __name__ == "__main__":
    main()
