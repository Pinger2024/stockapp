from flask import Flask, render_template, request, jsonify, Response
from pymongo import MongoClient, errors
import logging
import os
import csv
import io

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
    return render_template('index.html')

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    if client is None:
        return jsonify({"error": "Unable to connect to the database."}), 500

    try:
        total_tickers = ohlcv_collection.distinct('ticker')
        total_tickers_count = len(total_tickers)
        logging.info(f"Total unique tickers in database: {total_tickers_count}")
    except Exception as e:
        logging.error(f"Error fetching data from MongoDB: {e}")
        return jsonify({"error": "Error fetching data from the database."}), 500

    query = {}
    filters = request.args.to_dict()
    current_page = int(filters.pop('page', 1))

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

    # Pagination logic
    items_per_page = 20
    skip_items = (current_page - 1) * items_per_page

    try:
        # Fetch stocks using the query with pagination
        stocks = list(indicators_collection.find(
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

        total_results = indicators_collection.count_documents(query)
        total_pages = (total_results + items_per_page - 1) // items_per_page

        return jsonify({
            "stocks": stocks,
            "total_tickers": total_tickers_count,
            "current_page": current_page,
            "total_pages": total_pages,
            "total_results": total_results
        })

    except Exception as e:
        logging.error(f"Error querying MongoDB: {e}")
        return jsonify({"error": "Error fetching data from the database."}), 500

@app.route('/download-tickers', methods=['GET'])
def download_tickers():
    if client is None:
        return jsonify({"error": "Unable to connect to the database."}), 500

    try:
        # Fetch unique tickers from the database
        tickers = ohlcv_collection.distinct('ticker')

        # Create a CSV output in-memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Ticker'])  # Header

        for ticker in tickers:
            writer.writerow([ticker])

        output.seek(0)

        # Return CSV as a file download
        return Response(
            output,
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=tickers.csv"}
        )

    except Exception as e:
        logging.error(f"Error fetching or generating CSV: {e}")
        return jsonify({"error": "Error fetching or generating CSV file."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
