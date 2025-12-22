import sqlite3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/purchase/<item_num>', methods=['POST'])
def orders(item_num):
    base_url = 'http://localhost:5050/query'
    try:
        # Query the catalog service to check stock
        response = requests.get(base_url, params={'item_number': item_num})
        if not response.ok:
            return jsonify({'message': f'Failed to fetch catalog item {item_num}'}), 404

        data = response.json()
        if data['quantity'] <= 0:
            return jsonify({'message': "This book is out of stock"}), 406

        # Proceed to update stock in catalog
        update_response = requests.patch('http://localhost:5050/update',
                                         json={'stock_count': -1, 'item_number': item_num})

        print(f"Update Response: {update_response.json()}")  # Debugging line
        if  update_response.json() == {"message": f"Updated record {item_num} successfully"}:
            # Insert order into DB
            con = get_db_connection()
            con.cursor().execute("INSERT INTO 'order' (item_number) VALUES (?)", (item_num,))
            con.commit()
            return jsonify({'message': f'Successfully purchased item {item_num}'}), 200
        else:
            return jsonify({'message': f'Failed to update catalog for item {item_num}'}), 404
    except requests.RequestException as e:
        return jsonify({'message': f'Successfully purchased item {item_num}'}), 200


if __name__ == '__main__':
    # Ensure database is set up
    conn = sqlite3.connect('orders.db')
    conn.execute('CREATE TABLE IF NOT EXISTS "order" (id INTEGER PRIMARY KEY, item_number INTEGER)')
    conn.close()

    app.run(debug=False, host='0.0.0.0', port=5061)
