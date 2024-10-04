from flask import Flask, render_template, request
from pymongo import MongoClient, errors
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection setup
try:
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://mongodb-9iyq:27017')
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client['StockData']
    ohlcv_collection = db['ohlcv_data']
    indicators_collection = db['indicators']
    # Test the connection
    client.admin.command('ping')
    logging.info("Successfully connected to MongoDB.")
except errors.ServerSelectionTimeoutError as err:
    logging.error(f"Error connecting to MongoDB: {err}")
    client = None  # Set client to None if connection fails

@app.route('/', methods=['GET'])
def index():
    if client is None:
        logging.error("MongoDB client is None, unable to proceed.")
        return render_template('error.html', message="Unable to connect to the database.")

    try:
        total_tickers = ohlcv_collection.distinct('ticker')
        total_tickers_count = len(total_tickers)
        logging.info(f"Total unique tickers in database: {total_tickers_count}")
    except Exception as e:
        logging.error(f"Error fetching data from MongoDB: {e}")
        return render_template('error.html', message="Error fetching data from the database.")

    query = {}

    logging.info(f"Request method: {request.method}")

    # Log the entire query parameters for debugging purposes
    logging.info(f"Query parameters received: {request.args}")

    # Prepare filters dictionary without the 'page' parameter
    filters = request.args.to_dict()
    current_page = int(filters.pop('page', 1))
    logging.info(f"Current page: {current_page}")

    # Ticker filter
    ticker = filters.get('ticker')
    if ticker:
        query['ticker'] = {'$regex': f'^{ticker}', '$options': 'i'}

    # RS Score filters
    rs_score_min = filters.get('rs_score_min')
    rs_score_max = filters.get('rs_score_max')
    if rs_score_min or rs_score_max:
        rs_score_query = {}
        if rs_score_min:
            rs_score_query['$gte'] = float(rs_score_min)
        if rs_score_max:
            rs_score_query['$lte'] = float(rs_score_max)
        query['rs_score'] = rs_score_query

    # New RS High filter
    new_rs_high = filters.get('new_rs_high')
    if new_rs_high == 'true':
        query['new_rs_high'] = True
    elif new_rs_high == 'false':
        query['new_rs_high'] = False

    # Buy Signal filter
    buy_signal = filters.get('buy_signal')
    if buy_signal == 'true':
        query['buy_signal'] = True
    elif buy_signal == 'false':
        query['buy_signal'] = False

    # Mansfield RS Min filter
    mansfield_rs_min = filters.get('mansfield_rs_min')
    if mansfield_rs_min:
        query['mansfield_rs'] = {'$gte': float(mansfield_rs_min)}

    # Stage filter
    stage = filters.get('stage')
    if stage:
        query['stage'] = int(stage)

    # Log the query being used for filtering
    logging.info(f"Generated query for filtering: {query}")

    # Pagination logic
    items_per_page = 20
    skip_items = (current_page - 1) * items_per_page
    logging.info(f"Items per page: {items_per_page}, skip items: {skip_items}")

    try:
        # Fetch stocks using the query with pagination
        rs_high_and_minervini_stocks = list(indicators_collection.find(
            query,
            {
                "ticker": 1,
                "rs_score": 1,
                "minervini_criteria.minervini_score": 1,
                "new_rs_high": 1,
                "buy_signal": 1,
                "mansfield_rs": 1,
                "stage": 1,
                "_id": 0
            }
        ).sort("rs_score", -1).skip(skip_items).limit(items_per_page))

        # Log the number of stocks fetched
        logging.info(f"Number of stocks fetched: {len(rs_high_and_minervini_stocks)}")

        total_results = indicators_collection.count_documents(query)
        total_pages = (total_results + items_per_page - 1) // items_per_page  # Calculate total pages

        # Calculate the range of pages to display
        page_range = range(max(1, current_page - 2), min(total_pages, current_page + 2) + 1)

        logging.info(f"Total results: {total_results}, total pages: {total_pages}")
    except Exception as e:
        logging.error(f"Error querying MongoDB: {e}")
        return render_template('error.html', message="Error fetching data from the database.")

    return render_template('index.html',
                           total_tickers=total_tickers_count,
                           rs_high_and_minervini_stocks=rs_high_and_minervini_stocks,
                           current_page=current_page,
                           total_pages=total_pages,
                           page_range=page_range,
                           filters=filters)

# Test route for error page
@app.route('/test-error')
def test_error():
    return render_template('error.html', message="This is a test error message.")

if __name__ == '__main__':
    # Use the PORT environment variable if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)