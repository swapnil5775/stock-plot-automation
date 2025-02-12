from flask import Flask, request, jsonify, render_template
import requests
import pandas as pd
import plotly.graph_objects as go
import os

app = Flask(__name__)

POLYGON_API_KEY = "YOUR_POLYGON_API_KEY"  # Replace with your key

# Function to fetch stock data dynamically
def fetch_stock_data(ticker, start_date, end_date):
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/5/minute/{start_date}/{end_date}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": POLYGON_API_KEY
    }
    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return {"error": "Failed to fetch data from Polygon.io"}

    json_data = response.json()
    results = json_data.get("results", [])
    if not results:
        return {"error": "No data received from Polygon API."}

    df = pd.DataFrame(results)
    df['datetime'] = pd.to_datetime(df['t'], unit='ms', utc=True)
    df.sort_values('datetime', inplace=True)
    df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'}, inplace=True)
    df = df[['datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    return df.to_dict(orient='records')

# API endpoint to fetch stock data
@app.route("/api/get_stock_data", methods=["POST"])
def get_stock_data():
    data = request.json
    ticker = data.get("ticker", "AAPL")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    stock_data = fetch_stock_data(ticker, start_date, end_date)
    return jsonify(stock_data)

# Serve the frontend
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
