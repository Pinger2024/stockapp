import os
from flask import Flask, render_template, request
from pymongo import MongoClient
import logging

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://mongodb-9iyq:27017')
db = client['StockData']
ohlcv_collection = db['ohlcv_data']

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Fetch ticker count
    tickers_count = len(ohlcv_collection.distinct("ticker"))

    # Handle search result
    search_result = None
    if request.method == 'POST':
        ticker = request.form['ticker'].upper()  # Get the input ticker and make it uppercase
        logging.info(f"Searching for ticker: {ticker}")  # Log the search action
        result = ohlcv_collection.find_one({"ticker": ticker})
        if result:
            search_result = ticker
        else:
            search_result = 'not_found'

    # Fetch a small subset of OHLCV data to display
    stocks = ohlcv_collection.find().limit(5)

    return render_template('index.html', tickers_count=tickers_count, stocks=stocks, search_result=search_result)

if __name__ == "__main__":
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all available IPs (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
