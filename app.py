from flask import Flask, render_template, request, Response
from pymongo import MongoClient
import matplotlib.pyplot as plt
import io
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
    total_tickers = 0

    if request.method == 'POST':
        ticker = request.form['ticker'].upper()
        if ticker:
            # Fetch OHLCV data for the ticker
            ohlcv_data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", -1).limit(5))
            logging.info(f"Fetched {len(ohlcv_data)} OHLCV records for {ticker}")

            # Fetch RS Score for the ticker
            indicator_data = indicators_collection.find_one({"ticker": ticker})
            if indicator_data:
                # Use the correct RS score field, e.g., 'rs_score' or 'rs_63'
                rs_score = indicator_data.get("rs_score")  # Change this if your field is different
                logging.info(f"RS Score for {ticker}: {rs_score}")
            else:
                rs_score = None  # Handle missing RS score
                logging.info(f"No RS Score found for {ticker}")

    # Get total unique tickers
    total_tickers = len(ohlcv_collection.distinct("ticker"))

    # Get top 5 highest RS score stocks (use the correct field)
    highest_rs_stocks = list(indicators_collection.find().sort("rs_score", -1).limit(5))

    # Get top 5 stocks making new RS highs
    new_rs_high_stocks = list(indicators_collection.find({"rs_new_high": True}).limit(5))

    return render_template('index.html', ticker=ticker, ohlcv_data=ohlcv_data, rs_score=rs_score,
                           highest_rs_stocks=highest_rs_stocks, new_rs_high_stocks=new_rs_high_stocks,
                           total_tickers=total_tickers)

@app.route('/plot')
def plot():
    ticker = request.args.get('ticker')
    if not ticker:
        return "No ticker specified."
    ticker = ticker.upper()

    # Fetch OHLCV data from MongoDB
    ohlcv_data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", 1))
    if not ohlcv_data:
        return "No data available for this ticker."

    # Plotting the data using Matplotlib
    dates = [entry['date'] for entry in ohlcv_data]
    close_prices = [entry['close'] for entry in ohlcv_data]

    fig, ax = plt.subplots()
    ax.plot(dates, close_prices, label="Closing Prices", color='blue')
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.set_title(f"{ticker} Closing Prices")
    ax.legend()
    plt.xticks(rotation=45)

    # Save the plot to a BytesIO object and return it as a PNG
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close(fig)
    img.seek(0)
    return Response(img.getvalue(), mimetype='image/png')

if __name__ == "__main__":
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all available IPs (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
