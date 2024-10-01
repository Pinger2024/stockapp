import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import logging
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

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

@app.route('/plot')
def plot():
    # Get the ticker from the search or default to some value
    ticker = request.args.get('ticker', 'TSLA').upper()

    # Fetch stock data for the specific ticker
    stock_data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", 1))

    if not stock_data:
        return "No data found for ticker", 404

    # Prepare data for plotting
    dates = [entry['date'] for entry in stock_data]
    closes = [entry['close'] for entry in stock_data]

    # Create plot
    fig, ax = plt.subplots()
    ax.plot(dates, closes, label=ticker)
    ax.set_xlabel('Date')
    ax.set_ylabel('Closing Price')
    ax.set_title(f'Stock Prices for {ticker}')
    ax.legend()

    # Convert plot to PNG image
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    plt.close(fig)

    # Encode the image to display on the webpage
    encoded_img = base64.b64encode(output.getvalue()).decode('utf-8')

    return f"<img src='data:image/png;base64,{encoded_img}' alt='Stock Prices for {ticker}'>"

if __name__ == "__main__":
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all available IPs (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
