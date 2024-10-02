from flask import Flask, render_template, request
from pymongo import MongoClient
import matplotlib.pyplot as plt
import io
import base64
import os  # Add this import

# MongoDB connection (hardcoded)
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
        ticker = request.form.get("ticker")
        
        # Query for OHLCV data
        ohlcv_data = list(collection.find({"ticker": ticker}).sort("date", -1))
        print(f"OHLCV Data for {ticker}: {ohlcv_data}")  # Debugging output
        
        # Query for RS score
        rs_score = indicators_collection.find_one({"ticker": ticker})
        print(f"RS Score for {ticker}: {rs_score}")  # Debugging output

    return render_template("index.html", ohlcv_data=ohlcv_data, rs_score=rs_score, ticker=ticker)

@app.route("/plot")
def plot():
    ticker = request.args.get("ticker")
    ohlcv_data = list(collection.find({"ticker": ticker}).sort("date", 1))

    dates = [entry["date"].strftime("%Y-%m-%d") for entry in ohlcv_data]
    closing_prices = [entry["close"] for entry in ohlcv_data]

    fig, ax = plt.subplots()
    ax.plot(dates, closing_prices, label=ticker)
    ax.set_xlabel("Date")
    ax.set_ylabel("Closing Price")
    ax.legend()

    img = io.BytesIO()
    plt.xticks(rotation=45)
    plt.savefig(img, format="png")
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return f'<img src="data:image/png;base64,{plot_url}">'

if __name__ == "__main__":
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all available IPs (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
