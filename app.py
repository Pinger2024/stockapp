from flask import Flask, render_template, request, jsonify, Response
from pymongo import MongoClient, errors
from datetime import datetime, timedelta
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
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client['StockData']
    ohlcv_collection = db['ohlcv_data']
    indicators_collection = db['indicators']
    sector_trends_collection = db['sector_trends']
    client.admin.command('ping')
    logging.info("Successfully connected to MongoDB.")
except errors.ServerSelectionTimeoutError as err:
    logging.error(f"Error connecting to MongoDB: {err}")
    client = None

# Helper functions for pagination and error handling
def handle_pagination(query, collection, page, items_per_page):
    skip_items = (page - 1) * items_per_page
    total_results = collection.count_documents(query)
    results = list(collection.find(query).skip(skip_items).limit(items_per_page))
    total_pages = (total_results + items_per_page - 1) // items_per_page
    return results, total_results, total_pages

@app.route('/')
def index():
    return render_template('index.html')

# Fetch stocks with pagination and filtering by RS score
@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    if client is None:
        return jsonify({"error": "Unable to connect to the database."}), 500

    try:
        filters = request.args.to_dict()
        page = int(filters.pop('page', 1))
        items_per_page = 20

        query = {}
        rs_score_min = float(filters.get('rs_score_min', 50))
        query['rs_score'] = {"$gte": rs_score_min}

        stocks, total_results, total_pages = handle_pagination(query, indicators_collection, page, items_per_page)

        return jsonify({
            "stocks": stocks,
            "current_page": page,
            "total_pages": total_pages,
            "total_results": total_results
        })

    except Exception as e:
        logging.error(f"Error querying MongoDB: {e}")
        return jsonify({"error": "Error fetching data from the database."}), 500

# Route to download tickers without sector information
@app.route('/download-no-sector', methods=['GET'])
def download_no_sector_tickers():
    if client is None:
        return jsonify({"error": "Unable to connect to the database."}), 500

    try:
        tickers_no_sector = indicators_collection.find({"sector": {"$exists": False}}).distinct("ticker")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Ticker'])

        for ticker in tickers_no_sector:
            writer.writerow([ticker])

        output.seek(0)

        return Response(
            output,
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=tickers_no_sector.csv"}
        )

    except Exception as e:
        logging.error(f"Error generating CSV: {e}")
        return jsonify({"error": "Error generating CSV file."}), 500

# Fetch sector trends with date filters
@app.route('/api/sector-trends', methods=['GET'])
def get_sector_trends():
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else datetime.now() - timedelta(days=90)
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else datetime.now()

        trends = list(sector_trends_collection.find({"date": {"$gte": start_date, "$lte": end_date}}).sort("date", 1))

        response = {}
        for trend in trends:
            sector = trend.get('sector')
            date = trend.get('date')
            rs_score = trend.get('average_rs', None)

            if sector and rs_score:
                if sector not in response:
                    response[sector] = {'dates': [], 'rs_scores': []}
                response[sector]['dates'].append(date.strftime('%Y-%m-%d'))
                response[sector]['rs_scores'].append(rs_score)

        return jsonify(response)
    except Exception as e:
        logging.error(f"Error fetching sector trends: {e}")
        return jsonify({"error": "Error fetching sector trends"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
