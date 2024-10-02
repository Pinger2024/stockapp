from flask import Flask, render_template, request
from pymongo import MongoClient
import os
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# MongoDB connection (correct URI as per your setup)
client = MongoClient("mongodb://mongodb-9iyq:27017")
db = client['StockData']
ohlcv_collection = db['ohlcv_data']
indicators_collection = db['indicators']

@app.route("/", methods=['GET', 'POST'])
def index():
    total_tickers = ohlcv_collection.distinct("ticker")
    total_unique_tickers = len(total_tickers)

    ticker = None
    ohlcv_data = None
    rs_score = None

    if request.method == 'POST':
        ticker = request.form.get('ticker').upper()

        # Retrieve OHLCV data for the ticker
        ohlcv_data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", -1).limit(5))

        # Retrieve RS score for the ticker
        rs_score = indicators_collection.find_one({"ticker": ticker})

    return render_template("index.html", total_unique_tickers=total_unique_tickers, ohlcv_data=ohlcv_data, rs_score=rs_score)

@app.route("/plot")
def plot():
    ticker = request.args.get('ticker')

    # Get OHLCV data for plotting
    data = list(ohlcv_collection.find({"ticker": ticker}).sort("date", -1).limit(30))

    dates = [d['date'].strftime('%Y-%m-%d') for d in data]
    closing_prices = [d['close'] for d in data]

    fig, ax = plt.subplots()
    ax.plot(dates, closing_prices, label=ticker)
    ax.set_xlabel('Date')
    ax.set_ylabel('Closing Price')
    ax.legend()

    # Convert plot to PNG image and base64 encode it
    img = io.BytesIO()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return render_template("plot.html", plot_url=plot_url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
