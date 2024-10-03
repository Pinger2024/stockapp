from flask import Flask, render_template, request, Response
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
@app.route('/', methods=['GET'])
def index():
    total_tickers = ohlcv_collection.distinct('ticker')
    total_tickers_count = len(total_tickers)

    # Fetch stocks making a new RS High and meet at least 5 Minervini criteria
    rs_high_and_minervini_stocks = list(indicators_collection.find(
        {
            "new_rs_high": True,
            "minervini_criteria.minervini_score": {"$gte": 5}
        },
        {"ticker": 1, "rs_score": 1, "minervini_criteria.minervini_score": 1, "_id": 0}
    ))
    rs_high_and_minervini_stocks_display = rs_high_and_minervini_stocks[:10]
    rs_high_and_minervini_more = len(rs_high_and_minervini_stocks) > 10

    # Fetch stocks with buy signal, meet at least 6 Minervini criteria, and have an RS score over 60
    buy_signal_stocks = list(indicators_collection.find(
        {
            "buy_signal": True,
            "minervini_criteria.minervini_score": {"$gte": 6},
            "rs_score": {"$gte": 60}
        },
        {"ticker": 1, "rs_score": 1, "minervini_criteria.minervini_score": 1, "_id": 0}
    ))
    buy_signal_stocks_display = buy_signal_stocks[:10]
    buy_signal_more = len(buy_signal_stocks) > 10

    return render_template('index.html',
                           total_tickers=total_tickers_count,
                           rs_high_and_minervini_stocks=rs_high_and_minervini_stocks_display,
                           rs_high_and_minervini_more=rs_high_and_minervini_more,
                           buy_signal_stocks=buy_signal_stocks_display,
                           buy_signal_more=buy_signal_more)

# Route to display all stocks making a new RS High and meet at least 5 Minervini criteria
@app.route('/rs_high_and_minervini')
def rs_high_and_minervini():
    rs_high_and_minervini_stocks = list(indicators_collection.find(
        {
            "new_rs_high": True,
            "minervini_criteria.minervini_score": {"$gte": 5}
        },
        {"ticker": 1, "rs_score": 1, "minervini_criteria.minervini_score": 1, "_id": 0}
    ))
    return render_template('rs_high_and_minervini.html', stocks=rs_high_and_minervini_stocks)

# Route to display all stocks with buy signal, meet at least 6 Minervini criteria, and RS score over 60
@app.route('/buy_signal_stocks')
def buy_signal_stocks():
    buy_signal_stocks = list(indicators_collection.find(
        {
            "buy_signal": True,
            "minervini_criteria.minervini_score": {"$gte": 6},
            "rs_score": {"$gte": 60}
        },
        {"ticker": 1, "rs_score": 1, "minervini_criteria.minervini_score": 1, "_id": 0}
    ))
    return render_template('buy_signal_stocks.html', stocks=buy_signal_stocks)

# Route to download watchlist
@app.route('/download_watchlist')
def download_watchlist():
    watchlist_type = request.args.get('type')
    if watchlist_type == 'rs_high_and_minervini':
        stocks = list(indicators_collection.find(
            {
                "new_rs_high": True,
                "minervini_criteria.minervini_score": {"$gte": 5}
            },
            {"ticker": 1, "_id": 0}
        ))
    elif watchlist_type == 'buy_signal':
        stocks = list(indicators_collection.find(
            {
                "buy_signal": True,
                "minervini_criteria.minervini_score": {"$gte": 6},
                "rs_score": {"$gte": 60}
            },
            {"ticker": 1, "_id": 0}
        ))
    else:
        return "Invalid watchlist type", 400

    # Generate the .txt file content
    tickers = [stock['ticker'] for stock in stocks]
    tickers_text = '\n'.join(tickers)

    # Create a response with the .txt file
    response = Response(tickers_text, mimetype='text/plain')
    response.headers['Content-Disposition'] = 'attachment; filename=watchlist.txt'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
