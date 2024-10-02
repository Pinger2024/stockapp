from flask import Flask, render_template, request
from pymongo import MongoClient
import matplotlib.pyplot as plt
import io
import base64
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection setup
client = MongoClient("mongodb://mongodb-9iyq:27017")
db = client['StockData']
ohlcv_collection = db['ohlcv_data']
indicators_collection = db['indicators']

# Route for main page
@app.route('/', methods=['GET', 'POST'])
def index():
    ticker = None
    ohlcv_data = None
    rs_score = None
    total_tickers = ohlcv_collection.distinct('ticker')
    total_tickers_count = len(total_tickers)

    # Handle form submission to search for a specific ticker
    if request.method == 'POST':
        ticker = request.form['ticker'].upper()

        # Retrieve OHLCV data for the ticker
        ohlcv_data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", -1))

        # Retrieve the RS score for the ticker
        rs_entry = indicators_collection.find_one({"ticker": ticker})
        if rs_entry:
            rs_score = rs_entry.get('rs_score')

    # Find the top 5 stocks by RS score
    highest_rs_stocks = list(indicators_collection.find().sort("rs_score", -1).limit(5))

    # Find the stocks making a new RS high
    new_rs_high_stocks = list(indicators_collection.find({"rs_high": True}).sort("ticker", 1))

    return render_template('index.html', ticker=ticker, ohlcv_data=ohlcv_data, rs_score=rs_score,
                           highest_rs_stocks=highest_rs_stocks, new_rs_high_stocks=new_rs_high_stocks,
                           total_tickers=total_tickers_count)


# Route for plotting stock price chart
@app.route('/plot')
def plot():
    ticker = request.args.get('ticker')
    ohlcv_data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", 1))

    dates = [data['date'] for data in ohlcv_data]
    closes = [data['close'] for data in ohlcv_data]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, closes, label=f'{ticker} Closing Prices')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title(f'{ticker} Stock Price')
    plt.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return f'<img src="data:image/png;base64,{plot_url}">'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
