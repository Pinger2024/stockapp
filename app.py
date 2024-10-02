from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection (hardcoded)
client = MongoClient("mongodb://mongodb-9iyq:27017")
db = client['StockData']
ohlcv_collection = db['ohlcv_data']
indicator_collection = db['indicators']

@app.route("/", methods=["GET", "POST"])
def index():
    tickers_count = ohlcv_collection.distinct("ticker")
    search_result = None
    stocks = None
    rs_score = None
    
    if request.method == "POST":
        ticker = request.form["ticker"].upper()
        search_result = ohlcv_collection.find_one({"ticker": ticker})
        if search_result:
            # Fetch OHLCV data
            stocks = list(ohlcv_collection.find({"ticker": ticker}))
            
            # Fetch RS Score from indicators collection
            indicator = indicator_collection.find_one({"ticker": ticker})
            if indicator:
                rs_score = indicator.get("rs_63")  # Example RS score (use the correct period as needed)
        else:
            search_result = "not_found"
    
    return render_template("index.html", tickers_count=len(tickers_count), search_result=search_result, stocks=stocks, rs_score=rs_score)

if __name__ == "__main__":
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all available IPs (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
