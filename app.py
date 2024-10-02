import os
from flask import Flask, render_template, request
from pymongo import MongoClient
import logging

# Initialize the Flask app
app = Flask(__name__)

# MongoDB connection (ensure this connection string is correct)
client = MongoClient("mongodb://your-mongo-uri:27017")
db = client['StockData']
ohlcv_collection = db['ohlcv_data']
indicators_collection = db['indicators']

# Home route
@app.route("/", methods=["GET", "POST"])
def home():
    tickers_count = ohlcv_collection.count_documents({})
    search_result = None
    stocks = None
    rs_score = None

    if request.method == "POST":
        ticker = request.form.get("ticker").upper()
        logging.info(f"Searching for ticker: {ticker}")
        search_result = ohlcv_collection.find_one({"ticker": ticker})

        if search_result:
            stocks = list(ohlcv_collection.find({"ticker": ticker}).sort("date", -1).limit(5))
            rs_data = indicators_collection.find_one({"ticker": ticker})
            if rs_data:
                # Calculate the final RS score (if needed) or just display rs_63, rs_126, etc.
                rs_score = rs_data.get("rs_63")  # Or you can modify this to display the right value

        else:
            search_result = "not_found"
            logging.info(f"Ticker {ticker} not found in the database.")

    return render_template(
        "index.html",
        tickers_count=tickers_count,
        search_result=search_result,
        stocks=stocks,
        rs_score=rs_score,
    )


if __name__ == "__main__":
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all available IPs (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
