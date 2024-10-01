import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, render_template, Response
from pymongo import MongoClient
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb://mongodb-9iyq:27017")  # Adjust the connection string as needed
db = client['StockData']

# Collections for OHLCV data and Meta Data
ohlcv_collection = db['ohlcv_data']
meta_data_collection = db['meta_data']

# Function to fetch OHLCV data for a ticker
def fetch_ohlcv_data(ticker, limit=100):
    query = {'ticker': ticker}
    projection = {'_id': 0, 'date': 1, 'open': 1, 'high': 1, 'low': 1, 'close': 1, 'volume': 1}
    stock_data = list(ohlcv_collection.find(query, projection).limit(limit))
    return pd.DataFrame(stock_data)

@app.route('/')
def index():
    # Query the OHLCV collection for the first 5 tickers' daily data
    stock_data = list(ohlcv_collection.find().limit(5))
    print("Stock Data:", stock_data)  # Debugging: Print the fetched stock data

    # Ensure stock data is found
    if stock_data:
        # Count the number of distinct tickers in the OHLCV collection
        unique_tickers_count = len(ohlcv_collection.distinct('ticker'))
        print("Unique Tickers Count:", unique_tickers_count)  # Debugging: Print the count
    else:
        unique_tickers_count = 0

    # Optionally, retrieve some meta data (e.g., financials) for the first ticker
    meta_data = meta_data_collection.find_one({'ticker': stock_data[0]['ticker']}) if stock_data else {}
    print("Meta Data:", meta_data)  # Debugging: Print the fetched meta data

    # Pass the OHLCV data, meta data, and ticker count to the template
    return render_template('index.html', stocks=stock_data, meta_data=meta_data, tickers_count=unique_tickers_count)

@app.route('/plot')
def plot():
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # Modify this list with your desired tickers

    # Create a new plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Fetch and plot data for each ticker
    for ticker in tickers:
        df = fetch_ohlcv_data(ticker)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            ax.plot(df['date'], df['close'], label=ticker)

    ax.set_title('Stock Prices for Selected Tickers')
    ax.set_xlabel('Date')
    ax.set_ylabel('Closing Price')
    ax.legend(loc='best')
    ax.grid(True)
    plt.xticks(rotation=45)

    # Convert plot to PNG image
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    plt.close(fig)

    # Return image response
    return Response(output.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
