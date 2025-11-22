import sqlite3

import requests as requests
from flask import Flask, jsonify


def get_db_connection():
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)


@app.route('/purchase/<item_num>', methods=['POST'])
def orders(item_num):
    base_url = 'http://172.17.0.1:5050/query'
    response = requests.get(base_url, params={'item_number': item_num})

    if response.ok and response.status_code == 200:
        data = response.json()
        if data['quantity'] <= 0:
            return jsonify({'message': "this book is out of stock"}), 406

        response = requests.patch('http://172.17.0.1:5050/update', json={'stock_count': -1
            , 'item_number': item_num})
        if response.json() == {"message": f"Updated record {item_num} successfully"}:
            con = get_db_connection()
            con.cursor().execute("Insert Into 'order' (item_number) values (" + item_num + ")")
            con.commit()
            return jsonify({'message': f'successfully purchased item {item_num}'}), 200
        else:
            return jsonify({'message': f'failed to  purchase item {item_num}'}), 404
    else:
        return jsonify({'message': f'failed to  purchase item {item_num}'}), 404


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
