from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://mongodb-9iyq:27017')
db = client['StockData']
ohlcv_collection = db['ohlcv_data']

@app.route('/', methods=['GET', 'POST'])
def index():
    # Fetch ticker count
    tickers_count = len(ohlcv_collection.distinct("ticker"))

    # Handle search result
    search_result = None
    if request.method == 'POST':
        ticker = request.form['ticker'].upper()  # Get the input ticker and make it uppercase
        result = ohlcv_collection.find_one({"ticker": ticker})
        if result:
            search_result = ticker
        else:
            search_result = 'not_found'

    # Fetch a small subset of OHLCV data to display
    stocks = ohlcv_collection.find().limit(5)

    return render_template('index.html', tickers_count=tickers_count, stocks=stocks, search_result=search_result)

# Other routes (e.g., for plotting) remain unchanged

if __name__ == "__main__":
    app.run(debug=True)
