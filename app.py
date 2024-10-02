from flask import Flask, render_template, request, Response
from pymongo import MongoClient
import matplotlib.pyplot as plt
import io
import base64
import os
import logging
from datetime import datetime

app = Flask(__name__)

# MongoDB connection (hardcoded)
client = MongoClient("mongodb://mongodb-9iyq:27017")
db = client['StockData']
ohlcv_collection = db['ohlcv_data']
indicators_collection = db['indicators']

logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET', 'POST'])
def index():
    ticker = None
    ohlcv_data = []
    rs_score = None
    highest_rs_stocks = []
    new_rs_high_stocks = []

    if request.method == 'POST':
        ticker = request.form['ticker']
        if ticker:
            # Fetch OHLCV data for the ticker
            ohlcv_data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", -1).limit(5))
            
            # Fetch RS Score for the ticker
            indicator_data = indicators_collection.find_one({"ticker": ticker})
            if indicator_data:
                rs_score = indicator_data.get("rs_score")

    # Get top 5 highest RS score stocks
    highest_rs_stocks = list(indicators_collection.find().sort("rs_score", -1).limit(5))

    # Get top 5 stocks making new RS highs
    new_rs_high_stocks = list(indicators_collection.find({"rs_new_high": True}).limit(5))

    return render_template('index.html', ticker=ticker, ohlcv_data=ohlcv_data, rs_score=rs_score,
                           highest_rs_stocks=highest_rs_stocks, new_rs_high_stocks=new_rs_high_stocks)

@app.route('/plot')
def plot():
    ticker = request.args.get('ticker')
    if not ticker:
        return "No ticker specified."

    # Fetch OHLCV data from MongoDB
    ohlcv_data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", 1))
    if not ohlcv_data:
        return "No data available for this ticker."

    # Plotting the data using Matplotlib
    dates = [entry['date'] for entry in ohlcv_data]
    close_prices = [entry['close'] for entry in ohlcv_data]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, close_prices, label="Closing Prices", color='blue')
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.title(f"{ticker} Closing Prices")
    plt.legend()

    # Save the plot to a BytesIO object and return it as a PNG
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return render_template('plot.html', plot_url=plot_url)

if __name__ == "__main__":
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all available IPs (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
