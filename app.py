from flask import Flask, render_template, request, Response
from pymongo import MongoClient
import matplotlib.pyplot as plt
import io
import base64
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# MongoDB connection (as provided)
client = MongoClient("mongodb://mongodb-9iyq:27017")
db = client['StockData']
collection = db['ohlcv_data']
indicators_collection = db['indicators']

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    ticker = None
    ohlcv_data = []
    rs_score = None

    if request.method == "POST":
        ticker = request.form.get("ticker").upper()
        logging.debug(f"Ticker received: {ticker}")

        # Query for OHLCV data
        ohlcv_data = list(collection.find({"ticker": ticker}).sort("date", -1))
        logging.debug(f"OHLCV Data for {ticker}: {ohlcv_data}")

        # Query for RS score
        rs_score = indicators_collection.find_one({"ticker": ticker})
        logging.debug(f"RS Score for {ticker}: {rs_score}")

    return render_template("index.html", ohlcv_data=ohlcv_data, rs_score=rs_score, ticker=ticker)

@app.route("/plot")
def plot():
    ticker = request.args.get("ticker").upper()
    logging.debug(f"Ticker for plot: {ticker}")

    ohlcv_data = list(collection.find({"ticker": ticker}).sort("date", 1))

    if not ohlcv_data:
        return Response("No data available for plotting.", status=404)

    dates = []
    closing_prices = []

    for entry in ohlcv_data:
        # Handle date parsing
        if isinstance(entry["date"], str):
            try:
                date_obj = datetime.strptime(entry["date"], "%Y-%m-%d")
            except ValueError:
                # Handle different date format if necessary
                date_obj = datetime.strptime(entry["date"], "%Y-%m-%d %H:%M:%S")
        else:
            date_obj = entry["date"]
        dates.append(date_obj.strftime("%Y-%m-%d"))
        closing_prices.append(entry["close"])

    fig, ax = plt.subplots()
    ax.plot(dates, closing_prices, label=ticker)
    ax.set_xlabel("Date")
    ax.set_ylabel("Closing Price")
    ax.legend()
    plt.xticks(rotation=45)

    img = io.BytesIO()
    plt.savefig(img, format="png", bbox_inches='tight')
    plt.close(fig)
    img.seek(0)
    return Response(img.getvalue(), mimetype='image/png')

if __name__ == "__main__":
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all available IPs (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
