from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB setup
client = MongoClient('your_mongodb_connection_string')
db = client['StockData']
indicators_collection = db['indicators']

@app.route('/', methods=['GET', 'POST'])
def index():
    query = {}
    
    if request.method == 'POST':
        # Ticker filter
        ticker = request.form.get('ticker')
        if ticker:
            query['ticker'] = ticker.upper()  # Assume tickers are stored in uppercase

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
            query['mansfield_rs'] = {'$gte': float(mansfield_rs_min)}

        # Stage filter
        stage = request.form.get('stage')
        if stage:
            query['stage'] = int(stage)

    # Query the database
    stocks = indicators_collection.find(query)

    return render_template('index.html', total_tickers=indicators_collection.count_documents({}), rs_high_and_minervini_stocks=stocks)

if __name__ == '__main__':
    app.run(debug=True)
