from flask import Flask, render_template, request
from pymongo import MongoClient
import datetime

app = Flask(__name__)

# MongoDB connection (hardcoded)
client = MongoClient("mongodb://mongodb-9iyq:27017")
db = client['StockData']
ohlcv_collection = db['ohlcv_data']
indicators_collection = db['indicators']

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
            rs_score = indicators_collection.find_one({"ticker": ticker})

    # Fetch highest RS Score stocks (for now, show test tickers)
    highest_rs_stocks = list(indicators_collection.find().sort("rs_score", -1).limit(5))

    # Fetch stocks making a new RS High (for now, mock condition)
    new_rs_high_stocks = list(indicators_collection.find({"new_rs_high": True}).limit(5))

    # Get the total number of unique tickers
    total_tickers = ohlcv_collection.distinct("ticker")
    
    return render_template('index.html', ohlcv_data=ohlcv_data, rs_score=rs_score,
                           highest_rs_stocks=highest_rs_stocks, new_rs_high_stocks=new_rs_high_stocks,
                           total_tickers=len(total_tickers), ticker=ticker)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
