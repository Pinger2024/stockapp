from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb://mongodb-9iyq:27017")  # Replace with your MongoDB connection string
db = client['StockData']  # Connect to your MongoDB database
collection = db['comprehensive_data']

@app.route('/')
def index():
    # Query the MongoDB collection for the first 5 documents
    stock_data = list(collection.find().limit(5))

    # Count the number of distinct tickers in the collection
    unique_tickers_count = len(collection.distinct('ticker'))

    # Pass data to the HTML template to render on the page
    return render_template('index.html', stocks=stock_data, tickers_count=unique_tickers_count)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
