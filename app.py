from flask import Flask, render_template, request, Response
from pymongo import MongoClient
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection setup
client = MongoClient("mongodb://mongodb-9iyq:27017")
db = client['StockData']
ohlcv_collection = db['ohlcv_data']
indicators_collection = db['indicators']

@app.route('/', methods=['GET', 'POST'])
def index():
    total_tickers = ohlcv_collection.distinct('ticker')
    total_tickers_count = len(total_tickers)
    query = {}

    logging.info(f"Request method: {request.method}")

    if request.method == 'POST':
        # Log the entire form data for debugging purposes
        logging.info(f"Form data received: {request.form}")

        # Ticker filter
        ticker = request.form.get('ticker')
        if ticker:
            query['ticker'] = ticker.upper()

        # RS Score filters
        rs_score_min = request.form.get('rs_score_min')
        rs_score_max = request.form.get('rs_score_max')
        if rs_score_min:
            query['rs_score'] = {'$gte': float(rs_score_min)}
        if rs_score_max:
            if 'rs_score' in query:
                query['rs_score']['$lte'] = float(rs_score_max)
            else:
                query['rs_score'] = {'$lte': float(rs_score_max)}

        # New RS High filter
        new_rs_high = request.form.get('new_rs_high')
        if new_rs_high == 'true':
            query['new_rs_high'] = True
        elif new_rs_high == 'false':
            query['new_rs_high'] = False

        # Buy Signal filter
        buy_signal = request.form.get('buy_signal')
        if buy_signal == 'true':
            query['buy_signal'] = True
        elif buy_signal == 'false':
            query['buy_signal'] = False

        # Mansfield RS Min filter
        mansfield_rs_min = request.form.get('mansfield_rs_min')
        if mansfield_rs_min:
            if 'mansfield_rs' in query:
                query['mansfield_rs']['$gte'] = float(mansfield_rs_min)
            else:
                query['mansfield_rs'] = {'$gte': float(mansfield_rs_min)}

        # Stage filter
        stage = request.form.get('stage')
        if stage:
            query['stage'] = int(stage)

    # Log the query being used for filtering
    logging.info(f"Generated query for filtering: {query}")

    # Pagination logic
    current_page = int(request.args.get('page', 1))
    items_per_page = 20
    skip_items = (current_page - 1) * items_per_page

    # Fetch stocks using the query with pagination
    rs_high_and_minervini_stocks = list(indicators_collection.find(
        query,
        {"ticker": 1, "rs_score": 1, "minervini_criteria.minervini_score": 1, "new_rs_high": 1, "buy_signal": 1, "mansfield_rs": 1, "stage": 1, "_id": 0}
    ).skip(skip_items).limit(items_per_page))

    total_results = indicators_collection.count_documents(query)
    total_pages = (total_results + items_per_page - 1) // items_per_page  # Calculate total pages

    return render_template('index.html',
                           total_tickers=total_tickers_count,
                           rs_high_and_minervini_stocks=rs_high_and_minervini_stocks,
                           current_page=current_page,
                           total_pages=total_pages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)